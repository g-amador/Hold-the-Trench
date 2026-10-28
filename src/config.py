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
# per-axis stretch. With the doubled 80x46 map (world 2560x1472) and
# this 40px bar the zoom is exactly 728/1472 ≈ 0.4946, so every tile
# renders as a ~15.8px SQUARE and the leftover horizontal space is
# drawn as dark side bands. Editing the bar, the window, TILE_SIZE,
# or the map is fine — the one rule: keep the single-factor zoom.
HUD_BAR_HEIGHT = 40

# ---------------- View zoom (+ / - keys) ----------------
# Exactly TWO views (per user; no in-between zoom steps):
#   VIEW_FULL  = full zoom-out: whole battlefield below the HUD bar
#     (the uniform-zoom render).
#   VIEW_CLOSE = zoomed in: the player rides CENTER of a screen-wide
#     window CLOSE_VIEW_TILES tiles across ("10 tiles back and
#     forth"), scaled uniformly so it OCCUPIES the full visible
#     strip — no side bands (scale 4x at 1280x768: one tile spans
#     128 screen px, ~5.7 tiles fit vertically, still within the
#     "at most 5 in each direction" cap).
# '+' zooms IN (CLOSE), '-' zooms OUT (FULL); both keys work live and
# paused, and the HUD label after the pause info shows the current
# view. Each new battle starts at VIEW_FULL.
VIEW_FULL = "FULL"
VIEW_CLOSE = "CLOSE"
CLOSE_VIEW_TILES = 10

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

# Starting balance, tuned to let the player afford one building
# or a few partial payments early on.
START_GOLD = 500

# ---------------- Build costs (gold) ----------------
# Player buildings are paid in partial payments: AssaultPhase tracks
# how much was already paid per spot in tilemap.paid_amount and
# constructs the building only when the full cost is covered.
# Enemy variants cost 0 because they are placed free from map markers.
BUILD_COSTS = {
    "mg": 0,
    "bunker": 0,
    "barracks": 0,
    "artillery": 0,
    "air_field": 0,
    "tank_factory": 0,

    "enemy_mg": 0,
    "enemy_bunker": 0,
    "enemy_barracks": 0,
    "enemy_artillery": 0,
    "enemy_air_field": 0,
    "enemy_tank_factory": 0,
}

# ---------------- Combat ----------------
# Max bullet travel distance in px. Every engagement range must stay
# below it (player 300, infantry 200, MG nest 220, artillery 400); the
# +100 margin over artillery guarantees a max-range shell still lands
# on its target before the bullet expires. Pass: bullets vanish after
# flying this far instead of streaking across the whole map.
BULLET_RANGE_PX = 500

# ---------------- Armor (tank factory units) ----------------
# User spec: factories produce armored vehicles; tanks have 100 hp,
# the British machine-gun car 80. ONLY artillery splash and other
# tanks' shots can damage armor (infantry/MG/car fire can't); tanks
# hurt infantry AND other tanks, cars hurt infantry only.
TANK_HP = 100
CAR_HP = 80

# Advance speeds (px/s) toward the enemy base / enemy bunker; the
# car is faster (it is a light vehicle), tanks crawl.
TANK_SPEED = 30
CAR_SPEED = 60

# Production cadence: 1 tank per 3 infantry created (user rule). The
# infantry timeline is one deployment every 5 s (Barracks), so a
# factory rolls out a vehicle every 3 x 5 s.
FACTORY_UNIT_INTERVAL = 15.0

# On-board machine guns ("shoot as machine guns"): the tank's gun
# matches the MG-nest range; damage is bigger per hit, fired slower.
TANK_MG_RANGE = 220
TANK_MG_DAMAGE = 20
TANK_MG_FIRE_RATE = 0.6

# The British car is literally an MG nest on wheels: MG-nest stats.
CAR_MG_RANGE = 220
CAR_MG_DAMAGE = 8
CAR_MG_FIRE_RATE = 0.2

# ---------------- Building footprints (tiles) ----------------
# How many tiles each building kind covers: the drawn sprite/block, the
# build-spot outlines, and collision all scale with these. The anchor
# (marker) tile is the TOP-LEFT of the footprint; it extends right and
# down. Spot kinds can be prefixed ("enemy_mg"): strip the prefix and
# look up the kind.
# USER SIZES: MG 4x4, artillery 4x2, barracks 4x4, bunker 6x6,
# statics (air field / tank factory) 7x7.
BUILD_FOOTPRINTS = {
    "mg": (4, 4),
    # Barracks 4x4, bunker 6x6; artillery 4x2 — wide emplacement
    # (4 across, 2 deep), anchored at its marker's top-left.
    "barracks": (4, 4),
    "artillery": (4, 2),
    "bunker": (6, 6),
    # Static markers placed FREE at battle start (F = air field,
    # K = tank factory): 7x7 per the user; no cost, no firing yet.
    "air_field": (7, 7),
    "tank_factory": (7, 7),
}
