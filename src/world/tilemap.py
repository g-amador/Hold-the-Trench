"""
Tilemap for static ASCII battlefield.

Loads STATIC_MAP from TrenchGenerator and turns it into a Tile grid.
Everything is exactly as written in ASCII: the map is the level
editor. Buildings attach to tiles (tile.building), which makes the
map the authority on layout, occupancy, and (with spot_types) build
locations.
"""

import pygame

from config import TILE_SIZE
from world.trench_generator import (
    TrenchGenerator,
    TILE_EMPTY,
    TILE_TRENCH,
    TILE_CRATER,
    TILE_WIRE,
    TILE_MUD,
    TILE_HILL,
    TILE_HILL_PATH,
)


class Tile:
    """One world cell: terrain type plus an optional building anchor."""

    def __init__(self, x, y, tile_type):
        self.x = x
        self.y = y
        self.type = tile_type
        # Buildings live on tiles: collision, queries, and drawing all
        # walk the tile grid instead of a second entity list.
        self.building = None

        # Convert numeric tile type -> ASCII character: chars double as
        # the tokens game logic tests against (player.py keeps sets of
        # them); keep TileMap and TrenchGenerator in sync on these.
        if tile_type == TILE_TRENCH:
            self.type_char = "#"
        elif tile_type == TILE_CRATER:
            self.type_char = "C"
        elif tile_type == TILE_WIRE:
            self.type_char = "W"
        elif tile_type == TILE_MUD:
            self.type_char = "~"
        elif tile_type == TILE_HILL:
            self.type_char = "H"
        elif tile_type == TILE_HILL_PATH:
            self.type_char = "P"
        else:
            self.type_char = "."

    def draw(self, screen, camera_x):
        """Paint this tile, then delegate to its building, if any.

        Flat palette per terrain type plus a 1px grid outline; camera
        only shifts x because the battlefield is a horizontal strip.
        """
        px = self.x * TILE_SIZE - camera_x
        py = self.y * TILE_SIZE

        colors = {
            TILE_EMPTY: (50, 50, 50),
            TILE_TRENCH: (90, 60, 40),
            TILE_CRATER: (70, 50, 50),
            TILE_WIRE: (150, 150, 150),
            TILE_MUD: (80, 70, 50),
            TILE_HILL: (120, 100, 60),
            TILE_HILL_PATH: (100, 80, 20),
        }

        pygame.draw.rect(screen, colors[self.type], (px, py, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(screen, (20, 20, 20), (px, py, TILE_SIZE, TILE_SIZE), 1)

        if self.building:
            self.building.draw(screen, camera_x)


class TileMap:
    """Grid of tiles from the ASCII map, plus build-spot bookkeeping."""

    def __init__(self):
        # The generator is the single level source; rebuilding it gives
        # a pristine battlefield (menu does this once per battle).
        generator = TrenchGenerator()
        result = generator.generate_sector()

        layout = result["tiles"]
        self.build_candidates = result["build_candidates"]

        self.width = len(layout[0])
        self.height = len(layout)

        # Row-major tile grid; x grows right, y grows down.
        self.tiles = [
            [Tile(x, y, layout[y][x]) for x in range(self.width)]
            for y in range(self.height)
        ]

        # Build spot types (mg, bunker, barracks, artillery, enemy
        # versions), keyed by tile coordinate for O(1) lookups.
        self.spot_types = {(c["x"], c["y"]): c["type"] for c in self.build_candidates}

        # Partial payments: key (x, y) -> gold already paid by the
        # player toward that spot. The battle state tops these up each
        # frame; the building appears when payments cover the cost.
        self.paid_amount = {(x, y): 0 for (x, y) in self.spot_types}

        # Friendly boundary = first '|' in row 0 (S1 rule): the player
        # side ends at this tile column.
        row0 = generator.ascii_map[0]
        self.friendly_boundary = row0.index("|")

    # WaveDirector expects this to exist
    def configure_build_spots(self, *args, **kwargs):
        # KNOWN ISSUE (AI.md #5): dead compatibility stub; build spots
        # already come from TrenchGenerator.
        return

    def is_build_spot(self, x, y):
        """True when this tile is a player/enemy build spot marker."""
        return (x, y) in self.spot_types

    def get_tile(self, x, y):
        """Return the tile, or None for any out-of-grid coordinate."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def is_walkable(self, x, y):
        """Strict spawn-walkability: only '.' counts as empty ground.

        Deliberately excludes trenches, mud, craters, wire, and hills:
        units and spawn searches treat everything else as blocked.
        """
        tile = self.get_tile(x, y)
        if not tile:
            return False

        # Only '.' counts as empty for spawning (Option B)
        return tile.type_char == "."

    def draw(self, screen, camera_x):
        """Draw every tile, then outline build spots for the player."""
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x].draw(screen, camera_x)

        # Debug/assist overlay: green squares around build candidates.
        # These also draw over constructed buildings, which is why a
        # built spot still shows its outline in game.
        for (x, y) in self.spot_types:
            px = x * TILE_SIZE - camera_x
            py = y * TILE_SIZE
            pygame.draw.rect(screen, (0, 255, 0), (px + 4, py + 4, TILE_SIZE - 8, TILE_SIZE - 8), 1)
