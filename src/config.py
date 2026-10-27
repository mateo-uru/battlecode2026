"""Every tunable of fade in one place.

The bot reads only names from this module, so a new doctrine, a different phase trigger or a new
build is a data change here. Nothing in this file may depend on a map name or an opponent.
"""

# ChampionDraft ids (draft phase).
RYTH, VESPER, VENDETTA, CASSI_ISSAC, STELLAR, PRISM, MARCELLA, WILLOW, REN, VARG, TAVI, HEART = range(12)

# ChampionType ids (in game; Cassi & Issac are two bodies, so the numbering differs).
T_RYTH, T_VESPER, T_VENDETTA, T_CASSI, T_ISSAC, T_STELLAR, T_PRISM, T_MARCELLA, T_WILLOW, T_REN, T_VARG, \
    T_TAVI, T_HEART = range(13)

# --- Leader -----------------------------------------------------------------------------------
# The leader is the first pick: high health, stores the team's gems, heals itself early.
# Picks are only unique within a team, so the first entry is always available.
LEADER_DRAFT = (MARCELLA, RYTH, VARG, HEART)
# In game the leader is the ally whose type comes first here (ties and others: lowest handle).
LEADER_TYPES = (T_MARCELLA, T_RYTH, T_VARG, T_HEART, T_REN, T_ISSAC, T_VENDETTA)

# --- Doctrines ----------------------------------------------------------------------------------
# `picks` follows the leader. Built from nameless' two orders (grouped maps: Varg, Cassi & Issac,
# Ryth, Stellar, Ren, Tavi; sparse maps: Tavi, Vendetta, Vesper, Varg), reordered for the doctrine and
# with the new Heart of Ruin added. Draft A/B on this pool: "stun" beat "fighters" 73:58 wins.
# engage: local strength ratio needed to start a fight with champions (lower = braver).
# UPGRADE: counter-pick from cambc.draft.current_draft(Team.ENEMY) (e.g. Marcella vs stun teams).
DOCTRINES = {
    "stun": dict(
        picks=(RYTH, TAVI, HEART, CASSI_ISSAC, REN, VARG, PRISM, STELLAR, VESPER, VENDETTA, WILLOW, MARCELLA),
        engage=1.25, hunt_engage=1.0, radius=3, stun_chain=True),
    "fighters": dict(
        picks=(VARG, VENDETTA, HEART, VESPER, CASSI_ISSAC, TAVI, RYTH, REN, STELLAR, PRISM, WILLOW, MARCELLA),
        engage=1.05, hunt_engage=0.85, radius=4, stun_chain=False),
}
DOCTRINE_FORCE = None       # name of a doctrine to use on every map (tests); None = map rule
# Draft the fighters when the spawns are closer than this (walking). Ladder v19: fighters on 4 maps,
# 3 of them bad (rushbait_v2, elk_arena, reverse_spiral), swirl good. deimos sets 0 (stun everywhere).
FIGHTERS_SPAWN_DIST = 0 
# Draft a healer as last pick when the team has at least this many picks (None disables).
SUPPORT_PICK = WILLOW
SUPPORT_MIN_TEAM = 99   # off by default; Willow is weak alone. Set to 5 to try "leader + healer".

# --- Phases -------------------------------------------------------------------------------------
HUNT_ROUND = 1000           # switch to HUNT at this round ...
HUNT_ENEMY_GEMS = 700       # ... or once the enemy tributed this many ...
HUNT_ENEMY_LEAD = 200       # ... or once the enemy leads by this many.
PREY_RADIUS = 12            # HUNT: chase reported isolated enemies only this close (far chases cost farming)

# --- Group --------------------------------------------------------------------------------------
LEADER_WAIT_TURNS = 6       # leader waits at most this long for stragglers before moving on
ANCHOR_STALE = 4            # rounds after which a broadcast anchor is ignored
REGROUP_FRACTION = 0.5      # if at least this share of the team is healing, the rest regroup at spawn
SPAWN_CROWDED = 2           # ... unless this many enemies were seen next to our spawn
DETOUR_CLUSTER = 3          # followers may leave the radius by this much to hit a free cluster
WORK_EXTRA = 4              # followers farm their own camps within radius + this of the anchor ...
WORK_MAP_DIV = 30           # ... plus (width + height) / this ...
WORK_MAP_MAX = 6            # ... at most this much
REGION_SHARE = 0.4          # leader adds this share of nearby camps' value to a target (farming regions)
SUB_MAX_WALK = 8            # followers only take own camps within this walking distance ...
SUB_WALK_MAP_DIV = 999      # ... plus (width + height) / this (big sparse maps)
LEASH_SLACK = 8             # a follower working its own camp may drift this far beyond the work radius
HANDOFF = 3                 # a follower captures itself if the leader is further than this from the camp

# --- Split farming on sparse maps (phobos) ----------------------------------------------------------
# Ladder evidence (v19, 625 ranked games): on big sparse maps the winners farm with ~4 champions ~20 tiles
# apart and tribute twice as often; fade walked as one group (leader collected 71 % of the gems).
SPLIT = True                # switch for A/B tests
SPLIT_AREA = 2400           # a map is sparse with at least this many tiles ...
SPLIT_SPARSE = 120          # ... and at least this many tiles per camp group
SPLIT_BUDDY = True          # the leader keeps the next champion in LEADER_TYPES order as its group
ROAM_PAIRS = True           # two roamers share a region and take camps needing two champions together
ROAM_PAIR_DIST = 8          # ... when the partner is this close
ROAM_BANK_MIN = 12          # roamers bank from this bag ...
ROAM_BANK_PER_TILE = 0.4    # ... plus this per tile to the altar
ROAM_HELP = 15              # roamers this close join the leader holding at a big camp
ROAM_ANY = 25               # region dry: any feasible camp this close
SPLIT_DEATHS = 4            # this many roamer deaths within SPLIT_DEATH_WINDOW rounds ...
SPLIT_DEATH_WINDOW = 150
SPLIT_PAUSE = 300           # ... send everybody back to the group for this long
KMEANS_ITERATIONS = 8

# --- Gem-poor maps (phobos) -------------------------------------------------------------------------
# elk_arena: 72 gems of camps on the whole map, the enemy's gems come from our carriers (58 deaths/game).
POOR_GEMS = 150             # total camp gem value below this: gem-poor map
POOR_BANK = 8               # bank from this bag when an altar is within POOR_BANK_DIST
POOR_BANK_DIST = 20
POOR_CARRY = 10             # while carrying this many gems ...
POOR_ENGAGE = 1.5           # ... start fights only with this times the usual strength ratio

# --- Health -------------------------------------------------------------------------------------
HEAL_AT = 0.35              # retreat below this health share
LEADER_HEAL_AT = 0.5        # the leader heals earlier while it carries the gems ...
LEADER_CAREFUL_GEMS = 15    # ... from this bag size on
HEAL_UNTIL = 0.95           # stay on spawn until this share
# UPGRADE: explicit tank rotation on big camps (second bruiser steps in before the tank leaves).

# --- Gems ---------------------------------------------------------------------------------------
BANK_MIN = 20               # bag that is always worth a trip when the altar is close
BANK_PER_TILE = 0.6         # extra gems required per tile of distance to the altar
BANK_MAX = 60               # never walk around with more than this
BANK_FOLLOWER = 20          # followers bank alone from this bag on
ESCORT_BAG = 40             # the group escorts a leader banking at least this many gems
SPLIT_REWARD = 25           # rewards this large are split among all members present

# --- Camps --------------------------------------------------------------------------------------
BIG_CAMPS = (1, 4, 5)       # elk, monolith, golem: tank-first protocol ...
BIG_STRENGTH = 60           # ... and any group hitting this hard (wolf packs of 3+)
# Monsters hit the nearest champion, so a big camp is survived by tanks taking turns (each retreats with
# about half its health). Champions needed n: strength * hp / (n * dps) <= n * maxhp * BIG_USABLE.
BIG_USABLE = 0.5
BIG_HOLD = 6                # the leader waits this far from a big camp until enough champions are present
BIG_WAIT_TURNS = 12         # ... at most this long, then the camp is skipped for a while
ESCAPE_TURNS = 4            # step out of reach when visible awake camps would kill us this fast ...
ESCAPE_HOLD = 8             # ... and stay out this long (the next champion in line takes the hits)
GIANT_RADIUS = 6            # camp groups this close to a monolith/golem group ...
GIANT_NEIGHBOUR = 1.0       # ... are worth this much less
GUARD_BONUS = 3.0           # value multiplier for camps that block every altar approach
GOLEM_HUNT_BONUS = 1.6      # value multiplier for golems/elks in HUNT
MONOLITH_MIN_DPS = 250      # group damage per turn needed before a monolith is considered
GOLD_WEIGHT = 0.45          # value of one gold relative to one gem (scaled by 3 below)
STUCK_TURNS = 30            # give up a target after this many rounds without progress
BLIND_TURNS = 4             # ... or after this many rounds next to it without seeing a camp
CLAIM_STICKY = 1.25         # bonus for keeping the current target
GROUP_DAMAGE = 0.75         # share of camp damage a group really takes (stuns, kills during the fight)
MAX_DAMAGE_SHARE = 0.6      # skip camps whose expected damage exceeds this share of the team's health

# --- Safety features (switches for A/B tests) -------------------------------------------------
AVOID_BYSTANDERS = True     # area effects / Varg splash never hit sleeping camps outside the target
HAZARD_FLEE = True          # step out of reach of awake monoliths/golems that are not our fight
LONE_HOME = True            # acting leader with no safe target walks home instead of idling

# --- Shop ---------------------------------------------------------------------------------------
# Item names per role; each shard is bought until its emblem completes (5 shards), then the next.
BUILDS = {
    "leader": ("JUNGLE_SHARD_OF_HEALTH", "DURABILITY_SHARD_OF_HEALTH", "POWER_SHARD_OF_STRENGTH",
               "HOME_SHARD_OF_HEALTH", "POWER_SHARD_OF_STRENGTH"),
    "bruiser": ("MONSTER_SHARD_OF_STRENGTH", "DURABILITY_SHARD_OF_HEALTH", "POWER_SHARD_OF_STRENGTH",
                "POWER_SHARD_OF_HEALTH"),
    "striker": ("MONSTER_SHARD_OF_STRENGTH", "POWER_SHARD_OF_STRENGTH", "DURABILITY_SHARD_OF_HEALTH",
                "POWER_SHARD_OF_STRENGTH"),
    "caster": ("POWER_SHARD_OF_FOCUS", "MONSTER_SHARD_OF_FOCUS", "DURABILITY_SHARD_OF_HEALTH",
               "POWER_SHARD_OF_FOCUS"),
    "marksman": ("TREASURE_SHARD_OF_STRENGTH", "MONSTER_SHARD_OF_STRENGTH", "POWER_SHARD_OF_STRENGTH",
                 "DURABILITY_SHARD_OF_HEALTH"),
    "support": ("POWER_SHARD_OF_FOCUS", "DURABILITY_SHARD_OF_HEALTH", "POWER_SHARD_OF_FOCUS"),
}
ROLE_OF_TYPE = {
    T_MARCELLA: "bruiser", T_RYTH: "bruiser", T_VARG: "bruiser", T_HEART: "bruiser",
    T_VENDETTA: "striker", T_ISSAC: "striker", T_REN: "striker",
    T_STELLAR: "caster", T_PRISM: "caster", T_CASSI: "caster", T_TAVI: "caster",
    T_VESPER: "marksman", T_WILLOW: "support",
}
LOCK_AFTER_SHARDS = 5       # buy an altar lock once this many shards are owned
SHOP_TRIP_GOLD = 300        # go home to shop with this much gold when nothing urgent happens ...
SHOP_TRIP_PER_TILE = 5      # ... plus this much per tile of walking distance from spawn
SHOP_TRIP_HURT = 0.65       # below this health share ...
SHOP_TRIP_HURT_GOLD = 150   # ... this much gold is enough (heal and shop in one trip)
SHOP_EARLY_SHARDS = 0       # the same low bar until this many shards are owned (0 = off)

# --- Debug ------------------------------------------------------------------------------------
STATS = False               # print turns per decision branch every 500 rounds
TRACE = 0                  # print one status line per champion every TRACE rounds (0 = off)

# --- Fuel ---------------------------------------------------------------------------------------
RESERVE = 300_000           # yield when less fuel than this is left (Python gets 2.5M per turn)
