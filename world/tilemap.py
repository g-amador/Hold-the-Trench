"""
world/tilemap.py

Tile grid system for Hold the Trench.
"""

from config import (
    MAP_WIDTH,
    MAP_HEIGHT,
    TILE_SIZE
)

from world.tile import Tile

class TileMap:
    """
    The battlefield tile grid.
    """

    def __init__(self):

        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT

        #
        # Generate tile grid
        #
        self.tiles = [
            [
                Tile(x, y)
                for y in range(self.height)
            ]
            for x in range(self.width)
        ]

    def get_tile(self, x, y):
        """
        Safely retrieve a tile.
        """

        if (
            0 <= x < self.width and
            0 <= y < self.height
        ):
            return self.tiles[x][y]

        return None

    def world_to_tile(self, mouse_x, mouse_y):
        """
        Convert screen coordinates to tile coordinates.
        """

        tile_x = mouse_x // TILE_SIZE
        tile_y = mouse_y // TILE_SIZE

        return tile_x, tile_y

    def draw(self, screen):
        """
        Draw all tiles.
        """

        for column in self.tiles:
            for tile in column:
                tile.draw(screen)