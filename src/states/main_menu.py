"""
Main menu state.
Press ENTER to start.
"""

import pygame

from config import WHITE, BLACK
from world.tilemap import TileMap


class MainMenu:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("arial", 40)
        self.small_font = pygame.font.SysFont("arial", 25)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                from states.assault_phase import AssaultPhase

                self.game.tilemap = TileMap()
                self.game.change_state(AssaultPhase(self.game))
            if event.key == pygame.K_q:
                self.game.running = False

    def update(self, dt):
        pass

    def render(self, screen):
        screen.fill(BLACK)

        title = self.font.render("HOLD THE TRENCH", True, WHITE)
        start = self.small_font.render("Press ENTER to Start", True, WHITE)
        quit_text = self.small_font.render("Press Q to Quit", True, WHITE)

        screen.blit(title, (180, 150))
        screen.blit(start, (200, 250))
        screen.blit(quit_text, (200, 300))
