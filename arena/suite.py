#!/usr/bin/env python3
"""Run all 40 maps from both sides and write a gem table.

Manifest rows match `cambc run-batch`: bot-a bot-b map replay.
Our side is A when the first bot is ours. Maps live in arena/maps.
"""
import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ARENA = Path(__file__).resolve().parent
ROW = re.compile(
    r"^\s*([AB])\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.*)$"
)
RESULT = re.compile(r"^finished: round (\d+)/2000 — (teamA|teamB)")


def maps():
    names = sorted(path.name[: -len(".map26a")] for path in (ARENA / "maps").glob("*.map26a"))
    if len(names) != 40:
        raise SystemExit(f"expected 40 maps, found {len(names)}")
    return names


def parse_log(text, opponent):
    """Pull the scoreboard that cambc prints after each match, in manifest order."""
    games = []
    pending_round = None
    pending_winner = None
    rows = {}
    for line in text.splitlines():
        found = RESULT.search(line.strip())
        if found:
            pending_round = int(found.group(1))
            pending_winner = found.group(2)
            rows = {}
            continue
        matched = ROW.match(line)
        if not matched or pending_round is None:
            continue
        side, bot, gems, kills, deaths, gold, crashes, draft = matched.groups()
        rows[side] = {
            "bot": bot,
            "gems": int(gems),
            "kills": int(kills),
            "deaths": int(deaths),
            "gold": int(gold),
            "crashes": int(crashes),
            "draft": draft.strip(),
        }
        if "A" in rows and "B" in rows:
            ours = rows["A"] if rows["A"]["bot"] == "ours" else rows["B"]
            opp = rows["B"] if ours is rows["A"] else rows["A"]
            our_side = "A" if ours is rows["A"] else "B"
            winner = "A" if pending_winner == "teamA" else "B"
            games.append({
                "opponent": opponent,
                "side": our_side,
                "round": pending_round,
                "ours": ours,
                "opp": opp,
                "win": winner == our_side,
            })
            pending_round = None
    return games


def run_one(opponent, name, side, replay_dir, log_dir, timeout):
    if side == "A":
        bots = ["ours", opponent]
    else:
        bots = [opponent, "ours"]
    log_path = log_dir / f"{name}_{side}.log"
    cmd = [
        "cambc", "run", *bots, "--map", name, "--release",
        "--log-limit", "2000000", "-o", str(replay_dir),
    ]
    text, code = "", 1
    for attempt in range(2):
        try:
            proc = subprocess.run(cmd, cwd=ARENA, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, timeout=timeout)
            text = proc.stdout
            code = proc.returncode
        except subprocess.TimeoutExpired as error:
            text = (error.stdout or "") + "\nTIMEOUT\n"
            code = 124
        # Parallel first builds of the same bot can truncate the wasm module.
        if code == 0 or "end-of-file" not in text and "at least one module field" not in text:
            break
    log_path.write_text(text)
    games = parse_log(text, opponent)
    if len(games) != 1:
        print(f"parse {name} {side}: {len(games)} boards exit={code}", file=sys.stderr, flush=True)
        return None
    game = games[0]
    game["map"] = name
    return game


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    replay_dir = args.out / "replays"
    log_dir = args.out / "logs"
    replay_dir.mkdir(exist_ok=True)
    log_dir.mkdir(exist_ok=True)
    tasks = [(name, side) for name in maps() for side in ("A", "B")]
    games = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [
            pool.submit(run_one, args.opponent, name, side, replay_dir, log_dir, args.timeout)
            for name, side in tasks
        ]
        for future in as_completed(futures):
            game = future.result()
            if game is not None:
                games.append(game)
                print(f"{game['map']} {game['side']} {'W' if game['win'] else 'L'} "
                      f"{game['ours']['gems']}-{game['opp']['gems']}", flush=True)
    games.sort(key=lambda game: (game["map"], game["side"]))
    rows_out = []
    for game in games:
        rows_out.append(
            f"{args.opponent},{game['map']},{game['side']},{int(game['win'])},{game['ours']['gems']},"
            f"{game['opp']['gems']},{game['ours']['kills']},{game['ours']['deaths']},"
            f"{game['ours']['gold']},{game['opp']['gold']},{game['round']},{game['ours']['crashes']}"
        )
    proc = type("P", (), {"returncode": 0 if len(games) == 80 else 1})()
    csv_path = args.out / "scores.csv"
    csv_path.write_text(
        "opponent,map,side,win,our_gems,opp_gems,our_kills,our_deaths,our_gold,opp_gold,round,crashes\n"
        + "\n".join(rows_out) + ("\n" if rows_out else "")
    )
    wins = sum(1 for game in games if game["win"])
    diff = sum(game["ours"]["gems"] - game["opp"]["gems"] for game in games)
    print(f"games={len(games)} wins={wins} gem_diff={diff} exit={proc.returncode}", flush=True)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
