"""
systems/building_query.py

Utility for collecting structures
placed on the battlefield.
"""


class BuildingQuery:
    """
    Query helper for map buildings.
    """

    @staticmethod
    def get_all_buildings(tilemap):
        """
        Return every placed structure.
        """

        buildings = []

        for column in tilemap.tiles:

            for tile in column:

                if tile.building is not None:

                    buildings.append(
                        tile.building
                    )

        return buildings

    @staticmethod
    def get_buildings_of_type(
        tilemap,
        building_type
    ):
        """
        Return structures matching a type.
        """

        buildings = []

        for column in tilemap.tiles:

            for tile in column:

                if tile.building is None:
                    continue

                if isinstance(
                    tile.building,
                    building_type
                ):

                    buildings.append(
                        tile.building
                    )

        return buildings