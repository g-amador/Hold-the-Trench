"""
HUD drawing: gold, building counts, bunker HP, and legend with cost.
"""

import pygame

from config import WHITE, BLACK, SCREEN_WIDTH


class HUD:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 20)

    def draw(self, screen, bunker_hp, gold):
        pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, 40))
        
        bunker_text = self.font.render(f"Bunker HP: {bunker_hp}", True, WHITE)
        gold_text = self.font.render(f"Gold: {gold}", True, WHITE)        
        
        screen.blit(bunker_text, (50, 5))
        screen.blit(gold_text, (250, 5))

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
