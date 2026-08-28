"""
engine/game.py

Main game controller for Hold the Trench.
"""

import pygame

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GAME_TITLE,
    FPS
)

from engine.asset_manager import AssetManager
from states.main_menu import MainMenu


class Game:
    """
    Main game controller.
    """

    def __init__(self):
        """
        Initialize the game.
        """

        #
        # Initialize pygame
        #
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()

        #
        # Window
        #
        self.screen = pygame.display.set_mode(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT
            )
        )

        pygame.display.set_caption(
            GAME_TITLE
        )

        #
        # Timing
        #
        self.clock = pygame.time.Clock()

        self.delta_time = 0

        #
        # Running state
        #
        self.running = True

        #
        # Asset manager
        #
        self.assets = AssetManager()

        #
        # Current game state
        #
        self.current_state = MainMenu(
            self
        )

    def change_state(
        self,
        new_state
    ):
        """
        Change active game state.
        """

        self.current_state = new_state

    def handle_events(
        self
    ):
        """
        Handle pygame events.
        """

        for event in pygame.event.get():

            #
            # Window close
            #
            if event.type == pygame.QUIT:

                self.running = False

                return

            #
            # Forward to active state
            #
            self.current_state.handle_event(
                event
            )

    def update(
        self
    ):
        """
        Update active state.
        """

        self.current_state.update(
            self.delta_time
        )

    def render(
        self
    ):
        """
        Render active state.
        """

        self.current_state.render(
            self.screen
        )

        pygame.display.flip()

    def run(
        self
    ):
        """
        Main game loop.
        """

        while self.running:

            #
            # Frame timing
            #
            self.delta_time = (
                self.clock.tick(
                    FPS
                ) / 1000.0
            )

            #
            # Input
            #
            self.handle_events()

            #
            # Simulation
            #
            self.update()

            #
            # Rendering
            #
            self.render()

        self.shutdown()

    def shutdown(
        self
    ):
        """
        Cleanup.
        """

        try:

            self.assets.unload_all()

        except Exception:
            pass

        pygame.quit()