"""Who is who: ranks, the designated leader and the acting leader.

Every champion computes the same answer from public data (champion types are readable without
vision), so no communication is needed to agree on the leader.
"""
import cambc
from cambc import Team

import config


class Roster:
    def __init__(self, me):
        allies = cambc.champions(Team.ALLY)
        self.unit = {int(c): c for c in allies}
        self.type = {int(c): int(c.champion_name()) for c in allies}
        self.handles = sorted(self.unit)
        self.rank_of = {h: i for i, h in enumerate(self.handles)}
        self.me = int(me)
        self.rank = self.rank_of[self.me]
        self.size = len(self.handles)

        def pref(h):
            t = self.type[h]
            return (config.LEADER_TYPES.index(t) if t in config.LEADER_TYPES else 99, h)

        # Leadership passes down this order while the leader heals or is dead.
        self.order = sorted(self.handles, key=pref)
        self.leader = self.order[0]

    def alive(self, h):
        try:
            return self.unit[h].is_alive()
        except cambc.Error:
            return True

    def acting_leader(self, healing_mask):
        for h in self.order:
            if not healing_mask >> self.rank_of[h] & 1 and self.alive(h):
                return h
        return self.leader

    def role(self, h=None):
        h = self.me if h is None else h
        if h == self.leader:
            return "leader"
        return config.ROLE_OF_TYPE.get(self.type[h], "striker")

    def priority(self, h=None):
        """Higher acts first: the leader broadcasts before followers read."""
        h = self.me if h is None else h
        return 100 - self.order.index(h)
