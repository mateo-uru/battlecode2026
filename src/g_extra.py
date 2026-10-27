"""Enhanced extra gene: shield_self + dead claim clear + smart altar locks + free wards + lethal channel cancel."""
from body import cheb


def pre(b):
    b.shield_self()
    b.lock_enemy_tribute()
    if b.enemies:
        for u in b.enemies:
            if not u.in_spawn and (u.gems >= 12 or (u.st & 4)):
                for ax, ay in b.altar_pos:
                    if cheb(ax, ay, u.x, u.y) <= 3 and b.lock_altar(ax, ay):
                        return


def post(b):
    if not b.enemies and b.altar_pos:
        ax, ay = b.altar_pos[0]
        b.place_ward_towards(ax, ay)


def channel(b):
    for u in b.enemies:
        if u.d <= 2 and u.hp <= b.str * 1.5 and b.recalling and b.hpf > 0.3:
            b.cancel_channel()
            return
    if b.submitting and b.dmg_taken > 0 and b.hp <= b.dmg_taken * 1.5:
        b.cancel_channel()
        b.shield_self(force=True)
        b.flee()


def dead(b):
    b.claim(None)
    b.mem["br_obj"] = None
    b.mem["banking"] = False
