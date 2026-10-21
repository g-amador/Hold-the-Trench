"""
Combat system: placeholder module.

The combat-system hookup was planned here (buildings auto-shooting
enemies in range), but that logic currently lives in two places:
entity-side firing rules in mg_nest.py / artillery.py / entities +
bullet resolution loops in states/assault_phase.py.

Implement combat rules here before adding new combat features, so the
rules are not duplicated further.
"""

import math


class CombatSystem:
    """Unused placeholder; kept so the systems package layout stays stable."""

    def __init__(self):
        pass

    def update(self, buildings, enemies):
        # Intended contract: iterate buildings, pick in-range targets,
        # and emit bullets. Not wired into the game loop yet.
        pass
