"""
Trench building.
Provides basic defensive structure.
"""

import pygame
from config import TILE_SIZE, BROWN


class Trench:
    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

    def update(self):
        pass

    def draw(self, screen, camera_x):
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, BROWN, rect)
