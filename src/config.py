"""
Global configuration: screen size, tile size, FPS, colors.
"""

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

# Tile size (pixels)
TILE_SIZE = 32

# Frames per second
FPS = 60

# Colors (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (90, 60, 40)
GREY = (150, 150, 150)
GOLD = (255, 215, 0)
RED = (200, 50, 50)
BLUE = (0, 200, 255)

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
