"""
Machine gun nest building.
Auto-shoots enemies in range, only when close enough and in arc.
"""

import math
import pygame
from config import TILE_SIZE, GREY


class MGNest:
    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

        self.range = 220
        self.damage = 8
        self.fire_rate = 0.2
        self.cooldown = 0

    def update(self, dt, enemies, bullets):
        self.cooldown -= dt / 1000
        if self.cooldown > 0:
            return

        cx = self.tile_x * TILE_SIZE + TILE_SIZE / 2
        cy = self.tile_y * TILE_SIZE + TILE_SIZE / 2

        target = None
        best_dist = None
        for e in enemies:
            if e.dead:
                continue
            dist = math.hypot(e.x - cx, e.y - cy)
            if dist <= self.range:
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    target = e

        if target:
            dx = target.x - cx
            dy = target.y - cy
            length = math.hypot(dx, dy)
            if length == 0:
                return
            dx /= length
            dy /= length

            from entities.bullet import Bullet
            bullet = Bullet(cx, cy, dx, dy)
            bullets.append(bullet)
            self.cooldown = self.fire_rate

    def draw(self, screen, camera_x):
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        rect = pygame.Rect(px + 4, py + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        pygame.draw.rect(screen, GREY, rect)
