"""
HUD drawing: bunker HP, gold balance, the two-column force counts
panel (player X/Y buildables + enemy totals), graphics-mode label,
and reusable text helpers.

The HUD is dumb by design: the battle state computes all values and
passes them in; the HUD only formats and blits.
"""

import pygame

from config import WHITE, BLACK, SCREEN_WIDTH, HUD_BAR_HEIGHT


class HUD:
    def __init__(self):
        # One font per HUD instance; texts are rendered every frame,
        # which pygame can handle easily at this text volume.
        self.font = pygame.font.SysFont("arial", 20)

    def draw(self, screen, bunker_hp, gold, graphics_label="", view_label="", fps=None):
        """Draw the top status bar: bunker HP, gold, frames rate, mode.

        graphics_label is the current sprite/block mode name from
        graphics.render_mode; view_label is the current zoom view
        (config VIEW_FULL/VIEW_CLOSE) shown after the pause info;
        fps is the battle's smoothed frames-per-second (None hides
        it); empty labels hide their indicator.
        """
        # Full-width bar sized by config: the battle renderer reserves
        # exactly this strip between HUD and world view.
        pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, HUD_BAR_HEIGHT))

        bunker_text = self.font.render(f"Bunker HP: {bunker_hp}", True, WHITE)
        gold_text = self.font.render(f"Gold: {gold}", True, WHITE)

        screen.blit(bunker_text, (50, 5))
        screen.blit(gold_text, (250, 5))

        # FPS readout (user request): right after the gold balance, so
        # the performance number is always visible during play.
        if fps is not None:
            fps_text = self.font.render(f"FPS: {fps}", True, WHITE)
            screen.blit(fps_text, (430, 5))

        # Right-aligned combined hint, permanently visible: the pause
        # control reference, the +/- zoom view (per user: right after
        # the pause info), then the current graphics mode label.
        if graphics_label:
            hint = f"SPACE: pause"
            if view_label:
                hint += f" | +/-: view {view_label}"
            hint += f" | G: {graphics_label}"
            mode_text = self.font.render(hint, True, WHITE)
            screen.blit(
                mode_text,
                (SCREEN_WIDTH - mode_text.get_width() - 10, 5),
            )

    def draw_building_counts(self, screen, counts):
        """List built buildings starting under the status bar, one per row.

        Legacy simple table; the battle panel now uses draw_force_counts.
        """
        x = 10
        y = 40

        for name, count in counts.items():
            text = self.font.render(f"{name}: {count}", True, WHITE)
            screen.blit(text, (x, y))
            y += 20

    def draw_force_counts(self, screen, rows):
        """Two-column force summary under the status bar.

        rows is a list of (name, player_text, enemy_text); the battle
        state computes every value (X/Y limits included) so the HUD
        stays a dumb renderer. Player counts anchor at the far LEFT
        edge; enemy counts right-align at the FAR RIGHT edge so the
        two sides read as opposite ends of the battlefield. One row
        per entry.
        """
        x_player = 10  # far-left anchor
        y = 45

        for name, player_text, enemy_text in rows:
            left = self.font.render(f"{name}: {player_text}", True, WHITE)
            right = self.font.render(
                f"Enemy {name}: {enemy_text}",
                True,
                WHITE,
            )
            screen.blit(left, (x_player, y))

            # Right-aligned: 10px inside the far right edge, mirroring
            # the left column's margin.
            screen.blit(
                right,
                (SCREEN_WIDTH - right.get_width() - 10, y),
            )
            y += 20

    def draw_text(self, screen, text, x, y):
        """Convenience one-liner for overlay text anywhere on screen."""
        surf = self.font.render(text, True, WHITE)
        screen.blit(surf, (x, y))
