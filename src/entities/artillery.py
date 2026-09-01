"""
Artillery building.
Slow but high-damage long-range attack.
"""

import pygame
from config import TILE_SIZE, GREY


class Artillery:
    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

        self.range = 300
        self.damage = 50
        self.fire_rate = 0.1
        self.cooldown = 0

    def update(self):
        """
        Behavior handled in combat_system.
        """
        pass

    def draw(self, screen):
        """
        Draw artillery as a tall grey rectangle.
        """
        px = self.tile_x * TILE_SIZE
        py = self.tile_y * TILE_SIZE

        rect = pygame.Rect(px + 8, py, TILE_SIZE - 16, TILE_SIZE)
        pygame.draw.rect(screen, GREY, rect)
