"""
states/prep_phase.py

Preparation phase of Hold the Trench.

Players build defenses before the assault begins.
"""

import pygame

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BLACK,
    WHITE,
    PREP_TIME_SECONDS
)

from world.tilemap import TileMap
from world.map_generator import MapGenerator

from systems.building_system import BuildingSystem
from systems.economy_system import EconomySystem

from states.assault_phase import AssaultPhase


class PrepPhase:
    """
    Preparation state.
    """

    def __init__(self, game):

        self.game = game

        #
        # Timer
        #
        self.time_remaining = PREP_TIME_SECONDS

        #
        # Pause state
        #
        self.paused = False

        #
        # Battlefield
        #
        self.tilemap = TileMap()

        MapGenerator().generate(
            self.tilemap
        )

        #
        # Economy
        #
        self.economy = EconomySystem()

        #
        # Building system
        #
        self.building_system = BuildingSystem()

        #
        # Font
        #
        self.font = pygame.font.SysFont(
            "Arial",
            28
        )

    def handle_event(self, event):
        """
        Process player input.
        """

        if event.type == pygame.KEYDOWN:

            #
            # Pause
            #
            if event.key == pygame.K_ESCAPE:

                self.paused = not self.paused

                return

            #
            # Start Assault
            #
            if event.key == pygame.K_RETURN:

                self.game.change_state(

                    AssaultPhase(
                        self.game,
                        self.tilemap,
                        self.economy
                    )

                )

                return

        #
        # Building input
        #
        if not self.paused:

            self.building_system.handle_event(
                event,
                self.tilemap,
                self.economy
            )

    def update(self, delta_time):
        """
        Update prep phase.
        """

        if self.paused:
            return

        #
        # Countdown
        #
        self.time_remaining -= delta_time

        #
        # Auto-start assault
        #
        if self.time_remaining <= 0:

            self.game.change_state(

                AssaultPhase(
                    self.game,
                    self.tilemap,
                    self.economy
                )

            )

    def render(self, screen):
        """
        Draw prep phase.
        """

        screen.fill(BLACK)

        #
        # Battlefield
        #
        self.tilemap.draw(screen)

        #
        # Title
        #
        title = self.font.render(
            "Preparation Phase",
            True,
            WHITE
        )

        screen.blit(
            title,
            (20, 20)
        )

        #
        # Timer
        #
        timer = self.font.render(
            f"Time Remaining: {int(self.time_remaining)}",
            True,
            WHITE
        )

        screen.blit(
            timer,
            (20, 60)
        )

        #
        # Supplies
        #
        supplies = self.font.render(
            f"Supplies: {self.economy.supplies}",
            True,
            WHITE
        )

        screen.blit(
            supplies,
            (20, 100)
        )

        #
        # Selected building
        #
        selected = self.font.render(
            f"Selected: {self.building_system.selected_building}",
            True,
            WHITE
        )

        screen.blit(
            selected,
            (20, 140)
        )

        #
        # Controls
        #
        controls = self.font.render(
            "1=Trench  2=MG Nest  ENTER=Start Assault  ESC=Pause",
            True,
            WHITE
        )

        screen.blit(
            controls,
            (20, SCREEN_HEIGHT - 50)
        )

        #
        # Pause overlay
        #
        if self.paused:

            overlay = pygame.Surface(
                (
                    SCREEN_WIDTH,
                    SCREEN_HEIGHT
                )
            )

            overlay.set_alpha(180)

            overlay.fill(
                (30, 30, 30)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            pause_text = self.font.render(
                "PAUSED",
                True,
                WHITE
            )

            screen.blit(
                pause_text,
                (
                    SCREEN_WIDTH // 2 - 70,
                    SCREEN_HEIGHT // 2
                )
            )