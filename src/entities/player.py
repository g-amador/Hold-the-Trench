"""
WW1 infantry player with WASD movement, collision, sliding, snapping, and wire slow-down.
"""

import math
import pygame
from config import SCREEN_HEIGHT, TILE_SIZE

BLOCKING_TILES = {"#", "H"}
BLOCKING_BUILDINGS = {"mg", "bunker", "barracks", "artillery"}
SLOW_TILES = {"W"}


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.speed = 200
        self.width = 24
        self.height = 32

        self.shoot_cooldown = 0.25
        self.shoot_timer = 0

        self.max_world_x = 2000

    def handle_input(self, dt, tilemap):
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1

        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        tile = tilemap.get_tile(int(self.x / TILE_SIZE), int(self.y / TILE_SIZE))
        speed = self.speed
        if tile and tile.type_char in SLOW_TILES:
            speed *= 0.45

        move_x = dx * speed * dt / 1000
        move_y = dy * speed * dt / 1000

        new_x = self.x + move_x
        new_y = self.y + move_y

        # X collision
        tile_x = int(new_x / TILE_SIZE)
        tile_y = int(self.y / TILE_SIZE)
        tile = tilemap.get_tile(tile_x, tile_y)

        block_x = tile and (
            tile.type_char in BLOCKING_TILES or
            (tile.building and hasattr(tile.building, "type") and tile.building.type in BLOCKING_BUILDINGS)
        )

        # Y collision
        tile_x = int(self.x / TILE_SIZE)
        tile_y = int(new_y / TILE_SIZE)
        tile = tilemap.get_tile(tile_x, tile_y)

        block_y = tile and (
            tile.type_char in BLOCKING_TILES or
            (tile.building and hasattr(tile.building, "type") and tile.building.type in BLOCKING_BUILDINGS)
        )

        if not block_x:
            self.x = new_x
        else:
            self.x = round(self.x / TILE_SIZE) * TILE_SIZE

        if not block_y:
            self.y = new_y
        else:
            self.y = round(self.y / TILE_SIZE) * TILE_SIZE

    def clamp_to_world(self):
        hud_height = 40

        self.x = max(0, min(self.x, self.max_world_x))
        self.y = max(hud_height, min(self.y, SCREEN_HEIGHT - self.height))

    def update(self, dt, tilemap):
        self.handle_input(dt, tilemap)
        self.clamp_to_world()

        if self.shoot_timer > 0:
            self.shoot_timer -= dt / 1000

    def can_shoot(self):
        return self.shoot_timer <= 0

    def shoot_toward(self, target):
        if not self.can_shoot():
            return None

        from entities.bullet import Bullet

        tx = target.x + target.width / 2
        ty = target.y + target.height / 2

        dx = tx - (self.x + self.width / 2)
        dy = ty - (self.y + self.height / 2)

        length = math.hypot(dx, dy)
        if length == 0:
            return None

        dx /= length
        dy /= length

        bullet = Bullet(self.x + self.width / 2, self.y + self.height / 2, dx, dy)
        self.shoot_timer = self.shoot_cooldown
        return bullet

    def auto_fire(self, dt, enemies, bullets):
        fire_range = 300

        target = None
        best_dist = None
        for e in enemies:
            if e.dead:
                continue
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= fire_range:
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    target = e

        if target and self.can_shoot():
            bullet = self.shoot_toward(target)
            if bullet:
                bullets.append(bullet)

    def draw(self, screen, camera_x):
        pygame.draw.rect(
            screen,
            (0, 200, 255),
            (self.x - camera_x, self.y, self.width, self.height)
        )
