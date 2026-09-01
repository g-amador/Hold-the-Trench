"""
Bunker building.
Acts as the player's castle with health and larger size.
"""

import pygame
from config import TILE_SIZE, GREY


class Bunker:
    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

        self.hp = 200
        self.width = TILE_SIZE * 2
        self.height = TILE_SIZE * 2

    def update(self):
        pass

    def take_damage(self, dmg):
        self.hp -= dmg

    def is_destroyed(self):
        return self.hp <= 0

    def draw(self, screen, camera_x):
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE - (self.height - TILE_SIZE)
        rect = pygame.Rect(px, py, self.width, self.height)
        pygame.draw.rect(screen, GREY, rect)
