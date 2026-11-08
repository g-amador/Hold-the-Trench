"""Small geometry helpers shared by entities."""

import math


def distance_to_rect(rect, x, y):
    """Distance from a point (x, y) to the NEAREST point of a rect.

    Returns 0 when the point lies inside the rect. Used for
    wall-proximity rules — e.g. rifle infantry stop and open fire one
    tile from the enemy BUNKER'S WALL, not from its center.
    """
    dx = max(rect.left - x, 0, x - rect.right)
    dy = max(rect.top - y, 0, y - rect.bottom)
    return math.hypot(dx, dy)
