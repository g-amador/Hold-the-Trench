"""
Friendly infantry spawned from barracks.
Advance and fight enemy infantry in melee.
"""

import pygame


class FriendlyInfantry:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.speed = 50
        self.hp = 40
        self.width = 20
        self.height = 28
        self.dead = False

    def update(self, dt, enemies):
        if self.dead:
            return

        self.x += self.speed * dt / 1000

        for e in enemies:
            if e.dead:
                continue
            if (self.x < e.x + e.width and
                self.x + self.width > e.x and
                self.y < e.y + e.height and
                self.y + self.height > e.y):
                e.take_damage(10)
                self.hp -= 10
                if self.hp <= 0:
                    self.dead = True

    def draw(self, screen, camera_x):
        pygame.draw.rect(
            screen,
            (0, 150, 255),
            (self.x - camera_x, self.y, self.width, self.height)
        )
