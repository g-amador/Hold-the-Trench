"""
Tilemap with procedural trenches and dynamic build spots.
"""

import pygame
from config import TILE_SIZE
from world.trench_generator import TrenchGenerator, TILE_TRENCH, TILE_CRATER, TILE_WIRE, TILE_MUD


class Tile:
    def __init__(self, x, y, tile_type):
        self.x = x
        self.y = y
        self.type = tile_type
        self.building = None

    def draw(self, screen, camera_x):
        px = self.x * TILE_SIZE - camera_x
        py = self.y * TILE_SIZE

        color = (50, 50, 50)

        if self.type == TILE_TRENCH:
            color = (90, 60, 40)
        elif self.type == TILE_CRATER:
            color = (70, 50, 50)
        elif self.type == TILE_WIRE:
            color = (150, 150, 150)
        elif self.type == TILE_MUD:
            color = (80, 70, 50)

        rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (20, 20, 20), rect, 1)

        if self.building:
            self.building.draw(screen)


class TileMap:
    def __init__(self, width=40, height=15):
        self.width = width
        self.height = height

        generator = TrenchGenerator(width, height)
        layout = generator.generate_sector()

        self.tiles = [
            [Tile(x, y, layout[y][x]) for x in range(width)]
            for y in range(height)
        ]

        # Build spots: will be configured per wave
        self.build_spots = []
        self.trench_y = height // 2

    def configure_build_spots(self, wave_strength):
        """
        Decide where build spots are based on wave strength.
        More strength → more spots further forward.
        """
        self.build_spots = []

        # Base number of spots
        base_spots = 3
        extra_spots = min(3, wave_strength // 200)
        total_spots = base_spots + extra_spots

        # Place them along trench line, spaced
        start_x = 4
        step = 2

        for i in range(total_spots):
            x = start_x + i * step
            if x < self.width // 3:  # keep them near trench
                self.build_spots.append((x, self.trench_y))

    def is_build_spot(self, x, y):
        return (x, y) in self.build_spots

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def draw(self, screen, camera_x):
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x].draw(screen, camera_x)

        # Draw build spots as faint squares
        for (bx, by) in self.build_spots:
            px = bx * TILE_SIZE - camera_x
            py = by * TILE_SIZE
            rect = pygame.Rect(px + 4, py + 4, TILE_SIZE - 8, TILE_SIZE - 8)
            pygame.draw.rect(screen, (0, 255, 0), rect, 1)
