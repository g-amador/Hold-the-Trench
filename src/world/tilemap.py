"""
Tilemap for static ASCII battlefield.

Loads STATIC_MAP from TrenchGenerator.
Everything is exactly as written in ASCII.
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
    TILE_HILL
)


class Tile:
    def __init__(self, x, y, tile_type):
        self.x = x
        self.y = y
        self.type = tile_type
        self.building = None

        # Convert numeric tile type → ASCII character
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
        else:
            self.type_char = "."

    def draw(self, screen, camera_x):
        px = self.x * TILE_SIZE - camera_x
        py = self.y * TILE_SIZE

        colors = {
            TILE_EMPTY: (50, 50, 50),
            TILE_TRENCH: (90, 60, 40),
            TILE_CRATER: (70, 50, 50),
            TILE_WIRE: (150, 150, 150),
            TILE_MUD: (80, 70, 50),
            TILE_HILL: (120, 100, 60),
        }

        pygame.draw.rect(screen, colors[self.type], (px, py, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(screen, (20, 20, 20), (px, py, TILE_SIZE, TILE_SIZE), 1)

        if self.building:
            self.building.draw(screen, camera_x)


class TileMap:
    def __init__(self):
        generator = TrenchGenerator()
        result = generator.generate_sector()

        layout = result["tiles"]
        self.build_candidates = result["build_candidates"]

        self.width = len(layout[0])
        self.height = len(layout)

        self.tiles = [
            [Tile(x, y, layout[y][x]) for x in range(self.width)]
            for y in range(self.height)
        ]

        # Build spot types (mg, bunker, barracks, artillery, enemy versions)
        self.spot_types = {(c["x"], c["y"]): c["type"] for c in self.build_candidates}

        # Track how much the player has paid for each build spot
        self.paid_amount = {(x, y): 0 for (x, y) in self.spot_types}

        # Friendly boundary = first '|' in row 0 (S1 rule)
        row0 = generator.ascii_map[0]
        self.friendly_boundary = row0.index("|")

    # WaveDirector expects this to exist
    def configure_build_spots(self, *args, **kwargs):
        # Build spots already come from TrenchGenerator; nothing else needed.
        return

    def is_build_spot(self, x, y):
        return (x, y) in self.spot_types

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def is_walkable(self, x, y):
        tile = self.get_tile(x, y)
        if not tile:
            return False

        # Only '.' counts as empty for spawning (Option B)
        return tile.type_char == "."

    def draw(self, screen, camera_x):
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x].draw(screen, camera_x)

        # Draw green squares around build candidates
        for (x, y) in self.spot_types:
            px = x * TILE_SIZE - camera_x
            py = y * TILE_SIZE
            pygame.draw.rect(screen, (0, 255, 0), (px + 4, py + 4, TILE_SIZE - 8, TILE_SIZE - 8), 1)
