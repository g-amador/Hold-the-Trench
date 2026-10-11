"""
Friendly infantry spawned from barracks.
Moves toward nearest enemy, engages in melee.
Kills exactly one enemy and dies.
"""

import math
import pygame


class FriendlyInfantry:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.speed = 40
        self.hp = 40
        self.width = 20
        self.height = 28
        self.dead = False

        # Tracks if this infantry already killed one enemy
        self.kill_count = 0

    def update(self, dt, enemies):
        if self.dead:
            return

        target = None
        best_dist = None

        for enemy in enemies:
            if enemy.dead:
                continue

            dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                target = enemy

        if target is None:
            return

        dx = target.x - self.x
        dy = target.y - self.y
        length = math.hypot(dx, dy)

        if length > 0:
            dx /= length
            dy /= length
            self.x += dx * self.speed * dt / 1000
            self.y += dy * self.speed * dt / 1000

        friendly_rect = pygame.Rect(
            round(self.x), round(self.y), self.width, self.height
        )
        enemy_rect = target.get_hitbox() if hasattr(target, "get_hitbox") else pygame.Rect(
            round(target.x), round(target.y), target.width, target.height
        )

        if friendly_rect.colliderect(enemy_rect):
            if self.kill_count == 0:
                target.take_damage(target.hp)
                self.kill_count = 1

            self.hp = 0
            self.dead = True

    def draw(self, screen, camera_x):
        pygame.draw.rect(
            screen,
            (0, 150, 255),
            (self.x - camera_x, self.y, self.width, self.height)
        )
