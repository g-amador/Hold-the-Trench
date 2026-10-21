"""
HUD drawing: bunker HP, gold balance, building counts, graphics-mode
label, and reusable text helpers.

The HUD is dumb by design: the battle state computes all values and
passes them in; the HUD only formats and blits.
"""

import pygame

from config import WHITE, BLACK, SCREEN_WIDTH


class HUD:
    def __init__(self):
        # One font per HUD instance; texts are rendered every frame,
        # which pygame can handle easily at this text volume.
        self.font = pygame.font.SysFont("arial", 20)

    def draw(self, screen, bunker_hp, gold, graphics_label=""):
        """Draw the top status bar: bunker HP, gold, and graphics mode.

        graphics_label is the current sprite/block mode name from
        graphics.render_mode; empty hides the indicator.
        """
        # Full-width dark bar so the numbers read against any terrain.
        pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, 40))

        bunker_text = self.font.render(f"Bunker HP: {bunker_hp}", True, WHITE)
        gold_text = self.font.render(f"Gold: {gold}", True, WHITE)

        screen.blit(bunker_text, (50, 5))
        screen.blit(gold_text, (250, 5))

        # Right-aligned combined hint, permanently visible: the pause
        # control reference plus the current graphics mode label.
        if graphics_label:
            mode_text = self.font.render(
                f"SPACE: pause | G: {graphics_label}",
                True,
                WHITE,
            )
            screen.blit(
                mode_text,
                (SCREEN_WIDTH - mode_text.get_width() - 10, 5),
            )

    def draw_building_counts(self, screen, counts):
        """List built buildings starting under the status bar, one per row."""
        x = 10
        y = 40

        for name, count in counts.items():
            text = self.font.render(f"{name}: {count}", True, WHITE)
            screen.blit(text, (x, y))
            y += 20

    def draw_text(self, screen, text, x, y):
        """Convenience one-liner for overlay text anywhere on screen."""
        surf = self.font.render(text, True, WHITE)
        screen.blit(surf, (x, y))
