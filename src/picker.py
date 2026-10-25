"""Pick which bot plays this map: bbot by default, src on maps matching structural features or known sweeps.

Rule: src plays a map if it won both games there (one from each side) or matches the zero-fuel
structural classifier for compact low-wall arenas, high-altar multi-lane maps, or huge moderate-bush
macro maps. Every other map gets bbot.

Maps are recognised by cheap public geometry (size and tile counts), the same for both
sides and for the draft and every champion.
"""
from cambc import game_map

SRC, BBOT = "src", "bbot"
FORCE = None  # set to SRC or BBOT for experiments

# (width, height, walls, holes, altars, bushes) -> brain.
SRC_MAPS = {
    (30, 30, 0, 108, 2, 16): SRC,        # gemfight     1042:129, 1031:75   +1869
    (45, 30, 30, 354, 2, 14): SRC,       # swirl        979:15, 953:64      +1853
    (41, 30, 36, 22, 1, 24): SRC,        # eight        1011:11, 1005:161   +1844
    (80, 80, 664, 58, 2, 78): SRC,       # starvation   608:368, 656:116    +780
    (100, 100, 540, 1832, 4, 132): SRC,  # ambush       673:353, 561:452    +429
    (90, 30, 0, 76, 18, 144): SRC,       # lanes        1002:431, 1004:941  +634
    (30, 30, 0, 36, 2, 36): SRC,         # elkring      1001:704, 1001:814  +484
}

_choice = None
_key = None


def map_key():
    global _key
    if _key is None:
        _key = (game_map.width(), game_map.height(), game_map.walls().count(), game_map.holes().count(),
                game_map.altars().count(), game_map.bushes().count())
    return _key


def is_src_map(key):
    if key in SRC_MAPS:
        return True
    w, h, wc, hc, ac, bc = key
    area = w * h
    # 1. Compact low-wall, low-bush arenas (e.g. gemfight, eight, swirl, elkring; excludes bridges/graveyard/fragment)
    if area <= 1400 and ac <= 2 and wc <= 40 and bc <= 36 and not (bc >= 24 and hc >= 200):
        return True
    # 2. Multi-altar lane maps (e.g. lanes with 18 altars)
    if ac >= 15:
        return True
    # 3. Huge walled macro maps with moderate bush density (e.g. starvation, ambush; excludes maze/thevoid/forts)
    if area >= 6400 and 50 <= bc <= 160 and wc >= 500:
        return True
    return False


def choose():
    global _choice
    if _choice is None:
        if FORCE is not None:
            _choice = FORCE
        else:
            try:
                _choice = SRC if is_src_map(map_key()) else BBOT
            except Exception:
                _choice = BBOT
    return _choice
