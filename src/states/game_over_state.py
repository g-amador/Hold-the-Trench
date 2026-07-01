"""
states/game_over_state.py

Defeat screen for Hold the Trench.
"""

import pygame

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BLACK,
    WHITE
)

from src.states.prep_phase import PrepPhase


class GameOverState:
    """
    Displayed when the player loses.
    """

    def __init__(
        self,
        game
    ):

        self.game = game

        self.selected_index = 0

        self.options = [

            "Retry Scenario",

            "Generate New Scenario",

            "Exit Game"

        ]

        self.title_font = pygame.font.SysFont(
            "Arial",
            48
        )

        self.font = pygame.font.SysFont(
            "Arial",
            36
        )

    def handle_event(
        self,
        event
    ):

        if event.type != pygame.KEYDOWN:
            return

        #
        # Navigate
        #
        if event.key == pygame.K_UP:

            self.selected_index -= 1

            if self.selected_index < 0:

                self.selected_index = (
                    len(self.options) - 1
                )

        elif event.key == pygame.K_DOWN:

            self.selected_index += 1

            if self.selected_index >= len(
                self.options
            ):

                self.selected_index = 0

        #
        # Confirm
        #
        elif event.key == pygame.K_RETURN:

            self.activate_option()

    def activate_option(
        self
    ):
        """
        Execute selected action.
        """

        choice = self.options[
            self.selected_index
        ]

        #
        # Retry
        #
        if choice == (
            "Retry Scenario"
        ):

            self.game.change_state(

                PrepPhase(
                    self.game
                )

            )

        #
        # New scenario
        #
        elif choice == (
            "Generate New Scenario"
        ):

            self.game.change_state(

                PrepPhase(
                    self.game
                )

            )

        #
        # Exit
        #
        elif choice == (
            "Exit Game"
        ):

            self.game.running = False

    def update(
        self,
        delta_time
    ):
        pass

    def render(
        self,
        screen
    ):

        screen.fill(
            BLACK
        )

        #
        # Title
        #
        title = self.title_font.render(
            "DEFEAT",
            True,
            WHITE
        )

        screen.blit(
            title,
            (
                SCREEN_WIDTH // 2
                - title.get_width() // 2,
                120
            )
        )

        #
        # Subtitle
        #
        subtitle = self.font.render(
            "The trench line has fallen.",
            True,
            WHITE
        )

        screen.blit(
            subtitle,
            (
                SCREEN_WIDTH // 2
                - subtitle.get_width() // 2,
                200
            )
        )

        #
        # Options
        #
        for index, option in enumerate(
            self.options
        ):

            prefix = (
                "> "
                if index ==
                self.selected_index
                else "  "
            )

            text = self.font.render(
                prefix + option,
                True,
                WHITE
            )

            screen.blit(
                text,
                (
                    SCREEN_WIDTH // 2
                    - text.get_width() // 2,
                    320 + index * 60
                )
            )

        #
        # Controls
        #
        controls = self.font.render(
            "UP/DOWN = Select | ENTER = Confirm",
            True,
            WHITE
        )

        screen.blit(
            controls,
            (
                SCREEN_WIDTH // 2
                - controls.get_width() // 2,
                SCREEN_HEIGHT - 80
            )
        )