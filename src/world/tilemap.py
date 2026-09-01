"""
Tilemap with bunker behind trench, structured MG, barracks, and artillery positions.
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
            self.building.draw(screen, camera_x)


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

        self.trench_y = height // 2
        self.build_spots = []
        self.spot_types = {}

    def configure_build_spots(self, wave_strength, has_tanks, has_cavalry):
        self.build_spots = []
        self.spot_types = {}

        trench_y = self.trench_y

        mg_positions = [6, 8, 10]
        for x in mg_positions:
            self.build_spots.append((x, trench_y))
            self.spot_types[(x, trench_y)] = "mg"

        barracks_positions = [4, 12]
        for x in barracks_positions:
            self.build_spots.append((x, trench_y - 1))
            self.spot_types[(x, trench_y - 1)] = "barracks"

        artillery_positions = [2, 14]
        for x in artillery_positions:
            self.build_spots.append((x, trench_y - 2))
            self.spot_types[(x, trench_y - 2)] = "artillery"

        if has_tanks or wave_strength > 500:
            extra_x = 16
            self.build_spots.append((extra_x, trench_y - 2))
            self.spot_types[(extra_x, trench_y - 2)] = "artillery"

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

        for (bx, by) in self.build_spots:
            px = bx * TILE_SIZE - camera_x
            py = by * TILE_SIZE
            rect = pygame.Rect(px + 4, py + 4, TILE_SIZE - 8, TILE_SIZE - 8)
            pygame.draw.rect(screen, (0, 255, 0), rect, 1)
