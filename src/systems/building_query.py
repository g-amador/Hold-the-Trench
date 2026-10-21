"""
Utility functions to query buildings from the tilemap.

Buildings are stored on Tile objects (tile.building), so any "list the
buildings" question is answered by flattening the tile grid. These
helpers are how the battle state and HUD avoid touching tile internals.
"""

from collections import Counter


class BuildingQuery:
    @staticmethod
    def get_all_buildings(tilemap):
        """Return every building on the grid as a flat list.

        Scans the full 2D grid, skipping empty tiles and tiles with no
        building attached. Grid size is small, so the linear scan is
        cheap enough to run once per simulation frame.
        """
        buildings = []
        for y in range(tilemap.height):
            for x in range(tilemap.width):
                tile = tilemap.get_tile(x, y)
                if tile and tile.building:
                    buildings.append(tile.building)
        return buildings

    @staticmethod
    def count_buildings(tilemap):
        """Return building counts keyed by class name, for the HUD legend.

        Uses the class display name as the key, which is why MG nests
        show up as "MGNest" in the builds list.
        """
        counts = Counter()
        for y in range(tilemap.height):
            for x in range(tilemap.width):
                tile = tilemap.get_tile(x, y)
                if tile and tile.building:
                    counts[type(tile.building).__name__] += 1
        return counts
