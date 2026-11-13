"""
The PAUSED panel: dim layer + centered text stack for a frozen battle.

Pause is battle-state-OWNED (AssaultPhase flips it with SPACE / ESC);
the overlay art itself lives here so the battle state keeps only the
flag. Every surface/font is built once at construction — pausing
costs nothing per frame — and draw() recomputes only the layout
(centering + the live player tile readout).
"""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, TILE_SIZE


class PauseOverlay:
    """Owns the pause art; draw() renders the whole PAUSED panel."""

    def __init__(self):
        # Translucent dim surface so the frozen battle stays readable
        # underneath; fullscreen software blit, no per-frame churn.
        self.overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        self.overlay.fill((0, 0, 0, 140))

        # Fonts sized for the fixed layout in draw().
        self.title_font = pygame.font.SysFont("arial", 46)
        self.hint_font = pygame.font.SysFont("arial", 20)

    def draw(self, screen, player_x, player_y):
        """Draw the dim + centered PAUSED panel with resume instructions."""
        screen.blit(self.overlay, (0, 0))

        screen_w, screen_h = screen.get_size()

        # Centered text stack: title, resume hint, hard-coded controls
        # so the player always knows what is usable while frozen.
        title = self.title_font.render("PAUSED", True, WHITE)
        title_rect = title.get_rect(centerx=screen_w // 2, y=screen_h // 3)
        screen.blit(title, title_rect)

        hint = self.hint_font.render(
            "Press SPACE (or ESC) to resume",
            True,
            WHITE,
        )
        hint_rect = hint.get_rect(
            centerx=screen_w // 2,
            y=screen_h // 3 + 60,
        )
        screen.blit(hint, hint_rect)

        # Live player tile position while frozen, 1-BASED per tile
        # (floor divide; the NW-most tile is X=1, Y=1 since world x
        # in [0, TILE_SIZE) belongs to tile 1). Enables distance
        # reading against the hand-edited map markers.
        tile_x = int(player_x // TILE_SIZE) + 1
        tile_y = int(player_y // TILE_SIZE) + 1
        pos = self.hint_font.render(
            f"Player tile: X {tile_x} | Y {tile_y}",
            True,
            WHITE,
        )
        pos_rect = pos.get_rect(
            centerx=screen_w // 2,
            y=screen_h // 3 + 96,
        )
        screen.blit(pos, pos_rect)

        # Control reference while frozen: the help the user reads
        # whenever the battle is paused.
        controls = self.hint_font.render(
            "SPACE: pause/resume | +: zoom in | -: zoom out | G: graphics toggle | WASD: move",
            True,
            WHITE,
        )
        controls_rect = controls.get_rect(
            centerx=screen_w // 2,
            y=screen_h - 60,
        )
        screen.blit(controls, controls_rect)
