# CAMBC 2026a — Winning strategy & implementation spec

Game: Cambridge Battlecode 2026, event `cambc2026a` (engine/CLI `cambc` 3.0.5, 40-map pool).
NOT the classic MIT Battlecode, and not the earlier "Titan mining/core" cambc game: this is the
champions / camps / gems / altars MOBA-style game (draft 3–5 champions, farm camps, capture,
tribute gems at altars; first to 1000 tributed gems or most at round 2000; tiebreak gold earned → kills → Team B).

## 1. Current approach (what the zip contains)
Python bot, `src/main.py` is a **meta-bot ("berfer")** gluing two complete bots:
- **src / "deimos" (brain.py, ~1k lines)**: leader-anchor group AI. First pick = tanky leader
  (Marcella>Ryth>Varg>Heart) that carries the team's gems; followers farm small camps around the anchor
  broadcast in the 8 shared bytes; tank rotation on big camps; split/roaming farming on big sparse maps;
  HUNT phase at r1000 / enemy lead; altar locks; build tables per role (config.py). Draft doctrine "stun"
  (Ryth, Tavi, Heart, Cassi&Issac, Ren...).
- **bbot / genome "g2_gobr" (body.py ~1.5k lines + g_*.py genes)**: evolved-style per-champion bot with
  ordered genes survive→bank→fight→farm; all-melee draft (Varg, Vendetta, Ryth, Heart, Ren, C&I);
  Treasure emblem then Power shards; bank at 40 gems / enemy near.
- `picker.py` fingerprints the map by (w,h,walls,holes,altars,bushes) and runs src on 5 known maps
  (gemfight, swirl, eight, starvation, ambush), bbot everywhere else (incl. any unseen map).

## 2. Local measurement (box, `cambc run --release`, ours vs starter-python, both sides, 40 maps)
Ours reaches 1000 on most maps, but clear failures even vs the *starter bot*:
| map | side | result | note |
|---|---|---|---|
| 01corridors | A | **16 – 504 LOSS** | bbot all-melee team farmed almost nothing (stuck/pathing or camps judged infeasible) ; side B 946 – inconsistent |
| 00ambush | A | **353 – 428 LOSS** | src brain: 8,944 gold earned but only 353 gems tributed → banking/hauling failure on 100x100 |
| 01boss-battle | A/B | 0 – 0 (won on gold tiebreak) | nobody kills the boss; 0 gems is a coin-flip vs anyone competent |
| 00stampede | A/B | 320 – 0 | 59 kills but only 320 gems: fights instead of farming/banking |
| 00pilgrimage | A/B | 707/818 | slow economy, never hits 1000 |
| 00rows, 00rushbait-v2(A) | | 741 / 791 | side-dependent |
(Full raw logs: /workspace/battlecode/arena/res/*.log; rerun `arena/batch.sh`.)

## 3. Weaknesses
1. **Two bots + map-fingerprint switch = overfitting.** Unknown/edited tournament maps always get bbot;
   any map tweak breaks the key. Two codebases double the maintenance and neither is complete.
2. **Banking/hauling is the binding constraint**, not combat: big maps (ambush, pilgrimage) show huge gold
   but few tributed gems. Single-leader gem carrier = slow trips, a juicy kill target, and lost tempo.
3. **Big-camp / boss maps unsolved** (boss-battle 0 gems; monolith = 200 gems is the single best reward).
4. **Draft ignores the enemy** (`current_draft(Team.ENEMY)` unused) and ignores map size/team size
   beyond a binary doctrine; bbot drafts all-melee, which can't clear ranged-heavy maps safely.
5. **Shop:** Treasure-first is a tiebreak/gold play, not a gem play. Gold is only useful turned into kill speed.
   No Monster/Jungle emblem on farmers in bbot; Home emblem (recall 5→3) not prioritised for carriers.
6. **Altar locks** barely used offensively (10g to cancel/deny enemy tributes is the cheapest swing in the game).
7. **Fuel:** Python; known hotspots (camp_groups ~1.1M of 2.5M) and the "drop the turn if resumed" guard
   means heavy turns become idle turns. Draft-phase 10x fuel / 1024-byte draft memory almost unused (3 bytes).
8. Fights for kills (stampede 59 kills) even when farming would win faster; side-asymmetric results.

## 4. Language verdict
Per-turn fuel (Wasmtime, deterministic): **C++/Rust 100k, OCaml 500k, Python 2.5M (25x)**; draft turn 1 gets
10x, first game turn 2x. Fuel ≈ wasm instructions. An interpreted CPython-in-wasm op costs roughly 30–100
native instructions, so in *effective* compute **C++ ≈ 1.5–4x more than Python** — the 25x allowance mostly
compensates. That matters only for heavy search (per-turn BFS over 100x100, combat simulation).
**Verdict: stay in Python for this season.** The losses above are strategic/behavioural (banking, boss camps,
draft, pathing), not compute. A C++ rewrite of 4.6k lines would cost weeks and reset tuning. Revisit only if,
after fixes, profiling shows >5% of turns yielding on 100x100 maps — then move just the pathfinding/distance
fields to precomputation in the draft turn + draft memory, or (last resort) port to C++.
(Public info about this specific 2026a game is very thin; no published top-team writeups were found, so
recommendations derive from the rules + local measurements.)

## 5. Prioritised implementation spec (for a coding agent)
Work in `/workspace/battlecode/src`; test harness `/workspace/battlecode/arena` (`cambc run ours <opp> --map <m> --release`,
`arena/batch.sh` runs jobs.txt on all 40 maps × both sides). Every change must be A/B'd on all 80 games vs
the previous version (keep a frozen copy as `bots/baseline`) — accept only if total wins and total gem
differential improve and no map regresses by >150 gems.

P0 — Harness & baseline (day 1)
- Add `bots/baseline` (current code) and self-play jobs (ours vs baseline, both sides). Parse logs to a CSV
  (map, side, gems, kills, deaths, gold, winner). Also run vs the platform's top teams via
  `cambc match-groups` (unranked, needs Mateo's login — only with his approval).

P1 — One bot, no fingerprints
- Pick the stronger codebase per *map features*, not map key: start from **src/brain.py** (more general),
  port bbot's survive/bank heuristics where they win. Replace `picker.SRC_MAPS` with feature rules
  (area, camp density, spawn distance, altar distance, boss presence). Delete the dual main loop.

P2 — Gem throughput (biggest win)
- Every champion banks independently: bank when `gems >= BANK_MIN + BANK_PER_TILE*altar_dist` OR enemy
  champion within 8 and gems ≥ 10 OR round + altar_dist + 30 ≥ 2000 OR ally_tributed+bag ≥ 1000.
  Drop "leader carries everything" except on tiny maps.
- Route planning: score camps by `(gems + 0.15*gold) / (walk_to_camp + clear_turns + 5 capture + walk_camp_to_nearest_altar*share)`;
  prefer camps on the way to altars. Respawn timers: track captured groups and return when they respawn.
- Capture solo where safe (rewards are split among capturers — only stack if contested).
- Buy **Home emblem** on whoever banks most (recall 3 turns) and use recall→spawn→walk to altar when spawn is nearer.
- Tribute bags ≤10 when enemies are near (1-turn channel) to avoid lock/stun cancels.

P3 — Big camps & bosses
- Implement explicit tank rotation (already UPGRADE note): monsters hit the nearest champion; tank steps
  out at ~45% HP, next tank steps in; casters/ranged hit from max range. Compute feasibility with real team
  DPS (Monster emblem +10%, Jungle −30% camp damage). Target Golem (36 gems) and Monolith (200 gems) once
  team DPS ≥ threshold; on boss-battle-type maps this is the only gem source — never end with 0 gems.
- Fix 01corridors: log why bbot/brain farms nothing (pathing through corridors, camps marked `bad`,
  BIG_WAIT skip loops). Add a fallback: if no tribute by round 300, take the nearest feasible camp regardless.

P4 — Draft
- Use 10x draft fuel to precompute: camp groups, distance fields spawn→camps→altars, region assignment;
  pack into the 1024-byte draft memory (camp order per champion, altar per region) so champions skip
  `camp_groups()` (~1.1M fuel) at game start.
- Map-aware composition: always 1–2 durable camp clearers (Varg splash for wolf packs/clusters, Ryth/Heart),
  1 ranged sustained DPS (Vesper: +33% gold, strong basics; Tavi), Marcella when enemy drafts stun.
  Read `current_draft(Team.ENEMY)` each pick: vs many stuns → Marcella; vs squishy casters → Vendetta/Heart dive.
  Avoid all-melee on maps with many Elk/Golem (range 4).

P5 — Shop
- Farmers: Monster(STR or FOCUS) → Jungle(HEALTH) → Power. Carriers: Home → Durability. Vesper: Treasure
  only if gold tiebreak matters. Always carry an altar lock (10g) once ≥ 3 shards owned.

P6 — Interaction / denial (after economy is solid)
- Altar lock: when an enemy is seen channelling tribute (or carrying ≥20 gems near an altar) within 2 tiles
  of the altar, place a lock — cancels the channel. Clear our altars of locks (5 basic attacks) as a task.
- Hunt only gem carriers (kill = their whole bag + 100g) when odds ≥ 1.2 and target bag ≥ 20; never chase
  an empty champion across the map. Use the 8 shared bytes for a focus target (enemy id + pos) so stuns chain.
- Late game: if behind by > remaining camp throughput, switch to camping enemy's nearest altar with locks.

P7 — Fuel hygiene
- Cache distance fields; incremental updates only on newly seen tiles. Keep RESERVE but resume partial
  work instead of dropping the whole turn (do movement/attack first, planning last).

Acceptance target: beat baseline ≥ 70/80 on the 40-map pool, ≥ 1000 gems on every map vs starter-python
from both sides, and positive record in unranked match-groups vs top-10 ladder teams.
