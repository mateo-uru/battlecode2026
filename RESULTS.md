# Arena results

`src/` is the frozen baseline plus four edits in `picker.py`, `mapinfo.py`, `body.py`, and `g_farm.py`. The root-cause write-up is `STRATEGY_V2.md`. This file is the score of that bot on this machine.

Games were `cambc run --release` with CLI 3.0.5, a 2000-round limit, and 3 workers. The suite ran from 19:25 to 19:53 Europe/Madrid on 25 October 2026. A win is the engine's winner (gems, then gold earned, then kills, then team B). Gem differential is our tributed gems minus the opponent's, summed over all 80 games.

`STRATEGY_V2.md` records an earlier run of the same four edits at 49–31 and +6,709 gems (53,851 vs 47,142). This run does not reproduce that record. Several maps match it exactly: 00ambush, 00elkring, 00rows, 00lanes side A, and 00pilgrimage side A. Others move. 01islands is 0–2 here and 2–0 in that write-up. The tables below are this run.

## The four edits

1. **`picker.py`.** `00lanes` `(90, 30, 0, 76, 18, 144)` and `00elkring` `(30, 30, 0, 36, 2, 36)` join the maps sent to deimos. On those two maps deimos beats bbot from both sides. The other five deimos maps are unchanged.
2. **`mapinfo.py`.** `sparse` now also requires `area < 9000`. 00ambush and 01big-world are 100×100 (area 10,000), so the squad stays together and can clear camps that need three champions. 01starvation is 80×80 (area 6,400) and still splits.
3. **`body.py`.** While a camp is respawning, the wait counter advances and the champion stops at range 3 only when the camp tiles are actually in vision. Otherwise it steps in to distance 1. The ready check uses the walk to the camp, so `pick()` and `farm_group()` stop handing the same group back and forth. On 01corridors the centroid sits on the side-A side of a bush curtain, and the old range-3 park left side A blind for the whole game.
4. **`g_farm.py`.** When no camp is safe to claim, a champion that is off spawn and either below 85% health or holding at least 60 gold recalls or walks home. That covers the corridor case where a champion at about 37.5% health was marching into a dead end, because the survive recall only fires below 35% and the shop recall wants zero gems and 150 gold.

## Versus the frozen baseline

**46 wins / 34 losses, 53,845 vs 46,673 gems, differential +7,172, 0 crashes.**

The frozen bot's self-play on the same 80 games was 40–40 and differential 0. Wins and gem differential both go up.

Ten maps are 2–0:

| map | side A | side B | net gems |
| --- | --- | --- | ---: |
| 00ambush | 673–353 | 561–452 | +429 |
| 00contest | 1000–0 | 1000–0 | +2000 |
| 00corners | 1019–974 | 1022–488 | +579 |
| 00elkring | 1001–704 | 1001–814 | +484 |
| 00lanes | 961–357 | 1000–789 | +815 |
| 00monolith | 1003–605 | 1012–641 | +769 |
| 00pilgrimage | 561–246 | 577–511 | +381 |
| 00reverse-spiral | 1002–200 | 1002–626 | +1178 |
| 00rows | 696–321 | 736–340 | +771 |
| 01corridors | 1030–16 | 1022–40 | +1996 |

Seven maps lose more than 150 gems across the pair. Self-play nets zero on every map, so these are the regressions past the 150-gem line in `STRATEGY.md`. Four of them are 0–2:

| map | record | side A | side B | net gems |
| --- | --- | --- | --- | ---: |
| 00fragment | 0–2 | 426–478 | 88–722 | -686 |
| 00interlock | 1–1 | 1002–540 | 209–1016 | -345 |
| 00quadrants | 0–2 | 559–1007 | 902–1000 | -546 |
| 00rushbait-v2 | 0–2 | 510–1020 | 364–1021 | -1167 |
| 01big-world | 1–1 | 821–1012 | 1007–969 | -153 |
| 01islands | 0–2 | 484–1055 | 658–1026 | -939 |
| 01the-farm | 1–1 | 89–65 | 0–257 | -233 |

The pair still finishes ahead. The 2–0 maps, led by 00contest (+2,000) and 01corridors (+1,996), outweigh those seven. 01corridors was 32–16 / 16–32 in self-play. 00ambush was 514–333 / 333–514.

00stampede is 0–0 both ways. Side A wins on gold (9,364 vs 8,684) and side B loses on gold (8,100 vs 9,064). 01boss-battle is 0–0 both ways. Side A wins on gold (2,206 vs 1,978) and side B loses on gold (2,048 vs 2,206).

| map | side | gems | opponent | result | round |
| --- | --- | ---: | ---: | --- | ---: |
| 00ambush | A | 673 | 353 | W | 2000 |
| 00ambush | B | 561 | 452 | W | 2000 |
| 00collision | A | 1001 | 444 | W | 1460 |
| 00collision | B | 304 | 1008 | L | 1793 |
| 00contest | A | 1000 | 0 | W | 1995 |
| 00contest | B | 1000 | 0 | W | 1613 |
| 00corners | A | 1019 | 974 | W | 1513 |
| 00corners | B | 1022 | 488 | W | 1252 |
| 00eight | A | 110 | 1013 | L | 1714 |
| 00eight | B | 1013 | 110 | W | 1714 |
| 00elkring | A | 1001 | 704 | W | 1911 |
| 00elkring | B | 1001 | 814 | W | 1838 |
| 00expanse | A | 1028 | 593 | W | 1366 |
| 00expanse | B | 630 | 1017 | L | 1555 |
| 00fragment | A | 426 | 478 | L | 2000 |
| 00fragment | B | 88 | 722 | L | 2000 |
| 00gem-fields | A | 616 | 1051 | L | 1320 |
| 00gem-fields | B | 1010 | 453 | W | 1161 |
| 00gemfight | A | 1001 | 82 | W | 1389 |
| 00gemfight | B | 82 | 1001 | L | 1389 |
| 00great-wall | A | 1000 | 703 | W | 1633 |
| 00great-wall | B | 978 | 1000 | L | 1479 |
| 00interlock | A | 1002 | 540 | W | 1988 |
| 00interlock | B | 209 | 1016 | L | 1549 |
| 00lanes | A | 961 | 357 | W | 2000 |
| 00lanes | B | 1000 | 789 | W | 1944 |
| 00lost-world | A | 1011 | 504 | W | 1032 |
| 00lost-world | B | 842 | 1009 | L | 1253 |
| 00monolith | A | 1003 | 605 | W | 1313 |
| 00monolith | B | 1012 | 641 | W | 1636 |
| 00packs | A | 218 | 1000 | L | 1321 |
| 00packs | B | 1002 | 166 | W | 1126 |
| 00pilgrimage | A | 561 | 246 | W | 2000 |
| 00pilgrimage | B | 577 | 511 | W | 2000 |
| 00quadrants | A | 559 | 1007 | L | 890 |
| 00quadrants | B | 902 | 1000 | L | 880 |
| 00reverse-spiral | A | 1002 | 200 | W | 1692 |
| 00reverse-spiral | B | 1002 | 626 | W | 2000 |
| 00road-of-riches | A | 1009 | 616 | W | 1806 |
| 00road-of-riches | B | 624 | 1030 | L | 1711 |
| 00rows | A | 696 | 321 | W | 2000 |
| 00rows | B | 736 | 340 | W | 2000 |
| 00rushbait-v2 | A | 510 | 1020 | L | 1783 |
| 00rushbait-v2 | B | 364 | 1021 | L | 1498 |
| 00split | A | 158 | 1004 | L | 1200 |
| 00split | B | 1009 | 97 | W | 1150 |
| 00stampede | A | 0 | 0 | W | 2000 |
| 00stampede | B | 0 | 0 | L | 2000 |
| 00swirl | A | 862 | 186 | W | 2000 |
| 00swirl | B | 186 | 862 | L | 2000 |
| 01big-world | A | 821 | 1012 | L | 1760 |
| 01big-world | B | 1007 | 969 | W | 1976 |
| 01boss-battle | A | 0 | 0 | W | 2000 |
| 01boss-battle | B | 0 | 0 | L | 2000 |
| 01broken-curve | A | 772 | 1035 | L | 1312 |
| 01broken-curve | B | 1015 | 546 | W | 1142 |
| 01concentrated-wealth | A | 373 | 1000 | L | 1893 |
| 01concentrated-wealth | B | 1018 | 387 | W | 1866 |
| 01corridors | A | 1030 | 16 | W | 1476 |
| 01corridors | B | 1022 | 40 | W | 1792 |
| 01elk-arena | A | 792 | 72 | W | 2000 |
| 01elk-arena | B | 72 | 720 | L | 2000 |
| 01fracture | A | 1028 | 739 | W | 1883 |
| 01fracture | B | 601 | 1000 | L | 1887 |
| 01gold-rush | A | 451 | 596 | L | 2000 |
| 01gold-rush | B | 1007 | 198 | W | 1856 |
| 01hooks | A | 1012 | 44 | W | 1721 |
| 01hooks | B | 22 | 1012 | L | 1731 |
| 01islands | A | 484 | 1055 | L | 1594 |
| 01islands | B | 658 | 1026 | L | 1631 |
| 01shortcut | A | 711 | 681 | W | 2000 |
| 01shortcut | B | 512 | 604 | L | 2000 |
| 01starfish | A | 1017 | 181 | W | 1502 |
| 01starfish | B | 177 | 1019 | L | 1455 |
| 01starvation | A | 456 | 155 | W | 2000 |
| 01starvation | B | 155 | 456 | L | 2000 |
| 01the-farm | A | 89 | 65 | W | 2000 |
| 01the-farm | B | 0 | 257 | L | 2000 |
| 01yellow-brick-road | A | 1028 | 613 | W | 1259 |
| 01yellow-brick-road | B | 934 | 1001 | L | 1133 |

## Versus starter-python

**80 wins / 80 games, 74,235 vs 9,465 gems, differential +64,770, 0 crashes.**

The frozen bot was 78/80 and +62,157 against the same starter. The two losses are now wins: 01corridors side A was 16–504 and is 1,014–258; 00ambush side A was 353–428 and is 797–418. `STRATEGY_V2.md` lists that ambush game as 658–531. This run scored 797–418.

These games finish under 1,000 of our gems. All of them are still wins:

| map | side | gems | opponent | our gold | opp gold |
| --- | --- | ---: | ---: | ---: | ---: |
| 00ambush | A | 797 | 418 | 6378 | 3285 |
| 00ambush | B | 644 | 362 | 4724 | 2178 |
| 00pilgrimage | A | 800 | 0 | 7078 | 3720 |
| 00pilgrimage | B | 803 | 0 | 7908 | 3878 |
| 00rows | A | 913 | 252 | 14656 | 3392 |
| 00rows | B | 839 | 193 | 12524 | 3100 |
| 00rushbait-v2 | A | 824 | 44 | 4764 | 1560 |
| 00stampede | A | 320 | 0 | 22620 | 4320 |
| 00stampede | B | 480 | 0 | 20144 | 5282 |
| 01boss-battle | A | 0 | 0 | 1996 | 529 |
| 01boss-battle | B | 0 | 0 | 3628 | 680 |
| 01shortcut | B | 873 | 0 | 4188 | 640 |
| 01starvation | A | 864 | 0 | 5548 | 0 |
| 01starvation | B | 886 | 0 | 5712 | 0 |
| 01the-farm | A | 0 | 0 | 904 | 548 |
| 01the-farm | B | 0 | 0 | 720 | 244 |

01boss-battle and 01the-farm are 0–0 from both sides and win on gold. 01the-farm side B was 159–45 on the frozen bot and is 0–0 here (gold 720 vs 244).

| map | side | gems | opponent | result | round |
| --- | --- | ---: | ---: | --- | ---: |
| 00ambush | A | 797 | 418 | W | 2000 |
| 00ambush | B | 644 | 362 | W | 2000 |
| 00collision | A | 1005 | 46 | W | 983 |
| 00collision | B | 1032 | 62 | W | 1060 |
| 00contest | A | 1000 | 0 | W | 1542 |
| 00contest | B | 1000 | 0 | W | 1760 |
| 00corners | A | 1009 | 38 | W | 828 |
| 00corners | B | 1004 | 20 | W | 870 |
| 00eight | A | 1058 | 44 | W | 1229 |
| 00eight | B | 1017 | 72 | W | 1210 |
| 00elkring | A | 1000 | 514 | W | 1426 |
| 00elkring | B | 1001 | 488 | W | 1387 |
| 00expanse | A | 1007 | 274 | W | 1201 |
| 00expanse | B | 1017 | 200 | W | 1171 |
| 00fragment | A | 1006 | 8 | W | 1523 |
| 00fragment | B | 1022 | 12 | W | 1627 |
| 00gem-fields | A | 1040 | 504 | W | 866 |
| 00gem-fields | B | 1062 | 343 | W | 670 |
| 00gemfight | A | 1005 | 91 | W | 985 |
| 00gemfight | B | 1008 | 57 | W | 1075 |
| 00great-wall | A | 1030 | 135 | W | 1350 |
| 00great-wall | B | 1071 | 139 | W | 1484 |
| 00interlock | A | 1037 | 113 | W | 1051 |
| 00interlock | B | 1005 | 68 | W | 960 |
| 00lanes | A | 1001 | 349 | W | 1583 |
| 00lanes | B | 1015 | 464 | W | 1458 |
| 00lost-world | A | 1018 | 0 | W | 434 |
| 00lost-world | B | 1004 | 0 | W | 404 |
| 00monolith | A | 1007 | 122 | W | 1024 |
| 00monolith | B | 1002 | 59 | W | 985 |
| 00packs | A | 1004 | 56 | W | 873 |
| 00packs | B | 1006 | 112 | W | 852 |
| 00pilgrimage | A | 800 | 0 | W | 2000 |
| 00pilgrimage | B | 803 | 0 | W | 2000 |
| 00quadrants | A | 1000 | 290 | W | 664 |
| 00quadrants | B | 1020 | 245 | W | 628 |
| 00reverse-spiral | A | 1000 | 189 | W | 1588 |
| 00reverse-spiral | B | 1007 | 168 | W | 1508 |
| 00road-of-riches | A | 1005 | 181 | W | 1602 |
| 00road-of-riches | B | 1002 | 196 | W | 1969 |
| 00rows | A | 913 | 252 | W | 2000 |
| 00rows | B | 839 | 193 | W | 2000 |
| 00rushbait-v2 | A | 824 | 44 | W | 2000 |
| 00rushbait-v2 | B | 1026 | 109 | W | 1403 |
| 00split | A | 1059 | 68 | W | 1030 |
| 00split | B | 1007 | 96 | W | 972 |
| 00stampede | A | 320 | 0 | W | 2000 |
| 00stampede | B | 480 | 0 | W | 2000 |
| 00swirl | A | 1014 | 10 | W | 1837 |
| 00swirl | B | 1008 | 78 | W | 1809 |
| 01big-world | A | 1005 | 259 | W | 1549 |
| 01big-world | B | 1017 | 180 | W | 1647 |
| 01boss-battle | A | 0 | 0 | W | 2000 |
| 01boss-battle | B | 0 | 0 | W | 2000 |
| 01broken-curve | A | 1179 | 44 | W | 1126 |
| 01broken-curve | B | 1020 | 48 | W | 1006 |
| 01concentrated-wealth | A | 1000 | 80 | W | 1296 |
| 01concentrated-wealth | B | 1003 | 63 | W | 1333 |
| 01corridors | A | 1014 | 258 | W | 1598 |
| 01corridors | B | 1036 | 58 | W | 1493 |
| 01elk-arena | A | 1008 | 0 | W | 1573 |
| 01elk-arena | B | 1008 | 0 | W | 1581 |
| 01fracture | A | 1028 | 90 | W | 1793 |
| 01fracture | B | 1012 | 110 | W | 1514 |
| 01gold-rush | A | 1001 | 193 | W | 1355 |
| 01gold-rush | B | 1007 | 341 | W | 1528 |
| 01hooks | A | 1012 | 154 | W | 1392 |
| 01hooks | B | 1012 | 0 | W | 1303 |
| 01islands | A | 1067 | 0 | W | 1279 |
| 01islands | B | 1011 | 0 | W | 1297 |
| 01shortcut | A | 1019 | 0 | W | 1911 |
| 01shortcut | B | 873 | 0 | W | 2000 |
| 01starfish | A | 1022 | 69 | W | 1309 |
| 01starfish | B | 1049 | 71 | W | 1302 |
| 01starvation | A | 864 | 0 | W | 2000 |
| 01starvation | B | 886 | 0 | W | 2000 |
| 01the-farm | A | 0 | 0 | W | 2000 |
| 01the-farm | B | 0 | 0 | W | 2000 |
| 01yellow-brick-road | A | 1004 | 60 | W | 1100 |
| 01yellow-brick-road | B | 1017 | 98 | W | 1080 |

## Before this patch

The bot at `9769186`, copied into `arena/bots/baseline`, played itself 40–40 with differential 0. Every map mirrored. Against starter-python that same bot was 78/80 and +62,157, losing only 01corridors side A (16–504) and 00ambush side A (353–428).

## Attempts that were measured and not kept

Acceptance rule from `STRATEGY.md`: keep a change only when total wins and total gem differential against the frozen bot both improve, and no map drops by more than 150 gems. The four edits above improve both totals. They also miss the per-map line on the seven maps in the regression table. They are the patch this run was asked to verify, and the overall record is a win, so they are what shipped.

**One merged bot** (independent banking, Home emblem first, enemy-reactive draft, tank rotation everywhere, denial and hunting) lost to the frozen bot **18/78, gem differential −28,636**. Two games in that run did not produce a scoreboard. It was reverted.

**Corridor farmer.** A brain that walks to the nearest gem camp and skips the monolith raised 01corridors side A to 425–261 against the starter and dropped side B to 176–202. Net gems against the starter fell. A wall-fraction switch (walls covering at least 12% of the tiles) also sent 00great-wall, 00lost-world, 00road-of-riches, 01broken-curve, and 01shortcut to that farmer. Those maps are rooms behind a wall, not one-tile halls. Not kept.

**Altar monolith, forced.** Treating the monolith on 01boss-battle as the only legal target made the team stand in the beam: 0 gems, 0 gold, 64 deaths, and a gold-tiebreak loss to the starter. Not kept.

**Altar monolith, soft, plus a per-turn fuel log.** Waiving the damage cap for a monolith that blocks the altar, and giving it a score floor of 50, scored **279–0** against the starter from side A (side B stayed 0–0 and won on gold). Against the frozen bot the same change scored **0–87** and **0–0** (gold loss). The fuel log, which calls `fuel_remaining` every turn and prints a histogram every 100 rounds, also broke self-play on maps that do not have that monolith: 01starvation went from a 456–155 mirror to 101–571 and 260–384, and 00corners and 00ambush stopped mirroring. 00corners never recorded a turn above 75% of the budget, so the print alone was enough to move the game. Not kept.

## Fuel

Python's budget is 2,500,000 fuel per turn. The first game turn is 2× and the first draft turn is 10×. The numbers below are from the instrumented build on the earlier 160-game run (both opponents, every champion-turn), before these four edits. An out is a turn ended by `TurnBudget`: the 120,000 reserve, or a stack the engine resumed on a later round. Percents are of that turn's own budget. p95 is the top of the 5% histogram bin that contains the 95th percentile, so 55 means at least 95% of turns used at most 55% of the budget.

| slice | turns | outs | out rate | max | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 100×100 | 55478 | 51 | 0.092% | 99.4% | 55% |
| every other size | 371992 | 98 | 0.026% | 98.9% | 40% |
| all turns | 427470 | 149 | 0.035% | 99.4% | 45% |

100×100 is 00ambush and 01big-world. The highest single turn on those maps was 99.4% of the budget.

**Stay in Python.** `STRATEGY.md` says to port only if more than 5% of turns on 100×100 maps yield. The measured rate is 0.09%. C++ and Rust get 100,000 fuel, 25× less. Most of that gap pays for the interpreter, so a port is roughly 1.5–4× more search, and it would rewrite the bot that won 80/80 against the starter. The logger is not in the shipped bot.

## Reproduce

```bash
cd arena
./batch.sh baseline 3 /tmp/bc-out/baseline
./batch.sh starter-python 3 /tmp/bc-out/starter
```

`arena/fuel.py` reads `FUEL` histogram lines out of a replay's stdout. The shipped bot does not print those lines. `arena/bots/ours/src` points at the repo `src/`. `arena/bots/baseline` is a copy of that tree at the frozen commit. `arena/bots/starter-python` is the SDK Python template.
