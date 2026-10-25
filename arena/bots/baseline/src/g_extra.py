"""Extra gene (brawler): shield whenever something hits us."""


def pre(b):
    b.shield_self()


def post(b):
    pass


def channel(b):
    # a recall is pointless if an enemy we could kill walks by
    for u in b.enemies:
        if u.d <= 2 and u.hp <= b.str * 1.5 and b.recalling and b.hpf > 0.3:
            b.cancel_channel()
            return
