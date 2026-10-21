"""
Main menu state.

Background is the serialized Startmenu image (scaled once to the
window, cached by the image loader). Press ENTER to start a battle, Q
to quit.
"""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE
from utils.image_loader import load_image
from world.tilemap import TileMap


class MainMenu:
    def __init__(self, game):
        # Keep the Game reference so the menu can switch states and
        # rebuild the shared world.
        self.game = game
        self.font = pygame.font.SysFont("arial", 40)
        self.small_font = pygame.font.SysFont("arial", 25)

        # Preload the background once: window-sized scaled copy, cached
        # by image_loader so every state shares the same surface.
        self.background = load_image(
            "Startmenu.jpeg",
            alpha=False,
            size=(SCREEN_WIDTH, SCREEN_HEIGHT),
        )

        # Translucent wash for text readability over the photo,
        # built once here (building it per frame would churn).
        self.text_wash = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        self.text_wash.fill((0, 0, 0, 110))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Imported here (not top-level) to avoid a circular
                # import: assault_phase imports states it can switch to.
                from states.assault_phase import AssaultPhase

                # Fresh world per battle so existing buildings/pays
                # from a previous fight never carry over.
                self.game.tilemap = TileMap()

                self.game.change_state(AssaultPhase(self.game))
            if event.key == pygame.K_q:
                # Ending the loop from the menu quits the process cleanly.
                self.game.running = False

    def update(self, dt):
        # Static screen: no simulated elements yet.
        pass

    def render(self, screen):
        # Background: static image covers the whole window; the wash
        # dims it slightly so the white text stays readable.
        screen.blit(self.background, (0, 0))
        screen.blit(self.text_wash, (0, 0))

        title = self.font.render("HOLD THE TRENCH", True, WHITE)
        start = self.small_font.render("Press ENTER to Start", True, WHITE)
        quit_text = self.small_font.render("Press Q to Quit", True, WHITE)

        screen.blit(title, (180, 150))
        screen.blit(start, (200, 250))
        screen.blit(quit_text, (200, 300))
