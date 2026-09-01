"""
Gold dropped by enemies.
Player collects gold by walking near it.
"""

import math
import pygame


class GoldPickup:
    def __init__(self, x, y, amount):
        self.x = x
        self.y = y
        self.amount = amount

        self.collected = False

        self.float_phase = 0
        self.y_offset = 0

        self.width = 12
        self.height = 12

    def update(self, dt, player):
        if self.collected:
            return False

        self.float_phase += dt / 200
        self.y_offset = math.sin(self.float_phase) * 3

        dist = math.hypot(player.x - self.x, player.y - self.y)
        if dist < 64:
            self.collected = True
            return True

        return False

    def draw(self, screen, camera_x):
        if self.collected:
            return

        pygame.draw.rect(
            screen,
            (255, 215, 0),
            (self.x - camera_x, self.y + self.y_offset, self.width, self.height)
        )
