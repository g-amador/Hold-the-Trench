"""
Global configuration values.
"""

# ------------------------
# GAME INFO
# ------------------------

GAME_TITLE = "Hold the Trench"
VERSION = "0.1.0"

# ------------------------
# DISPLAY
# ------------------------

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

FPS = 60

FULLSCREEN = False


# ------------------------
# WORLD
# ------------------------

TILE_SIZE = 32

MAP_WIDTH = 40
MAP_HEIGHT = 22


# ------------------------
# PHASE DURATIONS
# ------------------------

PREP_TIME_SECONDS = 90


# ------------------------
# PLAYER ECONOMY
# ------------------------

STARTING_SUPPLIES = 100

SUPPLIES_PER_WAVE = 50


# ------------------------
# BUILDING COSTS
# ------------------------

TRENCH_COST = 5

MG_NEST_COST = 20

ARTILLERY_COST = 50

BUNKER_COST = 40


# ------------------------
# GAMEPLAY
# ------------------------

MIN_WAVES = 5
MAX_WAVES = 12


# ------------------------
# WEATHER
# ------------------------

WEATHER_TYPES = [
    "clear",
    "rain",
    "fog"
]


# ------------------------
# COLORS
# ------------------------

WHITE = (255, 255, 255)

BLACK = (0, 0, 0)

RED = (200, 50, 50)

GREEN = (50, 200, 50)

YELLOW = (240, 220, 70)

MUD = (90, 70, 50)

CRATER = (70, 60, 60)

FOREST = (50, 90, 50)


# ------------------------
# WAVE GENERATION
# ------------------------

MIN_WAVES = 5
MAX_WAVES = 12