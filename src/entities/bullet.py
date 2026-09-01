"""
Bullet fired by the player.
Moves toward target direction and damages enemies.
"""

import pygame


class Bullet:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y

        self.speed = 400
        self.damage = 20

        self.width = 6
        self.height = 3

        self.dead = False

        self.dx = dx
        self.dy = dy

    def update(self, dt):
        self.x += self.dx * self.speed * dt / 1000
        self.y += self.dy * self.speed * dt / 1000

        if self.x > 5000 or self.x < -500 or self.y < -500 or self.y > 5000:
            self.dead = True

    def draw(self, screen, camera_x):
        pygame.draw.rect(
            screen,
            (255, 255, 0),
            (self.x - camera_x, self.y, self.width, self.height)
        )
