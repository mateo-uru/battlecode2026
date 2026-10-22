"""Shop gene (goldrush): Treasure emblem of the main stat (+20% gold), then power shards."""
from body import CASTERS, CT, shard


def shop(b):
    if b.gold < 30:
        return
    stat = "FOCUS" if b.type in CASTERS else ("HEALTH" if b.type == CT.RYTH else "STRENGTH")
    t = b.mem.get("gr_tr", 0)
    if t < 5:
        t += b.buy(shard("TREASURE", stat), 5 - t)
        b.mem["gr_tr"] = t
        if t < 5:
            return
    n = b.mem.get("gr_n", 0)
    for _ in range(20):
        if b.buy(shard("POWER", "HEALTH" if n % 3 == 2 else stat), 1) == 0:
            break
        n += 1
    b.mem["gr_n"] = n
