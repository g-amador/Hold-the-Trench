"""
HUD drawing: supplies, wave info, building counts.
"""

import pygame
from config import WHITE, BLACK, SCREEN_WIDTH


class HUD:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 20)

    def draw(self, screen, supplies, wave_number, total_waves):
        """
        Draw basic HUD: supplies and wave info.
        """
        # Background bar
        pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, 40))

        supplies_text = self.font.render(f"Supplies: {supplies}", True, WHITE)
        wave_text = self.font.render(f"Wave: {wave_number}/{total_waves}", True, WHITE)

        screen.blit(supplies_text, (10, 10))
        screen.blit(wave_text, (200, 10))

    def draw_building_counts(self, screen, counts):
        """
        Draw building counts on the HUD.
        """
        x = 400
        y = 10

        for name, count in counts.items():
            text = self.font.render(f"{name}: {count}", True, WHITE)
            screen.blit(text, (x, y))
            y += 20
