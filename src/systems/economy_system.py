"""
Economy system.
Tracks supplies, total defense cost, spent cost, and total gold obtainable.
"""

BUILD_COSTS = {
    "mg": 20,
    "bunker": 40,
    "barracks": 30,
    "artillery": 60,
}

class EconomySystem:
    def __init__(self):
        self.supplies = 50
        self.total_defense_cost = 0
        self.spent_defense_cost = 0

        # Total gold obtainable from all waves
        self.total_gold_available = 0

    def register_cost(self, cost):
        self.total_defense_cost += cost

    def spend(self, cost):
        self.supplies -= cost
        self.spent_defense_cost += cost

    def add_wave_gold(self, gold_amount):
        self.total_gold_available += gold_amount
