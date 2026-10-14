"""
Economy system.
Tracks gold.
"""

BUILD_COSTS = {
    "mg": 20,
    "bunker": 40,
    "barracks": 30,
    "artillery": 60,
}

class EconomySystem:
    def __init__(self):
        self.gold = 50

    def spend(self, cost):
        self.gold -= cost

