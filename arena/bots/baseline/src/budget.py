"""Yield explicitly before the fuel runs out instead of resuming stale work next round."""
import cambc

import config

_expected_round = None


class TurnBudget(Exception):
    pass


def begin_turn():
    global _expected_round
    _expected_round = cambc.round_number()


def check(reserve=config.RESERVE):
    # A suspended Python stack resumes next round; its observations are stale, so drop the turn.
    if _expected_round is not None and cambc.round_number() != _expected_round:
        raise TurnBudget()
    if cambc.fuel_remaining() < reserve:
        raise TurnBudget()
