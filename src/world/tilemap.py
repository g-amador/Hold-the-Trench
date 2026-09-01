"""
Tilemap with bunker behind trench, structured MG, barracks, and artillery positions.
Build spots dynamically match total gold obtainable.
"""

import pygame
from config import TILE_SIZE
from world.trench_generator import TrenchGenerator, TILE_TRENCH, TILE_CRATER, TILE_WIRE, TILE_MUD


MG_COST = 20
BARRACKS_COST = 30
ARTILLERY_COST = 60


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

    def configure_build_spots(self, wave_strength, has_tanks, has_cavalry, total_gold_available):
        self.build_spots = []
        self.spot_types = {}

        trench_y = self.trench_y

        # Costs
        mg_cost = MG_COST
        barracks_cost = BARRACKS_COST
        artillery_cost = ARTILLERY_COST

        # Build spot candidates
        mg_positions = [6, 8, 10]
        barracks_positions = [4, 12]
        artillery_positions = [2, 14]

        if has_tanks or wave_strength > 500:
            artillery_positions.append(16)

        # Build spots in priority order
        ordered_spots = []

        for x in mg_positions:
            ordered_spots.append((x, trench_y, "mg", mg_cost))

        for x in barracks_positions:
            ordered_spots.append((x, trench_y - 1, "barracks", barracks_cost))

        for x in artillery_positions:
            ordered_spots.append((x, trench_y - 2, "artillery", artillery_cost))

        # Select spots until total cost matches total gold available
        running_cost = 0
        for (x, y, spot_type, cost) in ordered_spots:
            if running_cost + cost <= total_gold_available:
                self.build_spots.append((x, y))
                self.spot_types[(x, y)] = spot_type
                running_cost += cost

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
