"""Movement: breadth-first distance fields from the native SDK, cached per goal set.

Static fields (terrain only) are cached by key and reused every turn; next_moves_from() gives every
optimal step in one call, and units are skipped when choosing among them. If all optimal steps are
blocked by units, one dynamic field is computed around them.
UPGRADE: danger-weighted fields (cost of tiles inside enemy/camp range), bush-aware ambush routes,
teleport crystals across walls, and multi-turn reservations so allies do not swap-block each other.
"""
import cambc
from cambc import vision, Bitboard, DistanceField, Team

import budget
from mapinfo import INF

MAX_CACHE = 40


def dist(a, b):
    return a.chebyshev_distance(b)


def area(p, r):
    b = Bitboard()
    b.draw_chebyshev(p, r)
    return b


def single(p):
    b = Bitboard()
    b.set(p)
    return b


class Nav:
    def __init__(self, info):
        self.static = info.blocked | info.enemy_home
        self.cache = {}

    def field(self, key, goals):
        f = self.cache.get(key)
        if f is None:
            budget.check()
            if len(self.cache) >= MAX_CACHE:
                self.cache.pop(next(iter(self.cache)))
            f = DistanceField()
            f.compute(self.static, goals & ~self.static, Bitboard())
            self.cache[key] = f
        return f

    def blocked_now(self, pos):
        b = self.static | vision.champion_tiles() | vision.camp_tiles() | vision.teleport_tiles()
        b.set(pos, False)
        return b

    def step(self, me, goals, key=None, dash=False):
        """Move one step (or dash) towards the goal tiles. Returns True if the champion moved.

        key: cache the terrain-only field for these goals under this key (for fixed goal sets).
        """
        if not me.can_move():
            return False
        pos = me.position()
        budget.check()
        if key is not None:
            field = self.field(key, goals)
            here = field.get(pos)
            if here == 0 or here >= INF:
                return False
            blocked = self.blocked_now(pos)
            if dash and self._dash(me, field, blocked, here):
                return True
            for d in field.next_moves_from(pos):
                p = pos + d
                if blocked.is_set(p):
                    continue
                try:
                    if me.move_absolute(p):
                        return True
                except cambc.Error:
                    pass
            # every optimal step is taken by a unit (or hid one): walk around them
        else:
            blocked = self.blocked_now(pos)
        free = goals & ~blocked
        if free.is_empty() or free.is_set(pos):
            return False
        field = DistanceField()
        field.compute_to(blocked, free, single(pos), Bitboard())
        here = field.get(pos)
        if here >= INF:
            # Walled in by units: plan through allies (they move on) and take any free better step.
            through = blocked & ~vision.champion_tiles(Team.ALLY)
            through.set(pos, False)
            field.compute_to(through, goals & ~through, single(pos), Bitboard())
            here = field.get(pos)
            if here >= INF:
                return False
            for p in blocked.reachable_tiles(pos, 1).positions():
                if p != pos and field.get(p) < here:
                    try:
                        if me.move_absolute(p):
                            return True
                    except cambc.Error:
                        pass
            return False
        if dash and key is None and self._dash(me, field, blocked, here):
            return True
        for d in field.next_moves_from(pos):
            try:
                if me.move_absolute(pos + d):
                    return True
            except cambc.Error:
                pass
        return False

    def _dash(self, me, field, blocked, here):
        if not me.can_cast():
            return False
        for a in me.abilities():
            if not a.is_dash() or not a.is_ready():
                continue
            try:
                landing = a.valid_tiles() & ~blocked
            except cambc.Error:
                return False
            best, cost = None, here - 2          # only worth it if it gains more than a walk
            for p in landing.positions():
                c = field.get(p)
                if c < cost:
                    best, cost = p, c
            if best is not None:
                try:
                    return bool(a.use(best))
                except cambc.Error:
                    return False
        return False

    def flee(self, me, threats, home_field):
        """Step to the neighbour that is furthest outside the threats' reach, drifting home."""
        if not me.can_move() or not threats:
            return False
        pos = me.position()
        blocked = self.blocked_now(pos)

        def score(p):
            clear = min(dist(p, t) - r for t, r in threats)
            return clear * 6 - home_field.get(p) * 0.05

        cells = blocked.reachable_tiles(pos, 1).positions()
        cells.sort(key=score, reverse=True)
        for p in cells:
            if p == pos:
                return False
            try:
                if me.move_absolute(p):
                    return True
            except cambc.Error:
                pass
        return False
