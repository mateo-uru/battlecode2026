"""Fight gene (from brawler, gen 2): still engages what is close, but brawler fought at 0.8 odds
and lost 248 gems per lost game to kills. Now 1.05 odds with every visible enemy counted,
1.5 while carrying a bag, and below 35% health it stops trading."""


def act(b):
    best = None
    for u in b.enemies:
        if u.in_spawn or u.d > 7:
            continue
        s = u.d * 100 + u.hp * 0.1
        if best is None or s < best[0]:
            best = (s, u)
    if best is None:
        return False
    u = best[1]
    if u.hp <= b.str * 3 and u.d <= b.arange + 1:
        return b.engage(u)
    mine, theirs, ne = b.odds()
    need = 1.05 if b.gems < 25 else 1.5
    if b.recently_fled():
        need += 0.3
    if b.hpf >= 0.35 and mine >= theirs * need:
        return b.engage(u)
    if u.d <= 3:
        return b.retreat(u)
    return False
