"""Farm gene (brawler): the closest group that is worth anything; melee bodies soak camp hits,
so a group is taken if the damage taken stays below twice our health."""
from body import cheb


def pick(b):
    claimed = b.claims()
    dps = b.str + 0.25 * b.foc
    best = None
    for g in b.groups:
        if g.bad or g.i in claimed:
            continue
        r = b.round
        d = (b._gd or b.group_dists())[g.i]
        if g.state == 3:
            if g.ready > r + d + 6:
                continue
            d = max(d, g.ready - r)
        clear = 0 if g.state == 2 else g.hp_left / max(1.0, dps)
        if g.dmg * clear > b.hp * 2.0:
            continue
        s = (g.gems + 0.2 * g.gold) / (d * 1.5 + clear + 4)
        if b.group_danger(g):
            s *= 0.6          # gen 2: enemies seen there recently
        if best is None or s > best[0]:
            best = (s, g)
    return None if best is None else best[1]


def act(b):
    g = b.mem.get("br_obj")
    if g is None or g.bad or b.round - b.mem.get("br_t", 0) > 90:
        g = pick(b)
        b.mem["br_obj"] = g
        b.mem["br_t"] = b.round
        b.claim(g)
    if g is None:
        return b.step_toward(b.W // 2, b.H // 2, 3)
    if not b.farm_group(g, kite=False):
        g2 = pick(b)
        b.mem["br_obj"] = g2
        b.mem["br_t"] = b.round
        b.claim(g2)
        if g2 is not None and g2 is not g:
            b.farm_group(g2, kite=False)
    return True
