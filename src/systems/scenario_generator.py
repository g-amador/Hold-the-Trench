"""
systems/scenario_generator.py

Procedural battle scenario generation
for Hold the Trench.
"""

import random

from src.config import (
    STARTING_SUPPLIES,
    MIN_WAVES,
    MAX_WAVES
)


class Scenario:
    """
    Represents one battle scenario.
    """

    def __init__(self):

        #
        # Identity
        #
        self.seed = random.randint(
            1,
            999999999
        )

        self.scenario_number = 1

        #
        # Battle settings
        #
        self.wave_count = 5

        self.enemy_strength = 1.0

        self.starting_supplies = (
            STARTING_SUPPLIES
        )

        #
        # Environment
        #
        self.weather = "clear"

        self.map_type = "trenches"

        #
        # Future modifiers
        #
        self.visibility_modifier = 1.0

        self.movement_modifier = 1.0


class ScenarioGenerator:
    """
    Generates procedural battles.
    """

    WEATHER_TYPES = [
        "clear",
        "fog",
        "rain"
    ]

    MAP_TYPES = [
        "trenches",
        "forest",
        "craters"
    ]

    def generate(
        self,
        scenario_number=1
    ):
        """
        Generate a scenario.
        """

        scenario = Scenario()

        scenario.scenario_number = (
            scenario_number
        )

        #
        # Waves
        #
        scenario.wave_count = (
            random.randint(
                MIN_WAVES,
                MAX_WAVES
            )
        )

        #
        # Environment
        #
        scenario.weather = (
            random.choice(
                self.WEATHER_TYPES
            )
        )

        scenario.map_type = (
            random.choice(
                self.MAP_TYPES
            )
        )

        #
        # Supplies
        #
        scenario.starting_supplies = (
            random.randint(
                80,
                150
            )
        )

        #
        # Difficulty scaling
        #
        scenario.enemy_strength = round(
            1.0 +
            (
                scenario_number
                * 0.15
            ),
            2
        )

        #
        # Weather effects
        #
        if scenario.weather == "fog":

            scenario.visibility_modifier = (
                0.60
            )

        elif scenario.weather == "rain":

            scenario.movement_modifier = (
                0.80
            )

        return scenario