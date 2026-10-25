"""Survive gene (from goldrush, gen 2): recall at 35% or when 2-3 more hits would kill us;
recall to shop when 150 gold sit unspent (kept from gen 1)."""
from body import CT


def act(b):
    if b.at_spawn and b.hpf < 0.9 and b.dmg_taken <= 0 and b.mem.get("hw", 0) < 6:
        b.mem["hw"] = b.mem.get("hw", 0) + 1
        return True
    b.mem["hw"] = 0
    if b.hpf < 0.35 or b.dmg_taken * 2.5 >= b.hp:
        if b.try_submit():
            return True
        if (b.dmg_taken > 0 or b.nearest_enemy(5) is not None) and b.retreat():
            return True
        return b.recall() or b.flee()
    if (b.type != CT.TAVI and b.gems == 0 and b.gold >= 150 and not b.enemies and b.dmg_taken <= 0
            and b.spawn_field.get(b.pos) > 8):
        return b.recall()
    return False
