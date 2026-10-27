"""Patch 2.0.0 Shop gene: Prospector/Monster -> Jungle -> Capture -> Durability -> Skirmish -> Collectors -> Bruiser."""
from body import CASTERS, CT, GEM_CLUSTER, GOLD_CLUSTER, ConsumableType, shard


def _build_fams(b):
    fams = b.mem.get("p2_fams")
    if fams is not None:
        return fams
    c_gems = 0
    for g in b.groups:
        if GEM_CLUSTER in g.kinds or GOLD_CLUSTER in g.kinds:
            c_gems += g.gems + g.gold // 3
    if c_gems >= 25:
        fams = ["PROSPECTOR", "MONSTER", "CAPTURE", "JUNGLE", "DURABILITY", "SKIRMISH", "COLLECTORS", "BRUISER"]
    elif b.ranged:
        fams = ["MONSTER", "CAPTURE", "DURABILITY", "JUNGLE", "SKIRMISH", "COLLECTORS", "BRUISER"]
    else:
        fams = ["MONSTER", "JUNGLE", "CAPTURE", "DURABILITY", "SKIRMISH", "COLLECTORS", "BRUISER"]
    b.mem["p2_fams"] = fams
    return fams


def shop(b):
    if b.gold < 10:
        return
    # Buy Altar Lock once we have at least 1 emblem (n >= 5) and spare 10g
    n = b.mem.get("gr_n", 0)
    if b.alive and n >= 5 and (b.gold % 30 >= 10 or b.gold >= 160):
        b.buy_consumable(ConsumableType.ALTAR_LOCK)

    if b.gold < 30:
        return
    # Tavi is an attack-damage marksman (+5 str/shard + AttackReset), not a pure Focus caster!
    is_caster = (b.type in CASTERS) and (b.type != CT.TAVI)
    stat = "FOCUS" if is_caster else ("HEALTH" if b.type == CT.RYTH else "STRENGTH")
    fams = _build_fams(b)
    for _ in range(25):
        fam_idx = min(n // 5, len(fams) - 1)
        fam = fams[fam_idx]
        emblem_slot = n // 5
        if fam == "DURABILITY":
            st = "HEALTH"
        elif fam == "JUNGLE":
            st = "HEALTH" if not b.ranged else stat
        elif fam == "BRUISER":
            # Alternate primary stat Bruiser (5 stat + 1 hp + 1 other) and Health Bruiser (5 hp + 1 str + 1 foc)
            st = "HEALTH" if (emblem_slot % 3 == 1) else stat
        else:
            st = stat
        if b.buy(shard(fam, st), 1) == 0:
            break
        n += 1
        if n % 5 == 0:
            b.mem["has_" + fam] = True
    b.mem["gr_n"] = n
