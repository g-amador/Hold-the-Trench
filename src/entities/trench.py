"""
Trench building: a placeable defensive structure with no behavior yet.

No combat, no costs, no spawning are wired up; it exists so the
entity model has a defensive building type with the standard
construct/update/draw interface.

Note: the trenches visible on the battlefield from the ASCII map are
terrain tiles (TileMap), not instances of this class.
"""

import pygame

from config import TILE_SIZE, BROWN


class Trench:
    def __init__(self, tile_x, tile_y):
        # Tile grid position; pixels are derived only when drawing.
        self.tile_x = tile_x
        self.tile_y = tile_y

    def update(self):
        # Static building: nothing to simulate.
        pass

    def draw(self, screen, camera_x):
        # Tile position -> screen position; the camera only offsets x
        # because the battlefield is a horizontal strip.
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE

        rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, BROWN, rect)
