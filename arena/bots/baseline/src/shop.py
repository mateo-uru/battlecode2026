"""Spend gold on spawn (or while dead; Tavi anywhere) following the role's build in config.BUILDS.

Each build entry is bought five times (one emblem), then the next entry; the last one repeats.
UPGRADE: adapt the build to the enemy draft (Durability vs burst casters, Jungle vs camp-heavy maps).
"""
import cambc
from cambc import ItemType, ConsumableType

import config

LOCK = ConsumableType.ALTAR_LOCK


class Shop:
    def __init__(self, role):
        self.build = [getattr(ItemType, name) for name in config.BUILDS[role]]
        self.bought = 0

    def run(self, me):
        for _ in range(40):
            if me.gold_count() < 30:
                break
            item = self.build[min(self.bought // 5, len(self.build) - 1)]
            try:
                if not me.can_buy(item):
                    break
                me.buy(item)
            except cambc.Error:
                break
            self.bought += 1
        try:
            if (self.bought >= config.LOCK_AFTER_SHARDS and me.consumables()[int(LOCK)].count() == 0
                    and me.gold_count() >= 10 and me.can_buy(LOCK)):
                me.buy(LOCK)
        except cambc.Error:
            pass

    @staticmethod
    def has_lock(me):
        try:
            return me.consumables()[int(LOCK)].count() > 0
        except cambc.Error:
            return False
