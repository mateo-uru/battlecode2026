"""Per-turn decisions of one champion: heal, fight, bank, regroup, lead or follow.

Group model: the acting leader (roles.Roster) picks a target and broadcasts its position (the anchor).
Followers help at the leader's camp (big camps: tank first, then everybody), otherwise farm small camps
of their own within the work radius of the leader or its target, and leash back when they drift off.
The leader captures alone so the gems collect in its bag (followers clear the capture tiles); rewards
of SPLIT_REWARD or more are split among everybody present. A leader with a heavy bag is escorted to
the altar. Altars whose approaches are occupied by camps (a "boss") are opened by killing those camps.
Phases: FARM (camps, gold, kills when favourable) and HUNT (isolated enemies nearby, golems/elks first).

phobos additions (docs/PLAN-phobos-deimos.md):
- Sparse maps (MapInfo.sparse): the leader keeps its buddy, the other champions roam a region each
  (k-means on the camp groups), farm what they can take alone and bank themselves; back to the group
  for SPLIT_PAUSE rounds after SPLIT_DEATHS roamer deaths.
- Big camps: need_for() champions take turns tanking (monsters hit the nearest champion); the leader
  holds BIG_HOLD tiles away until they are present; escape() steps a tank out before it dies.
- Gem-poor maps (MapInfo.poor): small bags are banked, fights are avoided while carrying.

Fuel: Python pays for every call (see mapinfo.py), so groups are summarised once (resumable setup),
tracked through one representative tile each, and allies are only snapshotted when needed.

UPGRADE: fighters doctrine: camp outside the enemy spawn and pick off respawning or lone champions.
UPGRADE: sweep the remaining parameters (radius, wait, bank thresholds) per map class in a tournament.
UPGRADE: golems are untested (no map has one): verify the tank-first protocol on a golem map.
"""
import math

import cambc
from cambc import game_map, vision, Team, ChampionState

import budget
import combat
import comms
import config
from comms import ALTAR, PREY, ESCORT
from mapinfo import MapInfo, INF
from nav import Nav, area, dist, single
from roles import Roster
from shop import Shop

FARM, HUNT = 0, 1
RECALLING, SUBMITTING, TELEPORTING = ChampionState.RECALLING, ChampionState.SUBMITTING_GEMS, ChampionState.TELEPORTING
ALIVE = ChampionState.ALIVE


class Group:
    __slots__ = ("unit", "rep", "tiles", "hp", "strength", "gems", "gold", "big", "monolith", "giant",
                 "near_giant", "respawn", "reward", "avoid")


class Brain:
    def __init__(self):
        me = cambc.me()
        self.info = info = MapInfo()
        self.doctrine = comms.read_draft(info)
        self.doc = config.DOCTRINES[self.doctrine]
        self.radius = self.doc["radius"]
        # Followers farm their own camps within this distance of the anchor; larger maps, wider net.
        self.sub_walk = config.SUB_MAX_WALK + (info.width + info.height) // config.SUB_WALK_MAP_DIV
        self.reach = self.radius + config.WORK_EXTRA + min(config.WORK_MAP_MAX, (info.width + info.height) // config.WORK_MAP_DIV)
        self.stun = self.doc["stun_chain"]
        self.nav = Nav(info)
        self.roster = Roster(me)
        self.role = self.roster.role()
        self.shop = Shop(self.role)
        self.comms = comms.Comms()
        # Split farming (sparse maps): the leader keeps its buddy, everybody else roams a region of its own.
        order = self.roster.order
        self.roamers = order[2 if config.SPLIT_BUDDY else 1:] if info.sparse and len(order) >= 3 else []
        self.region = None                      # set of camp group indices (set up after the groups)
        self.km = None                          # k-means state while the regions are computed
        self.roam_alive = {h: True for h in self.roamers}
        self.roam_deaths = []                   # rounds in which a roamer died
        self.split_pause = 0                    # everybody back to the group until this round
        self.tavi = self.roster.type[self.roster.me] == config.T_TAVI
        self.healer = any(a.is_heal() for a in me.abilities())
        self.range = me.attack_range()
        altars = game_map.altars()
        self.altars = altars.positions()
        self.bank_goals = cambc.Bitboard()
        for p in self.altars:
            self.bank_goals.draw_chebyshev(p, 1)
        self.groups = []
        self.index = {}
        self.kind_stats = {}
        self.camp_union = cambc.Bitboard()      # every camp spawn tile (camps stand there while alive)
        self.altar_guards = []                  # groups that occupy every altar approach (a "boss")
        self.bank_open = self.bank_goals
        self.setup_i = 0
        self.target = -1          # camp group index, or PREY/ALTAR codes while leading
        self.next_choice = 0
        self.wait = 0
        self.heal_mode = False
        self.awake_since = {}
        self.progress = (-1, INF, 0, 0)  # see _watch
        self.now = 0
        self._allies = None
        self._counts = None
        self.stats = {}           # turns per decision branch (config.STATS)
        self.blind, self.blind_target = 0, -1
        self.last_center = None
        self.sub_progress = (-1, INF, 0, 0)
        self.sub = -1             # follower's own camp near the anchor
        self.sub_until = 0
        self.hold = 0             # rounds the leader waited at a big camp for helpers
        self.escape_until, self.escape_from = 0, []
        self._dps, self._dps_round = 1.0, -1

    def setup(self):
        """Summarise camp groups, a few per turn if needed (resumes after a fuel yield)."""
        src = self.info.groups
        while self.setup_i < len(src):
            budget.check()
            unit = src[self.setup_i]
            g = Group()
            camps = unit.camps()
            g.unit, g.tiles, g.rep = unit, None, camps[0].spawn_position()
            g.hp = g.strength = 0.0
            kinds = set()
            for c in camps:
                self.camp_union.set(c.spawn_position())
                k = int(c.kind())
                s = self.kind_stats.get(k)
                if s is None:
                    b = c.base_stats()
                    s = self.kind_stats[k] = (b.base_health, b.base_strength)
                g.hp += s[0]
                g.strength += s[1]
                kinds.add(k)
            g.big = bool(kinds & set(config.BIG_CAMPS)) or g.strength >= config.BIG_STRENGTH
            g.monolith = 4 in kinds
            g.giant = bool(kinds & {4, 5})            # monolith or golem
            g.near_giant = False
            g.gems, g.gold = unit.gem_value(), unit.gold_value()
            g.respawn, g.reward, g.avoid = 0, False, 0
            self.groups.append(g)
            self.index[int(unit)] = self.setup_i
            self.setup_i += 1
        # Altars whose every approach tile is a camp spawn can only be used once those camps die.
        open_goals = self.bank_goals & ~self.nav.static & ~self.camp_union
        if open_goals.is_empty() and not self.bank_goals.is_empty():
            self.altar_guards = [i for i, g in enumerate(self.groups)
                                 if not (self.tiles(g) & self.bank_goals).is_empty()]
        else:
            self.bank_open = open_goals
        giants = [g for g in self.groups if g.giant]
        for g in self.groups:
            g.near_giant = not g.giant and any(dist(g.rep, o.rep) <= config.GIANT_RADIUS for o in giants)
        print(f"deimos ready rank={self.roster.rank} type={self.roster.type[self.roster.me]} role={self.role} "
              f"leader={self.roster.leader} doctrine={self.doctrine} groups={len(self.groups)} sparse={self.info.sparse} "
              f"poor={self.info.poor} region={sorted(self.region) if self.region is not None else None}", flush=True)
        return True

    def region_step(self):
        """One step of splitting the camp groups into regions for the roamers, per turn (Python fuel:
        a whole k-means does not fit one turn). k-means on positions, weighted by gems; regions ordered by
        walking distance from our spawn. Deterministic: every champion computes the same regions.
        A step only commits at its end, so a fuel yield simply repeats it next turn.
        UPGRADE: walking distances (walls), balance regions by total value."""
        k = self.region_count()
        n = len(self.groups)
        xs = [g.rep.x for g in self.groups]
        ys = [g.rep.y for g in self.groups]
        km = self.km
        if km is None:
            home = self.info.home_field
            hd = [home.get(g.rep) for g in self.groups]
            seeds = [min(range(n), key=lambda i: (hd[i], i))]
            near = [max(abs(xs[i] - xs[seeds[0]]), abs(ys[i] - ys[seeds[0]])) for i in range(n)]
            while len(seeds) < min(k, n):
                best, bi = -1, -1
                for i in range(n):
                    if near[i] > best:
                        best, bi = near[i], i
                seeds.append(bi)
                for i in range(n):
                    d = max(abs(xs[i] - xs[bi]), abs(ys[i] - ys[bi]))
                    if d < near[i]:
                        near[i] = d
            self.km = {"cent": [(xs[s], ys[s]) for s in seeds], "it": 0, "hd": hd}
            return
        cent = km["cent"]
        member = [0] * n
        for i in range(n):
            x, y = xs[i], ys[i]
            best, bj = 1 << 30, 0
            for j in range(len(cent)):
                d = max(abs(x - cent[j][0]), abs(y - cent[j][1]))
                if d < best:
                    best, bj = d, j
            member[i] = bj
        if km["it"] < config.KMEANS_ITERATIONS:
            sx, sy, sw = [0.0] * len(cent), [0.0] * len(cent), [0.0] * len(cent)
            for i in range(n):
                w = self.groups[i].gems + 1.0
                j = member[i]
                sx[j] += xs[i] * w
                sy[j] += ys[i] * w
                sw[j] += w
            km["cent"] = [(sx[j] / sw[j], sy[j] / sw[j]) if sw[j] else cent[j] for j in range(len(cent))]
            km["it"] += 1
            return
        hd = km["hd"]
        sets = [set(i for i in range(n) if member[i] == j) for j in range(len(cent))]
        sets.sort(key=lambda s: min((hd[i] for i in s), default=INF))
        while len(sets) < k:
            sets.append(set(range(n)))                # fewer camps than roamers: share the map
        self.region = sets[self.roamers.index(self.roster.me) % k]
        print(f"deimos region rank={self.roster.rank} r{self.now} groups={sorted(self.region)}", flush=True)

    def region_count(self):
        """Roamers share regions in pairs (ROAM_PAIRS): roamer i works region i % k, so with the draft order
        (bruisers first) a bruiser pairs with a caster."""
        n = len(self.roamers)
        return max(1, n // 2) if config.ROAM_PAIRS else n

    def partner_near(self):
        """A fellow roamer of the own region within sight: camps needing two champions are fine."""
        k = self.region_count()
        mine = self.roamers.index(self.roster.me) % k
        mates = [h for i, h in enumerate(self.roamers) if i % k == mine and h != self.roster.me]
        return any(int(a.unit) in mates and dist(a.pos, self.pos) <= config.ROAM_PAIR_DIST for a in self.allies)

    def roaming(self):
        return self.region is not None and self.now >= self.split_pause

    def tiles(self, g):
        if g.tiles is None:
            g.tiles = g.unit.spawn_tiles()
        return g.tiles

    # ------------------------------------------------------------------ observation
    @property
    def allies(self):
        if self._allies is None:
            self._allies = [a for a in combat.champions(Team.ALLY, full=False) if a.pos != self.pos]
        return self._allies

    def observe(self, me):
        self.hp, self.maxhp = me.health(), me.max_health()
        self.gems = me.gem_count()
        self.enemies = combat.champions(Team.ENEMY, self.info.enemy_home)
        self._allies = None
        self._counts = None
        if self.roamers:
            for h in self.roamers:
                a = self.roster.alive(h)
                if self.roam_alive[h] and not a:
                    self.roam_deaths.append(self.now)
                self.roam_alive[h] = a
            self.roam_deaths = [r for r in self.roam_deaths if self.now - r <= config.SPLIT_DEATH_WINDOW]
            if len(self.roam_deaths) >= config.SPLIT_DEATHS:
                self.split_pause, self.roam_deaths = self.now + config.SPLIT_PAUSE, []   # contested: regroup
        budget.check()
        visible = vision.visible_tiles()
        scan = self.groups if self.now % 5 == self.roster.rank % 5 else (
            [self.groups[self.target]] if 0 <= self.target < 250 else [])
        for g in scan:
            if not visible.is_set(g.rep):
                continue
            try:
                state = g.unit.state()
            except cambc.Error:
                continue
            if isinstance(state, game_map.CampGroupRespawning):
                g.respawn, g.reward = self.now + state.timer, False
            else:
                g.respawn, g.reward = 0, isinstance(state, game_map.CampGroupRewardAvailable)

    def power(self):
        me = cambc.me()
        return (me.strength() + me.focus() * 0.25) * (0.25 + 0.75 * self.hp / max(1.0, self.maxhp))

    def dps(self):
        if self._dps_round != self.now:          # engine getters cost fuel: once per round
            me = cambc.me()
            self._dps, self._dps_round = max(1.0, me.strength() * 1.1 + me.focus() * 0.3), self.now
        return self._dps

    def need_for(self, g):
        """Champions needed to clear big group g: strength * hp / (n * dps) <= n * maxhp * BIG_USABLE.

        Monsters hit the nearest champion, so tanks take turns (escape() steps a tank out in time).
        Uses this champion's damage and health as the team average. UPGRADE: real members' stats.
        """
        n2 = g.strength * g.hp / (self.dps() * self.maxhp * config.BIG_USABLE)
        return max(1, math.ceil(math.sqrt(n2)))

    def present(self, g):
        """This champion plus allies staged at group g: seen, or reported through the near mask
        (followers at the leader's big camp set it only when that close; walls block vision)."""
        seen = sum(1 for a in self.allies if dist(a.pos, g.rep) <= config.BIG_HOLD + 2)
        mask = self.comms.near_mask() & ~self.comms.healing_mask()
        told = sum(1 for h in self.roster.handles
                   if h != self.roster.me and self.roster.rank_of[h] < 6 and mask >> self.roster.rank_of[h] & 1)
        return 1 + max(seen, told)

    def phase(self):
        mine, theirs = cambc.global_submitted_gems(Team.ALLY), cambc.global_submitted_gems(Team.ENEMY)
        if self.now >= config.HUNT_ROUND or theirs >= config.HUNT_ENEMY_GEMS or theirs - mine >= config.HUNT_ENEMY_LEAD:
            return HUNT
        return FARM

    def healing_count(self):
        """Living members that are healing (dead ones are away for 60 rounds; nobody waits for them)."""
        return self.counts()[0]

    def counts(self):
        if self._counts is None:
            mask = self.comms.healing_mask()
            alive = [h for h in self.roster.handles if h == self.roster.me or self.roster.alive(h)]
            healing = sum(1 for h in alive if self.roster.rank_of[h] < 6 and mask >> self.roster.rank_of[h] & 1)
            self._counts = (healing, len(alive))
        return self._counts

    # ------------------------------------------------------------------ turn
    def turn(self):
        me = cambc.me()
        self.now = cambc.round_number()
        self.comms.read()
        rank = self.roster.rank
        state = me.state()
        if not state & ALIVE:
            self.comms.set_healing(rank, True)
            self.shop.run(me)
            self.target, self.heal_mode = -1, False
            return
        self.pos = me.position()
        self.at_home = self.info.home.is_set(self.pos)
        if self.at_home or self.tavi:
            self.shop.run(me)
        if state & RECALLING:
            self.comms.set_healing(rank, True)
            return
        if state & (SUBMITTING | TELEPORTING):
            return
        if self.setup_i < len(self.info.groups):
            self.setup()
        elif self.region is None and self.roster.me in self.roamers:
            self.region_step()
        if me.buffs().has_stun():
            return
        combat.begin_turn(me, bool(state & ChampionState.CAN_CAST))
        self.observe(me)
        self.mode = self.phase()
        self.leading = self.roster.acting_leader(self.comms.healing_mask()) == self.roster.me
        if self.at_home:
            self.comms.set_spawn_danger(sum(1 for e in self.enemies if dist(e.pos, self.pos) <= 6))
        self.report_prey()
        self.why = "?"
        try:
            if self.heal(me):
                self.why = "heal"
                self.comms.set_healing(rank, True)
                return
            self.comms.set_healing(rank, False)
            self.use_lock(me)
            if self.hazard(me):
                self.why = "hazard"
                return
            if self.escape(me):
                self.why = "escape"
                return
            if self.enemies and self.engage(me):
                self.why = "engage"
                return
            if self.bank(me):
                self.why = "bank"
                return
            if self.shop_trip(me):
                self.why = "shop"
                self.comms.set_healing(rank, True)
                return
            if self.regroup(me):
                self.why = "regroup"
                return
            if self.leading:
                self.why = "lead"
                self.lead(me)
            else:
                self.why = "follow"
                self.follow(me)
            if self.healer and self.allies:
                combat.support(me, self.allies, self.roster.leader)
        finally:
            if config.STATS:
                self.stats[self.why] = self.stats.get(self.why, 0) + 1
                if self.now % 500 == 0:
                    print(f"S r{self.now} k{rank} {sorted(self.stats.items(), key=lambda kv: -kv[1])}", flush=True)
            if config.TRACE and self.now % config.TRACE == 0:
                print(f"T r{self.now} k{rank} {self.pos.x},{self.pos.y} {self.why} lead={int(self.leading)} "
                      f"t={self.target} hp={int(self.hp)}/{int(self.maxhp)} g={self.gems} "
                      f"heal={self.comms.healing_mask():b} mode={self.mode} e={len(self.enemies)}"
                      + (self.trace_target() if self.leading else self.trace_sub()), flush=True)
            if self.leading and self.why != "heal":
                t = self.target
                code = t + 1 if 0 <= t < 250 else (t if t in (ALTAR, PREY, ESCORT) else 0)
                self.comms.write_anchor(me.position(), code, self.now)
            me.set_priority(200 if self.leading else self.roster.priority())

    def trace_target(self):
        t = self.target
        if not 0 <= t < 250:
            return ""
        g = self.groups[t]
        return f" rep={g.rep.x},{g.rep.y} d={dist(self.pos, g.rep)} rw={int(g.reward)} rs={g.respawn} wait={self.wait}"

    def trace_sub(self):
        if self.sub < 0:
            return ""
        g = self.groups[self.sub]
        return f" sub={self.sub} rep={g.rep.x},{g.rep.y} d={dist(self.pos, g.rep)} rw={int(g.reward)} rs={g.respawn}"

    # ------------------------------------------------------------------ health
    def heal(self, me):
        threshold = config.LEADER_HEAL_AT if self.role == "leader" and self.gems >= config.LEADER_CAREFUL_GEMS else config.HEAL_AT
        if self.at_home:
            if self.hp < self.maxhp * config.HEAL_UNTIL:
                if self.enemies:
                    combat.fight(me, self.enemies, (), defensive=True)
                return True
            self.heal_mode = False
            return False
        if not self.heal_mode and self.hp >= self.maxhp * threshold:
            return False
        if self.hp >= self.maxhp * config.HEAL_UNTIL:        # healed in the field (Willow)
            self.heal_mode = False
            return False
        self.heal_mode = True
        threats = [(e.pos, e.range + 1) for e in self.enemies if dist(e.pos, self.pos) <= e.range + 2]
        awake = vision.awake_camp_tiles() & area(self.pos, 6)
        for p in awake.positions():
            threats.append((p, 6))
        if not threats:
            try:
                me.recall()
                return True
            except cambc.Error:
                pass
        if self.enemies:
            combat.fight(me, self.enemies, (), defensive=True)
        if not self.nav.flee(me, threats, self.info.home_field):
            self.nav.step(me, self.info.home, key="home")
        return True

    def hazard(self, me):
        """Step out of reach of awake big camps (monolith, golem) that are not our fight."""
        if not config.HAZARD_FLEE:
            return False
        awake = vision.awake_camp_tiles() & area(self.pos, 6)
        if awake.is_empty():
            return False
        mine = self.target if self.leading else self.sub
        threats = []
        for p in awake.positions():
            try:
                c = vision.camp_at(p)
                if c.strength() < 120 or 0 <= mine < 250 and self.index.get(int(c.camp_group())) == mine:
                    continue
                if dist(p, self.pos) <= c.attack_range() + 1:
                    threats.append((p, c.attack_range() + 1))
            except cambc.Error:
                continue
        if not threats:
            return False
        return self.nav.flee(me, threats, self.info.home_field)

    def escape(self, me):
        """Step out of reach when visible awake camps would kill us within ESCAPE_TURNS (walking out takes
        rounds); the next champion in line takes the hits, so this is also the tank rotation.
        Never while enemy champions are visible (engage/heal decide). No guessing about camps hidden in
        bushes: enemies hiding there caused false alarms (fading A/B 33:37 -> 37:33 vs a hunter bot).
        """
        if self.enemies:
            return False
        holding = self.now < self.escape_until
        if not holding and self.hp >= self.maxhp * 0.75:
            return False
        awake = vision.awake_camp_tiles() & area(self.pos, 7)
        if awake.is_empty() and not holding:
            return False
        incoming, threats = 0, []
        for p in awake.positions():
            try:
                c = vision.camp_at(p)
                r = c.attack_range()
                if dist(p, self.pos) <= r + 1:
                    incoming += c.strength()
                    threats.append((p, r + 1))
            except cambc.Error:
                continue
        if not holding:
            if not threats or self.hp >= incoming * config.ESCAPE_TURNS:
                return False
            self.escape_until, self.escape_from = self.now + config.ESCAPE_HOLD, threats
        if self.nav.flee(me, threats or self.escape_from, self.info.home_field):
            return True
        self.fight_nearby(me)              # out of reach (or cornered): ranged champions keep hitting
        return True

    def shop_trip(self, me):
        """Recall to spend a large purse while the team is otherwise complete."""
        if self.gems >= 10 or self.enemies or self.healing_count():
            return False
        # A trip home costs the walk back: demand more gold far from spawn, less when hurt anyway.
        gold = me.gold_count()
        need = config.SHOP_TRIP_GOLD + self.info.home_field.get(self.pos) * config.SHOP_TRIP_PER_TILE
        if self.hp < self.maxhp * config.SHOP_TRIP_HURT or self.shop.bought < config.SHOP_EARLY_SHARDS:
            need = min(need, config.SHOP_TRIP_HURT_GOLD)   # hurt anyway, or the first items pay most
        if gold < need:
            return False
        if self.leading and 0 <= self.target < 250 and self.groups[self.target].reward:
            return False
        try:
            me.recall()
            self.heal_mode = True
            return True
        except cambc.Error:
            return False

    def regroup(self, me):
        """Many members healing: meet them near spawn, unless enemies crowd it (roamers keep farming)."""
        if self.roaming():
            return False
        healing, alive = self.counts()
        if healing == 0 or healing < config.REGROUP_FRACTION * alive:
            return False
        if self.comms.spawn_danger() >= config.SPAWN_CROWDED:
            return False
        if self.leading:
            self.target = -1
        if not self.nav.step(me, self.info.home, key="home"):
            self.fight_nearby(me)
        return True

    # ------------------------------------------------------------------ champions
    def report_prey(self):
        for e in self.enemies:
            if all(o is e or dist(o.pos, e.pos) > 5 for o in self.enemies):
                self.comms.write_prey(e.pos, self.now)
                return

    def engage(self, me):
        pos = self.pos
        ours = self.power()
        for a in self.allies:
            if dist(a.pos, pos) <= 5:
                ours += a.power()
        theirs = sum(e.power() for e in self.enemies if dist(e.pos, pos) <= e.range + 3)

        def score(e):
            alone = all(o is e or dist(o.pos, e.pos) > 5 for o in self.enemies)
            return e.hp - e.gems * 3 - (400 if e.channel else 0) - (250 if alone else 0) + dist(pos, e.pos) * 35

        target = min(self.enemies, key=score)
        ratio = self.doc["hunt_engage"] if self.mode == HUNT else self.doc["engage"]
        if self.info.poor and self.gems >= config.POOR_CARRY:
            ratio *= config.POOR_ENGAGE          # gem-poor map: our bag is what the enemy is after
        burst = me.strength() * 1.4 + (me.focus() * 2 if combat._ready else 0)
        finish = target.hp <= burst and dist(pos, target.pos) <= max(self.range, 4)
        incoming = any(dist(pos, e.pos) <= e.range + 1 for e in self.enemies)
        if theirs > 0 and ours < theirs * ratio * 0.7 and not finish:
            if not incoming:
                return False
            combat.fight(me, self.enemies, self.allies, self.roster.leader, defensive=True)
            self.nav.flee(me, [(e.pos, e.range + 1) for e in self.enemies], self.info.home_field)
            return True
        if not (ours >= theirs * ratio or finish or incoming):
            return False
        if self.mode == FARM and not finish and not incoming:
            alone = all(o is target or dist(o.pos, target.pos) > 5 for o in self.enemies)
            mates = sum(1 for a in self.allies if dist(a.pos, pos) <= 5) + 1
            foes = sum(1 for e in self.enemies if dist(e.pos, pos) <= 7)
            if not alone and mates < foes:
                return False
        # Stay with the group in FARM: no long chases away from the anchor.
        anchor, _ = self.comms.anchor(self.now)
        if (self.mode == FARM and not incoming and not finish and anchor is not None and not self.roaming()
                and dist(target.pos, anchor) > self.radius + 5):
            return False
        acted = combat.fight(me, self.enemies, self.allies, self.roster.leader, stun_chain=self.stun)
        if me.can_move() and dist(pos, target.pos) > self.range:
            if self.nav.step(me, area(target.pos, self.range), dash=True):
                self.pos = me.position()
                acted = combat.fight(me, combat.champions(Team.ENEMY, self.info.enemy_home), self.allies,
                                     self.roster.leader, stun_chain=self.stun) or True
        return acted                      # nothing hit, nothing reached (wall, hole): carry on farming

    def use_lock(self, me):
        """Lock an altar where an enemy is tributing (cancels the channel)."""
        if not self.enemies or not any(e.channel for e in self.enemies) or not Shop.has_lock(me):
            return
        for e in self.enemies:
            if not e.channel:
                continue
            for p in self.altars:
                if dist(p, e.pos) <= 1 and dist(p, self.pos) <= 2 and not vision.has_altar_lock(p):
                    try:
                        me.consumables()[int(cambc.ConsumableType.ALTAR_LOCK)].use(p)
                    except cambc.Error:
                        pass
                    return

    # ------------------------------------------------------------------ gems
    def altar_usable(self):
        """False while guard camps stand on every altar approach."""
        if not self.altar_guards:
            return True
        return any(self.groups[i].respawn > self.now or self.groups[i].reward for i in self.altar_guards)

    def bank(self, me):
        if self.gems == 0 or not self.altars or not self.altar_usable():
            return False
        field = self.nav.field("bank", self.bank_open)
        d = field.get(self.pos)
        if d >= INF:
            return False
        need = min(config.BANK_MAX, config.BANK_MIN + d * config.BANK_PER_TILE)
        if self.roaming():
            # Roamers carry alone: small bags (ladder winners on sparse maps tribute ~29 gems at a time).
            need = min(need, config.ROAM_BANK_MIN + d * config.ROAM_BANK_PER_TILE)
        if not self.leading and not self.roaming():
            anchor, code = self.comms.anchor(self.now)
            if not (code in (ALTAR, ESCORT) and anchor is not None and dist(anchor, self.pos) <= self.radius + 4):
                need = max(need, config.BANK_FOLLOWER)
        if self.info.poor and d <= config.POOR_BANK_DIST:
            need = min(need, config.POOR_BANK)   # gem-poor map: small bags, few to lose
        endgame = self.now + d + math.ceil(self.gems / 10) + 15 >= cambc.constants.MAX_ROUNDS
        winning = cambc.global_submitted_gems(Team.ALLY) + self.gems >= cambc.constants.WINNING_GEMS
        if not (self.gems >= need or endgame or winning or d <= 1):
            return False
        if self.leading:
            self.target = ESCORT if self.gems >= config.ESCORT_BAG else ALTAR
        if d == 0:
            for altar in self.altars:
                if dist(altar, self.pos) <= 1:
                    try:
                        me.submit_gems(altar)     # against an enemy lock this becomes an attack on it
                        return True
                    except cambc.Error as e:
                        if config.TRACE:
                            print(f"bank fail r{self.now} {self.pos} altar={altar} {e!r}", flush=True)
                        continue
            self.fight_nearby(me)
            return True
        if not self.nav.step(me, self.bank_open, key="bank"):
            if config.TRACE and self.now % 10 == 0:
                f = self.nav.field("bank", self.bank_open)
                moves = [(m.x, m.y) for m in f.next_moves_from(self.pos)]
                print(f"bank stuck r{self.now} {self.pos} d={d} moves={moves} can_move={me.can_move()}", flush=True)
            self.fight_nearby(me)
        return True

    # ------------------------------------------------------------------ camps
    def choose(self, me, center=None, limit=0, exclude=-1, only=None, walk=None, crew=1):
        """Best camp group by value per turn spent (nameless' formula plus group strength).

        Leader: whole map, with REGION_SHARE of nearby camps added (walk to farming regions).
        Follower (center = tuple of points): only small groups within `limit` of one of them, solo strength.
        """
        budget.check()
        from_me = cambc.DistanceField()
        from_me.compute(self.nav.static, single(self.pos), cambc.Bitboard())
        healing, alive = self.counts()
        group_mode = self.leading and center is None
        active = max(1, alive - healing) if group_mode else crew
        if group_mode and self.roamers and self.now >= self.split_pause:
            active = min(active, self.roster.size - len(self.roamers))   # the roamers are elsewhere
        team_dps = self.dps() * active
        team_hp = self.maxhp * active * 0.8 if group_mode else self.hp
        gold_w = config.GOLD_WEIGHT * (1.3 if self.mode == FARM else 0.7)
        hunt = self.mode == HUNT
        prepared = 0.7 if self.shop.bought >= 5 else 1.0
        now, rng, keep = self.now, self.range, (self.target if center is None else self.sub)
        scored = []
        for i, g in enumerate(self.groups):
            if g.avoid > now or i == exclude or g.monolith and (team_dps < config.MONOLITH_MIN_DPS or not group_mode):
                continue
            if only is not None and i not in only:
                continue
            if center is not None and (all(dist(c, g.rep) > limit for c in center)
                                       or g.big and not g.reward and self.need_for(g) > crew):
                continue
            d = from_me.get(g.rep)
            if d >= INF or center is not None and d > (self.sub_walk if walk is None else walk):
                continue
            travel = max(0, d - rng)
            wait = g.respawn - now - travel
            if wait > 15:
                continue
            clear = 0.0 if g.reward else g.hp / team_dps
            if g.big:
                # The nearest champion takes every hit: only as many champions as are coming can rotate.
                if not g.reward and self.need_for(g) > active and i not in self.altar_guards:
                    continue
                # Damage taken while clearing; rotating the tank spreads it but does not reduce it.
                taken = g.strength * clear * (config.GROUP_DAMAGE * prepared if active > 1 else 1.0)
                if taken > team_hp * config.MAX_DAMAGE_SHARE:
                    continue
            else:
                # Small camps: nameless' estimate, no cutoff (a retreat to heal is cheaper than idling).
                taken = g.strength * clear * 0.45 * prepared
            danger = max(0.1, 1 - taken / team_hp * 0.6)
            gems = g.gems * config.GOLEM_HUNT_BONUS if hunt and g.big else g.gems
            v = (3 * gems + gold_w * g.gold + 12) / (travel + max(0, wait) + clear + 7) * danger
            if g.near_giant:
                v *= config.GIANT_NEIGHBOUR      # a fight there can wake the giant (ours or theirs)
            if i in self.altar_guards:
                v *= config.GUARD_BONUS          # the only way to the altar
            if i == keep:
                v *= config.CLAIM_STICKY
            scored.append((v, i))
        if not scored:
            return -1
        scored.sort(reverse=True)
        if group_mode and len(scored) > 1:
            # Farming regions: a camp surrounded by other camps keeps the whole group busy.
            reach = self.reach
            best, chosen = 0.0, -1
            for v, i in scored[:5]:
                rep = self.groups[i].rep
                v += config.REGION_SHARE * sum(o for o, j in scored if j != i and dist(self.groups[j].rep, rep) <= reach)
                if v > best:
                    best, chosen = v, i
            return chosen
        return scored[0][1]

    def watch(self):
        """Give up on targets that make no progress for 30 rounds (unreachable, contested)."""
        t = self.target
        if not 0 <= t < 250:
            return
        self.progress = self._watch(t, self.progress)
        if self.progress[0] < 0:
            self.target = -1

    def _watch(self, t, state):
        """(target, best distance, gems, round of last progress); target -1 = gave up."""
        d = dist(self.pos, self.groups[t].rep)
        old_t, best, gems, since = state
        g = self.groups[t]
        fighting = d <= 6 and not (vision.awake_camp_tiles() & self.tiles(g)).is_empty()
        if old_t != t or d < best or self.gems > gems or g.reward and d <= 1 or fighting:
            return (t, min(d, best) if old_t == t else d, self.gems, self.now)
        if self.now - since >= config.STUCK_TURNS:
            self.groups[t].avoid = self.now + 40
            return (-1, INF, 0, self.now)
        return (old_t, best, self.gems, since)

    def lead(self, me, solo=False):
        t = self.target
        g = self.groups[t] if 0 <= t < 250 else None
        if (g is None and t != PREY or t in (ALTAR, ESCORT) or self.now >= self.next_choice
                or g is not None and (g.avoid > self.now or g.respawn > self.now + 15)):
            if self.mode == HUNT and not solo and self.hunt(me):
                return
            t = self.choose(me)
            if t != self.target:
                self.hold = 0
            self.target = t
            self.next_choice = self.now + 10
        if self.target == PREY:
            if not self.hunt(me):
                self.target = -1
            return
        if not 0 <= self.target < 250:
            if config.LONE_HOME and self.target < 0 and not self.at_home:
                self.nav.step(me, self.info.home, key="home")    # nothing safe to do: wait for the team
            self.fight_nearby(me)
            return
        self.watch()
        if self.target < 0:
            return
        g = self.groups[self.target]
        # Big camps: hold outside reach until enough champions are here to take turns tanking.
        if not solo and g.big and not g.reward and dist(self.pos, g.rep) <= config.BIG_HOLD + 1:
            awake = not (vision.awake_camp_tiles() & self.tiles(g)).is_empty()
            need = self.need_for(g)
            guard = self.target in self.altar_guards
            if guard:
                # The only way to score: chip it down with half the team (monsters do not heal while
                # alive; escape() keeps the tanks alive) and never give up on it.
                healing, alive = self.counts()
                need = min(need, max(1, (alive - healing + 1) // 2))
            if not awake and self.present(g) < need and not (guard and self.hold >= config.BIG_WAIT_TURNS):
                if self.hold >= config.BIG_WAIT_TURNS:
                    g.avoid, self.target, self.hold = self.now + 40, -1, 0
                    self.fight_nearby(me)
                    return
                self.why = "l-hold"
                self.hold += 1
                if dist(self.pos, g.rep) < config.BIG_HOLD:
                    self.nav.step(me, area(g.rep, config.BIG_HOLD + 1) & ~area(g.rep, config.BIG_HOLD - 1))
                else:
                    self.fight_nearby(me)
                return
        # Wait for stragglers before walking into a camp that needs the whole group.
        if not solo and g.big:
            healing, alive = self.counts()
            expected = max(0, alive - healing - 1)
            if self.roamers and self.now >= self.split_pause:
                expected = min(expected, self.roster.size - len(self.roamers) - 1)   # roamers are elsewhere
            mask = self.comms.near_mask() & ~self.comms.healing_mask()  # set by followers (vision is not shared)
            near = sum(1 for h in self.roster.handles
                       if h != self.roster.me and self.roster.rank_of[h] < 6 and mask >> self.roster.rank_of[h] & 1)
            if near < min(expected, 2) and dist(self.pos, g.rep) > 5 and self.wait < config.LEADER_WAIT_TURNS:
                self.why = "l-wait"
                self.wait += 1
                self.fight_nearby(me)
                return
            self.wait = max(0, self.wait - 2) if near < expected else 0
        self.work(me, self.target, tank=True, capture=True)

    def hunt(self, me):
        """HUNT: walk the group to the last isolated enemy anyone has seen."""
        prey = self.comms.prey(self.now)
        healing, alive = self.counts()
        if prey is None or dist(prey, self.pos) > config.PREY_RADIUS or alive - healing < 2:
            return False
        if dist(prey, self.pos) <= 2:
            return False                         # arrived, nothing to fight: the trail is cold
        self.target = PREY
        self.nav.step(me, area(prey, 1))
        return True

    def follow(self, me):
        if self.roaming() and self.roam(me):
            return
        self.follow_group(me)

    def roam(self, me):
        """Sparse maps: farm and bank alone in the own region; join the leader's big camp when close."""
        anchor, code = self.comms.anchor(self.now)
        lead_t = code - 1 if anchor is not None and 1 <= code <= len(self.groups) else -1
        self.comms.set_near(self.roster.rank, False)
        if lead_t >= 0:
            g = self.groups[lead_t]
            if (g.big and not g.reward and dist(anchor, g.rep) <= config.BIG_HOLD + 1
                    and dist(self.pos, g.rep) <= config.ROAM_HELP):
                self.why = "r-big"
                self.comms.set_near(self.roster.rank, dist(self.pos, g.rep) <= config.BIG_HOLD + 2)
                self.work(me, lead_t, tank=False, capture=False)
                return True
        s = self.sub
        if (s < 0 or self.now >= self.sub_until or self.groups[s].avoid > self.now
                or self.groups[s].respawn > self.now + 10):
            crew = 2 if self.partner_near() else 1
            s = self.choose(me, center=(self.pos,), limit=INF, only=self.region, walk=INF, crew=crew)
            if s < 0:
                s = self.choose(me, center=(self.pos,), limit=config.ROAM_ANY, walk=INF, crew=crew)
            self.sub, self.sub_until = s, self.now + 8
        if s >= 0:
            self.sub_progress = self._watch(s, self.sub_progress)
            if self.sub_progress[0] < 0:
                self.sub = s = -1
        if s >= 0:
            self.why = "r-farm"
            self.work(me, s, tank=True, capture=True)
            return True
        if self.cluster(me, self.pos):
            self.why = "r-cluster"
            return True
        return False                              # nothing alone: back to the group

    def follow_group(self, me):
        anchor, code = self.comms.anchor(self.now)
        reach = self.reach
        lead_t = code - 1 if anchor is not None and 1 <= code <= len(self.groups) else -1
        # The group works around where the leader is going, not where it currently stands.
        center = self.groups[lead_t].rep if lead_t >= 0 else anchor
        leader = anchor                              # the leader's real position (anchor may be redirected)
        if lead_t >= 0:
            self.last_center = center
        elif code == ALTAR and self.last_center is not None:
            anchor = center = self.last_center      # the leader banks alone; keep farming here
        near = anchor is not None and (dist(self.pos, anchor) <= reach or dist(self.pos, center) <= reach)
        self.comms.set_near(self.roster.rank, near)
        if anchor is None:
            self.lead(me, solo=True)            # no leader broadcast: farm alone
            return
        if lead_t >= 0:
            g = self.groups[lead_t]
            if g.reward and g.gems >= config.SPLIT_REWARD and dist(self.pos, g.rep) <= self.reach:
                # A big reward is split among everyone present: smaller bags tribute fast and die cheap.
                self.why = "f-split"
                if not self.tiles(g).is_set(self.pos):
                    self.nav.step(me, self.tiles(g), key=("g", lead_t))
                return
            if g.reward and dist(anchor, g.rep) <= config.HANDOFF + 2 and self.tiles(g).is_set(self.pos):
                self.why = "f-yield"                     # the leader captures: clear the tiles
                self.nav.step(me, area(self.pos, 2) & ~self.tiles(g))
                return
            if g.big and dist(anchor, g.rep) <= config.BIG_HOLD + 1 and not g.reward:
                # The leader is at (or holding before) its big camp: everybody comes, the tank opens.
                self.why = "f-big"
                self.comms.set_near(self.roster.rank, dist(self.pos, g.rep) <= config.BIG_HOLD + 2)
                self.work(me, lead_t, tank=False, capture=False)
                return
            if dist(anchor, g.rep) <= 5 and not g.reward:
                self.why = "f-help"                      # the leader is at its small camp: clear it
                self.work(me, lead_t, tank=True, capture=False)
                return
        # Leash back to the group; with a camp of its own (paths bend around walls) only when far off.
        slack = config.LEASH_SLACK if self.sub >= 0 else 2
        if not near and dist(self.pos, center) > reach + slack and dist(self.pos, anchor) > reach + slack:
            self.why = "f-leash"
            self.sub = -1
            if not self.nav.step(me, area(center, self.radius)):
                self.fight_nearby(me)
            return
        s = self.sub
        if (s < 0 or self.now >= self.sub_until or self.groups[s].avoid > self.now
                or self.groups[s].respawn > self.now + 10
                or dist(self.groups[s].rep, center) > reach and dist(self.groups[s].rep, anchor) > reach):
            self.sub = s = self.choose(me, center=(anchor, center), limit=reach)
            self.sub_until = self.now + 8
        if s >= 0:
            self.sub_progress = self._watch(s, self.sub_progress)
            if self.sub_progress[0] < 0:
                self.sub = s = -1
        if s >= 0:
            self.why = "f-sub"
            # Gems belong in the leader's bag when it is right there; otherwise capture yourself.
            capture = s != lead_t or dist(anchor, self.groups[s].rep) > config.HANDOFF
            self.work(me, s, tank=True, capture=capture)
            return
        if self.cluster(me, anchor):
            self.why = "f-cluster"
            return
        self.why = "f-idle"
        if dist(self.pos, leader) <= 1:
            self.nav.step(me, area(leader, 3) & ~area(leader, 1))   # make way
            return
        if dist(self.pos, center) > self.radius:
            goals = area(center, self.radius) & ~area(leader, 1)   # leave the leader room
            if lead_t >= 0:
                goals &= ~self.tiles(self.groups[lead_t])   # never park on the leader's capture tiles
            if not self.nav.step(me, goals):
                self.fight_nearby(me)
        else:
            self.fight_nearby(me)

    def cluster(self, me, anchor):
        """Followers grab free clusters next to the group."""
        near = vision.camp_tiles() & area(self.pos, 2)
        if near.is_empty():
            return False
        for p in near.positions():
            if dist(p, anchor) > self.radius + config.DETOUR_CLUSTER:
                continue
            try:
                c = vision.camp_at(p)
                if not (c.is_gem_cluster() or c.is_gold_cluster()):
                    continue
            except cambc.Error:
                continue
            units = combat.camps([c])
            if not combat.fight(me, units):
                self.nav.step(me, area(p, self.range))
                combat.fight(me, units)
            return True
        return False

    def fight_nearby(self, me):
        """Hit whatever awake camp or enemy is in reach without moving."""
        if self.enemies:
            combat.fight(me, self.enemies, self.allies, self.roster.leader, stun_chain=self.stun)
            return
        awake = vision.awake_camp_tiles() & area(self.pos, 4)
        if not awake.is_empty():
            units = []
            for p in awake.positions():
                try:
                    units.append(vision.camp_at(p))
                except cambc.Error:
                    pass
            combat.fight(me, combat.camps(units))

    def work(self, me, i, tank, capture=True):
        """Clear and capture camp group i. tank: opens big camps; capture: stands on the reward."""
        g = self.groups[i]
        if g.reward:
            tiles = self.tiles(g)
            if capture:
                if not tiles.is_set(self.pos):
                    self.nav.step(me, tiles, key=("g", i))
                return
            if tiles.is_set(self.pos):                   # leave the bag to the leader
                self.nav.step(me, area(self.pos, 1) & ~tiles)
                return
            self.fight_nearby(me)
            return
        units = combat.camps(g.unit.camps())
        if not units:
            tiles = self.tiles(g)
            near = cambc.Bitboard()
            for p in tiles.positions():
                near.draw_chebyshev(p, 1)
            if near.is_set(self.pos):
                # Next to the camp and still nothing in sight: hidden in a bush (step in) or gone.
                self.blind = self.blind + 1 if self.blind_target == i else 1
                self.blind_target = i
                if self.blind > config.BLIND_TURNS:
                    g.avoid = self.now + 30
                    self.blind = 0
                    return
                self.nav.step(me, tiles)
                return
            if dist(self.pos, g.rep) <= 2:
                self.nav.step(me, near & ~tiles)
                return
            approach = cambc.Bitboard()
            for p in self.tiles(g).positions():
                approach.draw_chebyshev(p, max(1, self.range))
            if not self.nav.step(me, approach & ~self.tiles(g), key=("a", i, self.range)):
                self.fight_nearby(me)
            return
        awake = any(u.awake for u in units)
        if awake:
            self.awake_since.setdefault(i, self.now)
        else:
            self.awake_since.pop(i, None)
        if g.big and not tank:
            # Tank first: hold outside the camps' reach until it is awake, melee joins one turn later.
            if not awake or (self.range <= 1 and self.awake_since.get(i, self.now) >= self.now):
                reach = max(u.range for u in units) + 1
                stage, inner = cambc.Bitboard(), cambc.Bitboard()
                for u in units:
                    stage.draw_chebyshev(u.pos, reach + 1)
                    inner.draw_chebyshev(u.pos, reach)
                ring = stage & ~inner
                anchor, _ = self.comms.anchor(self.now)
                if anchor is not None:
                    close = ring & area(anchor, 4)        # next to the tank, not behind a wall
                    if not close.is_empty():
                        ring = close
                if not ring.is_set(self.pos):
                    self.nav.step(me, ring)
                return
        acted = combat.fight(me, units, self.allies if self.healer else (), self.roster.leader, stun_chain=self.stun)
        if me.can_move() and (not acted or self.range <= 1):
            goals = cambc.Bitboard()
            for u in units:
                goals.draw_chebyshev(u.pos, self.range)
            if self.range > 1 and g.big:
                for u in units:                          # casters keep their distance: tank is nearest
                    goals &= ~area(u.pos, self.range - 1)
            if not goals.is_set(self.pos) and self.nav.step(me, goals):
                combat.fight(me, combat.camps(g.unit.camps()), (), self.roster.leader, stun_chain=self.stun)
