# Cambridge Battlecode 2026 (`cambc2026a`) — Strategy V2 & Post-Mortem

## 1. Executive Summary

Earlier, `STRATEGY.md` proposed replacing our dual-bot dispatch (`picker.py`) with a single unified `brain.py` (`deimos`) bot and modifying `brain.py`'s combat/farming/emblem heuristics. When the Cursor Cloud Agent implemented `STRATEGY.md` (PR #1 on `mateo-uru/battlecode2026`) and benchmarked it head-to-head against the frozen baseline across all 80 games (40 maps × sides A & B), **the unified `brain.py` bot went 18–60 (−28,636 net gems)**. Even smaller overrides (a wall-density `choke_farm` override and a `boss` monolith override) lost head-to-head against the frozen baseline.

In this investigation, we:
1. **Diagnosed from the Cloud Agent transcript and full 80-game benchmarks why `STRATEGY.md` failed:** `bbot` (`body.py` + `g_*.py`, evolved genome `g2_gobr`) beats `deimos` (`brain.py`) **51–29 (+11,755 net gems)** across the 40-map pool (`54,283` vs `42,528` gems). Replacing `bbot` with `brain.py` on 35 maps threw away our strongest general-purpose bot.
2. **Ran a complete 80-game Head-to-Head (`deimos_only` vs `bbot_only`) across all 40 maps:** Found that `deimos` goes **2–0 (wins both Side A and Side B)** against `bbot` on **7 maps**, not 5—`00lanes` (+634 net gems) and `00elkring` (+484 net gems) were missing from `picker.py` (`00elkring` missed an arbitrary `+500` gem cutoff by 16 gems).
3. **Identified the exact step-by-step root causes of our two flagship failures (`01corridors` Side A and `00ambush` Side A):**
   - **`01corridors` Side A (16 gems vs 946 on Side B):** Caused by an integer-division centroid rounding asymmetry (`g.cy = (19+19+20+20)//4 = 19`) interacting with `body.py`'s `cheb(self.x, self.y, g.cx, g.cy) <= 3` wait condition during `g.state == 3` (respawn waiting) and symmetric bush curtains at `y = 17` (Side A) and `y = 22` (Side B), compounded by a `g_farm.py` stall when a damaged champion (`hpf = 0.375 >= 0.35`) cannot claim any camp (`g is None`).
   - **`00ambush` Side A (353–428 loss to `starter-python`):** Caused by `MapInfo.sparse = True` on `100×100` `00ambush`, which splits 4 of 6 champions into solo `roamers` that can only clear 0-gem gold clusters while leaving `active = 2` in the main squad—unable to clear the `need_for = 3` big gem camps until round ~850.
4. **Applied 4 surgical, 12-line fixes across `picker.py`, `mapinfo.py`, `body.py`, and `g_farm.py` and verified them across all 80 games against the frozen baseline:**
   - **Head-to-Head vs Frozen Baseline (80 games):** **49 wins / 31 losses (61.3% win rate), `53,851` vs `47,142` gems (+6,709 net gem differential), 0 crashes.**
   - **`01corridors` vs Baseline:** **2–0 sweep (`1000:16` on Side A, `1038:16` on Side B, +2,006 net gems).**
   - **`00ambush` vs Baseline:** **2–0 sweep (`673:353` on Side A, `561:452` on Side B, +429 net gems)**, and vs `starter-python` Side A jumps from **353–428 (LOSS)** to **658–531 (WIN, 0 deaths)**.

---

## 2. Post-Mortem: Why `STRATEGY.md` Failed

### 2.1 Replacing `bbot` with `brain.py` on 35 Maps Discarded Our Strongest Bot
Our repository contains two fundamentally different architectures:
- **`bbot` (`body.py` + `g_*.py`, evolved genome `g2_gobr`):**
  - Uses direct C/Rust `_cambc` bindings (`_bc.champion_get`, `_bc.camp_get`) with minimal Python bytecode overhead.
  - Precomputes static `DistanceField`s per camp group (`g.field`) and shares camp claims via 8-byte team shared memory (`bytes 0..5`), allowing 5 melee champions (`Varg, Vendetta, Ryth, Heart of Ruin, Ren`) to farm 5 separate camp groups in parallel across the map.
- **`deimos` (`brain.py` + `mapinfo.py` + `move.py`):**
  - Uses a centralized leader-anchor state machine (`Brain`) where followers trail a single leader (`rank 0`) to clear dense camps together or brawl as a deathball, plus k-means `roamers` when `mapinfo.sparse` is true.

When we tested `deimos_only` (`src`) vs `bbot_only` (`bbot`) across all 40 maps (80 games), **`bbot` won 51 of 80 games (63.8%) and out-scored `deimos` `54,283` to `42,528` (+11,755 gems)**. On open or multi-camp maps (`00fragment`, `00interlock`, `01yellow-brick-road`, `01concentrated-wealth`, `00expanse`, `00monolith`, `00corners`, `01big-world`), 5 independent `bbot` farmers out-farm `deimos`'s single pack by 1,000+ gems per map.

### 2.2 Why the Modifications to `brain.py` Regressed Even on `deimos`'s Own Maps
1. **Restricting `engage()` to gem carriers (`gems >= 20`) or incoming attackers:** On small brawl maps (`00eight`, `00gemfight`, `00swirl`), `deimos` wins by killing any isolated enemy within range to establish numbers advantage and control the central camps. Making `engage()` passive caused the merged bot to lose `00eight` `112–1008` (dying 99 times vs 24).
2. **Loosening `need_for()` and `solo_ok`:** Allowing followers to peel off and solo camps caused individual champions to walk into medium/large camps at low HP and die repeatedly.
3. **Buying `HOME` emblem before combat stats:** Delayed early weapon/vitality spikes, slowing first-clear times and losing early skirmishes.
4. **Heuristic overrides (`choke_farm` wall ratio >= 0.12 and `boss` monolith focus):**
   - Wall ratio `>= 0.12` misfired on room/maze maps (`00great-wall`, `00lost-world`, `00road-of-riches`, `01broken-curve`, `01shortcut`) and broke `01corridors` Side B (`946 -> 176` gems).
   - Forcing monolith focus on `01boss-battle` beat passive `starter-python` (`279–0`) but lost `0–87` to active `bbot` because tanking the monolith gets punished by enemy champions.
5. **Fuel Sensitivity:** While out-of-fuel faults only occur on 0.035% of turns (0.092% on 100×100 maps), `brain.py` runs close to the 2.5M bytecode fuel ceiling on 6-champion maps (`01starvation`, `00ambush`). Adding per-turn `DistanceField` recomputations or extra loops causes late-order champions to yield turns, snowballing mirror matches.

---

## 3. Complete 80-Game Benchmark: `deimos` (`src`) vs `bbot`

Across all 40 maps (Sides A & B, 80 games total):
- **`bbot` Wins:** 51 / 80 (63.8%), **54,283 total gems**
- **`deimos` Wins:** 29 / 80 (36.2%), **42,528 total gems**

### Maps Where `deimos` Sweeps `bbot` 2–0 (Both Side A and Side B)
| Map | Fingerprint `(W, H, walls, bushes, altars, camps)` | Side A (`deimos:bbot`) | Side B (`deimos:bbot`) | Net Gems | In Baseline `picker.py`? |
|---|---|---:|---:|---:|---|
| `00gemfight` | `(30, 30, 0, 108, 2, 16)` | `1042 : 129` (W) | `1031 : 75` (W) | `+1,869` | Yes |
| `00eight` | `(41, 30, 36, 22, 1, 24)` | `1011 : 11` (W) | `1005 : 161` (W) | `+1,844` | Yes |
| `00swirl` | `(45, 30, 30, 354, 2, 14)` | `902 : 260` (W) | `1029 : 360` (W) | `+1,311` | Yes |
| `01starvation` | `(80, 80, 664, 58, 2, 78)` | `526 : 198` (W) | `766 : 76` (W) | `+1,018` | Yes |
| **`00lanes`** | `(90, 30, 0, 76, 18, 144)` | **`1002 : 431` (W)** | **`1004 : 941` (W)** | **`+634`** | **NO (Added!)** |
| `00ambush` | `(100, 100, 540, 1832, 4, 132)` | `489 : 275` (W) | `690 : 341` (W) | `+563` | Yes |
| **`00elkring`** | `(30, 30, 0, 36, 2, 36)` | **`1001 : 704` (W)** | **`1001 : 814` (W)** | **`+484`** | **NO (Added!)** |

Adding `00lanes` and `00elkring` to `SRC_MAPS` in `picker.py` immediately captures two deterministic 2–0 sweeps (`+989` and `+484` net gems in H2H against the frozen baseline) with zero risk to any other map.

---

## 4. Exact Root-Cause Analysis of the Two Flagship Bugs

### 4.1 `01corridors` Side A (16 Gems) vs Side B (946 Gems)

#### Step 1: Map Geometry & Level-0 Camp Threshold
- `01corridors` (`51×40`) consists of 13 vertical corridors separated by walls (`y = 3..36`). Every camp group sits at the vertical midpoint **`y = 19..20`**.
- Across every corridor, there is a 1-tile horizontal bush curtain at **`y = 17` (Side A)** and a symmetric bush curtain at **`y = 22` (Side B)**.
- At level 0 (`hp = 1000..1600`), `g_farm.py` filters camps by `g.dmg * clear <= b.hp * 2.0`. Only two small wolf camps pass this check at level 0: **`G5` (`x = 8, y = 19..20`)** and **`G11` (`x = 44, y = 19..20`)** (`hp = 2940, dmg = 40, clear = 49 -> 1960 <= 2000`). All other gem camps have `g.dmg * clear = 6016 > 2000` and require buying items first.

#### Step 2: Integer-Division Centroid Rounding + Bush Vision Block in `body.py`
- Both `G5` and `G11` have 4 camp tiles at `y = 19, 19, 20, 20`.
- In `body.py`, the group center is computed with integer division:
  ```python
  g.cy = (19 + 19 + 20 + 20) // 4  # = 19 (rounds toward Side A!)
  ```
- After `G5` and `G11` are cleared once, they enter `g.state == 3` (respawning in 50 rounds). When a champion returns to farm a `state == 3` group, `body.py` (`farm_group`, lines 1218–1236) executes:
  ```python
  if g.state == 3:
      if g.ready > r + wait_respawn:
          return False
      ...
      if cheb(self.x, self.y, g.cx, g.cy) <= 3:
          return True
      self.go_group(g, 2)
      return True
  ```
- Look at where `cheb(self.x, self.y, g.cx, g.cy) <= 3` stops for each side relative to `g.cy = 19`:
  - **Side B (approaching from `y = 39` downward):** `y = 19 + 3 = 22`. Tile `y = 22` is **INSIDE the Side B bush curtain (`y = 22`)**! Standing inside the bush, Side B has unobstructed vision of `y = 19..20`, sees `G5` and `G11` the exact round they respawn (`update_groups` checks `_bc.vision() & self.camp_mask`), clears them repeatedly, buys weapon upgrades, and scales up to clear the `6016`-threshold camps (`946` gems).
  - **Side A (approaching from `y = 0` upward):** `y = 19 - 3 = 16`. Tile `y = 16` is **1 tile OUTSIDE the Side A bush curtain (`y = 17`)**! Because bushes block line-of-sight from outside, a Side A champion parked at `y = 16` **cannot see `y = 19..20` through the bush at `y = 17`**!
- Consequently, on Side A:
  1. `Vendetta` and `Varg` stop at `y = 16`, blind to `y = 19..20`.
  2. `G5` and `G11` respawn on schedule, but because `y = 19..20` is never in `_bc.vision()`, `g.state` remains `3` forever in `body.py`'s memory.
  3. After 25 turns of staring at the bush (`n > 25`), `farm_group` sets `g.ready = r + 30` and returns `False`.
  4. On the next turn, `g_farm.py`'s `pick()` re-selects the same group because `pick()` allows `g.ready <= r + d + 6` while `farm_group()` immediately rejects `g.ready > r + 4` (`wait_respawn = 4`), freezing the champion until `r >= g.ready - 4`, at which point it walks back to `y = 16` for another 25 blind turns—looping for the entire 2000-round game!

#### Step 3: Damaged Champion Stall (`g is None` in `g_farm.py`)
- Meanwhile, after `Ryth` clears `G11` once on Side A, `Ryth` is left at `hp = 600 / 1600` (`hpf = 0.375`), `gems = 16`, `gold = 120`.
- At `hp = 600`, `b.hp * 2.0 = 1200 < 1960`, so `pick(b)` returns `None` (no camp is safe to clear at 600 HP).
- However, `g_survive.py` only recalls to heal when `b.hpf < 0.35` (`0.375 >= 0.35`) and only recalls to shop when `b.gems == 0 and b.gold >= 150`.
- When `g is None`, `g_farm.py` executes `b.step_toward(b.W // 2, b.H // 2, 3)`, marching `Ryth` into a dead-end corridor wall near `(25, 20)` where it stands at 37.5% HP for the rest of the match!

---

### 4.2 `00ambush` Side A (353–428 Loss to `starter-python`)

1. **Camp Structure on `00ambush` (`100×100`, 12 camp groups):**
   - Groups `0, 1, 6, 7, 10, 11` are **BIG** camps (`hp = 4110..5160, str = 80..120, gems = 33..51, need_for = 3`).
   - Groups `2, 3, 4, 5` are **0-gem gold clusters** (`gems = 0, gold = 60..80, need_for = 1`).
   - Groups `8, 9` (`gems = 14`) are completely walled off (`home_field.get(rep) = 65535`).
2. **How `MapInfo.sparse = True` Starves the Main Squad:**
   - Because `self.area = 10000 >= 3200`, `MapInfo.sparse` is `True`.
   - `brain.py` assigns 4 of the 6 champions (`rank 2, 3, 4, 5`) to `self.roamers`, leaving only `rank 0` (Marcella) and `rank 1` (Ryth) in the main pack (`active = min(alive - healing, 6 - 4) = 2`).
   - Roamers only target camps with `need_for(g) <= crew` (`1..2`), so all 4 roamers spend the entire match cycling between the 0-gem gold clusters (`G2..G5`), banking **0 gems**.
   - Meanwhile, in `Brain.choose()`, every reachable gem-bearing camp on `00ambush` is `big = True` with `need_for(g) = 3 > active = 2`! The leader (`rank 0`) is forbidden from targeting any gem camp until she accumulates enough items from gold clusters around round 850 to reduce her personal `need_for(g)` from 3 to 2—wasting nearly half the game.
3. **The Fix:**
   - Excluding `area >= 9000` from `self.sparse` in `mapinfo.py` (`and self.area < 9000`) keeps all 6 champions together as a single pack on `00ambush` (`active = 6 >= 3`), allowing `deimos` to immediately clear the big gem camps from round 1 while leaving `80×80` `01starvation` (`area = 6400`) completely untouched.

---

## 5. Exact Surgical Changes Applied to `src/`

Only 4 files (`picker.py`, `mapinfo.py`, `body.py`, `g_farm.py`) are modified relative to the frozen baseline:

```diff
--- a/src/picker.py
+++ b/src/picker.py
@@ -20,6 +20,8 @@
     (41, 30, 36, 22, 1, 24): SRC,        # eight        1011:11, 1005:161   +1844
     (80, 80, 664, 58, 2, 78): SRC,       # starvation   608:368, 656:116    +780
     (100, 100, 540, 1832, 4, 132): SRC,  # ambush       489:275, 690:341    +563
+    (90, 30, 0, 76, 18, 144): SRC,       # lanes        1002:431, 1004:941  +634
+    (30, 30, 0, 36, 2, 36): SRC,         # elkring      1001:704, 1001:814  +484
 }
 
 _choice = None
--- a/src/mapinfo.py
+++ b/src/mapinfo.py
@@ -51,7 +51,7 @@
 
         # phobos: sparse maps get split farming, gem-poor maps carry discipline.
         # UPGRADE: walkable area and walking distances instead of raw area (walls, holes).
-        self.sparse = config.SPLIT and self.area >= config.SPLIT_AREA and self.area >= config.SPLIT_SPARSE * max(1, n)
+        self.sparse = config.SPLIT and self.area >= config.SPLIT_AREA and self.area >= config.SPLIT_SPARSE * max(1, n) and self.area < 9000
         self.gem_total = sum(g.gem_value() for g in self.groups)
         self.poor = self.gem_total < config.POOR_GEMS
 
--- a/src/body.py
+++ b/src/body.py
@@ -1216,9 +1216,10 @@
         self.mem[("air", g.i)] = 0
         wk = ("wait", g.i)
         if g.state == 3:
-            if g.ready > r + wait_respawn:
+            if g.ready > r + fd + wait_respawn + 2:
                 return False
-            n = self.mem.get(wk, 0) + 1
+            seen = bool((_bc.vision() & g.mask).count())
+            n = self.mem.get(wk, 0) + 1 if seen else 0
             self.mem[wk] = n
             if n > 25:
                 # the respawn does not come (a spawn tile is blocked): look elsewhere for a while
@@ -1230,9 +1231,9 @@
                 if not self.step_to(self.ring_tiles(g, 1)):
                     return False
                 return True
-            if cheb(self.x, self.y, g.cx, g.cy) <= 3:
+            if cheb(self.x, self.y, g.cx, g.cy) <= 3 and seen:
                 return True
-            self.go_group(g, 2)
+            self.go_group(g, 1 if cheb(self.x, self.y, g.cx, g.cy) <= 3 else 2)
             return True
         targets = self.group_targets(g)
         if targets:
--- a/src/g_farm.py
+++ b/src/g_farm.py
@@ -35,6 +35,8 @@
         b.mem["br_t"] = b.round
         b.claim(g)
     if g is None:
+        if not b.at_spawn and (b.hpf < 0.85 or b.gold >= 60):
+            return b.recall() or b.go_home()
         return b.step_toward(b.W // 2, b.H // 2, 3)
     if not b.farm_group(g, kite=False):
         g2 = pick(b)
```

---

## 6. Full 80-Game Verification: Surgical Bot (`inspector`) vs Frozen Baseline (`baseline`)

Tested across all 40 maps × Sides A & B (80 games) in `/workspace/battlecode/arena/h2h_inspector_baseline`:
- **Overall Record:** **49 Wins – 31 Losses (61.3% Win Rate), 0 Crashes**
- **Total Gems:** **`53,851` (Surgical V2) vs `47,142` (Frozen Baseline) — `+6,709` net gem differential** (compared to `18–60` and `−28,636` gems from `STRATEGY.md`).
- **2–0 Map Sweeps (11 maps swept 2–0 vs 2 maps lost 0–2):**
  - `01corridors`: **2–0** (`1000:16` Side A, `1038:16` Side B, **`+2,006` gems**)
  - `00monolith`: **2–0** (`1017:637` Side A, `1003:364` Side B, **`+1,019` gems**)
  - `00lanes`: **2–0** (`961:357` Side A, `1015:630` Side B, **`+989` gems**)
  - `00corners`: **2–0** (`1024:703` Side A, `1005:365` Side B, **`+961` gems**)
  - `00rows`: **2–0** (`696:321` Side A, `736:340` Side B, **`+771` gems**)
  - `01islands`: **2–0** (`1016:612` Side A, `946:799` Side B, **`+551` gems**)
  - `00elkring`: **2–0** (`1001:704` Side A, `1001:814` Side B, **`+484` gems**)
  - `00ambush`: **2–0** (`673:353` Side A, `561:452` Side B, **`+429` gems**)
  - `00pilgrimage`: **2–0** (`561:246` Side A, `451:398` Side B, **`+368` gems**)
  - `01the-farm`: **2–0** (`89:65` Side A, `1010:749` Side B, **`+285` gems**)
  - `01shortcut`: **2–0** (`711:681` Side A, `660:428` Side B, **`+262` gems**)
