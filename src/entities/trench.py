"""
Trench building entity.
Provides basic defensive structure.
"""

import pygame
from config import TILE_SIZE, BROWN


class Trench:
    def __init__(self, tile_x, tile_y):
        # Store tile coordinates
        self.tile_x = tile_x
        self.tile_y = tile_y

    def update(self):
        """
        Trench has no active behavior for now.
        """
        pass

    def draw(self, screen):
        """
        Draw trench as a darker rectangle in the tile.
        """
        px = self.tile_x * TILE_SIZE
        py = self.tile_y * TILE_SIZE

        rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, BROWN, rect)
