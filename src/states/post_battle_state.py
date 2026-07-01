"""
states/post_battle_state.py

Displayed after a battle is completed.
"""

import pygame

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BLACK,
    WHITE
)

from src.systems.scenario_generator import (
    ScenarioGenerator
)

from src.states.prep_phase import (
    PrepPhase
)


class PostBattleState:
    """
    Post battle menu.
    """

    def __init__(
        self,
        game,
        scenario_number=1
    ):

        self.game = game

        self.scenario_number = (
            scenario_number
        )

        self.selected_index = 0

        self.options = [

            "Continue Campaign",

            "Generate New Scenario",

            "Exit Game"

        ]

        self.font = pygame.font.SysFont(
            "Arial",
            36
        )

        self.title_font = (
            pygame.font.SysFont(
                "Arial",
                48
            )
        )

    def handle_event(
        self,
        event
    ):

        if event.type != pygame.KEYDOWN:
            return

        #
        # Move selection
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
        # Continue campaign
        #
        if choice == (
            "Continue Campaign"
        ):

            scenario = (
                ScenarioGenerator()
                .generate()
            )

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

            scenario = (
                ScenarioGenerator()
                .generate()
            )

            self.game.change_state(

                PrepPhase(
                    self.game
                )

            )

        #
        # Exit game
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
        title = (
            self.title_font.render(
                "Victory!",
                True,
                WHITE
            )
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
        # Scenario counter
        #
        scenario_text = (
            self.font.render(
                f"Scenario "
                f"{self.scenario_number}"
                f" Completed",
                True,
                WHITE
            )
        )

        screen.blit(
            scenario_text,
            (
                SCREEN_WIDTH // 2
                - scenario_text.get_width() // 2,
                200
            )
        )

        #
        # Menu options
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
        help_text = (
            self.font.render(
                "UP/DOWN = Select | ENTER = Confirm",
                True,
                WHITE
            )
        )

        screen.blit(
            help_text,
            (
                SCREEN_WIDTH // 2
                - help_text.get_width() // 2,
                SCREEN_HEIGHT - 80
            )
        )