"""
Bunker building.
Stronger defensive structure with higher damage and health.
"""

import pygame
from config import TILE_SIZE, GREY


class Bunker:
    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

        self.range = 220
        self.damage = 20
        self.fire_rate = 0.3
        self.cooldown = 0

        self.hp = 100  # bunker health

    def update(self):
        pass

    def take_damage(self, dmg):
        self.hp -= dmg

    def is_destroyed(self):
        return self.hp <= 0

    def draw(self, screen):
        px = self.tile_x * TILE_SIZE
        py = self.tile_y * TILE_SIZE

        rect = pygame.Rect(px + 2, py + 2, TILE_SIZE - 4, TILE_SIZE - 4)
        pygame.draw.rect(screen, GREY, rect)
