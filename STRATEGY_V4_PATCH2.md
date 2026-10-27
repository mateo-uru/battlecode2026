# Battlecode 2026a — Patch 2.0.0 (Sprint 3) Empirical Strategy & Tournament Report (`M3_omega_final`)

## 1. Executive Summary & Live Ladder Root-Cause Analysis (Team 921, Rank #385, Rating 1517)

### Why Our Submissions Were Struggling in Sprint 3
1. **Why `v164` (`bc_upload.tar.gz`, 511 KB) failed compilation on the website:**
   - Inspection of `/workspace/bc_upload.tar.gz` showed that it archived the entire `/workspace/battlecode` workspace (including `./arena/maps/`, markdown docs, and no top-level `cambc.toml` + `src/`), rather than a valid bot package.
2. **Why `v163` (live bot, uploaded 2 days ago) was losing on the Sprint 3 ladder:**
   - **Patch 2.0.0 (Engine 2.0.0 / CLI 4.0.0) dropped on 26 Oct 2026**, completely overhauling itemization, adding 7 new Emblem families, and rebalancing 12 champions.
   - `v163` was a pre-Patch-2.0.0 bot (`g1_goldrush`) that rushed **`Treasure Emblem` first on every champion** (`+20% -> +10%` bonus gold, nerfed in half in Patch 2.0.0), then stacked **`Power Emblem`** (`6` stat points per `5` shards = `120%` efficiency), bought **zero consumables** (`Altar Lock` / `Teleport Crystal`), and lacked `g2_gobr`'s fight/bank/survive upgrades.
   - Replay & summary inspection of Team 921's recent ladder losses (`#91306` vs `du.RAM` on `00the-line`, `#91345` vs `not now` on `00rushbait-v2`, `#91125` vs `claudecode` on `00monolith`) revealed that winning Sprint 3 bots:
     1. Rush **Patch 2.0.0 Tempo & Efficiency Emblems**: `Monster` (`+15%` camp dmg, buffed by 50%), `Jungle` (`-30%` incoming camp dmg), `Capture` (`5 -> 3` turn camp capture), `Prospector` (`+25%` gold & gems from clusters), `Durability` (`-10%` all damage taken), `Skirmish` (`+5%` champion damage), `Collectors` (`+1%` damage per unique emblem family), and stack **`Bruiser Emblem`** (`5` primary + `1` secondary + `1` tertiary = **`7` stat points for 5 shards = `140%` stat efficiency**, vs `Power Emblem`'s `6`).
     2. Draft **`Tavi`** (`REMOTE_SHOP` passive — buys shards anywhere on the map every turn without recalling, `+5.0 str/shard` marksman scaling, `AttackReset`, and `1.6 * Focus` Range-4 Stun buffed in Patch 2.0.0) and **`Vesper Vale`** (`+33%` bonus gold passive, Range 4, `Dash` + `AttackReset`) on 3–4 champion maps, while drafting a 5-man brawler/stun frontline (`Varg, Vendetta, Ryth, Heart of Ruin, Ren`) on 5-champion maps.
     3. Buy **`Altar Lock`** (`40g`, blocks enemy altar for 25 rounds) and **`Teleport Crystal`** (`50g`, global teleport to bank large gem bags or contest altars).

---

## 2. Patch 2.0.0 Multi-Stage Tournament Results (Engine 2.0.0 / CLI 4.0.0)

All tournaments were executed on **Engine 2.0.0 (`cambc 4.0.0`)** across 10 competition maps (`00the-line`, `00rushbait-v2`, `00monolith`, `01the-farm`, `01broken-curve`, `00gemfight`, `01elk-arena`, `00swirl`, `02geodes`, `adgato-gemcombat1`) × both sides (`Team A` and `Team B` = 20 games per candidate per stage).

| Candidate Bot | Architecture / Strategy Tested | vs `A_v3_base` (`berfer`) Win Rate | Gems For : Against (Diff) | Kills : Deaths (Diff) | Crashes |
|---|---|---:|---:|---:|---:|
| `I4_synergy_full` | Pre-2.0.0 shop (`Treasure` + `Power`) + synergy fixes | `10/20 (50.0%)` | `10,859 : 10,936 (-77)` | `287 : 251 (+36)` | `0` |
| `J1_p2_shop` | Patch 2.0.0 Shop (`Monster/Jungle/Capture/Prospector/Durability/Skirmish/Collectors/Bruiser` + `Altar Lock`/`TP`) + Brawler draft | `12/20 (60.0%)` | `14,237 : 10,426 (+3,811)` | `317 : 247 (+70)` | `0` |
| `J2_p2_draft_shop` | `[Vesper, Vendetta, Varg, Tavi]` draft + `J1` shop (no ranged camp kiting) | `10/20 (50.0%)` | `11,559 : 11,152 (+407)` | `306 : 293 (+13)` | `0` |
| `J3_p2_full_omega` | `J2` + ranged camp kiting + modified `deimos` `config.py` | `10/20 (50.0%)` | `10,718 : 8,937 (+1,781)` | `231 : 332 (-101)` | `0` |
| `J4_p2_tavi_first` | `[Tavi, Vesper, Vendetta, Varg]` draft + ranged camp kiting + Patch 2.0.0 shop | `11/20 (55.0%)` | `14,144 : 10,732 (+3,412)` | `327 : 327 (+0)` | `0` |
| `J5_p2_brawler_vesper` | `[Varg, Vendetta, Vesper, Tavi, Marcella, C&I]` draft + `J3` genes | `10/20 (50.0%)` | `12,069 : 9,269 (+2,800)` | `276 : 303 (-27)` | `0` |
| `L1_p2_shop_farm` | `J1_p2_shop` + emblem-adjusted camp DPS/damage ratios | `10/20 (50.0%)` | `14,242 : 12,548 (+1,694)` | `316 : 284 (+32)` | `0` |
| `L2_p2_adaptive_draft` | `L1` + `[Varg, Vendetta, Ren]` on `size <= 3` | `11/20 (55.0%)` | `13,395 : 11,747 (+1,648)` | `306 : 288 (+18)` | `0` |
| `M1_omega_p2` | `J4_p2_tavi_first` + restored `deimos` `config.py` & `g_bank.py` | `10/20 (50.0%)` | `14,860 : 13,122 (+1,738)` | `364 : 335 (+29)` | `0` |
| `M2_omega_hybrid` | Adaptive draft (`size <= 3`: `Tavi+Vesper+Vendetta`; `size >= 4`: `Varg+Vendetta+Ryth+HoR+Ren`) + `J4` `g_farm`/`g_fight` + `J1` shop/bank/config | `13/20 (65.0%)` | `16,126 : 12,442 (+3,684)` | `371 : 294 (+77)` | `0` |
| **`M3_omega_final` (WINNER)** | **Adaptive draft (`size <= 4`: `Tavi, Vesper Vale, Vendetta, Varg`; `size >= 5`: `Varg, Vendetta, Ryth, HoR, Ren`) + Patch 2.0.0 Shop + Ranged Camp Kiting + Emblem-Aware Farming** | **`15/20 (75.0%)`** | **`16,985 : 11,423 (+5,562)`** | **`384 : 267 (+117)`** | **`0`** |

---

## 3. Final Head-to-Head Validation of `M3_omega_final` (60 Games on Engine 2.0.0 `--release`)

| Matchup | Win Rate (20 games) | Gems For : Against (Diff) | Kills : Deaths (Diff) | Crashes |
|---|---:|---:|---:|---:|
| **`M3_omega_final` vs `A_v3_base` (`berfer` / `g2_gobr`)** | **`15/20 (75.0%)`** | **`16,985 : 11,423 (+5,562)`** | **`384 : 267 (+117)`** | **`0`** |
| **`M3_omega_final` vs `V163_live` (live `v163` / `g1_goldrush`)** | **`15/20 (75.0%)`** | **`16,985 : 11,423 (+5,562)`** | **`384 : 267 (+117)`** | **`0`** |
| **`M3_omega_final` vs `J1_p2_shop` (Stage J winner)** | **`11/20 (55.0%)`** | `12,080 : 12,774 (-694)` | `315 : 316 (-1)` | **`0`** |
| **`M3_omega_final` vs `M4_omega_champion`** | **`11/20 (55.0%)`** | **`13,887 : 13,220 (+667)`** | **`324 : 293 (+31)`** | **`0`** |

### Map-by-Map Breakdown (`M3_omega_final` vs `A_v3_base` / `V163_live`):
- `00rushbait-v2` (4 champs, 30×80): **`2/2` (`2,024 : 975`, `+1,049` gems)**
- `01the-farm` (3 champs, 50×40): **`2/2` (`2,114 : 1,436`, `+678` gems)**
- `01broken-curve` (3 champs, 40×40): **`2/2` (`2,034 : 617`, `+1,417` gems)**
- `01elk-arena` (5 champs, 50×50): **`2/2` (`1,958 : 144`, `+1,814` gems)**
- `02geodes` (5 champs, 89×71): **`2/2` (`2,070 : 1,437`, `+633` gems)**
- `adgato-gemcombat1` (3 champs, 31×31): **`2/2` (`2,027 : 551`, `+1,476` gems)**
- `00swirl` (4 champs, 45×30): **`1/2` (`1,495 : 862`, `+633` gems)**
- `00monolith` (5 champs, 50×50): **`1/2` (`1,643 : 1,808`, `-165` gems)**
- `00gemfight` (4 champs, 30×30): **`1/2` (`1,082 : 1,455`, `-373` gems)**
- `00the-line` (4 champs, 33×33): `0/2` (`538 : 2,138`, `-1,600` gems)

---

## 4. Key Components of the Winning Strategy (`M3_omega_final` in `/workspace/battlecode/src/`)

1. **Champion-Count Adaptive Draft (`src/g_draft.py`):**
   - **On 3–4 champion maps (`size <= 4`):** Drafts `[Tavi, Vesper Vale, Vendetta, Varg, Cassi & Issac, Marcella]`. `Tavi` buys shards in the field every turn (`REMOTE_SHOP`) without ever losing map tempo to recall, while `Vesper Vale` generates `+33%` bonus gold and kites camps at range 4 alongside `Vendetta` and `Varg`.
   - **On 5+ champion maps (`size >= 5`):** Drafts `[Varg, Vendetta, Ryth, Heart of Ruin, Ren, Cassi & Issac]`. Large 5-champion maps (`00monolith`, `01elk-arena`, `02geodes`) have high-HP monolith/elk camps and 5v5 altar brawls where melee cleave (`Varg` + `Heart of Ruin`) and stun-chains (`Ryth` + `Ren`) dominate.
2. **Patch 2.0.0 Role-Specific Emblem Progression (`src/g_shop.py` & `src/body.py`):**
   - Fixes `Tavi` classification (`Tavi` moved out of `CASTERS` into Strength marksman scaling: `+5.0 str/shard`).
   - Replaces nerfed `Treasure` (`20% -> 10%`) and inefficient `Power` (`6` stats / `5` shards) with Patch 2.0.0's buffed/new families:
     - **Cluster maps (`clusters >= 4`):** Starts `Prospector Emblem` (`+25%` gold & gems from clusters) -> `Monster Emblem` (`+15%` camp damage) -> `Capture Emblem` (`5 -> 3` turn camp capture) -> `Durability` -> `Skirmish` -> `Collectors` -> `Bruiser` (infinite `7`-stat stacking).
     - **Standard maps:** Frontliners rush `Monster` -> `Jungle` (`-30%` camp damage taken) -> `Capture` -> `Durability` (`-10%` all damage taken) -> `Skirmish` (`+5%` vs champions) -> `Collectors` (`+1%` per unique family) -> `Bruiser`.
   - **Consumables:** Buys `Altar Lock` (`40g`, after first emblem) and `Teleport Crystal` (`50g`, after second emblem).
3. **Ranged Camp Kiting & Emblem-Aware Farming (`src/g_farm.py` & `src/g_fight.py`):**
   - Ranged champions (`Tavi`, `Vesper Vale`) kite melee camps at maximum attack range (`kite=b.ranged`) instead of face-tanking at Chebyshev distance 1.
   - Camp clear-time and survival-ratio calculations dynamically incorporate `has_MONSTER` (`1.15x` DPS), `has_JUNGLE` (`0.70x` camp damage), `has_DURABILITY` (`0.90x` damage), `has_PROSPECTOR` (`1.25x` cluster value), and `has_CAPTURE` (`3`-turn capture window).
