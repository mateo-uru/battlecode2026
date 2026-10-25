"""berfer: plays src on the maps where src beat bbot by 500+ gems, bbot everywhere else (see picker.py)."""
import traceback

import cambc

import picker


def run_src():
    """src's main loop, unchanged."""
    import budget
    from budget import TurnBudget
    brain = None
    info = None
    low, yields = 1 << 30, 0
    while True:
        try:
            budget.begin_turn()
            if cambc.is_draft():
                import draft
                from mapinfo import MapInfo
                if info is None:
                    info = MapInfo()
                draft.play(info)
            else:
                if brain is None:
                    from brain import Brain
                    brain = Brain()
                brain.turn()
        except TurnBudget:
            yields += 1
        except Exception as error:
            where = " < ".join(l.strip() for l in traceback.format_exc().splitlines() if "File" in l)
            print(f"deimos error r{cambc.round_number()}: {error!r} | {where[-300:]}", flush=True)
        try:
            if brain is not None:
                low = min(low, cambc.fuel_remaining())
                if cambc.round_number() % 500 == 0:
                    print(f"deimos fuel r{cambc.round_number()} low={low} yields={yields}", flush=True)
                    low = 1 << 30
        except Exception:
            pass
        cambc.end_turn()


def run_bbot():
    """bbot's main loop, unchanged."""
    import genome
    from body import Body, run_draft
    body = Body(genome)
    errors = 0
    while True:
        try:
            if cambc.is_draft():
                run_draft(genome.DRAFT, genome.ID)
            else:
                body.turn()
        except Exception as error:
            errors += 1
            if errors <= 10:
                print(f"bot error: {type(error).__name__}: {error}", flush=True)
        cambc.end_turn()


def main():
    choice = picker.choose()
    try:
        print(f"berfer key={picker.map_key()} brain={choice}", flush=True)
    except Exception:
        pass
    if choice == picker.SRC:
        run_src()
    else:
        run_bbot()


if __name__ == "__main__":
    main()
