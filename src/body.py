"""Body: senses and motor skills shared by every bot of the from_start evolution.

Strategy lives in the gene modules (g_*.py) that genome.py lists; this file only offers
safe primitives (sensing, pathing, attacking, casting, shopping, banking) so genes can be
recombined freely between bots. Every bot carries an identical copy.

Python costs roughly 100 fuel per bytecode and a turn has ~2.5M fuel, so per-turn Python
work is kept small and heavy searches use the native Bitboard / DistanceField code.
"""
import _cambc as _bc
import cambc
from cambc import game_map, vision, Team, Vec2, Bitboard, DistanceField, ItemType, ConsumableType, Error

INF = 60000
TRACE = 0          # debug: print a status line every TRACE rounds (0 = off)
CT = cambc.ChampionType
DR = cambc.ChampionDraft

HOR = 12           # Heart of Ruin (ChampionType 12, ChampionDraft 11): melee, shield + stunning dash
HOR_DRAFT = 11
RANGED = (CT.VESPER_VALE, CT.CASSI, CT.STELLAR, CT.PRISM, CT.WILLOW, CT.TAVI)
MELEE = (CT.RYTH, CT.VENDETTA, CT.ISSAC, CT.MARCELLA, CT.REN, CT.VARG, HOR)
TANKS = (CT.RYTH, CT.MARCELLA, CT.VARG, CT.REN, CT.ISSAC, HOR)
CASTERS = (CT.STELLAR, CT.PRISM, CT.TAVI, CT.CASSI)
DIRS = ((0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1))

K_RESET, K_DAMAGE, K_AOE, K_CC, K_HEAL, K_DASH, K_SHIELD = 1, 2, 3, 4, 5, 6, 7
_KINDS = None

# camp type ids
WOLF, ELK, GEM_CLUSTER, GOLD_CLUSTER, MONOLITH = 0, 1, 2, 3, 4

# Shared memory layout (8 bytes), identical for every bot so genes can be mixed:
#   bytes 0..5: claimed camp group per body slot (group index + 1, 0 = none)
#   bytes 6, 7: point of interest (x + 1, y + 1), 0 = none (enemy carrier, fight, ...)
POI_X, POI_Y = 6, 7

# rough (health, damage per round incl. spells) per champion type, for planning
PLAN = {CT.RYTH: (1200, 62), CT.VESPER_VALE: (900, 51), CT.VENDETTA: (800, 79), CT.CASSI: (700, 48),
        CT.ISSAC: (900, 45), CT.STELLAR: (750, 60), CT.PRISM: (700, 55), CT.MARCELLA: (1200, 58),
        CT.WILLOW: (700, 50), CT.REN: (900, 56), CT.VARG: (1000, 75), CT.TAVI: (750, 63), HOR: (1000, 62)}


def cheb(ax, ay, bx, by):
    dx = ax - bx
    dy = ay - by
    if dx < 0:
        dx = -dx
    if dy < 0:
        dy = -dy
    return dx if dx > dy else dy


def draft_to_types(pick):
    pick = int(pick)
    if pick < 3:
        return [pick]
    if pick == 3:
        return [int(CT.CASSI), int(CT.ISSAC)]
    return [pick + 1]


def shard(family, stat):
    """shard('MONSTER', 'STRENGTH') -> ItemType.MONSTER_SHARD_OF_STRENGTH"""
    return getattr(ItemType, family + "_SHARD_OF_" + stat)


def kinds():
    global _KINDS
    if _KINDS is None:
        _KINDS = ((K_RESET, cambc.AbilityAttackReset), (K_DAMAGE, cambc.AbilityDamage),
                  (K_AOE, cambc.AbilityAoeDamage), (K_CC, cambc.AbilityCc), (K_HEAL, cambc.AbilityHeal),
                  (K_DASH, cambc.AbilityDash), (K_SHIELD, cambc.AbilityShield))
    return _KINDS


# ---------------------------------------------------------------------------- draft
def draft_info():
    """Static map summary for the draft genes (the whole map is visible in the draft)."""
    info = {}
    W = game_map.width()
    H = game_map.height()
    info["W"] = W
    info["H"] = H
    info["area"] = W * H
    sp = game_map.spawn_region(Team.ALLY).positions()
    ep = game_map.spawn_region(Team.ENEMY).positions()
    hx = sum(p.x for p in sp) // max(1, len(sp))
    hy = sum(p.y for p in sp) // max(1, len(sp))
    ex = sum(p.x for p in ep) // max(1, len(ep))
    ey = sum(p.y for p in ep) // max(1, len(ep))
    info["spawn_d"] = cheb(hx, hy, ex, ey)
    n = {WOLF: 0, ELK: 0, GEM_CLUSTER: 0, GOLD_CLUSTER: 0, MONOLITH: 0}
    groups = 0
    gems = 0
    big_gems = 0
    near_gems = 0
    for g in game_map.camp_groups():
        groups += 1
        gv = g.gem_value()
        gems += gv
        hp = 0
        cx = 0
        cy = 0
        k = 0
        for c in g.camps():
            kd = int(c.kind())
            n[kd] = n.get(kd, 0) + 1
            hp += (1350, 2400, 500, 500, 20000)[kd] if kd <= 4 else 1000
            s = c.spawn_position()
            cx += s.x
            cy += s.y
            k += 1
        if hp >= 8000:
            big_gems += gv
        if k:
            cx //= k
            cy //= k
            if cheb(cx, cy, hx, hy) <= cheb(cx, cy, ex, ey):
                near_gems += gv
    info["groups"] = groups
    info["gems"] = gems
    info["big_gems"] = big_gems
    info["big_frac"] = big_gems / max(1, gems)
    info["near_gems"] = near_gems
    info["wolves"] = n[WOLF]
    info["elks"] = n[ELK]
    info["gem_clusters"] = n[GEM_CLUSTER]
    info["gold_clusters"] = n[GOLD_CLUSTER]
    info["monoliths"] = n[MONOLITH]
    info["bushes"] = game_map.bushes().count()
    info["walls"] = game_map.walls().count()
    info["altars"] = game_map.altars().count()
    return info


_DRAFT_INFO = None


def run_draft(gene, genome_id):
    # Only the first draft turn has 10x fuel: compute the map summary once and keep it.
    global _DRAFT_INFO
    ally = [int(p) for p in cambc.draft.current_draft(Team.ALLY)]
    enemy = [int(p) for p in cambc.draft.current_draft(Team.ENEMY)]
    size = cambc.draft.team_size()
    info = _DRAFT_INFO
    if info is None:
        try:
            info = draft_info()
        except Exception:
            info = {"W": 50, "H": 50, "area": 2500, "groups": 10, "gems": 300, "big_frac": 0.0, "monoliths": 0,
                    "elks": 0, "wolves": 0, "gem_clusters": 0, "gold_clusters": 0, "bushes": 0, "walls": 0,
                    "spawn_d": 40, "near_gems": 150, "big_gems": 0, "altars": 2}
        _DRAFT_INFO = info
    try:
        prefs = [int(p) for p in gene.preferences(info, size, ally, enemy)]
    except Exception as e:
        print("draft gene error", e)
        prefs = []
    prefs += [4, 3, 0, 9, 8, 10, 11, 2, 5, 1, 6, 7]
    pick = next(p for p in prefs if 0 <= p <= 11 and p not in ally)
    types = []
    for p in ally + [pick]:
        types += draft_to_types(p)
    mem = bytes([0xFE, genome_id & 255, len(types)] + types)
    try:
        cambc.draft_memory.submit(mem[:1024])
    except Exception:
        pass
    cambc.draft.pick(pick)


# ---------------------------------------------------------------------------- records
class G:
    """Static facts and remembered state of one camp group."""
    __slots__ = ("i", "obj", "h", "tiles", "mask", "cx", "cy", "gems", "gold", "hp", "dmg", "resp", "state",
                 "ready", "hp_left", "kinds", "monolith", "elk", "harmless", "home_d", "enemy_d", "mine", "bad",
                 "field", "seen", "taken_by_enemy", "home_walk", "island", "afield")


class U:
    """Snapshot of a visible champion."""
    __slots__ = ("c", "x", "y", "hp", "maxhp", "type", "gems", "st", "str", "foc", "d", "in_spawn", "ranged")


class C:
    """Snapshot of a visible camp."""
    __slots__ = ("c", "x", "y", "hp", "gi", "kind", "awake")


class Body:
    def __init__(self, genome):
        self.genome = genome
        self.ready = False
        self.mem = {}
        self.hidden = {}
        self.prev = None
        self.stuck = 0
        self.last_hp = None
        self.errors = 0

    # ------------------------------------------------------------------ init
    def init(self):
        me = cambc.me()
        self.me = me
        self.type = me.champion_name()
        self.ranged = self.type in RANGED
        self.arange = me.attack_range()
        self.W = game_map.width()
        self.H = game_map.height()
        self.walls = game_map.walls()
        self.holes = game_map.holes()
        self.altars = game_map.altars()
        self.bushes = game_map.bushes()
        self.ally_spawn = game_map.spawn_region(Team.ALLY)
        self.enemy_spawn = game_map.spawn_region(Team.ENEMY)
        self.walk_walls = self.walls | self.holes | self.enemy_spawn      # altars are roots for altar fields
        self.block = self.walk_walls | self.altars
        self.dash_block = self.walls | self.altars | self.enemy_spawn     # dashes cross holes
        self.altar_pos = [(p.x, p.y) for p in self.altars.positions()]
        sp = self.ally_spawn.positions()
        self.hx = sum(p.x for p in sp) // max(1, len(sp))
        self.hy = sum(p.y for p in sp) // max(1, len(sp))
        ep = self.enemy_spawn.positions()
        self.ex = sum(p.x for p in ep) // max(1, len(ep))
        self.ey = sum(p.y for p in ep) // max(1, len(ep))
        self.max_rounds = cambc.constants.MAX_ROUNDS
        self.win_gems = cambc.constants.WINNING_GEMS
        self.h = int(me)
        self.groups = []
        self.gbyh = {}
        self.tile_group = {}
        self.camp_mask = Bitboard()
        self._gd = None
        self._allies = None
        kstats = {}
        for i, g in enumerate(game_map.camp_groups()):
            o = G()
            o.i = i
            o.obj = g
            o.h = int(g)
            o.tiles = []
            hp = 0
            dmg = 0
            o.kinds = set()
            mask = Bitboard()
            sx = 0
            sy = 0
            for c in g._camps:
                s = c._spawn_position
                o.tiles.append((s.x, s.y))
                sx += s.x
                sy += s.y
                mask.set(s)
                k = c._type
                o.kinds.add(k)
                st = kstats.get(k)
                if st is None:
                    st = c.base_stats()
                    st = (st.base_health, st.base_strength)
                    kstats[k] = st
                hp += st[0]
                dmg += st[1]
            o.monolith = MONOLITH in o.kinds
            o.elk = ELK in o.kinds
            o.mask = mask
            n = max(1, len(o.tiles))
            o.cx = sx // n
            o.cy = sy // n
            o.gems = g._gems
            o.gold = g._gold
            o.hp = hp
            o.hp_left = hp
            o.dmg = dmg
            o.harmless = dmg <= 0
            o.resp = g._respawn
            o.state = 1          # 1 alive, 2 reward available, 3 respawning
            o.ready = 0
            o.bad = False
            o.field = None
            o.seen = -1
            o.taken_by_enemy = 0
            o.island = False
            o.afield = None
            o.home_d = cheb(o.cx, o.cy, self.hx, self.hy)
            o.enemy_d = cheb(o.cx, o.cy, self.ex, self.ey)
            o.mine = o.home_d <= o.enemy_d
            self.groups.append(o)
            self.gbyh[o.h] = o
            for t in o.tiles:
                self.tile_group[t] = o
            self.camp_mask |= o.mask
        dm = b""
        try:
            dm = bytes(cambc.DraftMemoryBuffer())
        except Exception:
            pass
        self.team_types = []
        if len(dm) >= 3 and dm[0] == 0xFE:
            self.team_types = list(dm[3:3 + dm[2]])
        t = int(self.type)
        self.slot = self.team_types.index(t) if t in self.team_types else int(me) % 6
        self.team_size = max(1, len(self.team_types))
        self.abil = []
        for a in me.abilities():
            info = a.info()
            if info is None:
                continue
            kind = 0
            for k, cls in kinds():
                if isinstance(info, cls):
                    kind = k
            self.abil.append((a, kind, getattr(info, "range", 0.0), bool(info.exclusive_with_movement),
                              getattr(info, "modifier", 0.0), bool(getattr(info, "enhanced_attack", False)),
                              getattr(info, "radius", 0.0)))
        self.kinds = set(e[1] for e in self.abil)
        sf = DistanceField()
        reach = Bitboard()
        sf.compute(self.block, self.ally_spawn & ~self.block, reach)
        self.spawn_field = sf
        self.reach = reach
        # holes can be crossed by a dash (2 steps): champions with a dash may farm islands
        self.has_dash = K_DASH in self.kinds
        self.air_walls = self.walls | self.altars | self.enemy_spawn
        air = None
        for g in self.groups:
            g.island = False
            if (g.mask & reach).is_empty():
                g.home_walk = INF
                if self.has_dash:
                    if air is None:
                        air = Bitboard()
                        DistanceField().compute(self.air_walls, self.ally_spawn & ~self.block, air)
                    if not (g.mask & air).is_empty():
                        g.island = True
                        continue
                g.bad = True           # cannot be reached from our spawn
            else:
                t = g.tiles[0]
                g.home_walk = sf.get(Vec2(t[0], t[1]))
        self._altar_field = None
        self.total_gems = sum(g.gems for g in self.groups)
        self.ready = True

    def compute(self, roots, walls):
        f = DistanceField()
        f.compute(walls, roots & ~walls, Bitboard())
        return f

    @property
    def altar_field(self):
        if self._altar_field is None and self.altar_pos:
            f = DistanceField()
            f.compute(self.walk_walls, self.altars, Bitboard())
            self._altar_field = f
        return self._altar_field

    def gfield(self, g):
        if g.field is None:
            f = DistanceField()
            f.compute(self.block, g.mask, Bitboard())
            g.field = f
        return g.field

    def pfield(self, key, x, y, r=0):
        """Cached static field to a point (or a Chebyshev square around it)."""
        k = ("pf", key)
        f = self.mem.get(k)
        if f is None:
            roots = Bitboard()
            roots.draw_chebyshev(Vec2(x, y), r)
            roots = roots & ~self.block
            if roots.is_empty():
                roots.set(Vec2(x, y))
            f = DistanceField()
            f.compute(self.block, roots, Bitboard())
            self.mem[k] = f
        return f

    # --------------------------------------------------------------- refresh
    def refresh(self):
        # direct engine calls: the SDK wrappers cost several thousand fuel each
        h = self.h
        self.round = _bc.round_number()
        st = _bc.champion_get(h, 8)
        self.alive = st & 1
        self._camps = None
        self._occ = None
        self._gd = None
        self._allies = None
        self._dm = None
        self.moved = False
        self.lock_move = False
        self.attacked = False
        self.cast = False
        self.enemies = []
        if not self.alive:
            self.last_hp = None
            self.gold = _bc.champion_gold(h)
            self.gems = 0
            return
        self.recalling = st & 2
        self.submitting = st & 4
        self.teleporting = st & 4096
        self.can_move = st & 8
        self.can_attack = st & 16
        self.can_cast = st & 2048
        p = _bc.champion_get(h, 2)
        self.pos = p
        x = p.x
        y = p.y
        self.x = x
        self.y = y
        hp = _bc.champion_get(h, 3)
        self.hp = hp
        self.maxhp = _bc.champion_get(h, 4)
        self.hpf = hp / max(1.0, self.maxhp)
        lh = self.last_hp
        self.dmg_taken = 0 if lh is None or lh <= hp else lh - hp
        self.last_hp = hp
        self.gems = _bc.champion_gems(h)
        self.gold = _bc.champion_gold(h)
        self.at_spawn = self.ally_spawn.is_set(p)
        self.str = _bc.champion_get(h, 5)
        self.foc = _bc.champion_get(h, 6)
        eocc = _bc.enemy_occupancy()
        if not eocc.is_empty():
            espawn = self.enemy_spawn
            for c in vision.champions(Team.ENEMY):
                ch = c._handle
                q = _bc.champion_get(ch, 2)
                u = U()
                u.c = c
                u.x = q.x
                u.y = q.y
                u.hp = _bc.champion_get(ch, 3)
                u.maxhp = _bc.champion_get(ch, 4)
                u.type = _bc.champion_identity(ch, 1)
                u.gems = _bc.champion_gems(ch)
                u.st = _bc.champion_get(ch, 8)
                u.str = _bc.champion_get(ch, 5)
                u.foc = _bc.champion_get(ch, 6)
                dx = q.x - x
                dy = q.y - y
                if dx < 0:
                    dx = -dx
                if dy < 0:
                    dy = -dy
                u.d = dx if dx > dy else dy
                u.in_spawn = espawn.is_set(q)
                u.ranged = u.type in RANGED
                self.enemies.append(u)

    @property
    def allies(self):
        """Visible team-mates (lazy: only built when a gene asks)."""
        a = self._allies
        if a is None:
            a = []
            aocc = _bc.ally_occupancy()
            if aocc.count() > 1:
                x = self.x
                y = self.y
                for c in vision.champions(Team.ALLY):
                    ch = c._handle
                    if ch == self.h:
                        continue
                    q = _bc.champion_get(ch, 2)
                    u = U()
                    u.c = c
                    u.x = q.x
                    u.y = q.y
                    u.hp = _bc.champion_get(ch, 3)
                    u.maxhp = _bc.champion_get(ch, 4)
                    u.type = _bc.champion_identity(ch, 1)
                    u.gems = _bc.champion_gems(ch)
                    u.st = 0
                    u.str = _bc.champion_get(ch, 5)
                    u.foc = _bc.champion_get(ch, 6)
                    dx = q.x - x
                    dy = q.y - y
                    if dx < 0:
                        dx = -dx
                    if dy < 0:
                        dy = -dy
                    u.d = dx if dx > dy else dy
                    u.in_spawn = False
                    u.ranged = u.type in RANGED
                    a.append(u)
            self._allies = a
        return a

    def camps(self):
        if self._camps is None:
            out = []
            if not _bc.camp_occupancy().is_empty():
                aw = _bc.awake_camp_occupancy()
                gbyh = self.gbyh
                for c in vision.camps():
                    ch = c._handle
                    ci = C()
                    q = _bc.camp_get(ch, 0)
                    ci.c = c
                    ci.x = q.x
                    ci.y = q.y
                    ci.hp = _bc.camp_get(ch, 1)
                    ci.kind = c._type
                    g = gbyh.get(c._group)
                    ci.gi = g.i if g is not None else -1
                    ci.awake = aw.is_set(q)
                    out.append(ci)
            self._camps = out
        return self._camps

    def occ(self):
        if self._occ is None:
            self._occ = _bc.ally_occupancy() | _bc.enemy_occupancy() | _bc.camp_occupancy() | _bc.teleport_occupancy()
        return self._occ

    def dist(self, x, y):
        return cheb(self.x, self.y, x, y)

    def group_dists(self):
        """Chebyshev distance from me to every group centre, indexed by group.i (cached per turn)."""
        d = self._gd
        if d is None:
            x = self.x
            y = self.y
            d = []
            for g in self.groups:
                dx = g.cx - x
                dy = g.cy - y
                if dx < 0:
                    dx = -dx
                if dy < 0:
                    dy = -dy
                d.append(dx if dx > dy else dy)
            self._gd = d
        return d

    def enemies_live(self):
        """Visible enemies that are worth considering (not healing inside their spawn)."""
        return [u for u in self.enemies if not u.in_spawn]

    def nearest_enemy(self, maxd=99):
        best = None
        for u in self.enemies:
            if u.in_spawn or u.d > maxd:
                continue
            if best is None or u.d < best.d:
                best = u
        return best

    # ------------------------------------------------------------ knowledge
    def update_groups(self):
        """Refresh the state of camp groups with a spawn tile in vision (cheap bitboard test first)."""
        near = _bc.vision() & self.camp_mask
        if near.is_empty():
            return
        r = self.round
        done = set()
        tg = self.tile_group
        for p in near.positions():
            g = tg.get((p.x, p.y))
            if g is None or g.i in done:
                continue
            done.add(g.i)
            s = _bc.camp_group_state(g.h)
            if s == 0:
                continue
            g.seen = r
            if s == 3:
                if g.state != 3:
                    g.hp_left = g.hp
                g.state = 3
                g.ready = r + _bc.camp_group_cooldown(g.h)
            elif s == 2:
                g.state = 2
                g.hp_left = 0
            else:
                if g.state != 1:
                    g.hp_left = g.hp
                g.state = 1
        if not _bc.camp_occupancy().is_empty():
            seen = {}
            for ci in self.camps():
                if ci.gi >= 0:
                    seen[ci.gi] = seen.get(ci.gi, 0) + ci.hp
            for gi, hp in seen.items():
                g = self.groups[gi]
                g.state = 1
                if (_bc.vision() & g.mask).count() >= len(g.tiles):
                    g.hp_left = hp
                else:
                    g.hp_left = max(hp, min(g.hp, g.hp_left))

    def group_at_tile(self):
        """Camp group whose spawn tiles include my tile, or None."""
        return self.tile_group.get((self.x, self.y))

    # ---------------------------------------------------------- shared mem
    def mem_get(self, i):
        try:
            return _bc.shared_memory_get(i)
        except Exception:
            return 0

    def mem_set(self, i, v):
        try:
            _bc.shared_memory_set(i, v & 255)
        except Exception:
            pass

    def claim(self, g):
        if self.slot < 6:
            self.mem_set(self.slot, 0 if g is None else g.i + 1)

    def claims(self):
        """Group indices claimed by team-mates."""
        out = set()
        for i in range(6):
            if i == self.slot:
                continue
            v = self.mem_get(i)
            if v:
                out.add(v - 1)
        return out

    def claim_of(self, slot):
        v = self.mem_get(slot)
        if v and v <= len(self.groups):
            return self.groups[v - 1]
        return None

    def set_poi(self, x, y):
        self.mem_set(POI_X, x + 1)
        self.mem_set(POI_Y, y + 1)
        self.mem[("poi_set",)] = self.round

    def clear_poi(self):
        self.mem_set(POI_X, 0)
        self.mem_set(POI_Y, 0)

    def poi(self):
        x = self.mem_get(POI_X)
        y = self.mem_get(POI_Y)
        if x == 0 or y == 0:
            return None
        return (x - 1, y - 1)

    # ------------------------------------------------------------- movement
    def step_field(self, f, stop_at=0, avoid=None):
        """Descend a static field one tile, trying alternatives on blocked tiles.
        avoid(x, y) -> extra cost used to break ties (e.g. danger)."""
        if self.moved or self.lock_move or not self.can_move:
            return False
        pos = self.pos
        cur = f.get(pos)
        if cur <= stop_at or cur >= INF:
            return False
        occ = self.occ()
        hidden = self.hidden
        r = self.round
        if avoid is None and self.stuck == 0:
            # fast path: the field's own optimal steps (static walls already excluded)
            for dl in f.next_moves_from(pos):
                v = pos + dl
                if occ.is_set(v):
                    continue
                k = (v.x, v.y)
                hh = hidden.get(k)
                if hh is not None and hh > r:
                    continue
                try:
                    if self.me.move_absolute(v):
                        self._moved_to(v)
                        self.prev = (pos.x, pos.y)
                        return True
                    hidden[k] = r + 20
                except Error:
                    hidden[k] = r + 3
        block = self.block
        W = self.W
        H = self.H
        hidden = self.hidden
        r = self.round
        prev = self.prev
        stuck = self.stuck
        opts = []
        for dx, dy in DIRS:
            nx = self.x + dx
            ny = self.y + dy
            if nx < 0 or ny < 0 or nx >= W or ny >= H:
                continue
            h = hidden.get((nx, ny))
            if h is not None and h > r:
                continue
            v = Vec2(nx, ny)
            if block.is_set(v) or occ.is_set(v):
                continue
            d = f.get(v)
            extra = avoid(nx, ny) if avoid is not None else 0
            if d < cur:
                opts.append((d + extra, 0, nx, ny, v, d))
            elif d == cur and stuck >= 1 and (nx, ny) != prev:
                opts.append((d + extra, 1, nx, ny, v, d))
            elif d == cur + 1 and stuck >= 3 and (nx, ny) != prev:
                opts.append((d + extra, 2, nx, ny, v, d))
        opts.sort(key=lambda o: (o[0], o[1]))
        here = (self.x, self.y)
        for _, _, nx, ny, v, d in opts:
            try:
                if self.me.move_absolute(v):
                    self._moved_to(v)
                    self.prev = here
                    if d < cur:
                        self.stuck = 0
                    return True
                hidden[(nx, ny)] = r + 20
            except Error:
                hidden[(nx, ny)] = r + 3
                continue
        self.stuck += 1
        return False

    def _moved_to(self, v):
        self.moved = True
        self.pos = v
        self.x = v.x
        self.y = v.y
        self._occ = None
        self.at_spawn = self.ally_spawn.is_set(v)
        if self.ranged:
            self.can_attack = False
        self._gd = None
        for u in self.enemies:
            u.d = cheb(self.x, self.y, u.x, u.y)
        for u in (self._allies or ()):
            u.d = cheb(self.x, self.y, u.x, u.y)

    def step_to(self, goals, avoid=None):
        """Dynamic one-step move towards a set of goal tiles."""
        if self.moved or self.lock_move or not self.can_move:
            return False
        if goals.is_set(self.pos):
            return False
        blocked = self.block | self.occ()
        if self.hidden:
            r = self.round
            for (hx, hy), t in list(self.hidden.items()):
                if t > r:
                    blocked.set(Vec2(hx, hy))
                else:
                    del self.hidden[(hx, hy)]
        blocked.set(self.pos, False)
        goals = goals & ~blocked
        if goals.is_empty():
            return False
        f = DistanceField()
        here = Bitboard()
        here.set(self.pos)
        f.compute_to(blocked, goals, here, Bitboard())
        if f.get(self.pos) >= INF:
            return False
        return self.step_field(f, 0, avoid)

    def step_toward(self, x, y, r=0):
        goals = Bitboard()
        goals.draw_chebyshev(Vec2(x, y), r)
        return self.step_to(goals)

    def step_away(self, x, y):
        """One step that maximises the distance from (x, y), preferring the way home."""
        if self.moved or self.lock_move or not self.can_move:
            return False
        occ = self.occ()
        best = None
        here = cheb(self.x, self.y, x, y)
        sf = self.spawn_field
        for dx, dy in DIRS:
            nx = self.x + dx
            ny = self.y + dy
            if nx < 0 or ny < 0 or nx >= self.W or ny >= self.H:
                continue
            v = Vec2(nx, ny)
            if self.block.is_set(v) or occ.is_set(v):
                continue
            d = cheb(nx, ny, x, y)
            if d < here:
                continue
            score = d * 10 - min(200, sf.get(v)) * 0.1
            if best is None or score > best[0]:
                best = (score, v)
        if best is None:
            return False
        try:
            if self.me.move_absolute(best[1]):
                self._moved_to(best[1])
                return True
        except Error:
            pass
        return False

    def dash_along(self, f, min_gain=2):
        """Use a dash ability to descend field f by up to 2 tiles."""
        e = self.ability(K_DASH)
        if e is None or not self.ab_ready(e):
            return False
        cur = f.get(self.pos)
        occ = self.occ()
        best = None
        rng = int(e[2]) if e[2] else 2
        for dx in range(-rng, rng + 1):
            for dy in range(-rng, rng + 1):
                if dx == 0 and dy == 0:
                    continue
                nx = self.x + dx
                ny = self.y + dy
                if nx < 0 or ny < 0 or nx >= self.W or ny >= self.H:
                    continue
                v = Vec2(nx, ny)
                if self.block.is_set(v) or occ.is_set(v):
                    continue
                d = f.get(v)
                if d <= cur - min_gain and (best is None or d < best[0]):
                    best = (d, v)
        if best is None:
            return False
        try:
            if e[0].use(best[1]):
                self.cast = True
                was = self.moved
                self._moved_to(best[1])
                self.moved = was
                return True
        except Error:
            pass
        return False

    def travel(self, f, stop_at=0, dash=True, avoid=None):
        moved = self.step_field(f, stop_at, avoid)
        if dash and f.get(self.pos) > stop_at + 3:
            self.dash_along(f)
        return moved

    def go_home(self, dash=True):
        if self.spawn_field.get(self.pos) >= INF:
            return self.recall()
        return self.travel(self.spawn_field, 0, dash)

    def go_group(self, g, stop_at=1, dash=True):
        return self.travel(self.gfield(g), stop_at, dash)

    def walk_dist(self, g):
        return self.gfield(g).get(self.pos)

    # ------------------------------------------------------------- abilities
    def ability(self, kind):
        for e in self.abil:
            if e[1] == kind:
                return e
        return None

    def has_kind(self, kind):
        return kind in self.kinds

    def ab_ready(self, e):
        if self.cast or not self.can_cast:
            return False
        if e[3] and self.moved:
            return False
        try:
            return _bc.champion_cooldown(self.h, e[0]._slot) == 0
        except Exception:
            return False

    def use(self, e, target):
        try:
            ok = e[0].use(target)
        except Error:
            return False
        except Exception:
            return False
        if ok:
            self.cast = True
            if e[3]:
                self.lock_move = True
            if e[1] == K_RESET:
                self.can_attack = True
        return ok

    def try_attack(self, target):
        if self.attacked or not self.can_attack:
            return False
        try:
            self.me.attack(target)
        except Error:
            return False
        except Exception:
            return False
        self.attacked = True
        self.can_attack = False
        if self.ranged:
            self.lock_move = True
        return True

    def attack_reset(self, target, use_reset=True):
        """Basic attack, then (if available) reset and attack again."""
        if not self.try_attack(target):
            return False
        if not use_reset:
            return True
        for e in self.abil:
            if e[1] == K_RESET and self.ab_ready(e):
                if self.use(e, None):
                    self.attacked = False
                    self.can_attack = True
                    self.try_attack(target)
                break
        return True

    def spells_on_enemy(self, u, allow_stun_stack=False):
        """Offensive spells on enemy champion snapshot u. Returns True on a cast."""
        if self.cast or not self.can_cast:
            return False
        d = cheb(self.x, self.y, u.x, u.y)
        stunned = None
        for e in self.abil:
            k = e[1]
            if k in (K_DAMAGE, K_CC, K_AOE) and d <= e[2] and self.ab_ready(e):
                if k == K_CC and e[4] <= 0 and not allow_stun_stack:
                    if stunned is None:
                        try:
                            stunned = u.c.buffs().has_stun()
                        except Exception:
                            stunned = False
                    if stunned:
                        continue
                if k == K_AOE:
                    if self.use(e, Vec2(u.x, u.y)):
                        return True
                elif self.use(e, u.c):
                    return True
            elif k == K_DASH and e[4] > 0 and d <= e[2] + 1 and self.ab_ready(e):
                if self.dash_stun(e, u.x, u.y):
                    return True
        return False

    def spells_on_camps(self, targets, melee_keep_step=True):
        """Damage spells on camps. Returns True on a cast."""
        if self.cast or not self.can_cast or not targets:
            return False
        for e in self.abil:
            k = e[1]
            if k not in (K_DAMAGE, K_AOE, K_CC) or not self.ab_ready(e):
                continue
            if k == K_CC and e[4] <= 0:
                continue
            best = None
            for ci in targets:
                d = cheb(self.x, self.y, ci.x, ci.y)
                if d <= e[2]:
                    if melee_keep_step and e[3] and not self.ranged and d > 1:
                        continue
                    if best is None or ci.hp < best.hp:
                        best = ci
            if best is None:
                continue
            if k == K_AOE:
                bestc = best
                bestn = 0
                for ci in targets:
                    if cheb(self.x, self.y, ci.x, ci.y) > e[2]:
                        continue
                    n = 0
                    for cj in targets:
                        if cheb(ci.x, ci.y, cj.x, cj.y) <= 1:
                            n += 1
                    if n > bestn:
                        bestn = n
                        bestc = ci
                if self.use(e, Vec2(bestc.x, bestc.y)):
                    return True
            elif self.use(e, best.c):
                return True
        if not self.enemies and self.W * self.H > 1200:
            for e in self.abil:
                if e[1] == K_DASH and e[4] > 0 and len(targets) >= 2 and self.ab_ready(e):
                    c0 = targets[0]
                    if cheb(self.x, self.y, c0.x, c0.y) <= e[2] + 1 and self.dash_stun(e, c0.x, c0.y):
                        return True
        return False

    def dash_stun(self, e, tx, ty):
        occ = self.occ()
        rng = int(e[2]) if e[2] else 2
        best = None
        for dx in range(-rng, rng + 1):
            for dy in range(-rng, rng + 1):
                if dx == 0 and dy == 0:
                    continue
                nx = self.x + dx
                ny = self.y + dy
                if nx < 0 or ny < 0 or nx >= self.W or ny >= self.H:
                    continue
                if cheb(nx, ny, tx, ty) > 1:
                    continue
                v = Vec2(nx, ny)
                if self.block.is_set(v) or occ.is_set(v):
                    continue
                d = cheb(nx, ny, tx, ty)
                if best is None or d < best[0]:
                    best = (d, v)
        if best is None:
            return False
        try:
            if e[0].use(best[1]):
                self.cast = True
                was = self.moved
                self._moved_to(best[1])
                self.moved = was
                return True
        except Error:
            pass
        return False

    def heal_allies(self, min_missing=150):
        e = self.ability(K_HEAL)
        if e is None or not self.ab_ready(e):
            return False
        best = None
        for a in self.allies:
            miss = a.maxhp - a.hp
            if a.d <= e[2] and miss >= min_missing and (best is None or miss > best[0]):
                best = (miss, a)
        if best is None:
            return False
        return self.use(e, best[1].c)

    def shield_self(self, force=False):
        e = self.ability(K_SHIELD)
        if e is None or not self.ab_ready(e):
            return False
        if force or self.dmg_taken > 0 or any(u.d <= 3 for u in self.enemies):
            return self.use(e, None)
        return False

    # ---------------------------------------------------------------- combat
    def power_of(self, hp, strength, focus):
        return hp * (strength + 0.25 * focus)

    def balance(self, radius=7):
        """(our power, their power) around me; allies seen within 6 tiles count."""
        mine = self.power_of(self.hp, self.str, self.foc)
        for a in self.allies:
            if a.d <= 6:
                h, d = PLAN.get(a.type, (900, 55))
                mine += a.hp * d
        theirs = 0.0
        for u in self.enemies:
            if u.d <= radius and not u.in_spawn:
                theirs += self.power_of(u.hp, u.str, u.foc)
        return mine, theirs

    # ------------------------------------------------- threat helpers (gen 2+)
    def note_threats(self):
        """Remember where enemies were seen (last 25 rounds); call once per turn."""
        tm = self.mem.get("threats")
        if tm is None:
            tm = []
            self.mem["threats"] = tm
        r = self.round
        if tm and r - tm[0][2] > 25:
            tm[:] = [t for t in tm if r - t[2] <= 25]
        for u in self.enemies:
            if not u.in_spawn:
                tm.append((u.x, u.y, r))
        if len(tm) > 40:
            del tm[:len(tm) - 40]
        return tm

    def danger_at(self, x, y, radius=6, horizon=15):
        """How many recent enemy sightings are within radius of (x, y)."""
        tm = self.mem.get("threats")
        if not tm:
            return 0
        r = self.round
        n = 0
        for tx, ty, tr in tm:
            if r - tr <= horizon:
                dx = tx - x
                dy = ty - y
                if -radius <= dx <= radius and -radius <= dy <= radius:
                    n += 1
        return n

    def danger_map(self, horizon=20):
        """Set of coarse 6x6 cells (x // 6, y // 6) with an enemy sighting in the last
        `horizon` rounds, plus their 8 neighbour cells (cached per turn)."""
        dm = self._dm
        if dm is None:
            dm = set()
            tm = self.mem.get("threats")
            if tm:
                r = self.round
                for tx, ty, tr in tm:
                    if r - tr <= horizon:
                        cx = tx // 6
                        cy = ty // 6
                        for ox in (-1, 0, 1):
                            for oy in (-1, 0, 1):
                                dm.add((cx + ox, cy + oy))
            self._dm = dm
        return dm

    def group_danger(self, g):
        """True if enemies were seen near group g recently."""
        dm = self._dm if self._dm is not None else self.danger_map()
        return bool(dm) and (g.cx // 6, g.cy // 6) in dm

    def odds(self, radius=7, ally_radius=5):
        """(mine, theirs, n_enemies): effective power (health x damage) of the visible allies
        within ally_radius plus me, against all visible enemies within radius (not in spawn)."""
        mine = self.hp * (self.str + 0.3 * self.foc)
        theirs = 0.0
        ne = 0
        for u in self.enemies:
            if u.d <= radius and not u.in_spawn:
                theirs += u.hp * (u.str + 0.3 * u.foc)
                ne += 1
        if ne:
            for a in self.allies:
                if a.d <= ally_radius:
                    d = max(a.str + int(a.foc * 0.3), PLAN.get(a.type, (900, 55))[1], 30)
                    mine += a.hp * d
        return mine, theirs, ne

    def retreat(self, from_u=None):
        """Back off towards home with a dash if possible; remembers the round (hysteresis)."""
        self.mem["fled_at"] = self.round
        if self.go_home(True):
            return True
        if from_u is not None:
            return self.step_away(from_u.x, from_u.y)
        return False

    def recently_fled(self, rounds=4):
        return self.round - self.mem.get("fled_at", -100) <= rounds

    def engage(self, u):
        """Fight enemy snapshot u this turn (spells, attack, approach)."""
        self.spells_on_enemy(u)
        d = cheb(self.x, self.y, u.x, u.y)
        if d <= self.arange:
            self.attack_reset(u.c)
            return True
        if not self.ranged and d <= 3:
            e = self.ability(K_DASH)
            if e is not None and self.ab_ready(e):
                goals = Bitboard()
                goals.draw_chebyshev(Vec2(u.x, u.y), 1)
                goals = goals & ~self.block & ~self.occ()
                best = None
                for p in goals.positions():
                    dd = cheb(self.x, self.y, p.x, p.y)
                    if dd <= int(e[2]) and (best is None or dd < best[0]):
                        best = (dd, p)
                if best is not None and self.use(e, best[1]):
                    was = self.moved
                    self._moved_to(best[1])
                    self.moved = was
        d = cheb(self.x, self.y, u.x, u.y)
        if d > self.arange and not self.moved:
            self.step_toward(u.x, u.y, self.arange)
        d = cheb(self.x, self.y, u.x, u.y)
        if d <= self.arange:
            if not self.ranged:
                self.attack_reset(u.c)
            elif not self.attacked:
                for e in self.abil:
                    if e[1] == K_RESET and self.ab_ready(e) and self.use(e, None):
                        self.try_attack(u.c)
                        break
        return True

    def flee(self, dash=True):
        return self.go_home(dash)

    def recall(self):
        if self.at_spawn:
            return False
        try:
            self.me.recall()
            return True
        except Error:
            return False

    def cancel_channel(self):
        try:
            if self.recalling:
                self.me.cancel_recall()
            elif self.submitting:
                self.me.cancel_submit_gems()
            return True
        except Exception:
            return False

    # ---------------------------------------------------------------- camps
    def fight_camps(self, targets, kite=True, use_spells=True):
        """Damage the visible camps in targets; approach if nothing is in range."""
        inr = None
        best_adj = -1
        for ci in targets:
            if cheb(self.x, self.y, ci.x, ci.y) <= self.arange:
                if self.type == CT.VARG and len(targets) >= 2:
                    adj = sum(1 for cj in targets if abs(cj.x - ci.x) <= 1 and abs(cj.y - ci.y) <= 1)
                    if inr is None or (adj, -ci.hp) > (best_adj, -inr.hp):
                        best_adj = adj
                        inr = ci
                elif inr is None or ci.hp < inr.hp:
                    inr = ci
        if inr is not None and self.can_attack:
            self.attack_reset(inr.c)
            if use_spells:
                self.spells_on_camps(targets)
            if self.ranged:
                return True
        elif use_spells:
            self.spells_on_camps(targets)
        if not self.moved and inr is None:
            goals = Bitboard()
            for ci in targets:
                goals.draw_chebyshev(Vec2(ci.x, ci.y), self.arange)
            if self.ranged and kite:
                inner = Bitboard()
                for ci in targets:
                    inner.draw_chebyshev(Vec2(ci.x, ci.y), self.arange - 1)
                ring = goals & ~inner
                if not (ring & ~self.block & ~self.occ()).is_empty():
                    goals = ring
            self.step_to(goals)
            for ci in targets:
                if cheb(self.x, self.y, ci.x, ci.y) <= self.arange:
                    if not self.ranged and self.can_attack:
                        self.attack_reset(ci.c)
                    elif self.ranged and not self.attacked:
                        for e in self.abil:
                            if e[1] == K_RESET and self.ab_ready(e) and self.use(e, None):
                                self.try_attack(ci.c)
                                break
                    break
        return True

    def ring_tiles(self, g, r):
        out = Bitboard()
        for tx, ty in g.tiles:
            out.draw_chebyshev(Vec2(tx, ty), r)
        return out & ~g.mask

    def group_targets(self, g):
        return [ci for ci in self.camps() if ci.gi == g.i]

    def farm_group(self, g, kite=True, wait_respawn=4, use_spells=True):
        """Work on group g: approach, clear, capture, or wait for a close respawn.
        Returns False when there is nothing to do there (caller should pick another)."""
        r = self.round
        f = self.gfield(g)
        fd = f.get(self.pos)
        if fd >= INF:
            if g.island and self.has_dash:
                return self.air_approach(g)
            if not self.reach.is_set(self.pos):
                # we are cut off from the mainland (island, dash over a hole): go home
                return self.recall() or self.go_home()
            # no walking path to its spawn tiles: the reward can never be captured
            g.bad = True
            return False
        self.mem[("air", g.i)] = 0
        wk = ("wait", g.i)
        if g.state == 3:
            if self.W * self.H == 2040:
                if g.ready > r + fd + wait_respawn + 2:
                    return False
                seen = bool((_bc.vision() & g.mask).count())
                n = self.mem.get(wk, 0) + 1 if seen else 0
                self.mem[wk] = n
                if n > 25:
                    self.mem[wk] = 0
                    g.ready = r + 30
                    return False
                if g.mask.is_set(self.pos):
                    if not self.step_to(self.ring_tiles(g, 1)):
                        return False
                    return True
                if cheb(self.x, self.y, g.cx, g.cy) <= 3 and seen:
                    return True
                self.go_group(g, 1 if cheb(self.x, self.y, g.cx, g.cy) <= 3 else 2)
                return True
            if g.ready > r + wait_respawn:
                return False
            n = self.mem.get(wk, 0) + 1
            self.mem[wk] = n
            if n > 25:
                # the respawn does not come (a spawn tile is blocked): look elsewhere for a while
                self.mem[wk] = 0
                g.ready = r + 30
                return False
            if g.mask.is_set(self.pos):
                # an occupied spawn tile delays the respawn: wait next to it
                if not self.step_to(self.ring_tiles(g, 1)):
                    return False
                return True
            if cheb(self.x, self.y, g.cx, g.cy) <= 3:
                return True
            self.go_group(g, 2)
            return True
        targets = self.group_targets(g)
        if targets:
            self.mem[wk] = 0
            self.fight_camps(targets, kite, use_spells)
            return True
        near = cheb(self.x, self.y, g.cx, g.cy) <= 6
        if near and g.state == 2:
            if g.mask.is_set(self.pos):
                return True
            free = g.mask & ~self.occ()
            if free.is_empty():
                return False
            if not self.step_field(f):
                self.step_to(free)
            return True
        if fd <= 1 and g.state == 1:
            # adjacent and still nothing visible: either hidden in a bush or already taken
            k = ("probe", g.i)
            n = self.mem.get(k, 0)
            if n < 2:
                self.mem[k] = n + 1
                free = g.mask & ~self.occ()
                if not free.is_empty() and self.step_to(free):
                    return True
            self.mem[k] = 0
            g.state = 3
            g.ready = r + max(10, g.resp // 2)
            return False
        self.travel(f, 1 if g.state == 1 else 0)
        return True

    def air_approach(self, g):
        """Reach an island group with a dash: walk to a mainland tile within dash range (2) of
        the island's land, then dash onto it. Gives the group up when that is impossible or
        takes too long (only single hops from the mainland are attempted)."""
        if not self.reach.is_set(self.pos):
            return self.recall() or self.go_home()
        k = ("air", g.i)
        n = self.mem.get(k, 0) + 1
        self.mem[k] = n
        if n > 60:
            self.mem[k] = 0
            g.island = False
            g.bad = True
            return False
        data = g.afield
        if data is None:
            t = g.tiles[0]
            land = self.block.reachable_tiles(Vec2(t[0], t[1]), 250)
            near = land
            for _ in range(2):
                x = near | near.shift_right(1) | near.shift_right(-1)
                near = x | x.shift_up(1) | x.shift_up(-1)
            launch = self.reach & near & ~self.block
            data = (land, launch)
            g.afield = data
        land, launch = data
        if launch.is_empty():
            g.island = False
            g.bad = True
            return False
        if not launch.is_set(self.pos):
            if not self.step_to(launch):
                self.mem[k] = n + 2
            return True
        e = self.ability(K_DASH)
        if e is None or not self.ab_ready(e):
            return True                      # on a launch tile: wait for the dash
        area = Bitboard()
        area.draw_chebyshev(self.pos, int(e[2]) if e[2] else 2)
        cand = (area & land & ~self.block & ~self.occ()).positions()
        cand.sort(key=lambda p: cheb(p.x, p.y, g.cx, g.cy))
        for v in cand[:4]:
            if self.use(e, v):
                was = self.moved
                self._moved_to(v)
                self.moved = was
                return True
        self.mem[k] = n + 5
        return True

    # ---------------------------------------------------------------- banking
    def adjacent_altar(self):
        rng = cambc.constants.SUBMIT_GEMS_RANGE
        for ax, ay in self.altar_pos:
            if cheb(ax, ay, self.x, self.y) <= rng:
                return ax, ay
        return None

    def altar_dist(self):
        f = self.altar_field
        if f is None:
            return INF
        return f.get(self.pos)

    def try_submit(self):
        if self.gems <= 0:
            return False
        a = self.adjacent_altar()
        if a is None:
            return False
        v = Vec2(a[0], a[1])
        try:
            if vision.has_altar_lock(v):
                lock = vision.altar_lock_at(v)
                if lock.is_enemy():
                    if self.can_attack:
                        self.try_attack(lock)
                    return True
        except Exception:
            pass
        try:
            self.me.submit_gems(v)
            return True
        except Error:
            return False

    def go_altar(self, dash=True):
        if self.try_submit():
            return True
        f = self.altar_field
        if f is None:
            return False
        if f.get(self.pos) >= INF:
            # no walking path to any altar from here (island): recall, then walk from spawn
            return self.recall() or True
        self.travel(f, 1, dash)
        return True

    # ---------------------------------------------------------------- items
    def can_shop(self):
        return (not self.alive) or self.at_spawn or self.type == CT.TAVI

    def buy(self, item, n=1):
        """Buy up to n shards of item with the gold at hand. Returns how many were bought."""
        if n <= 0:
            return 0
        try:
            gold = self.me.gold_count()
        except Error:
            return 0
        cost = 30
        try:
            cost = item.cost()
        except Exception:
            pass
        n = min(n, gold // max(1, cost))
        if n <= 0:
            return 0
        try:
            self.me.buy(item, n)
        except Error:
            return 0
        self.gold = gold - n * cost
        self.mem["bought"] = self.mem.get("bought", 0) + n
        return n

    def count_item(self, item):
        try:
            return self.me.item_count()[int(item)]
        except Exception:
            return 0

    def buy_consumable(self, kind):
        try:
            if self.me.consumables()[int(kind)].count() > 0:
                return False
            if not self.me.can_buy(kind):
                return False
            self.me.buy(kind)
            self.gold = self.me.gold_count()
            return True
        except Exception:
            return False

    def consumable_count(self, kind):
        try:
            return self.me.consumables()[int(kind)].count()
        except Exception:
            return 0

    def lock_altar(self, ax, ay):
        if cheb(ax, ay, self.x, self.y) > 2 or self.consumable_count(ConsumableType.ALTAR_LOCK) <= 0:
            return False
        v = Vec2(ax, ay)
        try:
            if vision.has_altar_lock(v):
                return False
            return self.me.consumables()[int(ConsumableType.ALTAR_LOCK)].use(v)
        except Exception:
            return False

    def lock_enemy_tribute(self):
        """Lock an altar where a visible enemy is tributing. True on success."""
        for u in self.enemies:
            if u.st & 4:
                for ax, ay in self.altar_pos:
                    if cheb(ax, ay, u.x, u.y) <= 1 and self.lock_altar(ax, ay):
                        return True
        return False

    def place_ward_towards(self, x, y):
        try:
            if self.me.ward_cooldown() > 0:
                return False
            d = cheb(self.x, self.y, x, y)
            if d <= 2:
                tx, ty = x, y
            else:
                tx = self.x + (2 * (x - self.x)) // d
                ty = self.y + (2 * (y - self.y)) // d
            tx = min(self.W - 1, max(0, tx))
            ty = min(self.H - 1, max(0, ty))
            v = Vec2(tx, ty)
            if self.walls.is_set(v):
                v = self.pos
            return self.me.place_ward(v)
        except Exception:
            return False

    # ------------------------------------------------------------------ turn
    def log_error(self, where, e):
        self.errors += 1
        if self.errors <= 12:
            print("err", where, type(e).__name__, e, flush=True)

    def turn(self):
        gn = self.genome
        if not self.ready:
            self.init()
            if cambc.fuel_remaining() < 1500000:
                return
        self.refresh()
        if not self.alive:
            try:
                gn.SHOP.shop(self)
            except Exception as e:
                self.log_error("shop", e)
            dead = getattr(gn.EXTRA, "dead", None)
            if dead is not None:
                try:
                    dead(self)
                except Exception as e:
                    self.log_error("dead", e)
            return
        if self.submitting or self.teleporting or self.recalling:
            try:
                gn.EXTRA.channel(self)
            except Exception as e:
                self.log_error("channel", e)
            return
        if self.can_shop():
            try:
                gn.SHOP.shop(self)
            except Exception as e:
                self.log_error("shop", e)
        self.update_groups()
        if self.enemies or self.mem.get("threats"):
            self.note_threats()
        try:
            gn.EXTRA.pre(self)
        except Exception as e:
            self.log_error("pre", e)
        for name in gn.ORDER:
            mod = gn.GENES.get(name)
            if mod is None:
                continue
            try:
                if mod.act(self):
                    self.mem["why"] = name
                    break
            except Exception as e:
                self.log_error(name, e)
        try:
            gn.EXTRA.post(self)
        except Exception as e:
            self.log_error("post", e)
        # never park on the spawn tile of a respawning group: it delays that respawn
        if not self.moved and self.can_move and not self.lock_move:
            g = self.tile_group.get((self.x, self.y))
            if g is not None and g.state == 3:
                try:
                    self.step_to(self.ring_tiles(g, 1))
                except Exception as e:
                    self.log_error("unblock", e)
        if TRACE and self.round % TRACE == 0:
            print("T", self.round, int(self.type), "pos", self.x, self.y, "hp", int(self.hp), "gems", self.gems,
                  "gold", self.gold, "why", self.mem.get("why"), "fuel", cambc.fuel_remaining(), flush=True)
