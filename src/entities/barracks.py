"""
Barracks building.
Spawns friendly infantry every 5 seconds.
"""

import pygame
from config import TILE_SIZE


class Barracks:
    
    def __init__(self, tile_x, tile_y, is_enemy=False):
        self.type = "enemy_barracks" if is_enemy else "barracks"
        self.is_enemy = is_enemy

        self.tile_x = tile_x
        self.tile_y = tile_y

        self.spawn_cooldown = 5.0
        self.timer = 0

    def update(self, dt, units):
        self.timer += dt / 1000

        if self.timer < self.spawn_cooldown:
            return

        self.timer = 0

        x = self.tile_x * TILE_SIZE
        y = self.tile_y * TILE_SIZE

        if self.is_enemy:
            from entities.enemy import EnemyInfantry
            units.append(EnemyInfantry(x, y))
        else:
            from entities.friendly_infantry import FriendlyInfantry
            units.append(FriendlyInfantry(x, y))

    def draw(self, screen, camera_x):
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        rect = pygame.Rect(px + 4, py + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        pygame.draw.rect(screen, (0, 100, 255), rect)
