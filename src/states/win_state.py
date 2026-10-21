"""
Win state: shown when every enemy bunker is destroyed.

Background is the serialized Startmenu image (scaled once to the
window, cached by the image loader). R returns to the main menu
(which rebuilds the world for a fresh battle); Q quits the application.
"""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE
from utils.image_loader import load_image
from states.main_menu import MainMenu


class WinState:
    def __init__(self, game):
        # Keep the reference so this screen can switch states.
        self.game = game
        self.font = pygame.font.SysFont("arial", 40)
        self.small_font = pygame.font.SysFont("arial", 25)

        # Same background surface as the other static screens: the
        # image loader cache makes these constructions share it.
        self.background = load_image(
            "Startmenu.jpeg",
            alpha=False,
            size=(SCREEN_WIDTH, SCREEN_HEIGHT),
        )

        # Text readability wash, built once per state construction.
        self.text_wash = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        self.text_wash.fill((0, 0, 0, 110))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Back through the menu: starting a new battle there
                # rebuilds the world, so no stale buildings remain.
                self.game.change_state(MainMenu(self.game))
            if event.key == pygame.K_q:
                self.game.running = False

    def update(self, dt):
        # Static screen: nothing to simulate.
        pass

    def render(self, screen):
        # Background: static image + readability wash, like the menus.
        screen.blit(self.background, (0, 0))
        screen.blit(self.text_wash, (0, 0))

        text = self.font.render("YOU WIN!", True, WHITE)
        restart = self.small_font.render("Press R to Restart", True, WHITE)
        quit_text = self.small_font.render("Press Q to Quit", True, WHITE)

        screen.blit(text, (200, 150))
        screen.blit(restart, (200, 250))
        screen.blit(quit_text, (200, 300))
