"""
entities/mg_nest.py

Machine Gun Nest
Primary defensive weapon.
"""

import pygame

from src.config import (
    TILE_SIZE
)


class MGNest:
    """
    Machine gun nest.
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
        self.max_health = 200
        self.health = self.max_health

        #
        # Combat stats
        #
        self.range = 6

        self.damage = 10

        #
        # Fire every 30 frames
        #
        self.fire_rate = 30

        self.cooldown = 0

    def draw(self, screen):
        """
        Draw MG Nest.
        """

        x = self.tile_x * TILE_SIZE
        y = self.tile_y * TILE_SIZE

        #
        # Sandbag base
        #
        base_rect = pygame.Rect(
            x + 4,
            y + 4,
            TILE_SIZE - 8,
            TILE_SIZE - 8
        )

        pygame.draw.rect(
            screen,
            (140, 120, 80),
            base_rect
        )

        #
        # Gun housing
        #
        gun_rect = pygame.Rect(
            x + 10,
            y + 10,
            TILE_SIZE - 20,
            TILE_SIZE - 20
        )

        pygame.draw.rect(
            screen,
            (60, 60, 60),
            gun_rect
        )

        #
        # Health bar background
        #
        bg_bar = pygame.Rect(
            x + 2,
            y + 2,
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
        ratio = (
            self.health /
            self.max_health
        )

        hp_bar = pygame.Rect(
            x + 2,
            y + 2,
            int((TILE_SIZE - 4) * ratio),
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
        Damage structure.
        """

        self.health -= amount

        if self.health < 0:
            self.health = 0

    def is_destroyed(self):
        """
        Check destruction.
        """

        return self.health <= 0