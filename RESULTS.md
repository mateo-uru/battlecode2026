# Arena results

`src/` is now `M3_omega_final` (Patch 2.0.0). The package adds `cambc.toml` (`name = "bbot"`, Python) and the report in `STRATEGY_V4_PATCH2.md`. That report, on Engine 2.0.0 / CLI 4.0.0, is 15/20 against `A_v3_base` (+5,562 gems, +117 kills minus deaths, 0 crashes) across 10 maps from both sides. This machine checked `python3 -m py_compile src/*.py` and did not re-run that 20-game benchmark.

The tables below are the earlier CLI 3.0.5 measurement of the V3 bot, kept so that record stays in the repo. They are not the score of `M3_omega_final`.

`src/` at the time of those tables was the V3 bot: the frozen baseline, the V2 map split cap, and four further edits in `picker.py`, `body.py`, `g_farm.py`, and `g_bank.py`. The write-up for that bot is `STRATEGY_V3.md`.

Games were `cambc run --release` with CLI 3.0.5, a 2000-round limit, and 3 workers. The baseline suite finished at 21:32 Europe/Madrid and the starter suite at 21:46 Europe/Madrid on 25 October 2026. A win is the engine's winner (gems, then gold earned, then kills, then team B). Gem differential is our tributed gems minus the opponent's, summed over all 80 games. Gold differential is the same sum for gold earned.

`STRATEGY_V3.md` records 45–35, +3,977 gems, and +17,962 gold. This run matches the win count and the "no map is 0–2" result. Gems are +4,025 and gold is +20,988. The gaps are named under the baseline table.

## What V3 changes

1. **`picker.py`.** `is_src_map` still matches the seven known deimos maps by fingerprint `(width, height, walls, holes, altars, bushes)`, and it also matches three structural rules on that same tuple: a compact low-wall arena (`area <= 1400`, at most 2 altars, at most 40 walls, at most 36 bushes, and not both 24+ bushes and 200+ holes); a multi-altar map (15 or more altars); a large walled map (`area >= 6400`, at least 500 walls, 50 to 160 bushes). On this 40-map pool the rules add no map beyond those seven. Every other map stayed on bbot, which is why 34 of them mirror the frozen bot exactly.
2. **`mapinfo.py`.** Unchanged from V2: `sparse` requires `area < 9000`, so the 100×100 pack stays together. 01starvation (area 6,400) still splits.
3. **`body.py` and `g_farm.py`, corridors only.** The vision-gated respawn approach and the hurt-or-rich recall run only when `W * H == 2040` (51×40, 01corridors). Every other map uses the frozen respawn wait. That is what put `00fragment`, `00quadrants`, `00rushbait-v2`, and `01islands` back on 1–1.
4. **`g_bank.py`.** On `W * H == 2050` (50×41, 01boss-battle), banking unlatches after 12 turns that do not get closer to the altar, then waits 80 rounds. The monolith in front of the altar was latching champions into a walk that earned nothing.
5. **`g_farm.py`, stampede only.** After round 1000 on `W * H == 3000`, an elk camp that still holds gems may be taken when the damage product is up to 3.5× health instead of 2×. That is the late herd on 00stampede.

## Versus the frozen baseline

**45 wins / 35 losses, 52,986 vs 48,961 gems, differential +4,025. Gold 550,894 vs 529,906, differential +20,988. 0 crashes. 0 maps are 0–2.**

V2 on this same machine was 46–34 and +7,172 gems, with four maps at 0–2. V3 gives one win and 3,147 gems back, and those four maps are mirrors again. The extra V2 wins were side effects of applying the corridor fix on every map.

Five maps are 2–0:

| map | side A gems | side B gems | net gems | side A gold | side B gold | net gold |
| --- | --- | --- | ---: | --- | --- | ---: |
| 00ambush | 673–353 | 561–452 | +429 | 5,104–9,672 | 4,488–9,894 | −9,974 |
| 00elkring | 1001–704 | 1001–814 | +484 | 11,218–8,570 | 10,234–9,350 | +3,532 |
| 00lanes | 1002–431 | 1015–630 | +956 | 11,062–4,580 | 9,620–5,596 | +10,506 |
| 01boss-battle | 0–0 | 0–0 | 0 | 4,294–1,978 | 3,142–2,206 | +3,252 |
| 01corridors | 1030–16 | 1022–40 | +1,996 | 7,872–1,032 | 7,152–680 | +13,312 |

00stampede splits 1–1 and is not a mirror. Side A is 0–0 and loses on gold (8,416 vs 8,460). Side B is 160–0 (gold 8,916 vs 8,512). Net +160 gems and +360 gold. The write-up's 160–0 side B matches this run.

Where this run and `STRATEGY_V3.md` disagree:

- 00ambush side A is 673–353 here and 636–376 in the write-up. Side B is 561–452 in both. Net gems +429 here, +369 there.
- 01corridors is 1,030–16 / 1,022–40 here (+1,996) and 1,050–16 / 1,014–40 there (+2,008). Net gold is +13,312 in both.
- 01boss-battle gold is 4,294–1,978 / 3,142–2,206 here (+3,252) and 4,078–1,978 / 3,574–2,206 there (+3,468). Both are 2–0.
- 01starvation mirrors 456–155 / 155–456. The write-up has 101–571 / 593–123 and −3,964 gold. 00gem-fields and 01hooks also mirror here; the write-up gives them −96 and +696 gold. Those three clean mirrors are why gold is +20,988 here and +17,962 there.

The other 34 maps, including the four V2 regressions, are 1–1 with gem differential 0 and gold differential 0.

| map | side | gems | opponent | gold | opp gold | result | round |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| 00ambush | A | 673 | 353 | 5104 | 9672 | W | 2000 |
| 00ambush | B | 561 | 452 | 4488 | 9894 | W | 2000 |
| 00collision | A | 1001 | 380 | 7578 | 4474 | W | 1508 |
| 00collision | B | 380 | 1001 | 4474 | 7578 | L | 1508 |
| 00contest | A | 1000 | 0 | 17160 | 4588 | W | 1879 |
| 00contest | B | 0 | 1000 | 4588 | 17160 | L | 1879 |
| 00corners | A | 821 | 1011 | 8152 | 9140 | L | 1402 |
| 00corners | B | 1011 | 821 | 9140 | 8152 | W | 1402 |
| 00eight | A | 110 | 1013 | 2680 | 14852 | L | 1714 |
| 00eight | B | 1013 | 110 | 14852 | 2680 | W | 1714 |
| 00elkring | A | 1001 | 704 | 11218 | 8570 | W | 1911 |
| 00elkring | B | 1001 | 814 | 10234 | 9350 | W | 1838 |
| 00expanse | A | 647 | 1023 | 7678 | 10206 | L | 1600 |
| 00expanse | B | 1023 | 647 | 10206 | 7678 | W | 1600 |
| 00fragment | A | 738 | 28 | 9554 | 908 | W | 2000 |
| 00fragment | B | 28 | 738 | 908 | 9554 | L | 2000 |
| 00gem-fields | A | 498 | 1005 | 2774 | 5486 | L | 1254 |
| 00gem-fields | B | 1005 | 498 | 5486 | 2774 | W | 1254 |
| 00gemfight | A | 1001 | 82 | 7088 | 1336 | W | 1389 |
| 00gemfight | B | 82 | 1001 | 1336 | 7088 | L | 1389 |
| 00great-wall | A | 994 | 1004 | 6128 | 6770 | L | 1737 |
| 00great-wall | B | 1004 | 994 | 6770 | 6128 | W | 1737 |
| 00interlock | A | 1028 | 535 | 8708 | 5776 | W | 1704 |
| 00interlock | B | 535 | 1028 | 5776 | 8708 | L | 1704 |
| 00lanes | A | 1002 | 431 | 11062 | 4580 | W | 1813 |
| 00lanes | B | 1015 | 630 | 9620 | 5596 | W | 1862 |
| 00lost-world | A | 1010 | 732 | 3876 | 2118 | W | 1069 |
| 00lost-world | B | 732 | 1010 | 2118 | 3876 | L | 1069 |
| 00monolith | A | 1029 | 723 | 9262 | 7362 | W | 1377 |
| 00monolith | B | 723 | 1029 | 7362 | 9262 | L | 1377 |
| 00packs | A | 568 | 1000 | 5536 | 9236 | L | 1573 |
| 00packs | B | 1000 | 568 | 9236 | 5536 | W | 1573 |
| 00pilgrimage | A | 591 | 279 | 8204 | 5736 | W | 2000 |
| 00pilgrimage | B | 279 | 591 | 5736 | 8204 | L | 2000 |
| 00quadrants | A | 1007 | 909 | 3100 | 2220 | W | 923 |
| 00quadrants | B | 909 | 1007 | 2220 | 3100 | L | 923 |
| 00reverse-spiral | A | 966 | 218 | 7272 | 2154 | W | 2000 |
| 00reverse-spiral | B | 218 | 966 | 2154 | 7272 | L | 2000 |
| 00road-of-riches | A | 1028 | 387 | 4214 | 1910 | W | 1741 |
| 00road-of-riches | B | 387 | 1028 | 1910 | 4214 | L | 1741 |
| 00rows | A | 613 | 516 | 8328 | 8116 | W | 2000 |
| 00rows | B | 516 | 613 | 8116 | 8328 | L | 2000 |
| 00rushbait-v2 | A | 643 | 1000 | 4236 | 7728 | L | 1819 |
| 00rushbait-v2 | B | 1000 | 643 | 7728 | 4236 | W | 1819 |
| 00split | A | 158 | 1004 | 2474 | 7060 | L | 1200 |
| 00split | B | 1004 | 158 | 7060 | 2474 | W | 1200 |
| 00stampede | A | 0 | 0 | 8416 | 8460 | L | 2000 |
| 00stampede | B | 160 | 0 | 8916 | 8512 | W | 2000 |
| 00swirl | A | 862 | 186 | 16426 | 3630 | W | 2000 |
| 00swirl | B | 186 | 862 | 3630 | 16426 | L | 2000 |
| 01big-world | A | 1141 | 747 | 9208 | 6822 | W | 1937 |
| 01big-world | B | 747 | 1141 | 6822 | 9208 | L | 1937 |
| 01boss-battle | A | 0 | 0 | 4294 | 1978 | W | 2000 |
| 01boss-battle | B | 0 | 0 | 3142 | 2206 | W | 2000 |
| 01broken-curve | A | 484 | 1078 | 3960 | 6162 | L | 1100 |
| 01broken-curve | B | 1078 | 484 | 6162 | 3960 | W | 1100 |
| 01concentrated-wealth | A | 241 | 1000 | 3504 | 10178 | L | 1704 |
| 01concentrated-wealth | B | 1000 | 241 | 10178 | 3504 | W | 1704 |
| 01corridors | A | 1030 | 16 | 7872 | 1032 | W | 1476 |
| 01corridors | B | 1022 | 40 | 7152 | 680 | W | 1792 |
| 01elk-arena | A | 504 | 216 | 13156 | 11192 | W | 2000 |
| 01elk-arena | B | 216 | 504 | 11192 | 13156 | L | 2000 |
| 01fracture | A | 749 | 1003 | 7164 | 7050 | L | 1914 |
| 01fracture | B | 1003 | 749 | 7050 | 7164 | W | 1914 |
| 01gold-rush | A | 121 | 1007 | 1228 | 11832 | L | 1553 |
| 01gold-rush | B | 1007 | 121 | 11832 | 1228 | W | 1553 |
| 01hooks | A | 1012 | 66 | 14310 | 1898 | W | 1861 |
| 01hooks | B | 66 | 1012 | 1898 | 14310 | L | 1861 |
| 01islands | A | 1026 | 630 | 7680 | 7716 | W | 1633 |
| 01islands | B | 630 | 1026 | 7716 | 7680 | L | 1633 |
| 01shortcut | A | 324 | 814 | 3462 | 6054 | L | 2000 |
| 01shortcut | B | 814 | 324 | 6054 | 3462 | W | 2000 |
| 01starfish | A | 1031 | 347 | 11140 | 4852 | W | 1679 |
| 01starfish | B | 347 | 1031 | 4852 | 11140 | L | 1679 |
| 01starvation | A | 456 | 155 | 5536 | 3124 | W | 2000 |
| 01starvation | B | 155 | 456 | 3124 | 5536 | L | 2000 |
| 01the-farm | A | 89 | 65 | 1432 | 966 | W | 2000 |
| 01the-farm | B | 65 | 89 | 966 | 1432 | L | 2000 |
| 01yellow-brick-road | A | 1005 | 862 | 14336 | 14180 | W | 1337 |
| 01yellow-brick-road | B | 862 | 1005 | 14180 | 14336 | L | 1337 |

## Versus starter-python

**80 wins / 80 games, 73,803 vs 10,375 gems, differential +63,428. Gold differential +576,706. 0 crashes.**

The frozen bot was 78/80 and +62,157. V2 was 80/80 and +64,770. V3 keeps the sweep. 01corridors side A is 1,014–258 (the frozen bot lost 16–504). 00ambush side A is 797–418 (the frozen bot lost 353–428). 01boss-battle is 0–0 from both sides and wins on gold (1,996 vs 529, and 4,120 vs 1,020). 00stampede is 320–0 from both sides.

Games that finish under 1,000 of our gems, all of them wins:

| map | side | gems | opponent | our gold | opp gold |
| --- | --- | ---: | ---: | ---: | ---: |
| 00ambush | A | 797 | 418 | 6378 | 3285 |
| 00ambush | B | 644 | 362 | 4724 | 2178 |
| 00pilgrimage | A | 707 | 0 | 7218 | 3720 |
| 00pilgrimage | B | 818 | 0 | 8436 | 3878 |
| 00rows | A | 741 | 230 | 11312 | 3859 |
| 00rows | B | 942 | 208 | 13112 | 3300 |
| 00rushbait-v2 | A | 791 | 44 | 4332 | 1560 |
| 00stampede | A | 320 | 0 | 21264 | 4640 |
| 00stampede | B | 320 | 0 | 17748 | 4777 |
| 01big-world | A | 967 | 363 | 7754 | 3400 |
| 01boss-battle | A | 0 | 0 | 1996 | 529 |
| 01boss-battle | B | 0 | 0 | 4120 | 1020 |
| 01shortcut | B | 793 | 0 | 3928 | 960 |
| 01starvation | A | 864 | 0 | 5548 | 0 |
| 01starvation | B | 886 | 0 | 5712 | 0 |
| 01the-farm | A | 0 | 0 | 904 | 548 |
| 01the-farm | B | 159 | 45 | 2156 | 633 |

| map | side | gems | opponent | gold | opp gold | result | round |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| 00ambush | A | 797 | 418 | 6378 | 3285 | W | 2000 |
| 00ambush | B | 644 | 362 | 4724 | 2178 | W | 2000 |
| 00collision | A | 1007 | 52 | 8456 | 1660 | W | 1139 |
| 00collision | B | 1020 | 66 | 7728 | 1000 | W | 1150 |
| 00contest | A | 1000 | 0 | 20564 | 2565 | W | 1615 |
| 00contest | B | 1000 | 0 | 21816 | 2600 | W | 1806 |
| 00corners | A | 1050 | 25 | 10088 | 810 | W | 888 |
| 00corners | B | 1001 | 24 | 9252 | 1019 | W | 871 |
| 00eight | A | 1058 | 44 | 10826 | 1715 | W | 1229 |
| 00eight | B | 1017 | 72 | 10050 | 2086 | W | 1210 |
| 00elkring | A | 1000 | 514 | 9672 | 3796 | W | 1426 |
| 00elkring | B | 1001 | 488 | 8366 | 3356 | W | 1387 |
| 00expanse | A | 1003 | 296 | 8686 | 2500 | W | 1161 |
| 00expanse | B | 1034 | 286 | 8626 | 2394 | W | 1188 |
| 00fragment | A | 1024 | 16 | 15662 | 586 | W | 1588 |
| 00fragment | B | 1011 | 25 | 15062 | 750 | W | 1545 |
| 00gem-fields | A | 1049 | 501 | 4157 | 866 | W | 836 |
| 00gem-fields | B | 1007 | 418 | 3134 | 497 | W | 676 |
| 00gemfight | A | 1005 | 91 | 5186 | 1206 | W | 985 |
| 00gemfight | B | 1008 | 57 | 5276 | 753 | W | 1075 |
| 00great-wall | A | 1049 | 135 | 6350 | 1240 | W | 1395 |
| 00great-wall | B | 1000 | 100 | 5344 | 1280 | W | 1385 |
| 00interlock | A | 1005 | 65 | 8208 | 1202 | W | 1035 |
| 00interlock | B | 1001 | 165 | 8132 | 1673 | W | 1044 |
| 00lanes | A | 1011 | 335 | 8986 | 1779 | W | 1462 |
| 00lanes | B | 1015 | 464 | 8642 | 2300 | W | 1458 |
| 00lost-world | A | 1010 | 0 | 630 | 0 | W | 400 |
| 00lost-world | B | 1048 | 0 | 878 | 0 | W | 472 |
| 00monolith | A | 1009 | 182 | 11392 | 2206 | W | 1052 |
| 00monolith | B | 1004 | 59 | 10256 | 1160 | W | 1055 |
| 00packs | A | 1000 | 52 | 9500 | 1060 | W | 865 |
| 00packs | B | 1000 | 64 | 8328 | 1012 | W | 857 |
| 00pilgrimage | A | 707 | 0 | 7218 | 3720 | W | 2000 |
| 00pilgrimage | B | 818 | 0 | 8436 | 3878 | W | 2000 |
| 00quadrants | A | 1009 | 290 | 2750 | 1009 | W | 682 |
| 00quadrants | B | 1013 | 241 | 2152 | 794 | W | 583 |
| 00reverse-spiral | A | 1015 | 263 | 7928 | 360 | W | 1482 |
| 00reverse-spiral | B | 1006 | 154 | 7604 | 360 | W | 1445 |
| 00road-of-riches | A | 1003 | 152 | 3764 | 968 | W | 1680 |
| 00road-of-riches | B | 1014 | 238 | 4784 | 1330 | W | 1907 |
| 00rows | A | 741 | 230 | 11312 | 3859 | W | 2000 |
| 00rows | B | 942 | 208 | 13112 | 3300 | W | 2000 |
| 00rushbait-v2 | A | 791 | 44 | 4332 | 1560 | W | 2000 |
| 00rushbait-v2 | B | 1013 | 128 | 6104 | 2587 | W | 1427 |
| 00split | A | 1016 | 152 | 5358 | 1580 | W | 1101 |
| 00split | B | 1021 | 100 | 4908 | 1719 | W | 1072 |
| 00stampede | A | 320 | 0 | 21264 | 4640 | W | 2000 |
| 00stampede | B | 320 | 0 | 17748 | 4777 | W | 2000 |
| 00swirl | A | 1014 | 10 | 17668 | 1887 | W | 1837 |
| 00swirl | B | 1008 | 78 | 16190 | 2351 | W | 1809 |
| 01big-world | A | 967 | 363 | 7754 | 3400 | W | 2000 |
| 01big-world | B | 1013 | 249 | 9096 | 2221 | W | 1745 |
| 01boss-battle | A | 0 | 0 | 1996 | 529 | W | 2000 |
| 01boss-battle | B | 0 | 0 | 4120 | 1020 | W | 2000 |
| 01broken-curve | A | 1009 | 98 | 5972 | 1020 | W | 1051 |
| 01broken-curve | B | 1011 | 88 | 6288 | 1092 | W | 1031 |
| 01concentrated-wealth | A | 1038 | 80 | 8638 | 1115 | W | 1392 |
| 01concentrated-wealth | B | 1052 | 148 | 9056 | 1490 | W | 1316 |
| 01corridors | A | 1014 | 258 | 8832 | 1376 | W | 1598 |
| 01corridors | B | 1036 | 58 | 9676 | 360 | W | 1493 |
| 01elk-arena | A | 1008 | 0 | 21896 | 1952 | W | 1602 |
| 01elk-arena | B | 1008 | 0 | 18504 | 5560 | W | 1690 |
| 01fracture | A | 1028 | 96 | 10358 | 2831 | W | 1866 |
| 01fracture | B | 1035 | 164 | 9964 | 3394 | W | 1848 |
| 01gold-rush | A | 1007 | 330 | 14424 | 1200 | W | 1870 |
| 01gold-rush | B | 1095 | 330 | 13108 | 1280 | W | 1573 |
| 01hooks | A | 1012 | 110 | 15728 | 1446 | W | 1384 |
| 01hooks | B | 1012 | 0 | 14076 | 1615 | W | 1305 |
| 01islands | A | 1004 | 0 | 8258 | 773 | W | 1209 |
| 01islands | B | 1015 | 30 | 7262 | 1353 | W | 1390 |
| 01shortcut | A | 1007 | 0 | 5334 | 1630 | W | 1880 |
| 01shortcut | B | 793 | 0 | 3928 | 960 | W | 2000 |
| 01starfish | A | 1037 | 55 | 9264 | 1556 | W | 1138 |
| 01starfish | B | 1017 | 59 | 7808 | 1400 | W | 1219 |
| 01starvation | A | 864 | 0 | 5548 | 0 | W | 2000 |
| 01starvation | B | 886 | 0 | 5712 | 0 | W | 2000 |
| 01the-farm | A | 0 | 0 | 904 | 548 | W | 2000 |
| 01the-farm | B | 159 | 45 | 2156 | 633 | W | 2000 |
| 01yellow-brick-road | A | 1011 | 60 | 14834 | 1132 | W | 1027 |
| 01yellow-brick-road | B | 1006 | 90 | 8722 | 1398 | W | 1132 |

## Earlier measurements

The bot at `9769186` played itself 40–40 with differential 0, and beat starter-python 78/80 (+62,157), losing 01corridors side A (16–504) and 00ambush side A (353–428).

V2 (deimos on lanes and elkring, the area cap, and the corridor fix on every map) was 46–34 and +7,172 gems against the frozen bot, and 80/80 and +64,770 against the starter. It also went 0–2 on 00fragment, 00quadrants, 00rushbait-v2, and 01islands. V3 is the scoped replacement for that patch.

**One merged bot** (independent banking, Home emblem first, enemy-reactive draft, tank rotation everywhere, denial and hunting) lost to the frozen bot **18/78, gem differential −28,636**. Not kept.

**Corridor farmer and a wall-fraction switch.** Raising 01corridors side A against the starter dropped side B from 946 to 176. The wall test also pulled in open rooms. Not kept.

**Forcing the boss monolith** as the only target scored 0 gems, 0 gold, and 64 deaths. A softer version scored 279–0 against the starter from side A and 0–87 against the frozen bot. Not kept.

## Fuel

Python's budget is 2,500,000 fuel per turn. The first game turn is 2× and the first draft turn is 10×. The numbers below are from the instrumented build on the earlier 160-game run, before V2 and V3. An out is a turn ended by `TurnBudget`. p95 is the top of the 5% histogram bin that contains the 95th percentile.

| slice | turns | outs | out rate | max | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 100×100 | 55478 | 51 | 0.092% | 99.4% | 55% |
| every other size | 371992 | 98 | 0.026% | 98.9% | 40% |
| all turns | 427470 | 149 | 0.035% | 99.4% | 45% |

**Stay in Python.** `STRATEGY.md` says to port only if more than 5% of turns on 100×100 maps yield. The measured rate is 0.09%. The logger is not in the shipped bot. The picker reads public tile counts once per game, not per turn.

## Reproduce

```bash
cd arena
./batch.sh baseline 3 /tmp/bc-out/baseline
./batch.sh starter-python 3 /tmp/bc-out/starter
```

`arena/bots/ours/src` points at the repo `src/`. `arena/bots/baseline` is a copy of that tree at the frozen commit. `arena/bots/starter-python` is the SDK Python template.
