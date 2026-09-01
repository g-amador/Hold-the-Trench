"""
Procedural WW1 trench + no man's land generator.
Defines tile types and generates a sector layout.
"""

import random

# Tile type constants
TILE_EMPTY = 0
TILE_TRENCH = 1
TILE_CRATER = 2
TILE_WIRE = 3
TILE_MUD = 4


class TrenchGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def generate_sector(self):
        """
        Returns a 2D array of tile types for one trench sector.
        """

        tiles = [
            [TILE_EMPTY for _ in range(self.width)]
            for _ in range(self.height)
        ]

        # Trench line roughly in the middle vertically
        trench_y = self.height // 2

        # Trench on the left third of the map
        for x in range(0, self.width // 3):
            tiles[trench_y][x] = TILE_TRENCH

        # No man's land: craters, wire, mud, empty
        for x in range(self.width // 3, self.width):
            for y in range(trench_y - 2, trench_y + 3):
                roll = random.random()
                if roll < 0.1:
                    tiles[y][x] = TILE_CRATER
                elif roll < 0.2:
                    tiles[y][x] = TILE_WIRE
                elif roll < 0.35:
                    tiles[y][x] = TILE_MUD
                else:
                    tiles[y][x] = TILE_EMPTY

        return tiles
