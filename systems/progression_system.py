"""
systems/progression_system.py

Campaign progression system for Hold the Trench.
"""

import random


class ProgressionSystem:
    """
    Handles progression through
    procedurally generated scenarios.
    """

    def __init__(self):

        #
        # Current scenario
        #
        self.scenario_number = 1

        #
        # Difficulty multiplier
        #
        self.difficulty_multiplier = 1.0

        #
        # Consecutive victories
        #
        self.victories = 0

        #
        # Total enemies defeated
        #
        self.total_kills = 0

        #
        # Total supplies earned
        #
        self.total_supplies = 0

    def complete_scenario(
        self,
        enemies_killed=0,
        supplies_earned=0
    ):
        """
        Advance campaign.
        """

        self.victories += 1

        self.total_kills += (
            enemies_killed
        )

        self.total_supplies += (
            supplies_earned
        )

        self.scenario_number += 1

        #
        # Increase difficulty
        #
        self.difficulty_multiplier = (
            1.0 +
            (self.scenario_number - 1)
            * 0.15
        )

    def get_enemy_multiplier(
        self
    ):
        """
        Enemy stat scaling.
        """

        return (
            self.difficulty_multiplier
        )

    def get_wave_count(
        self
    ):
        """
        Number of waves.
        """

        return min(
            3 + self.scenario_number,
            20
        )

    def get_starting_supplies(
        self
    ):
        """
        Supplies for scenario.
        """

        base = 100

        bonus = (
            self.scenario_number
            * 5
        )

        return (
            base + bonus
        )

    def reset(
        self
    ):
        """
        Reset campaign.
        """

        self.scenario_number = 1

        self.difficulty_multiplier = 1.0

        self.victories = 0

        self.total_kills = 0

        self.total_supplies = 0

    def generate_seed(
        self
    ):
        """
        Generate scenario seed.
        """

        return random.randint(
            1,
            999999999
        )

    def get_summary(
        self
    ):
        """
        Return campaign statistics.
        """

        return {

            "scenario":
                self.scenario_number,

            "victories":
                self.victories,

            "kills":
                self.total_kills,

            "supplies":
                self.total_supplies,

            "difficulty":
                round(
                    self.difficulty_multiplier,
                    2
                )
        }