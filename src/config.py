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
# renderer reserves this strip: the world is drawn scaled below it, so
# the whole battlefield stays visible and no unit can be hidden by it.
# SQUARE-TILE LOCK: the static map's row count must satisfy
# rows * TILE_SIZE == SCREEN_HEIGHT - HUD_BAR_HEIGHT
# (768 - 32 = 736 = 23 rows) so the battle renderer's world->screen
# scale is exactly 1:1 and tiles stay true 32px squares (the old 40px
# bar squashed rows into vertical rectangles). Keeping this equation
# true is part of the render-layout contract; update map + bar together.
HUD_BAR_HEIGHT = 32

# ---------------- Colors (RGB) ----------------
# Palette shared by tiles, HUD, texts, pickups, and block-mode rendering.
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (90, 60, 40)     # trench terrain
GREY = (150, 150, 150)   # neutral buildings (e.g. artillery block)
GOLD = (255, 215, 0)     # gold pickups
RED = (200, 50, 50)      # enemy side (units, bullets, block fallback)
BLUE = (0, 200, 255)     # ally side (units, block fallback)

# Starting balance, tuned to let the player afford one building
# or a few partial payments early on.
START_GOLD = 500

# ---------------- Build costs (gold) ----------------
# Player buildings are paid in partial payments: AssaultPhase tracks
# how much was already paid per spot in tilemap.paid_amount and
# constructs the building only when the full cost is covered.
# Enemy variants cost 0 because they are placed free from map markers.
BUILD_COSTS = {
    "mg": 20,
    "bunker": 40,
    "barracks": 60,
    "artillery": 100,

    "enemy_mg": 0,
    "enemy_bunker": 0,
    "enemy_barracks": 0,
    "enemy_artillery": 0,
}

# ---------------- Combat ----------------
# Max bullet travel distance in px. Every engagement range must stay
# below it (player 300, infantry 200, MG nest 220, artillery 400); the
# +100 margin over artillery guarantees a max-range shell still lands
# on its target before the bullet expires. Pass: bullets vanish after
# flying this far instead of streaking across the whole map.
BULLET_RANGE_PX = 500

# ---------------- Building footprints (tiles) ----------------
# How many tiles each building kind covers: the drawn sprite/block, the
# build-spot outlines, and collision all scale with these. The anchor
# (marker) tile is the TOP-LEFT of the footprint; it extends right and
# down. Spot kinds can be prefixed ("enemy_mg"): strip the prefix and
# look up the kind.
# TEST STEP: only the MG is multi-tile (2x2) for now; the remaining
# kinds stay 1x1 until that pass is validated, then become 3x3 per the
# user's target layout.
BUILD_FOOTPRINTS = {
    "mg": (2, 2),
    # Flip to (3, 3) together when the user signs off on the MG pass:
    "barracks": (1, 1),
    "artillery": (1, 1),
    "bunker": (1, 1),
}
