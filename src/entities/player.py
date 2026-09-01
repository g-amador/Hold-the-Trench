"""
WW1 infantry player with free WASD movement, autofire toward closest enemy, and world boundaries.
"""

import math
import pygame
from config import SCREEN_HEIGHT


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

    def handle_input(self, dt):
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

        self.x += dx * self.speed * dt / 1000
        self.y += dy * self.speed * dt / 1000

    def clamp_to_world(self):
        hud_height = 40

        if self.x < 0:
            self.x = 0
        if self.x > self.max_world_x:
            self.x = self.max_world_x

        if self.y < hud_height:
            self.y = hud_height
        if self.y > SCREEN_HEIGHT - self.height:
            self.y = SCREEN_HEIGHT - self.height

    def update(self, dt):
        self.handle_input(dt)
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
