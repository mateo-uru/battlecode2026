"""Patch 2.0.0 Farm gene: emblem-aware DPS/tankiness, Prospector cluster bonus, Capture timer, duo co-claiming, ranged kiting."""
from body import CT, GEM_CLUSTER, GOLD_CLUSTER, cheb


def claim_counts(b):
    counts = {}
    for i in range(6):
        if i == b.slot:
            continue
        v = b.mem_get(i)
        if v:
            gi = v - 1
            counts[gi] = counts.get(gi, 0) + 1
    return counts


def pick(b):
    counts = claim_counts(b)
    dps = b.str + 0.25 * b.foc
    if b.mem.get("has_MONSTER"):
        dps *= 1.15
    if b.mem.get("has_COLLECTORS"):
        dps *= 1.06
    dmg_mult = (0.70 if b.mem.get("has_JUNGLE") else 1.0) * (0.90 if b.mem.get("has_DURABILITY") else 1.0)
    cap_t = 2.5 if b.mem.get("has_CAPTURE") else 4.0
    has_prosp = b.mem.get("has_PROSPECTOR", False)
    best = None
    for g in b.groups:
        if g.bad:
            continue
        c_cnt = counts.get(g.i, 0)
        r = b.round
        d = (b._gd or b.group_dists())[g.i]
        if g.state == 3:
            if g.ready > r + d + 6:
                continue
            d = max(d, g.ready - r)
        eff_dps = dps * (1.3 if (b.type == CT.VARG and len(g.tiles) >= 2) else 1.0)
        clear = 0 if g.state == 2 else g.hp_left / max(1.0, eff_dps)
        eff_dmg = g.dmg * dmg_mult
        ratio = (eff_dmg * clear) / max(1.0, b.hp)
        max_ratio = 3.5 if (g.elk and g.gems > 0 and b.round >= 1000 and b.W * b.H == 3000) else 2.0

        if ratio <= max_ratio:
            if c_cnt >= 1:
                continue
            mult = 1.0
        else:
            if ratio > 3.8 or c_cnt >= 2:
                continue
            if c_cnt == 1 and d <= 16:
                clear *= 0.55
                mult = 1.25
            elif c_cnt == 0 and any(cheb(a.x, a.y, g.cx, g.cy) <= 10 for a in b.allies):
                clear *= 0.6
                mult = 1.15
            else:
                continue

        val = g.gems + (0.25 if b.round < 250 else 0.20) * g.gold
        if GEM_CLUSTER in g.kinds or GOLD_CLUSTER in g.kinds:
            val *= (1.35 if has_prosp else 1.10)
        s = mult * val / (d * 1.5 + clear + cap_t)
        if b.group_danger(g):
            s *= 0.6
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
        if not b.at_spawn and b.W * b.H == 2040 and (b.hpf < 0.85 or b.gold >= 60):
            return b.recall() or b.go_home()
        return b.step_toward(b.W // 2, b.H // 2, 3)
    if not b.farm_group(g, kite=b.ranged):
        g2 = pick(b)
        b.mem["br_obj"] = g2
        b.mem["br_t"] = b.round
        b.claim(g2)
        if g2 is not None and g2 is not g:
            b.farm_group(g2, kite=b.ranged)
    return True
