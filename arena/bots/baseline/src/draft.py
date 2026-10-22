"""Draft: leader first, then the doctrine's priority list (nameless style).

Draft memory layout (read by every champion in comms.read_draft):
  0  magic b"F"
  1  doctrine index into config.DOCTRINES
  2  team size
UPGRADE: write precomputed plans (camp route order, altar choice per region) into the 1024 bytes;
the draft gets 10x fuel on its first turn.
"""
import cambc
from cambc import Team

import config

DOCTRINE_NAMES = tuple(config.DOCTRINES)


def choose_pick(doctrine, taken, size):
    taken = set(int(t) for t in taken)
    if not taken & set(config.LEADER_DRAFT):
        for pick in config.LEADER_DRAFT:
            if pick not in taken:
                return pick
    if (config.SUPPORT_PICK is not None and size >= config.SUPPORT_MIN_TEAM
            and len(taken) == size - 1 and config.SUPPORT_PICK not in taken):
        return config.SUPPORT_PICK
    for pick in config.DOCTRINES[doctrine]["picks"]:
        if pick not in taken:
            return pick
    return next(p for p in range(12) if p not in taken)


def play(info):
    doctrine = info.doctrine()
    size = cambc.draft.team_size()
    taken = cambc.draft.current_draft(Team.ALLY)
    if not taken:
        print("fade", info.describe(), flush=True)
    # Memory must be submitted before the pick closes this draft turn's input.
    cambc.draft_memory.submit(bytes((ord("F"), DOCTRINE_NAMES.index(doctrine), size)))
    cambc.draft.pick(choose_pick(doctrine, taken, size))
