"""
systems/economy_system.py

Handles player supplies and resource spending.
"""

from src.config import (
    STARTING_SUPPLIES,
    SUPPLIES_PER_WAVE
)


class EconomySystem:
    """
    Tracks the player's supplies.
    """

    def __init__(self):
        """
        Initialize the player's economy.
        """

        self.supplies = STARTING_SUPPLIES

    def can_afford(self, amount):
        """
        Check whether the player has enough supplies.
        """

        return self.supplies >= amount

    def spend(self, amount):
        """
        Spend supplies.

        Returns True if successful,
        False otherwise.
        """

        if not self.can_afford(amount):
            return False

        self.supplies -= amount

        return True

    def earn(self, amount):
        """
        Add supplies.
        """

        self.supplies += amount

    def reward_wave_completion(self):
        """
        Reward the player after surviving a wave.
        """

        self.earn(SUPPLIES_PER_WAVE)

    def reset(self):
        """
        Reset economy for a new scenario.
        """

        self.supplies = STARTING_SUPPLIES