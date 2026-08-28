"""
entities/artillery.py

WWI field artillery for Hold the Trench.
"""

import pygame

from config import (
    TILE_SIZE
)


class Artillery:
    """
    WWI field artillery.

    Long range, high damage,
    slow reload.
    """

    def __init__(self, tile):

        #
        # Position
        #
        self.tile = tile

        self.tile_x = tile.x
        self.tile_y = tile.y

        #
        # Health
        #
        self.max_health = 300
        self.health = self.max_health

        #
        # Combat
        #
        self.range = 12

        self.damage = 75

        #
        # Slow reload
        #
        self.fire_rate = 180

        self.cooldown = 0

        #
        # Structure type
        #
        self.structure_type = "artillery"

    def draw(self, screen):
        """
        Draw artillery.
        """

        x = self.tile_x * TILE_SIZE
        y = self.tile_y * TILE_SIZE

        #
        # Gun carriage
        #
        carriage = pygame.Rect(
            x + 4,
            y + 12,
            TILE_SIZE - 8,
            TILE_SIZE - 10
        )

        pygame.draw.rect(
            screen,
            (110, 80, 50),
            carriage
        )

        #
        # Cannon barrel
        #
        barrel = pygame.Rect(
            x + 8,
            y + 4,
            TILE_SIZE - 16,
            8
        )

        pygame.draw.rect(
            screen,
            (70, 70, 70),
            barrel
        )

        #
        # Wheels
        #
        pygame.draw.circle(
            screen,
            (40, 40, 40),
            (x + 8, y + TILE_SIZE - 6),
            5
        )

        pygame.draw.circle(
            screen,
            (40, 40, 40),
            (x + TILE_SIZE - 8, y + TILE_SIZE - 6),
            5
        )

        #
        # Health bar background
        #
        bg_bar = pygame.Rect(
            x + 2,
            y,
            TILE_SIZE - 4,
            4
        )

        pygame.draw.rect(
            screen,
            (80, 0, 0),
            bg_bar
        )

        #
        # Health bar
        #
        health_ratio = (
            self.health /
            self.max_health
        )

        hp_bar = pygame.Rect(
            x + 2,
            y,
            int(
                (TILE_SIZE - 4)
                * health_ratio
            ),
            4
        )

        pygame.draw.rect(
            screen,
            (0, 255, 0),
            hp_bar
        )

    def take_damage(
        self,
        amount
    ):
        """
        Damage artillery.
        """

        self.health -= amount

        if self.health < 0:
            self.health = 0

    def repair(
        self,
        amount
    ):
        """
        Repair artillery.
        """

        self.health += amount

        if self.health > self.max_health:

            self.health = (
                self.max_health
            )

    def is_destroyed(self):
        """
        Check destruction.
        """

        return (
            self.health <= 0
        )