"""Survive gene: release camp claim when retreating/recalling so allies can take the camp and we don't walk back into danger."""
from body import CT


def act(b):
    if b.at_spawn and b.hpf < 0.9 and b.dmg_taken <= 0 and b.mem.get("hw", 0) < 6:
        b.mem["hw"] = b.mem.get("hw", 0) + 1
        return True
    b.mem["hw"] = 0
    if b.hpf < 0.35 or b.dmg_taken * 2.5 >= b.hp:
        if b.try_submit():
            return True
        b.claim(None)
        b.mem["br_obj"] = None
        if (b.dmg_taken > 0 or b.nearest_enemy(5) is not None) and b.retreat():
            return True
        return b.recall() or b.flee()
    if (b.type != CT.TAVI and b.gems == 0 and b.gold >= 150 and not b.enemies and b.dmg_taken <= 0
            and b.spawn_field.get(b.pos) > 8):
        b.claim(None)
        b.mem["br_obj"] = None
        return b.recall()
    return False
