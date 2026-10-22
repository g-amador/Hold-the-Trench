"""
Win state: shown when every enemy bunker is destroyed.

Background keys off the played faction (victory shows the winner's
banner). R replays the same side, S switches faction for the next
battle, Q quits. All three restart through a fresh TileMap so no
buildings or wage bookkeeping leak between fights.
"""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE
from utils.image_loader import load_image
from systems.factions import VICTORY_BACKGROUND
from world.tilemap import TileMap


class WinState:
    def __init__(self, game):
        # Keep the reference so this screen can switch states.
        self.game = game
        self.font = pygame.font.SysFont("arial", 40)
        self.small_font = pygame.font.SysFont("arial", 25)

        # Faction-keyed victory art: allies win under the french
        # banner, axis under the german one (single source table).
        self.background = load_image(
            VICTORY_BACKGROUND[game.selected_faction],
            alpha=False,
            size=(SCREEN_WIDTH, SCREEN_HEIGHT),
        )

        # Text readability wash, built once per state construction.
        self.text_wash = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        self.text_wash.fill((0, 0, 0, 110))

    def _restart(self, faction=None):
        """Rebuild the world and drop into a battle.

        faction=None replays the same side; passing a faction switches
        sides for the next battle. Selecting here replicates the menu's
        start: fresh tilemap first, then the new battle state.
        """
        from states.assault_phase import AssaultPhase

        if faction is not None:
            self.game.selected_faction = faction

        self.game.tilemap = TileMap()
        self.game.change_state(AssaultPhase(self.game))

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_r:
            # Play again with the SAME faction (no menu round-trip).
            self._restart()
        elif event.key == pygame.K_s:
            # Switch to the other faction for the next battle.
            from systems.factions import other

            self._restart(other(self.game.selected_faction))
        elif event.key == pygame.K_q:
            self.game.running = False

    def update(self, dt):
        # Static screen: nothing to simulate.
        pass

    def render(self, screen):
        # Background: faction banner + readability wash.
        screen.blit(self.background, (0, 0))
        screen.blit(self.text_wash, (0, 0))

        text = self.font.render("YOU WIN!", True, WHITE)
        replay = self.small_font.render(
            "R: Play again (same side)",
            True,
            WHITE,
        )
        switch = self.small_font.render(
            "S: Switch faction",
            True,
            WHITE,
        )
        quit_text = self.small_font.render("Q: Quit", True, WHITE)

        screen.blit(text, (200, 150))
        screen.blit(replay, (200, 250))
        screen.blit(switch, (200, 300))
        screen.blit(quit_text, (200, 350))
