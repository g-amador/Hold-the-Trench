"""
Global configuration: screen size, tile size, FPS, colors, build costs.

This file is the project's single source of truth for shared tunables.
Other modules import constants from here — `systems/economy_system.py`
re-exports BUILD_COSTS only for import compatibility.
"""

# Window size in pixels. SCREEN_WIDTH also caps the camera scroll:
# the camera never scrolls past (tilemap.width * TILE_SIZE) - it.
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 768

# Tile size in pixels. World coordinates are always multiples of this
# for buildings; units use free float positions but tile-based collision.
TILE_SIZE = 32

# Frame rate cap. clock.tick() returns milliseconds consumed for the
# last frame, which is the `dt` unit used across the whole project.
FPS = 60

# Height of the HUD status bar at the top of the screen. The battle
# renderer reserves this strip: the world is drawn uniformly zoomed
# below it, so the whole battlefield stays visible and no unit can be
# hidden by it.
# UNIFORM-ZOOM LOCK (square tiles on ANY map): render() scales the
# whole map by ONE factor, min(fit_to_width, fit_to_height) — never a
# per-axis stretch. With the current 78x46 map (world 2496x1472) and
# this 40px bar the zoom is capped at 728/1472 ≈ 0.4946 by the
# height, so every tile renders as a ~15.8px SQUARE and the leftover
# horizontal space is drawn as dark side bands. Editing the bar, the
# window, TILE_SIZE, or the map is fine — the one rule: keep the
# single-factor zoom.
HUD_BAR_HEIGHT = 40

# ---------------- View zoom (+ / - keys) ----------------
# Exactly TWO views (per user; no in-between zoom steps):
#   VIEW_FULL  = full zoom-out: whole battlefield below the HUD bar
#     (the uniform-zoom render).
#   VIEW_CLOSE = zoomed in: the player rides CENTER of a screen-wide
#     window CLOSE_VIEW_TILES tiles across, scaled uniformly so it
#     OCCUPIES the full visible strip — no side bands (scale ≈3.1x at
#     1280x768 with 13 tiles: one tile spans ~98 screen px, ~7.4
#     tiles fit vertically). User tweak (was 10/4x): a WEAKER zoom
#     puts more native pixels under every screen pixel, so the 4K
#     ground reads sharper — the trade-off is the wider window now
#     spans ±6.5 tiles (the original design cap was "at most ~5 in
#     each direction", satisfied at 10).
# '+' zooms IN (CLOSE), '-' zooms OUT (FULL); both keys work live and
# paused, and the HUD label after the pause info shows the current
# view. Each new battle starts at VIEW_FULL.
VIEW_FULL = "FULL"
VIEW_CLOSE = "CLOSE"
CLOSE_VIEW_TILES = 13

# ---------------- Colors (RGB) ----------------
# Palette shared by tiles, HUD, texts, pickups, and block-mode rendering.
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (90, 60, 40)     # trench terrain
GREY = (150, 150, 150)   # neutral buildings (e.g. artillery block)
GOLD = (255, 215, 0)     # gold pickups
RED = (200, 50, 50)      # enemy side (units, bullets, block fallback)
BLUE = (0, 200, 255)     # ally side (units, block fallback)
YELLOW = (255, 255, 0)   # artillery muzzle flash (shell-flight marker)
PINK = (255, 20, 147)    # french female tank block body (both sides)

# Starting balance, tuned to let the player afford one building
# or a few partial payments early on.
START_GOLD = 1000

# Gold collect radius: the player picks up a coin by walking this
# close to it (radial distance test, friendlier than a collision box).
GOLD_PICKUP_RADIUS_PX = 64

# COIN MAGNETISM (user request: "like the player is a magnet attracting
# the coins"): a coin inside this radius slides TOWARD the player
# instead of waiting to be stepped over. The pull speed is px/s toward
# the player's position; GOLD_PICKUP_RADIUS_PX still triggers the
# payout, so the magnet radius must stay larger than it.
GOLD_MAGNET_RADIUS_PX = 80
GOLD_MAGNET_SPEED_PX_S = 260

# ---------------- Build costs (gold) ----------------
# Player buildings are paid in partial payments: AssaultPhase tracks
# how much was already paid per spot in tilemap.paid_amount and
# constructs the building only when the full cost is covered.
# Enemy variants cost 0 because they are placed free from map markers.
BUILD_COSTS = {
    "mg": 30,
    "bunker": 0,
    "barracks": 60,
    "artillery": 80,
    "air_field": 200,
    "tank_factory": 150,

    "enemy_mg": 0, #30
    "enemy_bunker": 0,
    "enemy_barracks": 0, #60
    "enemy_artillery": 0, #80
    "enemy_air_field": 0, #200
    "enemy_tank_factory": 0, #150
}

# ---------------- Combat ----------------
# Max bullet travel distance in px. Every engagement range must stay
# below it (player 300, infantry 200, MG nest 220, artillery 400); the
# +100 margin over artillery guarantees a max-range shell still lands
# on its target before the bullet expires. Pass: bullets vanish after
# flying this far instead of streaking across the whole map.
BULLET_RANGE_PX = 500

# Bullet flight speed (px/s); EVERY bullet shares it (the shared
# straight-line projectile, independent of who fired it).
BULLET_SPEED_PX_S = 400

# ---------------- Unit stats (speed px/s, hp, gold drops) ----------------
# USER RULE: every unit's speed, hp/armor and gold_drop lives HERE (no
# more stat literals inside entity classes). The per-nation handicap
# multipliers live in systems/factions.py and scale hp at spawn and
# bullet damage at fire time.
INFANTRY_HP = 40
INFANTRY_SPEED = 120
INFANTRY_GOLD_DROP = 5

# Infantry ranged/siege gear:
INFANTRY_SHOOT_RANGE_PX = 200
ENEMY_SIEGE_DAMAGE = 10
ENEMY_SIEGE_COOLDOWN = 1.0
FRIENDLY_SIEGE_DAMAGE = 10
FRIENDLY_SIEGE_COOLDOWN = 1.0
# Per-shot rifle damage (matches Bullet's default 20).
INFANTRY_BULLET_DAMAGE = 20

# WWI-standard rifle firing rate per ARMY (rounds per minute), used by
# both sides' rifle infantry:
#   fr  -> France, Lebel Mle 1886/93:  43 rounds/min
#   ger -> Germany, Gewehr 98:         15 rounds/min
RIFLE_ROUNDS_PER_MIN = {
    "fr": 43,
    "ger": 15,
}
# Fallback cadence for a nation missing from the table (rounds/min).
RIFLE_ROUNDS_PER_MIN_DEFAULT = 20
# Seconds between rifle shots = 60 / rpm, derived from the table.
RIFLE_SHOOT_COOLDOWN_S = {
    nation: 60.0 / rpm for nation, rpm in RIFLE_ROUNDS_PER_MIN.items()
}
RIFLE_SHOOT_COOLDOWN_S_DEFAULT = 60.0 / RIFLE_ROUNDS_PER_MIN_DEFAULT


def rifle_shoot_cooldown(nation):
    """Seconds between rifle shots for a nation's standard rifle."""
    return RIFLE_SHOOT_COOLDOWN_S.get(nation, RIFLE_SHOOT_COOLDOWN_S_DEFAULT)

# Distance (in TILES, measured to the bunker's WALL — utils/geometry)
# at which rifle infantry stop charging and OPEN FIRE on an enemy
# bunker (user: "when the distance is 1 square apart from enemy bunker
# shoot it"). Beyond it they charge; at it they stand and shoot at the
# rifle rate.
INFANTRY_BUNKER_SHOOT_TILES = 1

# Shared soldier animation timing, identical across the player and
# BOTH, enemy/friendly spawning infantry (run-cycle frame length and
# the shot-blip beat after each shot — the second rest pose plays
# while the blip is up):
INFANTRY_ANIM_FRAME_S = 0.12
INFANTRY_AIM_POSE_S = 0.18

# ---------------- Planes (air field production) ----------------
# USER SPEC: air fields spawn planes at the SAME cadence as tank
# factories (FACTORY_UNIT_INTERVAL). Planes fly, ignore ground
# collision, machine-gun enemy PLANES in range (like infantry vs
# infantry), and drop bombs on whatever enemy ground target (tank,
# building) they are OVER — nearest first, proximity only.
PLANE_HP = 30
PLANE_SPEED = 140
PLANE_SIZE = (96, 96)      # world px box (art scales to it)
PLANE_MG_RANGE = 200
PLANE_MG_DAMAGE = 10
PLANE_MG_FIRE_RATE = 0.4   # generic fallback seconds (unlisted nation)
PLANE_BOMB_DAMAGE = 35
PLANE_BOMB_COOLDOWN = 3.0
# "Over them" = the plane's center is this close to the target's
# center when the bomb is released (proximity only, no aim).
PLANE_BOMB_TRIGGER_PX = 40

# WWI cyclic dogfight rates (user spec), keyed by NATION: France's
# Vickers c. 450-600 rounds/min; Germany's Spandau lMG 08/15 c.
# 400-500 rounds/min. Midpoints sit in the table (bands above are the
# historical spread); AirplaneUnit turns rpm into its fire interval
# (60 / rpm). A nation not listed keeps the generic rate above.
PLANE_MG_ROUNDS_PER_MIN = {
    "fr": 525,   # Vickers (450-600 rpm band)
    "ger": 450,  # Spandau lMG 08/15 (400-500 rpm band)
}

# Plane bomb visuals (user spec): the released bomb is a small YELLOW
# dot in flight; on impact a RED flash appears briefly and the damage
# lands THEN (on touch-down, not on release).
PLANE_BOMB_FLIGHT_TIME = 0.6    # seconds the bomb is airborne
PLANE_BOMB_IMPACT_TIME = 0.5    # seconds the red blast stays visible

# ---------------- Building hp ----------------
# Buildings are destructible now (tanks shell them, planes bomb them).
# Bunker keeps its objective stats from this table too; MG nests,
# barracks, artillery, and the free statics share the rest. Enemies
# look up the same numbers: key maps via the "enemy_" prefix strip.
BUILDING_HP = {
    "mg": 120,
    "barracks": 150,
    "artillery": 100,
    "bunker": 200,
    "air_field": 150,
    "tank_factory": 150,
}


def footprint_for(kind, faction):
    """(fw, fh) in tiles for a building kind — BOTH sides share the
    table (the faction argument is kept for caller compatibility)."""
    return BUILD_FOOTPRINTS.get(kind, (1, 1))


# ---------------- Armor (tank factory units) ----------------
# User spec: factories produce armored vehicles; tanks have 100 hp.
# ONLY artillery splash and other tanks' shots can damage armor
# (infantry/MG fire can't); tanks hurt infantry AND other tanks.
TANK_HP = 100

# Advance speed (px/s) toward the enemy base / enemy bunker; tanks
# crawl. MOVEMENT SCALES TO MAP SIZE (user rule): the value is
# referenced to TANK_SPEED_REF_TILES map tiles — a wider map speeds
# tanks up proportionally, a narrower one slows them down
# (effective speed = TANK_SPEED * map_width / reference_width).
TANK_SPEED = 30
TANK_SPEED_REF_TILES = 79   # current STATIC_MAP width in tiles

# BUILDING STAND-OFF (user rule): a tank NEVER touches a building
# border — allied or enemy, targeted or not. Every building carries
# this invisible clear-air margin around its footprint; the tank's
# movement steers around the inflated zone and any hull ending up
# inside one is pushed back out.
TANK_BUILDING_STANDOFF_PX = 24

# Production cadence: armored vehicles keep their OWN flat interval —
# one roll every 15 s per factory, INDEPENDENT of the barracks section
# batch size (the infantry rate scales with BARRACKS_SPAWN_BATCH; the
# armor rate deliberately does not, so armor stays a slower drumbeat
# than a batched infantry deployment).
# WWI-INSPIRED RATES PER NATION (user: "longer production times for
# German tanks"): the A7V was a far heavier build than the FT. A
# nation not in the table keeps the generic interval above.
FACTORY_UNIT_INTERVAL = 15.0
FACTORY_UNIT_INTERVALS_BY_NATION = {
    "fr": 15.0,
    "ger": 20.0,
}

# Barracks spawn clock (s between infantry deployments) — the anchor
# the factory cadence multiplies off (see comment above). Factories
# read FACTORY_UNIT_INTERVAL directly; the barracks roll their own.
BARRACKS_SPAWN_INTERVAL = 5.0

# Barracks deploy a WHOLE SECTION per deployment (user request: army
# sizes in line with WW I, at battle start). A 1914 rifle section was
# 8-12 men: the
# section is the smallest formation a game-scale battle can place,
# so each barracks deployment is one section of 12. Enemy barracks
# deploy their sections with the same size (they share Barracks).
# Raise/lower to taste: bigger batches = denser melee lines and a
# heavier per-frame AI load.
BARRACKS_SPAWN_BATCH = 12

# Section FORMATION (user request: "4-4-4 aspect"): men per RANK
# across the barracks front. With the 12-man batch this lays the
# section as the classic 4-4-4 — three files of four, a compact
# square block instead of one stacked column. The last rank is
# shorter when the batch is not an exact multiple.
BARRACKS_FORMATION_ACROSS = 4

# Artillery fire clock (s between barrages) and the base splash on
# impact (nation-scaled at fire time). The BARRAGE GEOMETRY pattern
# (columns/rows band) stays on the Artillery class — it is a
# user-tuned map pattern, not a unit stat.
ARTILLERY_FIRE_INTERVAL = 1.5
ARTILLERY_SPLASH_DAMAGE = 20
# LETHAL zone (user: "an artillery explosion red dot should kill any
# infantry in a 5x5 tile radius considering the dot at its center"):
# any standing INFANTRY whose body center lies within this MANY-TILES
# square centered on the red dot's center dies outright (span 3 -> a
# 5x5 tile box, +-1.5 tiles from the dot). Armor is NOT instakilled —
# it keeps taking its ARTILLERY_SPLASH_DAMAGE chip (rifles can't hurt
# it; only splash/shells can).
ARTILLERY_KILL_SPAN_TILES = 5

# GOD MODE (user: "In god mode I can't be killed, with god mode to off
# shells can kill the player"): True = the player is INVINCIBLE — no
# artillery blast can kill them. False = the player is mortal: enemy
# AND own shells that land with his body center inside the red dot's
# 5x5 tile kill zone kill him, and a dead player ends the battle in
# defeat (his command unit is gone).
GOD_MODE = True

# On-board machine guns ("shoot as machine guns"): the tank's gun
# matches the MG-nest range; damage is bigger per hit, fired slower.
TANK_MG_RANGE = 220
TANK_MG_DAMAGE = 20
TANK_MG_FIRE_RATE = 0.6

# Static MG nest building: range/damage/cadence.
MG_NEST_RANGE = 220
MG_NEST_DAMAGE = 8
MG_NEST_FIRE_RATE = 0.1
# Firing arc (user rule: "MG-nest fire only in 25 degrees up or down
# in the direction of enemies in range"): the gun faces the battlefield
# horizontally and may elevate/depress at most this angle, so targets
# STEEPLY above or below the muzzle (beyond the cone; e.g. on different
# trench lines) are outside the arc even inside the circular range.
MG_NEST_ELEVATION_DEG = 25

# ---------------- Building footprints (tiles) ----------------
# How many tiles each building kind covers: the drawn sprite/block, the
# build-spot outlines, and collision all scale with these. The anchor
# (marker) tile is the TOP-LEFT of the footprint; it extends right and
# down. Spot kinds can be prefixed ("enemy_mg"): strip the prefix and
# look up the kind.
# USER SIZES: MG 4x4, artillery 3x2, barracks 4x4, bunker 6x6,
# statics (air field / tank factory) 7x7.
BUILD_FOOTPRINTS = {
    "mg": (4, 4),
    # Barracks 4x4, bunker 6x6; artillery 3x2 — wide emplacement
    # (3 across, 2 deep), anchored at its marker's top-left.
    "barracks": (4, 4),
    "artillery": (3, 2),
    "bunker": (6, 6),
    # Static markers placed FREE at battle start (F = air field,
    # K = tank factory): 7x7 per the user; no cost, no firing yet.
    "air_field": (7, 7),
    "tank_factory": (7, 7),
}

# Bunker footprint by ART nation (user: wide cutaway bunkers sit in a
# squat 6x4 box): the wide cutaway art occupies the 6x4 footprint;
# any other nation (fr — and the missing-art fallback) keeps the
# BUILD_FOOTPRINTS["bunker"] default of 6x6. Read per INSTANCE by
# entities/bunker.py, so the rolled art file decides the collision
# size for that battle. Further nations rejoin by adding a row here
# when their (wider) art returns.
BUNKER_FOOTPRINTS_BY_NATION = {
    "ger": (6, 4),
}

# ------------------------------ AUDIO ------------------------------
# Music and themes live in assets/music, menu stings in assets/sounds
# (bare filenames here; systems/audio.py resolves the folders).

# Start-menu music: loops for as long as the faction select screen is
# showing (user: "while start menu is showing play Menu_Loop.wav").
MENU_MUSIC = "Menu_Loop.wav"

# Faction-select sting: ONE sound per press of a faction-selection
# key (menu W/S/1/2, end-screen S switch).
MENU_SELECT_SOUND = "menu_select.wav"

# War background noise (user: the FIRST shot of the battle — from any
# source: infantry, MG nest, tank, plane, artillery, either side —
# starts ONE of these, picked at random; lives in assets/sounds).
WAR_NOISE_SOUNDS = ("war_back_noise1.mp3", "war_back_noise2.mp3")

# National victory themes (user spec): the WINNER's anthem plays on
# the end screens — winning = the player's own rolled nation; losing =
# the enemy nation that held the map. Keyed by unit nation; unknown
# nations stay silent. The table carries the two playable nations;
# further countries rejoin by adding a row (music in assets/music).
NATION_VICTORY_THEMES = {
    "ger": "Victory_Theme_die-deutsche-kaisergarde-german.mp3",
    "fr": "Victory_Theme_la-marseillaise-french.mp3",
}
