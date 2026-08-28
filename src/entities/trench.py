"""
entities/trench.py

Trench entity for Hold the Trench.
"""

import pygame

from config import (
    TILE_SIZE,
    BLACK
)


class Trench:
    """
    Represents a trench segment
    built by the player.
    """

    def __init__(self, tile):
        """
        Create a trench on a tile.
        """

        self.tile = tile

        #
        # Future mechanics
        #
        self.cover_bonus = 0.50
        self.max_health = 100
        self.health = self.max_health

    def draw(self, screen):
        """
        Draw the trench.
        """

        #
        # Slightly inset rectangle
        #
        rect = pygame.Rect(
            self.tile.x * TILE_SIZE + 4,
            self.tile.y * TILE_SIZE + 10,
            TILE_SIZE - 8,
            TILE_SIZE - 20
        )

        #
        # Trench color
        #
        pygame.draw.rect(
            screen,
            BLACK,
            rect
        )

        #
        # Border
        #
        pygame.draw.rect(
            screen,
            (90, 90, 90),
            rect,
            2
        )

    def take_damage(self, amount):
        """
        Damage the trench.
        """

        self.health -= amount

        if self.health < 0:
            self.health = 0

    def is_destroyed(self):
        """
        Check if trench has collapsed.
        """

        return self.health <= 0