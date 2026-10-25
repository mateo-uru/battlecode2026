#!/usr/bin/env python3
"""Summarise FUEL histogram lines printed by the bot.

Each line is one champion's cumulative histogram. The last line per (replay, team, rank)
is that champion's full match. Percents are of that turn's Python budget.
"""
import collections
import sys
import zipfile
from pathlib import Path

LINE = "FUEL "


def last_histograms(stdout):
    latest = {}
    for raw in stdout.splitlines():
        if "FUEL " not in raw:
            continue
        line = raw[raw.index("FUEL "):]
        fields = {}
        buckets = []
        for part in line.split():
            if part.startswith("b="):
                buckets = [int(x) for x in part[2:].split(",") if x != ""]
            elif "=" in part:
                key, value = part.split("=", 1)
                fields[key] = value
        if "r" not in fields or len(buckets) != 20:
            continue
        latest[fields["r"]] = (fields, buckets)
    return latest


def harvest(replay_dir):
    totals = collections.defaultdict(lambda: {"n": 0, "outs": 0, "max": 0.0, "buckets": [0] * 20})
    files = sorted(Path(replay_dir).glob("*.repl26a"))
    for path in files:
        name = path.name
        if name.startswith("ours-vs-"):
            team = "team-a.stdout"
        elif "-vs-ours-" in name:
            team = "team-b.stdout"
        else:
            continue
        try:
            with zipfile.ZipFile(path) as bundle:
                text = bundle.read(team).decode("utf-8", "replace").replace("\x00", "")
        except (KeyError, zipfile.BadZipFile, OSError):
            continue
        for fields, buckets in last_histograms(text).values():
            key = "100" if fields.get("w") == "100" and fields.get("h") == "100" else "other"
            bucket = totals[key]
            bucket["n"] += int(fields["n"])
            bucket["outs"] += int(fields["outs"])
            bucket["max"] = max(bucket["max"], float(fields["max"]))
            for i, count in enumerate(buckets):
                bucket["buckets"][i] += count
            # Also keep a per-map width record.
            size = f"{fields.get('w')}x{fields.get('h')}"
            sized = totals[size]
            sized["n"] += int(fields["n"])
            sized["outs"] += int(fields["outs"])
            sized["max"] = max(sized["max"], float(fields["max"]))
            for i, count in enumerate(buckets):
                sized["buckets"][i] += count
    return totals


def p95(buckets, n):
    if n <= 0:
        return 0
    need = int(n * 0.95 + 0.999999)
    acc = 0
    for i, count in enumerate(buckets):
        acc += count
        if acc >= need:
            return (i + 1) * 5
    return 100


def report(replay_dir):
    totals = harvest(replay_dir)
    print(f"dir {replay_dir}")
    for key in sorted(totals):
        if key in ("100", "other"):
            continue
        bucket = totals[key]
        if bucket["n"] == 0:
            continue
        rate = 100.0 * bucket["outs"] / bucket["n"]
        print(f"  {key:10} n={bucket['n']:7} outs={bucket['outs']:5} ({rate:.2f}%) "
              f"max={bucket['max']:.1f}% p95={p95(bucket['buckets'], bucket['n'])}%")
    for key in ("100", "other"):
        if key not in totals:
            continue
        bucket = totals[key]
        rate = 100.0 * bucket["outs"] / max(1, bucket["n"])
        label = "100x100" if key == "100" else "other"
        print(f"{label:10} n={bucket['n']:7} outs={bucket['outs']:5} ({rate:.2f}%) "
              f"max={bucket['max']:.1f}% p95={p95(bucket['buckets'], bucket['n'])}%")


if __name__ == "__main__":
    for directory in sys.argv[1:]:
        report(directory)
