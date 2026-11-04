"""Guard gene (Stage X): on single-altar maps one champion holds the altar zone, punishes arriving enemy carriers
and cashes in at once. MODE 'full' = always guard; 'react' = only when an enemy carrier is near the altar."""
from body import cheb, CT

MODE = "full"
PREF = (CT.VARG, CT.VENDETTA, CT.RYTH)


def is_guard(b):
    g = b.mem.get("guard_role")
    if g is None:
        g = False
        if len(b.altar_pos) == 1 and b.team_size >= 3:
            pick = None
            for t in PREF:
                if t in b.team_types:
                    pick = t
                    break
            if pick is None:
                pick = b.team_types[-1]
            g = (b.type == pick)
        b.mem["guard_role"] = g
    return g


def act(b):
    if not b.altar_pos or b.round < 40:
        return False
    ax, ay = b.altar_pos[0]
    da = cheb(b.x, b.y, ax, ay)
    carriers = [u for u in b.enemies if not u.in_spawn and cheb(u.x, u.y, ax, ay) <= 6 and (u.gems >= 10 or (u.st & 4))]
    if MODE == "react":
        if b.gems >= 20 or not carriers or da > 10 or b.hpf < 0.5:
            return False
        mine, theirs, ne = b.odds()
        if mine >= theirs * 0.9:
            u = min(carriers, key=lambda u: u.d)
            return b.engage(u)
        return False
    if not is_guard(b):
        return False
    if b.gems > 0 and b.try_submit():
        return True
    if b.hpf < 0.4:
        return False
    near = [u for u in b.enemies if not u.in_spawn and cheb(u.x, u.y, ax, ay) <= 5]
    if near:
        mine, theirs, ne = b.odds()
        u = min(near, key=lambda u: (-(u.st & 4), -u.gems, u.d))
        if mine >= theirs * 0.8 or (u.st & 4):
            return b.engage(u)
        if u.d <= 3:
            return b.retreat(u)
        return False
    g0 = b.mem.get("br_obj")
    if da > 2 and (g0 is None or getattr(g0, "bad", False) or cheb(g0.cx, g0.cy, ax, ay) > 6):
        b.claim(None)
        b.mem["br_obj"] = None
        return b.step_toward(ax, ay, 2)
    return False   # parked at the altar: let farm gene work camps (it will walk off only if a camp is picked)
