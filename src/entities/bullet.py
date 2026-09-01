"""
Bullet fired by the player.
Moves forward and damages enemies.
"""

import pygame


class Bullet:
    def __init__(self, x, y):
        # World position
        self.x = x
        self.y = y

        # Speed (pixels per second)
        self.speed = 400

        # Damage
        self.damage = 20

        # Bullet size
        self.width = 6
        self.height = 3

        # Whether the bullet should be removed
        self.dead = False

    def update(self, dt):
        """
        Move bullet forward.
        """
        self.x += self.speed * dt / 1000

        # Remove if too far
        if self.x > 5000:  # arbitrary far limit
            self.dead = True

    def draw(self, screen, camera_x):
        """
        Draw bullet.
        """
        pygame.draw.rect(
            screen,
            (255, 255, 0),
            (self.x - camera_x, self.y, self.width, self.height)
        )
