# Arena results

The bot in `src/` is the frozen baseline (`9769186`). Gameplay changes were measured on all 40 maps from both sides and kept only when they beat that bot. None did. This file is the score of that bot, the attempts that were thrown out, and the fuel profile.

Games were `cambc run --release` with CLI 3.0.5, 2000-round limit, 3 workers. A win is the engine's winner (gems, then gold earned, then kills, then team B). Gem differential is our tributed gems minus the opponent's, summed over all 80 games.

## Versus the frozen baseline

**40 wins / 80 games, gem differential 0, 0 crashes.**

This is self-play. On every map the side-B game is the side-A game with the teams swapped, so the two games split 1–1 and the gem differential is 0. A target of 70/80 against a copy of the same code is not a property the match can have: the map's favored side wins, and we play both sides. The variants below are what happened when the code actually differed.

| map | side | gems | opponent | result | round |
| --- | --- | ---: | ---: | --- | ---: |
| 00ambush | A | 514 | 333 | W | 2000 |
| 00ambush | B | 333 | 514 | L | 2000 |
| 00collision | A | 1001 | 380 | W | 1508 |
| 00collision | B | 380 | 1001 | L | 1508 |
| 00contest | A | 1000 | 0 | W | 1879 |
| 00contest | B | 0 | 1000 | L | 1879 |
| 00corners | A | 821 | 1011 | L | 1402 |
| 00corners | B | 1011 | 821 | W | 1402 |
| 00eight | A | 110 | 1013 | L | 1714 |
| 00eight | B | 1013 | 110 | W | 1714 |
| 00elkring | A | 1012 | 242 | W | 1215 |
| 00elkring | B | 242 | 1012 | L | 1215 |
| 00expanse | A | 647 | 1023 | L | 1600 |
| 00expanse | B | 1023 | 647 | W | 1600 |
| 00fragment | A | 738 | 28 | W | 2000 |
| 00fragment | B | 28 | 738 | L | 2000 |
| 00gem-fields | A | 498 | 1005 | L | 1254 |
| 00gem-fields | B | 1005 | 498 | W | 1254 |
| 00gemfight | A | 1001 | 82 | W | 1389 |
| 00gemfight | B | 82 | 1001 | L | 1389 |
| 00great-wall | A | 994 | 1004 | L | 1737 |
| 00great-wall | B | 1004 | 994 | W | 1737 |
| 00interlock | A | 1028 | 535 | W | 1704 |
| 00interlock | B | 535 | 1028 | L | 1704 |
| 00lanes | A | 1017 | 395 | W | 1424 |
| 00lanes | B | 395 | 1017 | L | 1424 |
| 00lost-world | A | 1010 | 732 | W | 1069 |
| 00lost-world | B | 732 | 1010 | L | 1069 |
| 00monolith | A | 1029 | 723 | W | 1377 |
| 00monolith | B | 723 | 1029 | L | 1377 |
| 00packs | A | 568 | 1000 | L | 1573 |
| 00packs | B | 1000 | 568 | W | 1573 |
| 00pilgrimage | A | 591 | 279 | W | 2000 |
| 00pilgrimage | B | 279 | 591 | L | 2000 |
| 00quadrants | A | 1007 | 909 | W | 923 |
| 00quadrants | B | 909 | 1007 | L | 923 |
| 00reverse-spiral | A | 966 | 218 | W | 2000 |
| 00reverse-spiral | B | 218 | 966 | L | 2000 |
| 00road-of-riches | A | 1028 | 387 | W | 1741 |
| 00road-of-riches | B | 387 | 1028 | L | 1741 |
| 00rows | A | 613 | 516 | W | 2000 |
| 00rows | B | 516 | 613 | L | 2000 |
| 00rushbait-v2 | A | 643 | 1000 | L | 1819 |
| 00rushbait-v2 | B | 1000 | 643 | W | 1819 |
| 00split | A | 158 | 1004 | L | 1200 |
| 00split | B | 1004 | 158 | W | 1200 |
| 00stampede | A | 0 | 0 | L | 2000 |
| 00stampede | B | 0 | 0 | W | 2000 |
| 00swirl | A | 862 | 186 | W | 2000 |
| 00swirl | B | 186 | 862 | L | 2000 |
| 01big-world | A | 1141 | 747 | W | 1937 |
| 01big-world | B | 747 | 1141 | L | 1937 |
| 01boss-battle | A | 0 | 0 | W | 2000 |
| 01boss-battle | B | 0 | 0 | L | 2000 |
| 01broken-curve | A | 484 | 1078 | L | 1100 |
| 01broken-curve | B | 1078 | 484 | W | 1100 |
| 01concentrated-wealth | A | 241 | 1000 | L | 1704 |
| 01concentrated-wealth | B | 1000 | 241 | W | 1704 |
| 01corridors | A | 32 | 16 | W | 2000 |
| 01corridors | B | 16 | 32 | L | 2000 |
| 01elk-arena | A | 504 | 216 | W | 2000 |
| 01elk-arena | B | 216 | 504 | L | 2000 |
| 01fracture | A | 749 | 1003 | L | 1914 |
| 01fracture | B | 1003 | 749 | W | 1914 |
| 01gold-rush | A | 121 | 1007 | L | 1553 |
| 01gold-rush | B | 1007 | 121 | W | 1553 |
| 01hooks | A | 1012 | 66 | W | 1861 |
| 01hooks | B | 66 | 1012 | L | 1861 |
| 01islands | A | 1026 | 630 | W | 1633 |
| 01islands | B | 630 | 1026 | L | 1633 |
| 01shortcut | A | 324 | 814 | L | 2000 |
| 01shortcut | B | 814 | 324 | W | 2000 |
| 01starfish | A | 1031 | 347 | W | 1679 |
| 01starfish | B | 347 | 1031 | L | 1679 |
| 01starvation | A | 456 | 155 | W | 2000 |
| 01starvation | B | 155 | 456 | L | 2000 |
| 01the-farm | A | 89 | 65 | W | 2000 |
| 01the-farm | B | 65 | 89 | L | 2000 |
| 01yellow-brick-road | A | 1005 | 862 | W | 1337 |
| 01yellow-brick-road | B | 862 | 1005 | L | 1337 |

Boss-battle is 0–0. Team A wins it on gold (2206 against team B's 1978), so side A is a win and side B is a loss. Stampede is also 0–0 against this copy; team B wins it on gold (8460 against 8416).

## Versus starter-python

**78 wins / 80 games, gem differential +62157, 0 crashes.**

The two losses are the ones already called out in `STRATEGY.md`:

| map | side | gems | starter | note |
| --- | --- | ---: | ---: | --- |
| 01corridors | A | 16 | 504 | bbot tributes almost nothing from this spawn |
| 00ambush | A | 353 | 428 | 8944 gold earned, 353 gems tributed |

01corridors side B is 946–236. 00stampede is 320–0 from both sides with 59 kills. 00pilgrimage is 707 and 818. 01boss-battle is 0–0 from both sides and wins on gold (1996 and 3628). 01the-farm side A is 0–0 and wins on gold (904 against 548).

Maps where we do not reach 1000 tributed gems:

| map | side | gems | starter | result |
| --- | --- | ---: | ---: | --- |
| 00ambush | A | 353 | 428 | L |
| 00ambush | B | 460 | 218 | W |
| 00pilgrimage | A | 707 | 0 | W |
| 00pilgrimage | B | 818 | 0 | W |
| 00rows | A | 741 | 230 | W |
| 00rows | B | 942 | 208 | W |
| 00rushbait-v2 | A | 791 | 44 | W |
| 00stampede | A | 320 | 0 | W |
| 00stampede | B | 320 | 0 | W |
| 01big-world | A | 967 | 363 | W |
| 01boss-battle | A | 0 | 0 | W |
| 01boss-battle | B | 0 | 0 | W |
| 01corridors | A | 16 | 504 | L |
| 01corridors | B | 946 | 236 | W |
| 01shortcut | B | 793 | 0 | W |
| 01starvation | A | 864 | 0 | W |
| 01starvation | B | 886 | 0 | W |
| 01the-farm | A | 0 | 0 | W |
| 01the-farm | B | 159 | 45 | W |

| map | side | gems | opponent | result | round |
| --- | --- | ---: | ---: | --- | ---: |
| 00ambush | A | 353 | 428 | L | 2000 |
| 00ambush | B | 460 | 218 | W | 2000 |
| 00collision | A | 1007 | 52 | W | 1139 |
| 00collision | B | 1020 | 66 | W | 1150 |
| 00contest | A | 1000 | 0 | W | 1615 |
| 00contest | B | 1000 | 0 | W | 1806 |
| 00corners | A | 1050 | 25 | W | 888 |
| 00corners | B | 1001 | 24 | W | 871 |
| 00eight | A | 1058 | 44 | W | 1229 |
| 00eight | B | 1017 | 72 | W | 1210 |
| 00elkring | A | 1001 | 209 | W | 901 |
| 00elkring | B | 1001 | 400 | W | 1347 |
| 00expanse | A | 1003 | 296 | W | 1161 |
| 00expanse | B | 1034 | 286 | W | 1188 |
| 00fragment | A | 1024 | 16 | W | 1588 |
| 00fragment | B | 1011 | 25 | W | 1545 |
| 00gem-fields | A | 1049 | 501 | W | 836 |
| 00gem-fields | B | 1007 | 418 | W | 676 |
| 00gemfight | A | 1005 | 91 | W | 985 |
| 00gemfight | B | 1008 | 57 | W | 1075 |
| 00great-wall | A | 1049 | 135 | W | 1395 |
| 00great-wall | B | 1000 | 100 | W | 1385 |
| 00interlock | A | 1005 | 65 | W | 1035 |
| 00interlock | B | 1001 | 165 | W | 1044 |
| 00lanes | A | 1004 | 243 | W | 1079 |
| 00lanes | B | 1006 | 199 | W | 971 |
| 00lost-world | A | 1010 | 0 | W | 400 |
| 00lost-world | B | 1048 | 0 | W | 472 |
| 00monolith | A | 1009 | 182 | W | 1052 |
| 00monolith | B | 1004 | 59 | W | 1055 |
| 00packs | A | 1000 | 52 | W | 865 |
| 00packs | B | 1000 | 64 | W | 857 |
| 00pilgrimage | A | 707 | 0 | W | 2000 |
| 00pilgrimage | B | 818 | 0 | W | 2000 |
| 00quadrants | A | 1009 | 290 | W | 682 |
| 00quadrants | B | 1013 | 241 | W | 583 |
| 00reverse-spiral | A | 1015 | 263 | W | 1482 |
| 00reverse-spiral | B | 1006 | 154 | W | 1445 |
| 00road-of-riches | A | 1003 | 152 | W | 1680 |
| 00road-of-riches | B | 1014 | 238 | W | 1907 |
| 00rows | A | 741 | 230 | W | 2000 |
| 00rows | B | 942 | 208 | W | 2000 |
| 00rushbait-v2 | A | 791 | 44 | W | 2000 |
| 00rushbait-v2 | B | 1013 | 128 | W | 1427 |
| 00split | A | 1016 | 152 | W | 1101 |
| 00split | B | 1021 | 100 | W | 1072 |
| 00stampede | A | 320 | 0 | W | 2000 |
| 00stampede | B | 320 | 0 | W | 2000 |
| 00swirl | A | 1014 | 10 | W | 1837 |
| 00swirl | B | 1008 | 78 | W | 1809 |
| 01big-world | A | 967 | 363 | W | 2000 |
| 01big-world | B | 1013 | 249 | W | 1745 |
| 01boss-battle | A | 0 | 0 | W | 2000 |
| 01boss-battle | B | 0 | 0 | W | 2000 |
| 01broken-curve | A | 1009 | 98 | W | 1051 |
| 01broken-curve | B | 1011 | 88 | W | 1031 |
| 01concentrated-wealth | A | 1038 | 80 | W | 1392 |
| 01concentrated-wealth | B | 1052 | 148 | W | 1316 |
| 01corridors | A | 16 | 504 | L | 2000 |
| 01corridors | B | 946 | 236 | W | 2000 |
| 01elk-arena | A | 1008 | 0 | W | 1602 |
| 01elk-arena | B | 1008 | 0 | W | 1690 |
| 01fracture | A | 1028 | 96 | W | 1866 |
| 01fracture | B | 1035 | 164 | W | 1848 |
| 01gold-rush | A | 1007 | 330 | W | 1870 |
| 01gold-rush | B | 1095 | 330 | W | 1573 |
| 01hooks | A | 1012 | 110 | W | 1384 |
| 01hooks | B | 1012 | 0 | W | 1305 |
| 01islands | A | 1004 | 0 | W | 1209 |
| 01islands | B | 1015 | 30 | W | 1390 |
| 01shortcut | A | 1007 | 0 | W | 1880 |
| 01shortcut | B | 793 | 0 | W | 2000 |
| 01starfish | A | 1037 | 55 | W | 1138 |
| 01starfish | B | 1017 | 59 | W | 1219 |
| 01starvation | A | 864 | 0 | W | 2000 |
| 01starvation | B | 886 | 0 | W | 2000 |
| 01the-farm | A | 0 | 0 | W | 2000 |
| 01the-farm | B | 159 | 45 | W | 2000 |
| 01yellow-brick-road | A | 1011 | 60 | W | 1027 |
| 01yellow-brick-road | B | 1006 | 90 | W | 1132 |

## Attempts that were measured and not kept

Acceptance rule from `STRATEGY.md`: keep a change only when total wins and total gem differential against the frozen bot both improve, and no map drops by more than 150 gems.

**One merged bot** (independent banking, Home emblem first, enemy-reactive draft, tank rotation everywhere, denial and hunting) lost to the frozen bot **18/78, gem differential −28636**. Two games in that run did not produce a scoreboard. It was reverted before the tables above.

**Corridor farmer.** 01corridors is side-asymmetric under bbot: side A scores 16 against the starter, side B scores 946. A brain that walks to the nearest gem camp and skips the monolith raised side A to 425–261 and dropped side B to 176–202. Net gems against the starter fell. A wall-fraction switch (walls covering at least 12% of the tiles) also sent 00great-wall, 00lost-world, 00road-of-riches, 01broken-curve and 01shortcut to that farmer; those maps are rooms behind a wall, not one-tile halls (the share of walkable tiles with both opposite neighbours blocked is about 0 on all of them, including corridors). Not kept.

**Altar monolith, forced.** Treating the monolith on 01boss-battle as the only legal target made the team stand in the beam: 0 gems, 0 gold, 64 deaths, and a gold-tiebreak loss to the starter. Not kept.

**Altar monolith, soft, plus a per-turn fuel log.** Waiving the damage cap for a monolith that blocks the altar, and giving it a score floor of 50, scored **279–0** against the starter from side A (side B stayed 0–0 and won on gold). Against the frozen bot the same change scored **0–87** and **0–0** (gold loss). The fuel log, which calls `fuel_remaining` every turn and prints a histogram every 100 rounds, also broke self-play on maps that do not have that monolith: 01starvation went from a 456–155 mirror to 101–571 and 260–384, and 00corners and 00ambush stopped mirroring. 00corners never recorded a turn above 75% of the budget, so the print alone was enough to move the game. Not kept. After removing both, all six maps mirror the frozen bot again (the baseline table above).

## Fuel

Python's budget is 2,500,000 fuel per turn. The first game turn is 2× and the first draft turn is 10×. The numbers below are from the instrumented build on the 160-game run (both opponents, every champion-turn). An out is a turn ended by `TurnBudget`: the 120,000 reserve, or a stack the engine resumed on a later round. Percents are of that turn's own budget. p95 is the top of the 5% histogram bin that contains the 95th percentile, so 55 means at least 95% of turns used at most 55% of the budget.

| slice | turns | outs | out rate | max | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 100×100 | 55478 | 51 | 0.092% | 99.4% | 55% |
| every other size | 371992 | 98 | 0.026% | 98.9% | 40% |
| all turns | 427470 | 149 | 0.035% | 99.4% | 45% |

100×100 is 00ambush and 01big-world. The highest single turn on those maps was 99.4% of the budget. Six turns on 45×30 (00swirl) and a handful of others reached the high 90s; the out rate there is 0.04%.

**Stay in Python.** `STRATEGY.md` says to port only if more than 5% of turns on 100×100 maps yield. The measured rate is 0.09%, about 50 times under that line. C++ and Rust get 100,000 fuel, 25× less. Most of that gap pays for the interpreter, so a port is roughly 1.5–4× more search, not 25×, and it would rewrite the bot that just won 78/80 against the starter. The turns that run out are rare enough that they are not why corridors, ambush, the boss, or stampede miss 1000 gems. The logger is not in the shipped bot; with it removed there is slightly more headroom than this table shows.

## Reproduce

```bash
cd arena
./batch.sh baseline 3 /tmp/bc-out/baseline
./batch.sh starter-python 3 /tmp/bc-out/starter
python3 fuel.py /tmp/bc-out/baseline/replays /tmp/bc-out/starter/replays
```

`arena/bots/ours/src` points at the repo `src/`. `arena/bots/baseline` is a copy of that tree at the frozen commit. `arena/bots/starter-python` is the SDK Python template.
