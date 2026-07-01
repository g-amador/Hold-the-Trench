"""
world/tile.py

Single tile on the battlefield for Hold the Trench.
"""

import pygame

from src.config import (
    TILE_SIZE,
    MUD,
    CRATER,
    FOREST
)


class Tile:
    """
    Represents a single tile on the battlefield.
    """

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.terrain = "mud"

        self.walkable = True

        self.building = None

    def draw(self, screen):
        """
        Draw the tile.
        """

        rect = pygame.Rect(
            self.x * TILE_SIZE,
            self.y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE
        )

        if self.terrain == "mud":
            color = MUD

        elif self.terrain == "crater":
            color = CRATER

        elif self.terrain == "forest":
            color = FOREST

        else:
            color = MUD

        pygame.draw.rect(
            screen,
            color,
            rect
        )

        #
        # Grid lines
        #
        pygame.draw.rect(
            screen,
            (50, 50, 50),
            rect,
            1
        )

        #
        # Draw structure
        #
        if self.building is not None:

            self.building.draw(screen)