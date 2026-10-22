"""The team's 8 shared bytes and the read-only draft memory.

  0 anchor x        position of the acting leader (the group walks around it)
  1 anchor y
  2 anchor target   0 none, 1..250 camp group index + 1, ALTAR, ESCORT (altar with a heavy bag), PREY
  3 anchor stamp    round stamp of the anchor write
  4 healing mask    bit r: champion of rank r is healing/dead (bits 0-5); bits 6-7 enemies at our spawn
  5 near mask       bit r: champion of rank r is within working distance of the anchor (bits 0-5);
                    bits 6-7 prey stamp (round // 4 % 4)
  6 prey x          last isolated enemy champion seen by anyone
  7 prey y
UPGRADE: a focus-target byte (enemy handle) so stuns chain on one target across the team.
"""
import cambc
from cambc import Vec2

import config
import draft

ALTAR, PREY, ESCORT = 254, 253, 252


def stamp(now):
    return now % 255 + 1          # 0 means "never written"


def fresh(value, now, limit):
    return value != 0 and (stamp(now) - value) % 255 <= limit


class Comms:
    def __init__(self):
        self.buf = bytearray(8)

    def read(self):
        cambc.shared_memory.read(0, self.buf)

    def _put(self, i, v):
        self.buf[i] = v
        cambc.shared_memory[i] = v

    # anchor
    def anchor(self, now):
        b = self.buf
        if not fresh(b[3], now, config.ANCHOR_STALE):
            return None, 0
        return Vec2(b[0], b[1]), b[2]

    def write_anchor(self, pos, target, now):
        if not (0 <= pos.x < 256 and 0 <= pos.y < 256 and 0 <= target < 256):
            return                    # e.g. the leader died this turn (no position)
        data = bytes((pos.x, pos.y, target, stamp(now)))
        cambc.shared_memory.write(0, data)
        self.buf[0:4] = data

    # healing
    def healing_mask(self):
        return self.buf[4] & 63

    def set_healing(self, rank, flag):
        if rank >= 6:
            return
        v = self.buf[4]
        nv = (v | (1 << rank)) if flag else (v & ~(1 << rank))
        if nv != v:
            self._put(4, nv)

    def spawn_danger(self):
        return self.buf[4] >> 6

    def set_spawn_danger(self, n):
        n = min(3, n)
        if n != self.spawn_danger():
            self._put(4, (self.buf[4] & 63) | (n << 6))

    # near
    def near_mask(self):
        return self.buf[5] & 63

    def set_near(self, rank, flag):
        if rank >= 6:
            return
        v = self.buf[5]
        nv = (v | (1 << rank)) if flag else (v & ~(1 << rank))
        if nv != v:
            self._put(5, nv)

    # prey
    def prey(self, now):
        """Fresh for 4-7 rounds: the stamp has two bits."""
        b = self.buf
        if b[6] == 0 and b[7] == 0 or (now // 4 - (b[5] >> 6)) % 4 > 1:
            return None
        return Vec2(b[6], b[7])

    def write_prey(self, pos, now):
        self._put(5, (self.buf[5] & 63) | (now // 4 % 4) << 6)
        cambc.shared_memory.write(6, bytes((pos.x, pos.y)))
        self.buf[6:8] = bytes((pos.x, pos.y))


def read_draft(info):
    """Doctrine chosen in the draft; recomputed from the map if the memory is missing."""
    try:
        data = bytes(cambc.draft_memory)
        if len(data) >= 2 and data[0] == ord("F") and data[1] < len(draft.DOCTRINE_NAMES):
            return draft.DOCTRINE_NAMES[data[1]]
    except Exception:
        pass
    return info.doctrine()
