"""
WW1 infantry player with free WASD movement, shooting, and world boundaries.
"""

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

        # Set by AssaultPhase
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
        # Horizontal
        if self.x < 0:
            self.x = 0
        if self.x > self.max_world_x:
            self.x = self.max_world_x

        # Vertical: HUD bar is 40px tall
        hud_height = 40
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

    def shoot(self):
        if not self.can_shoot():
            return None

        from entities.bullet import Bullet

        bullet = Bullet(self.x + self.width, self.y + self.height // 2)
        self.shoot_timer = self.shoot_cooldown
        return bullet

    def draw(self, screen, camera_x):
        pygame.draw.rect(
            screen,
            (0, 200, 255),
            (self.x - camera_x, self.y, self.width, self.height)
        )
