"""Bank gene (from goldrush, gen 2): bank at 40 gems (gen 1: 40; goldrush lost 86 carried gems per lost game), or at once with
15+ gems when an enemy is in sight, or when an altar is within 4."""
import cambc
from body import Team


def act(b):
    if b.gems <= 0:
        b.mem["banking"] = False
        return False
    if b.try_submit():
        return True
    if b.W * b.H == 2050 and b.round < b.mem.get("bank_wait", 0):
        return False
    ad = b.altar_dist()
    late = b.round + ad + 30 >= b.max_rounds
    win = cambc.global_submitted_gems(Team.ALLY) + b.gems >= b.win_gems
    hot = b.gems >= 15 and any(u.d <= 8 and not u.in_spawn for u in b.enemies)
    want = b.mem.get("banking") or b.gems >= 40 or ad <= 4 or late or win or hot
    b.mem["banking"] = want
    if not want:
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
    return b.go_altar()
