"""
Utility functions to query buildings from the tilemap.
"""

from collections import Counter


class BuildingQuery:
    @staticmethod
    def get_all_buildings(tilemap):
        buildings = []
        for y in range(tilemap.height):
            for x in range(tilemap.width):
                tile = tilemap.get_tile(x, y)
                if tile and tile.building:
                    buildings.append(tile.building)
        return buildings

    @staticmethod
    def count_buildings(tilemap):
        counts = Counter()
        for y in range(tilemap.height):
            for x in range(tilemap.width):
                tile = tilemap.get_tile(x, y)
                if tile and tile.building:
                    counts[type(tile.building).__name__] += 1
        return counts
