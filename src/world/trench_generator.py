"""
Procedural WW1 trench + no man's land generator.
Creates a trench band, crater field, wire, mud.
"""

import random

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
        tiles = [
            [TILE_EMPTY for _ in range(self.width)]
            for _ in range(self.height)
        ]

        trench_y = self.height // 2

        for x in range(self.width):
            tiles[trench_y][x] = TILE_TRENCH

        for x in range(self.width):
            for y in range(trench_y - 3, trench_y + 4):
                if y < 0 or y >= self.height:
                    continue
                roll = random.random()
                if roll < 0.1:
                    tiles[y][x] = TILE_CRATER
                elif roll < 0.2:
                    tiles[y][x] = TILE_WIRE
                elif roll < 0.35:
                    tiles[y][x] = TILE_MUD

        return tiles
