"""
Static battlefield loader.

STATIC_MAP is a list of short, readable ASCII rows.
Each row is a string representing tiles in that row.

You edit STATIC_MAP directly.

ASCII Legend (player):
# = trench wall
M = MG
B = bunker
R = barracks
A = artillery
H = hill
C = crater
W = wire
~ = mud
N = no man's land
. = empty ground

ASCII Legend (enemy):
m = enemy MG
e = enemy bunker
r = enemy barracks
a = enemy artillery
h = enemy hill

'|' is a visual separator (ignored).
"""

# Tile type constants
TILE_EMPTY  = 0
TILE_TRENCH = 1
TILE_CRATER = 2
TILE_WIRE   = 3
TILE_MUD    = 4

# ASCII → tile type
ASCII_TO_TILE = {
    '.': TILE_EMPTY,
    'N': TILE_EMPTY,

    '#': TILE_TRENCH,
    'M': TILE_TRENCH,
    'B': TILE_TRENCH,
    'R': TILE_TRENCH,

    'A': TILE_EMPTY,
    'H': TILE_MUD,
    'C': TILE_CRATER,
    'W': TILE_WIRE,
    '~': TILE_MUD,

    # Enemy
    'm': TILE_TRENCH,
    'e': TILE_TRENCH,
    'r': TILE_TRENCH,
    'a': TILE_EMPTY,
    'h': TILE_MUD,

    # Visual separator
    '|': TILE_EMPTY,
}

# ------------------------------------------------------------
# HUMAN‑READABLE STATIC MAP — YOU EDIT THIS
# ------------------------------------------------------------
STATIC_MAP = [
    "........#.#.#..#.#...|...N..C...C..~..N..W..N...|..##..#.#..##..#..........",
    ".HHH...#....#.##.M...|.NW.NN.CNC.NN.WN.N~.NN.WN.|.#...#....##..#.#...hhhhh.",
    ".HA...##.#.##.#..#...|..C..N..NN..N..~..N..C....|.###...m.#..r.#.....hhah..",
    ".H.H...#....R.....M..|..N~.NN.WN~.NN.WN.NC.NN...|.m.###..#.#....#....hh....",
    "........###..##.#.##.|....C..~...N..N..~..C..~..|.#..##..#.#..##.....hhah..",
    "........#.#.#..#.#...|...N..C...C..~..N..W..N...|..##..#.#..##..#..........",
    "..B....#....#........|.N~.NN.WN~.NN.WN.NC.NN....|.##.#.##..#.#.......hhah..",
    "..........#..#.#.#.#.|...~..C...N..N..C..~..N...|....#.#.r..##..#.#..hhhhh.",
    "........#.#.#..#.#...|...N..C...C..~..N..W..N...|..##..#.#..##..#..........",
    "..H.H...#.#..R...#.M.|.NN.NN.NNN.NN.NN.NN.NN....|.##..##..#.#..............",
    "...AH...###..##.#.##.|...C..~...N..N..~..C..~...|.m..#...m#.#.##..#........",
    "...AH...#.M..#.......|...H....N...H....N....H...|.##...#....##..#......e...",
    "..HHH..##...##.#.##..|..C..~..NN..N..~..C..~....|.#.#...#.#..##............",
    ".......#....#.....#..|.H....N...H....N....H.....|...#.#..##..r.#...........",
    ".......#....#.....#..|.H....N...H....N....H.....|...#.#..##..r.#...........",
]

class TrenchGenerator:
    def __init__(self):
        """
        No padding needed — rows are already readable and consistent.
        """
        self.ascii_map = STATIC_MAP
        self.height = len(STATIC_MAP)
        self.width = len(STATIC_MAP[0])

    def generate_sector(self):
        tiles = []
        build_candidates = []

        for y, row in enumerate(self.ascii_map):
            tile_row = []

            for x, ch in enumerate(row):
                tile_type = ASCII_TO_TILE.get(ch, TILE_EMPTY)
                tile_row.append(tile_type)

                # Buildings
                if ch == 'M': build_candidates.append({"x": x, "y": y, "type": "mg"})
                if ch == 'B': build_candidates.append({"x": x, "y": y, "type": "bunker"})
                if ch == 'R': build_candidates.append({"x": x, "y": y, "type": "barracks"})
                if ch == 'A': build_candidates.append({"x": x, "y": y, "type": "artillery"})

                if ch == 'm': build_candidates.append({"x": x, "y": y, "type": "enemy_mg"})
                if ch == 'e': build_candidates.append({"x": x, "y": y, "type": "enemy_bunker"})
                if ch == 'r': build_candidates.append({"x": x, "y": y, "type": "enemy_barracks"})
                if ch == 'a': build_candidates.append({"x": x, "y": y, "type": "enemy_artillery"})

            tiles.append(tile_row)

        return {
            "tiles": tiles,
            "build_candidates": build_candidates,
            "trench_graph": None
        }
