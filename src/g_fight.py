"""Fight gene (disciplined altar-denier & bag-punisher)."""


def act(b):
    best = None
    for u in b.enemies:
        if u.in_spawn or u.d > 7:
            continue
        submitting = bool(u.st & 4)
        bonus = -350 if submitting else (-min(250, u.gems * 8) if u.gems >= 20 else 0)
        s = u.d * 100 + u.hp * 0.1 + bonus
        if best is None or s < best[0]:
            best = (s, u)
    if best is None:
        return False
    u = best[1]
    submitting = bool(u.st & 4)
    if u.hp <= b.str * 3 and u.d <= b.arange + 1:
        return b.engage(u)
    if submitting and u.d <= b.arange + 2 and b.hpf >= 0.4:
        return b.engage(u)
    mine, theirs, ne = b.odds()
    need = 1.05 if b.gems < 25 else 1.5
    if submitting and b.gems < 25:
        need = 0.92
    if b.recently_fled():
        need += 0.3
    if b.hpf >= 0.35 and mine >= theirs * need:
        return b.engage(u)
    if u.d <= 3:
        return b.retreat(u)
    return False
