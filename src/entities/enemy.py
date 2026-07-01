"""
entities/enemy.py

Basic enemy infantry unit for Hold the Trench.
"""

import pygame

from src.config import (
    TILE_SIZE,
    RED
)


class Enemy:
    """
    Basic enemy infantry unit.
    """

    def __init__(self, tile_x, tile_y):
        """
        Create an enemy at the given tile coordinates.
        """

        #
        # Position (tile-based)
        #
        self.tile_x = tile_x
        self.tile_y = tile_y

        #
        # Statistics
        #
        self.max_health = 50
        self.health = self.max_health

        self.damage = 10

        #
        # Movement
        #
        self.speed = 1.0          # tiles per second

        self.move_timer = 0.0

        #
        # Future pathfinding support
        #
        self.path = []

        #
        # Suppression support
        #
        self.suppressed = False

    def update(self, delta_time):
        """
        Update the enemy.
        """

        #
        # Milestone 1:
        # Simple downward movement
        #
        self.move_timer += delta_time

        if self.move_timer >= 1.0 / self.speed:

            self.move_timer = 0.0

            self.tile_y += 1

    def draw(self, screen):
        """
        Draw the enemy.
        """

        padding = 6

        rect = pygame.Rect(
            self.tile_x * TILE_SIZE + padding,
            self.tile_y * TILE_SIZE + padding,
            TILE_SIZE - padding * 2,
            TILE_SIZE - padding * 2
        )

        pygame.draw.rect(
            screen,
            RED,
            rect
        )

        #
        # Health bar
        #
        bar_width = TILE_SIZE - 8

        health_ratio = (
            self.health /
            self.max_health
        )

        health_rect = pygame.Rect(
            self.tile_x * TILE_SIZE + 4,
            self.tile_y * TILE_SIZE + 2,
            int(bar_width * health_ratio),
            4
        )

        pygame.draw.rect(
            screen,
            (0, 255, 0),
            health_rect
        )

    def take_damage(self, amount):
        """
        Apply damage.
        """

        self.health -= amount

        if self.health < 0:
            self.health = 0

    def is_dead(self):
        """
        Has the unit died?
        """

        return self.health <= 0

    def reached_defenses(self, map_height):
        """
        Check if the enemy has crossed the battlefield.
        """

        return self.tile_y >= map_height - 1