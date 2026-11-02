import cambc
from body import cheb
from body import Team


def act(b):
    if b.gems <= 0:
        b.mem["banking"] = False
        b.mem["bank_ad"] = 9999
        b.mem["bank_st"] = 0
        return False
    if b.try_submit():
        return True
    if b.round < b.mem.get("bank_wait", 0) and (b.gems < 30 or b.W * b.H == 1681) and b.round < b.max_rounds - 200:
        return False
    ad = b.altar_dist()
    late = ad < 1000 and (b.round + ad + 35 >= b.max_rounds)
    win = cambc.global_submitted_gems(Team.ALLY) + b.gems >= b.win_gems
    hot = (b.gems >= 14 and any(u.d <= 8 and not u.in_spawn for u in b.enemies)) or (b.gems >= 20 and b.hpf < 0.48)
    near_altar = (b.gems >= 12 and ad <= 5) or (b.gems >= 24 and ad <= 8)
    need = min(38, 20 + 0.6 * ad) if ad < 1000 else 38
    opp = False
    if b.gems >= 16 and ad < 1000:
        g0 = b.mem.get("br_obj")
        if g0 is not None and not g0.bad:
            cd = max(1, cheb(b.x, b.y, g0.cx, g0.cy))
            opp = ad <= 0.5 * (cd + ad)
    want = b.mem.get("banking") or b.gems >= need or ad <= 4 or near_altar or late or win or hot or opp
    b.mem["banking"] = want
    if not want:
        b.mem["bank_ad"] = 9999
        b.mem["bank_st"] = 0
        return False
    if b.W * b.H == 2050:
        prev_ad = b.mem.get("bank_ad", 9999)
        st = b.mem.get("bank_st", 0)
        st = st + 1 if ad >= prev_ad else 0
        b.mem["bank_ad"] = ad
        b.mem["bank_st"] = st
        if st > 12:
            b.mem["banking"] = False
            b.mem["bank_st"] = 0
            b.mem["bank_wait"] = b.round + 80
            return False
    else:
        # stuck on the way (e.g. the altar field runs through a living camp): no new closest
        # approach for 15 turns -> farm for 80 rounds, then try again
        best = b.mem.get("bank_ad", 9999)
        st = 0 if (ad < best or (ad <= 1 and not any(u.d <= 4 and not u.in_spawn for u in b.enemies))) else b.mem.get("bank_st", 0) + 1
        b.mem["bank_ad"] = min(ad, best)
        b.mem["bank_st"] = st
        if (st > 15 and b.gems < 30 and b.round < b.max_rounds - 200) or st > 40:
            b.mem["banking"] = False
            b.mem["bank_ad"] = 9999
            b.mem["bank_st"] = 0
            b.mem["bank_wait"] = b.round + 80
            return False
    b.claim(None)
    return b.go_altar()
