"""
Main menu state.
Displays a simple menu and starts the AssaultPhase when the player presses a key.
"""

import pygame
from config import WHITE, BLACK, SCREEN_WIDTH, SCREEN_HEIGHT
from states.assault_phase import AssaultPhase


class MainMenu:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("arial", 32)

    def handle_event(self, event):
        # Start game on any key press
        if event.type == pygame.KEYDOWN:
            self.game.change_state(AssaultPhase(self.game))

    def update(self, dt):
        # No logic needed for a simple static menu
        pass

    def render(self, screen):
        screen.fill(BLACK)

        title = self.font.render("Hold the Trench", True, WHITE)
        prompt = self.font.render("Press any key to start", True, WHITE)

        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
        screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 250))
