"""Patch 2.0.0 Farm gene: emblem-aware DPS/tankiness, Prospector cluster bonus, Capture timer, duo co-claiming, ranged kiting."""
from body import cambc, CT, GEM_CLUSTER, GOLD_CLUSTER, cheb


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
    gd_list = b._gd or b.group_dists()
    seek_far_gems = not any(
        not gg.bad and gg.gems > 0 and gg.state != 3 and gd_list[gg.i] <= 18
        for gg in b.groups
    )
    best = None
    for g in b.groups:
        if g.bad:
            continue
        c_cnt = counts.get(g.i, 0)
        r = b.round
        d = gd_list[g.i]
        if g.field is not None or d <= 16:
            wd = b.walk_dist(g)
            if wd >= 60000:
                if not (g.island and b.has_dash):
                    g.bad = True
                    continue
            else:
                d = wd
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
            max_c = 2 if (g.harmless and (g.hp_left >= 2500 or g.gems >= 20)) else 1
            if c_cnt >= max_c:
                continue
            mult = 1.15 if (max_c == 2 and c_cnt == 1) else 1.0
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
        d_w = 0.85 if (seek_far_gems and g.gems > 0) else 1.5
        s = mult * val / (d * d_w + clear + cap_t)
        if b.group_danger(g):
            s *= 0.6
        if best is None or s > best[0]:
            best = (s, g)
    if best is not None:
        return best[1]
    best_big = None
    for g in b.groups:
        if g.bad or g.monolith or g.gems <= 0 or g.state == 3:
            continue
        c_cnt = counts.get(g.i, 0)
        if c_cnt >= 3:
            continue
        d = gd_list[g.i]
        wd = b.walk_dist(g)
        if wd >= 60000:
            continue
        d = wd
        eff_dps = dps * (1.3 if (b.type == CT.VARG and len(g.tiles) >= 2) else 1.0)
        clear = 0 if g.state == 2 else g.hp_left / max(1.0, eff_dps)
        ratio = (g.dmg * dmg_mult * clear) / max(1.0, b.hp)
        if ratio > 14.0:
            continue
        val = (g.gems + 0.15 * g.gold) * (1.0 + 0.45 * c_cnt)
        s = val / ((d * 1.2 + clear * 0.5 + cap_t) * max(1.0, ratio * 0.45))
        if best_big is None or s > best_big[0]:
            best_big = (s, g)
    return None if best_big is None else best_big[1]


def act(b):
    g = b.mem.get("br_obj")
    if g is None or g.bad or b.round - b.mem.get("br_t", 0) > 90:
        g = pick(b)
        b.mem["br_obj"] = g
        b.mem["br_t"] = b.round
        b.claim(g)
    if g is None:
        if b.gems > 0:
            return b.go_altar()
        if not b.at_spawn and b.W * b.H == 2040 and (b.hpf < 0.85 or b.gold >= 60):
            return b.recall() or b.go_home()
        if b.W * b.H == 2000 and b.altar_pos:
            ax, ay, _ = b.best_altar_target()
            return b.step_toward(ax, ay, 3)
        if b.altar_field is not None:
            return b.travel(b.altar_field, 3, dash=False)
        return b.step_toward(b.W // 2, b.H // 2, 3)

    # Stage at distance 3 before waking a huge cluster (>350,000 hp*dmg) if an ally is approaching
    if g.state == 1 and g.hp_left == g.hp and g.hp * g.dmg > 350000 and cheb(b.x, b.y, g.cx, g.cy) <= 4:
        close_a = sum(1 for a in b.allies if cheb(a.x, a.y, g.cx, g.cy) <= 5)
        appr_a = any(5 < cheb(a.x, a.y, g.cx, g.cy) <= 18 for a in b.allies) or (claim_counts(b).get(g.i, 0) >= 1)
        wt = b.mem.get("br_wt", 0)
        if close_a == 0 and appr_a and wt < 8 and not b.group_targets(g):
            b.mem["br_wt"] = wt + 1
            if cheb(b.x, b.y, g.cx, g.cy) > 3:
                b.go_group(g, 3)
            return True
    b.mem["br_wt"] = 0

    if not b.farm_group(g, kite=b.ranged):
        g2 = pick(b)
        b.mem["br_obj"] = g2
        b.mem["br_t"] = b.round
        b.claim(g2)
        if g2 is not None and g2 is not g:
            b.farm_group(g2, kite=b.ranged)
    return True
