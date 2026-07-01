"""
systems/combat_system.py

Handles combat interactions between
player defenses and enemies.
"""

import math


class CombatSystem:
    """
    Processes attacks and damage.
    """

    def __init__(self):
        pass

    def update(
        self,
        buildings,
        enemies
    ):
        """
        Update all combat interactions.
        """

        #
        # Process all buildings
        #
        for building in buildings:

            #
            # Skip if building
            # doesn't have combat stats
            #
            if not hasattr(building, "range"):
                continue

            #
            # Cooldown timer
            #
            if building.cooldown > 0:

                building.cooldown -= 1

                continue

            #
            # Find target
            #
            target = self.find_target(
                building,
                enemies
            )

            if target is None:
                continue

            #
            # Fire
            #
            target.take_damage(
                building.damage
            )

            #
            # Future:
            # suppression
            #
            target.suppressed = True

            building.cooldown = (
                building.fire_rate
            )

    def find_target(
        self,
        building,
        enemies
    ):
        """
        Find nearest enemy in range.
        """

        nearest_enemy = None

        nearest_distance = 999999

        for enemy in enemies:

            distance = math.dist(

                (
                    building.tile_x,
                    building.tile_y
                ),

                (
                    enemy.tile_x,
                    enemy.tile_y
                )

            )

            if distance > building.range:
                continue

            if distance < nearest_distance:

                nearest_distance = distance

                nearest_enemy = enemy

        return nearest_enemy