"""
world/map_generator.py

Procedural battlefield generation for Hold the Trench.
"""

import random


class MapGenerator:
    """
    Generates a WWI battlefield.
    """

    def generate(self, tilemap):
        """
        Populate the tilemap with terrain.
        """

        #
        # Reset everything to mud
        #
        for x in range(tilemap.width):

            for y in range(tilemap.height):

                tile = tilemap.get_tile(x, y)

                tile.terrain = "mud"

                tile.walkable = True

                tile.building = None

        #
        # Craters
        #
        crater_count = random.randint(20, 50)

        for _ in range(crater_count):

            crater_x = random.randint(
                0,
                tilemap.width - 1
            )

            crater_y = random.randint(
                0,
                tilemap.height - 1
            )

            crater_radius = random.randint(1, 2)

            self._paint_circle(
                tilemap,
                crater_x,
                crater_y,
                crater_radius,
                "crater"
            )

        #
        # Forest patches
        #
        forest_count = random.randint(3, 8)

        for _ in range(forest_count):

            forest_x = random.randint(
                0,
                tilemap.width - 1
            )

            forest_y = random.randint(
                0,
                tilemap.height - 1
            )

            forest_radius = random.randint(2, 4)

            self._paint_circle(
                tilemap,
                forest_x,
                forest_y,
                forest_radius,
                "forest"
            )

    def _paint_circle(
        self,
        tilemap,
        center_x,
        center_y,
        radius,
        terrain
    ):
        """
        Paint circular terrain areas.
        """

        for x in range(
            center_x - radius,
            center_x + radius + 1
        ):

            for y in range(
                center_y - radius,
                center_y + radius + 1
            ):

                tile = tilemap.get_tile(x, y)

                if tile is None:
                    continue

                dx = x - center_x
                dy = y - center_y

                #
                # Circular shape
                #
                if dx * dx + dy * dy <= radius * radius:

                    tile.terrain = terrain

                    #
                    # Future terrain rules
                    #
                    if terrain == "forest":

                        tile.walkable = True

                    elif terrain == "crater":

                        tile.walkable = True