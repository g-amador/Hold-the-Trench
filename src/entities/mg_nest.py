"""
Machine gun nest building.
Auto-shoots enemies in range, only when close enough and in arc.
"""

import math
import pygame
import random

from config import TILE_SIZE, GREY
from entities.bullet import Bullet
from utils.image_loader import load_image


class MGNest:
    
    def __init__(self, tile_x, tile_y, is_enemy=False):
        self.type = "enemy_mg" if is_enemy else "mg"
        self.is_enemy = is_enemy

        self.tile_x = tile_x
        self.tile_y = tile_y

        self.range = 220
        self.damage = 8
        self.fire_rate = 0.2
        self.cooldown = 0

        prefix = f"building_mg_nest"

        filename = random.choice([f"{prefix}_fr.png", f"{prefix}_brit.png"]) if is_enemy else random.choice([f"{prefix}_ger.png"])        
        self.image = load_image(
            filename,
            alpha=True, 
            size=(TILE_SIZE, TILE_SIZE),
        )

        if is_enemy:
            self.image = pygame.transform.flip(self.image, True, False)

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

            bullet = Bullet(cx, cy, dx, dy)
            bullets.append(bullet)
            self.cooldown = self.fire_rate

    def draw(self, screen, camera_x):
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        #rect = pygame.Rect(px + 4, py + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        #pygame.draw.rect(screen, GREY, rect)

        screen.blit(self.image, (px, py))
