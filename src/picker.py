"""Pick which bot plays this map: bbot by default, src where it beat bbot by 500+ gems.

Rule: src plays a map only if it won both games there (one from each side) and its
gem lead over the two games together is at least 500. Every other map, including
unknown ones, gets bbot.

Maps are recognised by cheap public geometry (size and tile counts), the same for both
sides and for the draft and every champion.
"""
from cambc import game_map

SRC, BBOT = "src", "bbot"
FORCE = None  # set to SRC or BBOT for experiments

# (width, height, walls, holes, altars, bushes) -> brain.
# Source: src vs bbot, cambc 3.0.5, 40-map pool, 2026-10-22. Gems src:bbot per game, then total lead.
SRC_MAPS = {
    (30, 30, 0, 108, 2, 16): SRC,        # gemfight     1042:129, 1031:75   +1869
    (45, 30, 30, 354, 2, 14): SRC,       # swirl        979:15, 953:64      +1853
    (41, 30, 36, 22, 1, 24): SRC,        # eight        1011:11, 1005:161   +1844
    (80, 80, 664, 58, 2, 78): SRC,       # starvation   608:368, 656:116    +780
    (100, 100, 540, 1832, 4, 132): SRC,  # ambush       489:275, 690:341    +563
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


def choose():
    global _choice
    if _choice is None:
        if FORCE is not None:
            _choice = FORCE
        else:
            try:
                _choice = SRC_MAPS.get(map_key(), BBOT)
            except Exception:
                _choice = BBOT
    return _choice
