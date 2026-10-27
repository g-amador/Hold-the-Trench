"""
Static battlefield loader.

STATIC_MAP is a list of short, readable ASCII rows.
Each row is a string representing tiles in that row.

You edit STATIC_MAP directly.

ASCII Legend (player):
# = trench path
M = MG
B = bunker
I = barracks
A = artillery
F = air field (free static, 4x4)
K = tank factory (free static, 4x4)
C = crater
T = tree
D = dead tree
W = wire
~ = mud
. = empty ground

ASCII Legend (enemy):
m = enemy MG
b = enemy bunker
i = enemy barracks
a = enemy artillery
"""

# Tile type constants: integers stored on Tile, converted to ASCII
# chars by Tile (game logic tests the chars, art tests the ints).
TILE_EMPTY     = 0
TILE_TRENCH    = 1
TILE_CRATER    = 2
TILE_WIRE      = 3
TILE_MUD       = 4

# ASCII -> tile type. Notably: trees, dead trees, and N collapse into
# empty ground; friendly AND enemy building markers both become their
# ground type here (the building itself is a build candidate, not a
# tile type).
ASCII_TO_TILE = {
    '.': TILE_EMPTY,
    'T': TILE_EMPTY,
    'D': TILE_EMPTY,

    '#': TILE_TRENCH,
    'M': TILE_TRENCH,
    'B': TILE_TRENCH,
    'I': TILE_TRENCH,
    'F': TILE_TRENCH,
    'K': TILE_TRENCH,
    
    'C': TILE_CRATER,
    'W': TILE_WIRE,
    '~': TILE_MUD,

    # Enemy
    'm': TILE_TRENCH,
    'b': TILE_TRENCH,
    'i': TILE_TRENCH
}

# ------------------------------------------------------------
# HUMAN‑READABLE STATIC MAP — YOU EDIT THIS
# ------------------------------------------------------------
# CURRENT STATE: an 80x46 tile canvas (EXACTLY DOUBLE the old 23x40
# old 23x40 screen-filling canvas: every marker sits at 2x its old
# coordinates). TILES STAY SQUARE through render()'s uniform zoom —
# the map no longer needs to divide the window exactly; AssaultPhase
# fits the whole map below the 40px HUD bar with ONE scale factor
# (~0.4946 -> ~15.8px screen squares, thin dark side bands). So you
# can grow or reshape the map freely; zoom adapts automatically.
# Consequences while it stays terrain-free: no enemy units spawn (no
# 'i' barracks markers), there is no enemy bunker ('b') so victory can
# never trigger, and no player bunker ('B') so defeat never triggers
# either — HUD shows Bunker HP 0. '|' separators restore a boundary.
# M = MG (footprint 2x2, marker = top-left)
# B = bunker
# I = barracks
# A = artillery
# C = crater
# ASCII Legend (player):
# | = battle separator (row 0): first | = friendly boundary AND the
#     WEST edge of no-man's-land; a second | = its east edge. Trains
#     the artillery to shell strictly BETWEEN the markers; the two
#     markers belong to YOUR enemy-MG line placement — move them with
#     the M/m markers when the front shifts.
# # = trench path
# M = MG
# B = bunker
# I = barracks
# A = artillery
# F = air field (free static, 4x4)
# K = tank factory (free static, 4x4)
# C = crater
# T = tree
# D = dead tree
# W = wire
# ~ = mud

STATIC_MAP = [
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '..........A..........A.........|.........|.........a........a.................',
    '...............A...............|.........|.............a......................',
    '...............................|.........|....................................',
    '...............................|.........|..m.................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '......K....................M...|.........|....................................',
    '...............................|.........|....................................',
    '...................I...........|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|...m................................',
    '...............................|.........|....................................',
    '.....F.........................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...................I........M..|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....m...............................',
    '...............................|.........|....................................',
    '...............................|.........|................b...................',
    '...............................|.........|....................................',
    '.................B.............|.........|....................................',
    '...............................|.........|....................................',
    '............................M..|.........|......m.............................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
    '...............................|.........|....................................',
]

def no_mans_land_bounds():
    """Return the columns of the first two row-0 '|' markers, or None."""
    if not STATIC_MAP:
        return None

    markers = [x for x, char in enumerate(STATIC_MAP[0]) if char == "|"]
    if len(markers) < 2:
        return None

    return markers[0], markers[1]

class TrenchGenerator:
    """Parse STATIC_MAP into tile rows plus build candidates"""
    def __init__(self):
        # Keep the raw rows around: TileMap reads row 0.
        self.ascii_map = STATIC_MAP
        self.height = len(STATIC_MAP)
        self.width = len(STATIC_MAP[0])

    def generate_sector(self):
        """Convert every ASCII character into a tile type and, when the
        char marks a building, record it as a build candidate.

        Returns tiles (row-major ints), build_candidates ({x, y, type}
        dicts), and trench_graph (kept None: reserved for future
        pathfinding work).
        """
        tiles = []
        build_candidates = []

        for y, row in enumerate(self.ascii_map):
            tile_row = []

            for x, ch in enumerate(row):
                # Unknown characters fall back to empty ground: the map
                # is safe to hand-edit without breaking the game.
                tile_type = ASCII_TO_TILE.get(ch, TILE_EMPTY)
                tile_row.append(tile_type)

                # Buildings: player markers create purchasable spots.
                if ch == 'M': build_candidates.append({"x": x, "y": y, "type": "mg"})
                if ch == 'B': build_candidates.append({"x": x, "y": y, "type": "bunker"})
                if ch == 'I': build_candidates.append({"x": x, "y": y, "type": "barracks"})
                if ch == 'A': build_candidates.append({"x": x, "y": y, "type": "artillery"})

                # Free player-side statics: placed (not purchased) by
                # AssaultPhase at battle start; rendered with scene art.
                if ch == 'F': build_candidates.append({"x": x, "y": y, "type": "air_field"})
                if ch == 'K': build_candidates.append({"x": x, "y": y, "type": "tank_factory"})

                # Enemy buildings: lowercase markers create free
                # pre-placed enemy defenses (AssaultPhase places them).
                if ch == 'm': build_candidates.append({"x": x, "y": y, "type": "enemy_mg"})
                if ch == 'b': build_candidates.append({"x": x, "y": y, "type": "enemy_bunker"})
                if ch == 'i': build_candidates.append({"x": x, "y": y, "type": "enemy_barracks"})
                if ch == 'a': build_candidates.append({"x": x, "y": y, "type": "enemy_artillery"})

            tiles.append(tile_row)

        return {
            "tiles": tiles,
            "build_candidates": build_candidates,
            "trench_graph": None
        }
