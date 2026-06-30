"""
systems/scenario_generator.py

Generates procedural battle scenarios.
"""

import random

from config import (
    STARTING_SUPPLIES,
    MIN_WAVES,
    MAX_WAVES
)


class Scenario:
    """
    Single procedural battle scenario.
    """

    def __init__(self):

        self.seed = random.randint(
            1,
            999999999
        )

        self.wave_count = 5

        self.weather = "clear"

        self.enemy_strength = 1.0

        self.starting_supplies = (
            STARTING_SUPPLIES
        )

        self.map_type = "trenches"

        self.scenario_number = 1


class ScenarioGenerator:
    """
    Generates battle scenarios.
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

        scenario.wave_count = random.randint(
            MIN_WAVES,
            MAX_WAVES
        )

        scenario.weather = random.choice(
            self.WEATHER_TYPES
        )

        scenario.map_type = random.choice(
            self.MAP_TYPES
        )

        scenario.starting_supplies = random.randint(
            80,
            150
        )

        #
        # Scale difficulty
        #
        scenario.enemy_strength = round(
            1.0 +
            (scenario_number * 0.15),
            2
        )

        return scenario