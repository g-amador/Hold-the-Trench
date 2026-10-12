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
H = hill path
C = crater
T = tree
D = dead tree
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
TILE_EMPTY     = 0
TILE_TRENCH    = 1
TILE_CRATER    = 2
TILE_WIRE      = 3
TILE_MUD       = 4
TILE_HILL      = 5
TILE_HILL_PATH = 6

# ASCII → tile type
ASCII_TO_TILE = {
    '.': TILE_EMPTY,
    'N': TILE_EMPTY,
    'T': TILE_EMPTY,
    'D': TILE_EMPTY,

    '#': TILE_TRENCH,
    'M': TILE_TRENCH,
    'B': TILE_TRENCH,
    'R': TILE_TRENCH,
    
    'H': TILE_HILL,
    'P': TILE_HILL_PATH,
    'A': TILE_HILL_PATH,
    'C': TILE_CRATER,
    'W': TILE_WIRE,
    '~': TILE_MUD,

    # Enemy
    'm': TILE_TRENCH,
    'e': TILE_TRENCH,
    'r': TILE_TRENCH,    
    'h': TILE_HILL,
    'p': TILE_HILL_PATH,
    'a': TILE_HILL_PATH,

    # Visual separator
    '|': TILE_EMPTY,
}

# ------------------------------------------------------------
# HUMAN‑READABLE STATIC MAP — YOU EDIT THIS
# ------------------------------------------------------------
STATIC_MAP = [
    "..........................|..........................|...........................",
    ".......#..##..#...#...#...|...N..C...C..~..N..W..N...|..##..#..#..##..###........",
    ".HHH...#..M.......##..M...|.NW.NN.CNC.NN.WN.N~.NN.WN.|.......m...##..#.....hhhhh.",
    ".HAP..##..#...##...#..#...|..C..N..NN..NT.~..N..C....|............r........hhap..",
    ".HPH...#.....#R.......M...|..N~.NN.WN~.NN.WN.NC.NN...|.m..##.....#...####..hhap..",
    ".............#...#...##...|....C..~.D.N..N..~..C..~..|.#...#..#..#..##..#..hhhh..",
    "...........###..##..#.....|...N..C...C..~..N..W..N...|.##..#..#....##..##........",
    "..B..####......##.........|.N~.NN.WN~.NN.WN.NC.NN....|..##..#..##.....###..hhph..",
    "......#........#......##..|...~..C...N..N..C..~..N...|......m...r##..####..hhahh.",
    "............#..#...#..#...|...N..C.T.HH.~..N..W..N...|......#..#..##..####..hhh..",
    "..HPH...#..##..R...####...|.NN.NN.NNHPPN.NN.NN.NN....|.##..#q#............#......",
    "..PAH..##...#..##.......#.|...C..~..HPH.N..~..C..~...|.m..#...m#.....##..........",
    "..PAH...R...M...#.......M.|...D.T..NPPPP....N...HH...|.#......#...#...#......e...",
    "..HHH#..##..##..#...#...#.|..C..~..NHHHN..~..C..~H...|....#...#..#..##..##.......",
    ".....M.......#..##..##....|.H....N..HH....N..D.N.....|...##.....#...r#...........",
]

class TrenchGenerator:
    def __init__(self):
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

                # Enemy buildings
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
