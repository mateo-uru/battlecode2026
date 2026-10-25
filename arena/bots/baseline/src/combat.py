"""Snapshots of visible units, basic attacks and ability casts.

The scoring follows nameless' micro (kill > burst > chip, stun what is dangerous or channelling), plus
stun chaining (never stun a stunned target) and landing-damage dashes (Heart of Ruin).
Fuel: Python pays ~3k per engine getter, so ability readiness is read once per turn (begin_turn) and
AoE tiles are only tried on target tiles.
UPGRADE: simulate one exchange (our burst vs their burst) instead of per-cast greedy values; kite
with ranged champions (step out of melee reach after attacking); coordinate one focus target.
"""
import cambc
from cambc import vision, ChampionState

import budget
import config
from nav import dist

CHANNEL = ChampionState.RECALLING | ChampionState.SUBMITTING_GEMS | ChampionState.TELEPORTING

_ready = []            # abilities ready this turn (cleared after the turn's one successful cast)
_varg = False


def begin_turn(me, can_cast):
    global _ready, _varg
    _varg = int(me.champion_name()) == config.T_VARG
    _ready = [a for a in me.abilities() if a.is_ready()] if can_cast else []


class Target:
    __slots__ = ("unit", "pos", "hp", "maxhp", "strength", "focus", "range", "champ", "gems", "channel",
                 "stunned", "kind", "awake")

    def power(self):
        return (self.strength + self.focus * 0.25) * (0.25 + 0.75 * self.hp / max(1.0, self.maxhp))


def champions(team, skip_home=None, full=True):
    """Visible living champions. full=False skips gems/state/buffs (allies)."""
    out = []
    for c in vision.champions(team):
        try:
            hp = c.health()
            if hp <= 0:
                continue
            t = Target()
            t.unit, t.pos, t.hp = c, c.position(), hp
            if skip_home is not None and skip_home.is_set(t.pos):
                continue
            t.maxhp, t.strength, t.focus = c.max_health(), c.strength(), c.focus()
            t.champ, t.awake, t.kind = True, True, 0
            if full:
                t.range, t.gems = c.attack_range(), c.gem_count()
                t.channel = bool(c.state() & CHANNEL)
                t.stunned = c.buffs().has_stun()
            else:
                t.range, t.gems, t.channel, t.stunned = 1, 0, False, False
        except cambc.Error:
            continue
        out.append(t)
    return out


def camps(units):
    out = []
    for c in units:
        try:
            if not c.is_visible():
                continue
            hp = c.health()
            if hp <= 0:
                continue
            t = Target()
            t.unit, t.pos, t.hp, t.maxhp = c, c.position(), hp, hp
            t.strength, t.focus, t.range = c.strength(), 0.0, c.attack_range()
            t.champ, t.gems, t.channel, t.stunned, t.kind = False, 0, False, False, int(c.kind())
            t.awake = c.is_awake()
        except cambc.Error:
            continue
        out.append(t)
    return out


def attack(me, targets):
    if not targets or not me.can_attack():
        return False
    budget.check()
    tiles = me.attack_tiles()
    strength = me.strength()
    avoid = bystanders(targets) if _varg and config.AVOID_BYSTANDERS else None
    best, value = None, -1e30
    for t in targets:
        if not tiles.is_set(t.pos):
            continue
        if avoid is not None and not (avoid & _ring(t.pos, 1)).is_empty():
            continue                     # Varg's splash would wake the neighbours
        v = (1000 if t.hp <= strength else 0) - t.hp / max(1.0, strength)
        if t.champ:
            v += 30 + t.gems * 0.2 + (40 if t.channel else 0)
        if _varg:
            v += sum(15 for o in targets if o is not t and dist(o.pos, t.pos) <= 1)
        if v > value:
            best, value = t, v
    if best is None:
        return False
    try:
        me.attack(best.unit)
        best.hp -= strength
        return True
    except cambc.Error:
        return False


def bystanders(targets):
    """Sleeping camps that are not targets: area effects must not wake them (a monolith next door)."""
    avoid = vision.asleep_camp_tiles()
    if not config.AVOID_BYSTANDERS:
        avoid.clear()
    for t in targets:
        avoid.set(t.pos, False)
    return avoid


def spell(me, targets, allies, leader=None, attacked=False, defensive=False, stun_chain=True, blocked=None):
    """Cast the most valuable ready ability. allies: Target snapshots of visible allies."""
    global _ready
    if not _ready:
        return False
    budget.check()
    avoid = None
    best_v, best = 0.0, None
    origin = me.position()
    for a in _ready:
        try:
            if a.is_heal():
                if not allies:
                    continue
                tiles = a.valid_tiles()
                for t in allies:
                    missing = t.maxhp - t.hp
                    if missing < 80 or not tiles.is_set(t.pos):
                        continue
                    v = min(missing, a.heal_amount()) * (2 if t.hp < t.maxhp * 0.45 else 1)
                    if int(t.unit) == leader:
                        v *= 1.5
                    if v > best_v:
                        best_v, best = v, (a, t.unit)
            elif a.is_shield():
                incoming = sum(t.strength for t in targets if t.awake and dist(t.pos, origin) <= t.range)
                if incoming > 0 and not me.buffs().has_shield():
                    v = min(a.shield_amount(), incoming * 4) * (2 if defensive else 0.7)
                    if v > best_v:
                        best_v, best = v, (a, None)
            elif a.is_attack_reset():
                if not attacked:
                    continue
                tiles = me.attack_tiles()
                inside = sum(1 for t in targets if tiles.is_set(t.pos))
                if inside:
                    v = me.strength() * (1.5 if a.info().enhanced_attack else 1) * (min(3, inside) if _varg else 1)
                    if v > best_v:
                        best_v, best = v, (a, None)
            elif a.is_dash():
                info = a.info()
                if info.modifier <= 0 or not targets:
                    continue                 # plain dashes are movement (nav.py)
                amount = a.damage_amount()
                near = cambc.Bitboard()
                for t in targets:
                    near.draw_chebyshev(t.pos, info.radius)
                land = a.valid_tiles() & near
                if blocked is not None:
                    land &= ~blocked
                if avoid is None:
                    avoid = bystanders(targets)
                for p in land.positions():
                    if not (avoid & _ring(p, info.radius)).is_empty():
                        continue
                    v = 0.0
                    for t in targets:
                        if dist(p, t.pos) <= info.radius:
                            v += min(t.hp, amount) + (t.strength * 0.6 if not t.stunned else 0)
                    if v * 0.9 > best_v:
                        best_v, best = v * 0.9, (a, p)
            elif a.is_aoe_damage():
                info = a.info()
                if info.exclusive_with_movement and not me.can_move():
                    continue
                tiles = a.valid_tiles()
                amount, stun = a.damage_amount(), info.duration > 0
                if avoid is None:
                    avoid = bystanders(targets)
                for c in targets:                # centre on a target: cheap and nearly optimal
                    if not tiles.is_set(c.pos) or not (avoid & _ring(c.pos, info.radius)).is_empty():
                        continue
                    v = 0.0
                    for o in targets:
                        if dist(c.pos, o.pos) <= info.radius:
                            v += min(o.hp, amount) + (o.strength * 0.6 if stun and o.champ and not o.stunned else 0)
                    if v > best_v:
                        best_v, best = v, (a, c.pos)
            elif a.is_damage() or a.is_cc():
                info = a.info()
                if info.exclusive_with_movement and not me.can_move():
                    continue
                tiles = a.valid_tiles()
                amount = a.damage_amount()   # stuns with damage (Prism, Tavi, Ren) are AbilityCc
                cc = a.is_cc()
                for t in targets:
                    if not tiles.is_set(t.pos):
                        continue
                    if t.champ and not a.can_target_enemies() or not t.champ and not a.can_target_camps():
                        continue
                    if not t.champ and amount <= 0:
                        continue             # pure stuns are for champions
                    v = min(t.hp, amount)
                    if cc and t.champ:
                        if not (stun_chain and t.stunned):
                            v += t.strength * (2 if defensive else 0.8) + (250 if t.channel else 0)
                    elif cc and not t.stunned:
                        v += t.strength * 0.3
                    if t.champ and amount >= t.hp:
                        v += 150 + t.gems
                    if v > best_v:
                        best_v, best = v, (a, t.unit)
        except (cambc.Error, TypeError, ValueError, AttributeError):
            continue
    if best is None:
        return False
    a, target = best
    try:
        ok = bool(a.use(target)) if target is not None else bool(a.use())
    except cambc.Error:
        _ready = [r for r in _ready if r is not a]
        return False
    if ok:
        _ready = []                          # one successful cast per turn
    return ok


def _ring(p, r):
    b = cambc.Bitboard()
    b.draw_chebyshev(p, r)
    return b


def fight(me, targets, allies=(), leader=None, defensive=False, stun_chain=True):
    """One round of attacks and casts against targets; True if anything happened."""
    if not targets:
        return False
    if me.attack_range() <= 1:
        hit = attack(me, targets)
        cast = spell(me, targets, allies, leader, hit, defensive, stun_chain)
        return (cast and attack(me, targets)) or hit or cast
    cast = spell(me, targets, allies, leader, False, defensive, stun_chain)
    hit = attack(me, targets)
    if not cast and _ready:
        cast = spell(me, targets, allies, leader, hit, defensive, stun_chain)
        if cast:
            hit = attack(me, targets) or hit
    return hit or cast


def support(me, allies, leader):
    """Heal/shield without targets (Willow keeps the leader topped up between fights)."""
    return spell(me, [], allies, leader)
