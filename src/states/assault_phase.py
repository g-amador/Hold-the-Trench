"""
states/assault_phase.py

Enemy assault phase for Hold the Trench.
"""

import pygame

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BLACK,
    WHITE
)

from src.systems.wave_director import WaveDirector
from src.systems.combat_system import CombatSystem
from src.systems.building_query import BuildingQuery
from src.systems.weather_system import WeatherSystem

from src.states.post_battle_state import PostBattleState
from src.states.game_over_state import GameOverState


class AssaultPhase:
    """
    Main combat phase.
    """

    def __init__(
        self,
        game,
        tilemap,
        economy,
        weather=None
    ):

        self.game = game

        #
        # Battlefield
        #
        self.tilemap = tilemap

        #
        # Economy
        #
        self.economy = economy

        #
        # Pause
        #
        self.paused = False

        #
        # Prevent multiple state changes
        #
        self.battle_complete = False

        #
        # Cache defenses
        #
        self.current_buildings = []

        #
        # Weather
        #
        self.weather = WeatherSystem(
            weather
        )

        #
        # Enemy waves
        #
        self.wave_director = WaveDirector()

        #
        # Combat
        #
        self.combat_system = CombatSystem()

        #
        # Font
        #
        self.font = pygame.font.SysFont(
            "Arial",
            28
        )

    def handle_event(
        self,
        event
    ):
        """
        Handle player input.
        """

        if event.type == pygame.KEYDOWN:

            #
            # Pause
            #
            if event.key == pygame.K_ESCAPE:

                self.paused = (
                    not self.paused
                )

    def update(
        self,
        delta_time
    ):
        """
        Update battle simulation.
        """

        if self.paused:
            return

        #
        # Weather
        #
        self.weather.update(
            delta_time
        )

        #
        # Waves
        #
        self.wave_director.update(
            delta_time
        )

        #
        # Buildings
        #
        self.current_buildings = (
            BuildingQuery.get_all_buildings(
                self.tilemap
            )
        )

        buildings = (
            self.current_buildings
        )

        #
        # Defeat
        #
        if (
            len(buildings) == 0
            and self.wave_director.current_wave > 0
            and not self.battle_complete
        ):

            self.battle_complete = True

            self.game.change_state(

                GameOverState(
                    self.game
                )

            )

            return

        #
        # Combat
        #
        self.combat_system.update(
            buildings,
            self.wave_director.enemies
        )

        #
        # Remove dead enemies
        #
        self.wave_director.enemies = [

            enemy

            for enemy in
            self.wave_director.enemies

            if not enemy.is_dead()

        ]

        #
        # Victory
        #
        if (
            self.wave_director.is_victory()
            and not self.battle_complete
        ):

            self.battle_complete = True

            self.game.change_state(

                PostBattleState(
                    self.game
                )

            )

    def render(
        self,
        screen
    ):
        """
        Draw combat scene.
        """

        #
        # Background
        #
        screen.fill(
            BLACK
        )

        #
        # Battlefield
        #
        self.tilemap.draw(
            screen
        )

        #
        # Enemies
        #
        self.wave_director.draw(
            screen
        )

        #
        # Weather
        #
        self.weather.draw_overlay(
            screen
        )

        #
        # Title
        #
        title = self.font.render(
            "Assault Phase",
            True,
            WHITE
        )

        screen.blit(
            title,
            (20, 20)
        )

        #
        # Wave count
        #
        wave_text = self.font.render(
            f"Wave: "
            f"{self.wave_director.current_wave}"
            f"/"
            f"{self.wave_director.total_waves}",
            True,
            WHITE
        )

        screen.blit(
            wave_text,
            (20, 60)
        )

        #
        # Supplies
        #
        supplies_text = self.font.render(
            f"Supplies: "
            f"{self.economy.supplies}",
            True,
            WHITE
        )

        screen.blit(
            supplies_text,
            (20, 100)
        )

        #
        # Enemies
        #
        enemy_text = self.font.render(
            f"Enemies: "
            f"{len(self.wave_director.enemies)}",
            True,
            WHITE
        )

        screen.blit(
            enemy_text,
            (20, 140)
        )

        #
        # Defenses
        #
        defense_text = self.font.render(
            f"Defenses: "
            f"{len(self.current_buildings)}",
            True,
            WHITE
        )

        screen.blit(
            defense_text,
            (20, 180)
        )

        #
        # Weather
        #
        weather_text = self.font.render(
            f"Weather: "
            f"{self.weather.get_description()}",
            True,
            WHITE
        )

        screen.blit(
            weather_text,
            (20, 220)
        )

        #
        # Controls
        #
        controls_text = self.font.render(
            "ESC = Pause",
            True,
            WHITE
        )

        screen.blit(
            controls_text,
            (
                20,
                SCREEN_HEIGHT - 50
            )
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

            overlay.set_alpha(
                180
            )

            overlay.fill(
                (
                    30,
                    30,
                    30
                )
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
                    SCREEN_WIDTH // 2
                    - pause_text.get_width() // 2,
                    SCREEN_HEIGHT // 2
                )
            )

        #
        # Victory banner
        #
        if self.wave_director.is_victory():

            victory_text = self.font.render(
                "VICTORY!",
                True,
                WHITE
            )

            screen.blit(
                victory_text,
                (
                    SCREEN_WIDTH // 2
                    - victory_text.get_width() // 2,
                    100
                )
            )