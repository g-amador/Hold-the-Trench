"""
Economy system: holds the player's gold balance.

Deliberately tiny on purpose: the gold source is gold pickups from
defeated enemies, spending happens through spend(), and partial
payments toward buildings are tracked per tile by the battle state in
tilemap.paid_amount (costs come from config.BUILD_COSTS).
"""

# Single source of truth for build costs is config.py. This module
# re-exports it so existing `from systems.economy_system import
# BUILD_COSTS` imports keep working.
from config import BUILD_COSTS  # noqa: F401


class EconomySystem:
    def __init__(self):
        # Starting balance, tuned to let the player afford one building
        # or a few partial payments early on.
        self.gold = 50

    def spend(self, cost):
        """Deduct gold, floored at zero so the balance never goes negative."""
        self.gold = max(0, self.gold - cost)
