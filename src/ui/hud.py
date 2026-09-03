"""
HUD drawing: supplies, wave info, building counts, bunker HP, and legend with cost.
"""

import pygame
from config import WHITE, BLACK, SCREEN_WIDTH


class HUD:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 20)

    def draw(self, screen, supplies, wave_number, total_waves, bunker_hp, total_cost, spent_cost):
        pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, 40))

        supplies_text = self.font.render(f"Supplies: {supplies}", True, WHITE)
        wave_text = self.font.render(f"Wave: {wave_number}/{total_waves}", True, WHITE)
        bunker_text = self.font.render(f"Bunker HP: {bunker_hp}", True, WHITE)
        gold_text = self.font.render(f"Gold: {supplies}", True, WHITE)
        legend = self.font.render("Green squares: MG / Barracks / Artillery spots", True, WHITE)

        screen.blit(supplies_text, (10, 5))
        screen.blit(wave_text, (200, 5))
        screen.blit(bunker_text, (350, 5))
        screen.blit(gold_text, (550, 5))
        screen.blit(legend, (10, 22))

    def draw_building_counts(self, screen, counts):
        x = 10
        y = 40

        for name, count in counts.items():
            text = self.font.render(f"{name}: {count}", True, WHITE)
            screen.blit(text, (x, y))
            y += 20

    def draw_text(self, screen, text, x, y):
        surf = self.font.render(text, True, WHITE)
        screen.blit(surf, (x, y))
