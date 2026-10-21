"""
Block-mode rendering helpers.

Used when the graphics toggle (graphics/render_mode.py) is in block
mode, and as the automatic fallback whenever sprite assets are missing
so the game still renders instead of crashing.
"""

import pygame


# Dark marker contrast color; picked against both ally/enemy body colors.
_MARKER_COLOR = (20, 20, 20)


def draw_unit_block(screen, x, y, width, height, facing, color):
    """Draw a unit as a flat block with a dark marker on its facing edge.

    The marker sits on the side the unit is moving/aiming toward
    (facing 1 = right edge, -1 = left edge), so direction is readable
    even without sprites.
    """
    px = round(x)
    py = round(y)

    # Body block: the unit's logical footprint.
    pygame.draw.rect(screen, color, (px, py, width, height))

    # Marker sized ~1/3 of the body (min 6px) so small units remain
    # readable.
    marker = max(6, width // 3)
    marker_x = px + width - marker if facing == 1 else px
    pygame.draw.rect(screen, _MARKER_COLOR, (marker_x, py, marker, marker))
