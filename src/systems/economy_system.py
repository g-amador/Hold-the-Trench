"""
Economy system.
Tracks supplies and total/used defense cost.
"""


class EconomySystem:
    def __init__(self):
        self.supplies = 50
        self.total_defense_cost = 0
        self.spent_defense_cost = 0

    def register_cost(self, cost):
        self.total_defense_cost += cost

    def spend(self, cost):
        self.supplies -= cost
        self.spent_defense_cost += cost
