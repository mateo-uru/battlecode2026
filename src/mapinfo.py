"""Static map analysis shared by the draft and the champions.

Only public geometry is used (sizes, camps, spawns, altars), never a map name, so unknown maps get the
same treatment as known ones. The draft and every champion compute the same result.

Fuel note (measured on a 60x60 map with 46 groups, Python): camp_groups() costs ~1.1M of the 2.5M turn
budget, a field.get ~2.6k, an engine getter ~3k, one Python loop iteration ~400. Load groups once.
"""
import cambc
from cambc import game_map, Team

import config

INF = 60000
_groups = None


def camp_groups():
    global _groups
    if _groups is None:
        _groups = game_map.camp_groups()
    return _groups


class MapInfo:
    def __init__(self):
        self.width, self.height = game_map.width(), game_map.height()
        self.area = self.width * self.height
        self.groups = camp_groups()
        n = len(self.groups)
        self.grouped = sum(1 for g in self.groups if len(g.camps()) > 1)
        self.blocked = game_map.walls() | game_map.holes() | game_map.altars()
        self.home = game_map.spawn_region(Team.ALLY)
        self.enemy_home = game_map.spawn_region(Team.ENEMY)

        # nameless' generic map classes (its fallback brain): crowded, dense, grouped.
        self.crowded = self.area <= 1750 or (min(self.width, self.height) <= 30 and n >= 20)
        self.dense = self.grouped * 4 > n and self.area > 1800
        self.is_grouped = self.grouped > n // 4

        # Walking distance between the spawns: short paths mean early fights.
        field = cambc.DistanceField()
        field.compute(self.blocked, self.home, cambc.Bitboard())
        self.home_field = field
        enemy = self.enemy_home.positions()
        self.spawn_distance = field.get(enemy[0]) if enemy else INF
        for p in enemy[1:]:
            d = field.get(p)
            if d < self.spawn_distance:
                self.spawn_distance = d

        # phobos: sparse maps get split farming, gem-poor maps carry discipline.
        # UPGRADE: walkable area and walking distances instead of raw area (walls, holes).
        self.sparse = config.SPLIT and self.area >= config.SPLIT_AREA and self.area >= config.SPLIT_SPARSE * max(1, n) and self.area < 9000
        self.gem_total = sum(g.gem_value() for g in self.groups)
        self.poor = self.gem_total < config.POOR_GEMS

    def doctrine(self):
        """Stun team where fights happen in packs (crowded/grouped maps), fighters on sparse maps.

        This mirrors nameless' split between its two draft orders.
        UPGRADE: score doctrines from more features (altar count, chokepoints, bush share) and learn
        the weights from tournament results instead of this rule.
        """
        if config.DOCTRINE_FORCE:
            return config.DOCTRINE_FORCE
        if self.spawn_distance < config.FIGHTERS_SPAWN_DIST:
            return "fighters"     # the enemy is next door: kill first
        if self.crowded or self.dense or self.is_grouped:
            return "stun"
        return "fighters"

    def describe(self):
        return (f"map {self.width}x{self.height} groups={len(self.groups)} grouped={self.grouped} "
                f"crowded={self.crowded} dense={self.dense} sparse={self.sparse} poor={self.poor} gems={self.gem_total} "
                f"spawn_dist={self.spawn_distance} "
                f"doctrine={self.doctrine()}")
