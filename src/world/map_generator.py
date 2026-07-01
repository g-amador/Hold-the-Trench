"""
world/map_generator.py

Procedural battlefield generation for Hold the Trench.
"""

import random


class MapGenerator:
    """
    Generates WWI battlefields
    based on scenario parameters.
    """

    def generate(
        self,
        tilemap,
        scenario
    ):
        """
        Generate battlefield terrain.
        """

        #
        # Use scenario seed
        #
        random.seed(
            scenario.seed
        )

        #
        # Reset battlefield
        #
        for x in range(tilemap.width):

            for y in range(tilemap.height):

                tile = tilemap.get_tile(
                    x,
                    y
                )

                tile.terrain = "mud"
                tile.walkable = True
                tile.building = None

        #
        # Determine terrain density
        #
        if scenario.map_type == "forest":

            crater_count = random.randint(
                5,
                20
            )

            forest_count = random.randint(
                8,
                15
            )

        elif scenario.map_type == "craters":

            crater_count = random.randint(
                40,
                80
            )

            forest_count = random.randint(
                0,
                3
            )

        else:  # trenches

            crater_count = random.randint(
                20,
                40
            )

            forest_count = random.randint(
                2,
                6
            )

        #
        # Paint craters
        #
        for _ in range(
            crater_count
        ):

            x = random.randint(
                0,
                tilemap.width - 1
            )

            y = random.randint(
                0,
                tilemap.height - 1
            )

            radius = random.randint(
                1,
                2
            )

            self._paint_circle(
                tilemap,
                x,
                y,
                radius,
                "crater"
            )

        #
        # Paint forests
        #
        for _ in range(
            forest_count
        ):

            x = random.randint(
                0,
                tilemap.width - 1
            )

            y = random.randint(
                0,
                tilemap.height - 1
            )

            radius = random.randint(
                2,
                4
            )

            self._paint_circle(
                tilemap,
                x,
                y,
                radius,
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
        Paint circular terrain.
        """

        for x in range(
            center_x - radius,
            center_x + radius + 1
        ):

            for y in range(
                center_y - radius,
                center_y + radius + 1
            ):

                tile = tilemap.get_tile(
                    x,
                    y
                )

                if tile is None:
                    continue

                dx = x - center_x
                dy = y - center_y

                if (
                    dx * dx +
                    dy * dy
                    <= radius * radius
                ):

                    tile.terrain = terrain

                    #
                    # Future:
                    # terrain penalties
                    #
                    tile.walkable = True