"""
entities/bunker.py

WWI defensive bunker for Hold the Trench.
"""

import pygame

from src.config import (
    TILE_SIZE
)


class Bunker:
    """
    Defensive bunker.

    High health, moderate damage,
    slower firing than MG nests.
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
        self.max_health = 500
        self.health = self.max_health

        #
        # Combat stats
        #
        self.range = 5

        self.damage = 20

        #
        # Fire every 60 ticks
        #
        self.fire_rate = 60

        self.cooldown = 0

        #
        # Classification
        #
        self.structure_type = "bunker"

    def draw(self, screen):
        """
        Draw bunker.
        """

        x = self.tile_x * TILE_SIZE
        y = self.tile_y * TILE_SIZE

        #
        # Concrete base
        #
        bunker_rect = pygame.Rect(
            x + 2,
            y + 2,
            TILE_SIZE - 4,
            TILE_SIZE - 4
        )

        pygame.draw.rect(
            screen,
            (90, 90, 90),
            bunker_rect
        )

        #
        # Roof
        #
        roof_rect = pygame.Rect(
            x + 6,
            y + 6,
            TILE_SIZE - 12,
            TILE_SIZE // 2
        )

        pygame.draw.rect(
            screen,
            (60, 60, 60),
            roof_rect
        )

        #
        # Firing slit
        #
        slit_rect = pygame.Rect(
            x + 10,
            y + TILE_SIZE // 2,
            TILE_SIZE - 20,
            4
        )

        pygame.draw.rect(
            screen,
            (20, 20, 20),
            slit_rect
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
        Damage bunker.
        """

        self.health -= amount

        if self.health < 0:
            self.health = 0

    def repair(
        self,
        amount
    ):
        """
        Repair bunker.
        """

        self.health += amount

        if self.health > self.max_health:
            self.health = (
                self.max_health
            )

    def is_destroyed(self):
        """
        Check if bunker
        has been destroyed.
        """

        return (
            self.health <= 0
        )