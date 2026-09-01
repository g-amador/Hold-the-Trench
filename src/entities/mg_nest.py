"""
Machine gun nest building.
Auto-shoots enemies in range.
"""

import pygame
from config import TILE_SIZE, GREY


class MGNest:
    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

        # Simple stats
        self.range = 200
        self.damage = 10
        self.fire_rate = 0.5  # shots per second
        self.cooldown = 0

    def update(self):
        """
        Cooldown timer is handled in combat_system.
        """
        pass

    def draw(self, screen):
        """
        Draw MG nest as a grey square.
        """
        px = self.tile_x * TILE_SIZE
        py = self.tile_y * TILE_SIZE

        rect = pygame.Rect(px + 4, py + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        pygame.draw.rect(screen, GREY, rect)
