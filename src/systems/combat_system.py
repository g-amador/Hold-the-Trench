"""
Combat system.
Handles buildings auto-shooting enemies in range.
"""

import math


class CombatSystem:
    def __init__(self):
        pass

    def update(self, buildings, enemies):
        """
        For each building, find enemies in range and apply damage based on fire rate.
        """

        # Simple per-frame shooting: no cooldown logic for now
        for building in buildings:
            # Determine building world position
            from config import TILE_SIZE
            bx = building.tile_x * TILE_SIZE + TILE_SIZE // 2
            by = building.tile_y * TILE_SIZE + TILE_SIZE // 2

            # Get stats if present, else skip
            range_ = getattr(building, "range", 0)
            damage = getattr(building, "damage", 0)

            if range_ <= 0 or damage <= 0:
                continue

            # Shoot the closest enemy in range
            target = None
            target_dist = None

            for enemy in enemies:
                if enemy.dead:
                    continue

                dist = math.hypot(enemy.x - bx, enemy.y - by)
                if dist <= range_:
                    if target is None or dist < target_dist:
                        target = enemy
                        target_dist = dist

            if target:
                target.take_damage(damage)
