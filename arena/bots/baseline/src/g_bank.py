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
    ad = b.altar_dist()
    late = b.round + ad + 30 >= b.max_rounds
    win = cambc.global_submitted_gems(Team.ALLY) + b.gems >= b.win_gems
    hot = b.gems >= 15 and any(u.d <= 8 and not u.in_spawn for u in b.enemies)
    want = b.mem.get("banking") or b.gems >= 40 or ad <= 4 or late or win or hot
    b.mem["banking"] = want
    return b.go_altar() if want else False
