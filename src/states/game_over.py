"""
Game Over state.
Player can restart or quit.
"""

import pygame
from config import WHITE, BLACK


class GameOverState:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("arial", 40)
        self.small_font = pygame.font.SysFont("arial", 25)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                from states.main_menu import MainMenu
                self.game.change_state(MainMenu(self.game))
            if event.key == pygame.K_q:
                self.game.running = False

    def update(self, dt):
        pass

    def render(self, screen):
        screen.fill(BLACK)

        text = self.font.render("GAME OVER", True, WHITE)
        restart = self.small_font.render("Press R to Restart", True, WHITE)
        quit_text = self.small_font.render("Press Q to Quit", True, WHITE)

        screen.blit(text, (200, 150))
        screen.blit(restart, (200, 250))
        screen.blit(quit_text, (200, 300))
