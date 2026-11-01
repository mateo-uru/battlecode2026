# R1_vesper_open (Cambridge Battlecode 2026 submission v170), 2026-10-28

Base: teammate's v169 ("47"), the live bot at the time. Only change: `src/g_draft.py` puts Vesper Vale first in every draft preference list (top-of-ladder meta opens Vesper; it also denies it to the enemy).

Local Engine 2.0.0 benchmark (`cambc run-batch --release`, both sides per map):

| Matchup | Games | Record | Net gems | Faults |
|---|---|---|---|---|
| R1 vs v169, 10-map suite | 20 | 10-10 (50.0%) | +1,047 | 0 |
| R1 vs v169, 5 ladder-loss maps (interlock, geodes, fields, elk-arena, road-of-riches) | 10 | 7-3 (70.0%) | +3,222 | 0 |
| R1 vs v169, 13 extra maps | 26 | 17-9 (65.4%) | +3,689 | 0 |
| R1 vs v169, all | 56 | 34-22 (60.7%) | +7,958 | 0 |
| R1 vs v167, 10-map suite | 20 | 10-10 (50.0%) | +819 | 0 |
| v169 vs v167 (reference), 15 maps | 30 | 18-12 (60.0%) | +878 | 0 |
| Heart-first draft variant vs v169 (rejected) | 30 | 10-20 (33.3%) | -4,412 | 0 |

Caveat: local results overrated v167 (63% locally vs ~45% on ladder), so watch v170's ranked record and revert to v169 if it underperforms.
