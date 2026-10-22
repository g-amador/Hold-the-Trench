"""
Main menu state.

Background is Menu_2_Start.jpeg (scaled once to the window, cached by
the image loader). The player picks a side with A/1 (Allies) or X/2
(Axis) and starts with ENTER (Q quits). The chosen side is stored on
Game.selected_faction and drives every texture decision downstream
(single source: systems/factions.py).
"""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GREY
from utils.image_loader import load_image
from systems.factions import (
    FACTIONS,
    MENU_BACKGROUND,
)
from world.tilemap import TileMap


class MainMenu:
    def __init__(self, game):
        # Keep the Game reference so the menu can switch states and
        # rebuild the shared world.
        self.game = game
        self.font = pygame.font.SysFont("arial", 40)
        self.small_font = pygame.font.SysFont("arial", 25)

        # Preload the faction menu background once: window-sized scaled
        # copy, cached by image_loader.
        self.background = load_image(
            MENU_BACKGROUND,
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

        # Selection is menu-local; it is promoted to game.selected_faction
        # only when a battle actually starts (backing out keeps whatever
        # side was last played).
        self.selected = "allies"

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        # Side selection: mnemonic A/X plus number shortcuts. The
        # labels in FACTIONS render these same keys as hints.
        if event.key in (pygame.K_a, pygame.K_1):
            self.selected = "allies"
        elif event.key in (pygame.K_x, pygame.K_2):
            self.selected = "axis"
        elif event.key == pygame.K_RETURN:
            # Imported here (not top-level) to avoid a circular
            # import: assault_phase imports states it can switch to.
            from states.assault_phase import AssaultPhase

            # Promote the choice before constructing anything: spawn
            # clocks, textures, and coin drops all read it.
            self.game.selected_faction = self.selected

            # Fresh world per battle so existing buildings/pays from a
            # previous fight never carry over.
            self.game.tilemap = TileMap()

            self.game.change_state(AssaultPhase(self.game))
        elif event.key == pygame.K_q:
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
        prompt = self.small_font.render("Choose your side:", True, WHITE)

        screen.blit(title, (180, 150))
        screen.blit(prompt, (200, 250))

        # Faction options: the picked line is bright, the other dimmed.
        for row, (faction_id, data) in enumerate(FACTIONS.items()):
            selected = faction_id == self.selected
            color = WHITE if selected else GREY
            marker = "> " if selected else "  "
            option = self.small_font.render(
                f"{marker}{data['label']}",
                True,
                color,
            )
            screen.blit(option, (220, 300 + row * 35))

        quit_text = self.small_font.render(
            "ENTER to start | Q to Quit",
            True,
            WHITE,
        )
        screen.blit(quit_text, (220, 390))
