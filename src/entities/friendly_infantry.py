"""
Friendly infantry spawned from barracks.
Advance toward closest enemy, engage in melee, and eventually die.
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

    def update(self, dt, enemies):
        if self.dead:
            return

        target = None
        best_dist = None
        for e in enemies:
            if e.dead:
                continue
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                target = e

        if target:
            dx = target.x - self.x
            dy = target.y - self.y
            length = math.hypot(dx, dy)
            if length > 0:
                dx /= length
                dy /= length
                self.x += dx * self.speed * dt / 1000
                self.y += dy * self.speed * dt / 1000

            if (self.x < target.x + target.width and
                self.x + self.width > target.x and
                self.y < target.y + target.height and
                self.y + self.height > target.y):
                target.take_damage(5)
                self.hp -= 5
                if self.hp <= 0:
                    self.dead = True

    def draw(self, screen, camera_x):
        pygame.draw.rect(
            screen,
            (0, 150, 255),
            (self.x - camera_x, self.y, self.width, self.height)
        )
