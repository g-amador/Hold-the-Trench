"""
Artillery building.

Slow but hard-hitting: fires one high-damage bullet at the nearest
enemy inside a long circular range. Built/built-enemy versions write
into the side-appropriate bullet list the battle state passes in.
Currently drawn as a grey block.
"""

import math

from config import TILE_SIZE, GREY
from entities.bullet import Bullet
from graphics.block_drawer import draw_unit_block


class Artillery:

    def __init__(self, tile_x, tile_y, is_enemy=False, faction="allies"):
        # type strings match the map spot_types keys.
        self.type = "enemy_artillery" if is_enemy else "artillery"
        self.is_enemy = is_enemy
        self.faction = faction

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Firing stats: long range, heavy damage, slow reload; the
        # cooldown is subtracted in update, hence starts at 0.
        self.range = 400
        self.damage = 50
        self.fire_rate = 1.5
        self.cooldown = 0

    def update(self, dt, enemies, bullets):
        """Fire one bullet at the nearest enemy inside `range`.

        Same targeting logic as MGNest, just longer range and fewer,
        heavier shots. `bullets` must be the side-appropriate list.
        """
        # Reload gate: no shots until the cooldown drains to 0.
        self.cooldown -= dt / 1000
        if self.cooldown > 0:
            return

        # Aim origin: building center in pixel coordinates.
        cx = self.tile_x * TILE_SIZE + TILE_SIZE / 2
        cy = self.tile_y * TILE_SIZE + TILE_SIZE / 2

        # Nearest-target selection: linear scan is fine at this unit count.
        target = None
        best_dist = None
        for e in enemies:
            if e.dead:
                continue
            dist = math.hypot(e.x - cx, e.y - cy)
            if dist <= self.range:
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    target = e

        if target:
            # Normalize the aim vector so bullet speed stays constant
            # regardless of target distance.
            dx = target.x - cx
            dy = target.y - cy
            length = math.hypot(dx, dy)
            if length == 0:
                return
            dx /= length
            dy /= length

            bullet = Bullet(cx, cy, dx, dy)
            bullets.append(bullet)

            self.cooldown = self.fire_rate

    def draw(self, screen, camera_x):
        """Flat grey block in BOTH modes: no sprite art exists yet.

        Uses the same full-tile block (facing marker included) as the
        other buildings, so all structures look consistent when the
        graphics toggle hides textures. `faction` is stored for the
        art pass (building_artillery_* assets do not exist yet).
        """
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        draw_unit_block(
            screen,
            px,
            py,
            TILE_SIZE,
            TILE_SIZE,
            -1 if self.is_enemy else 1,
            GREY,
        )
