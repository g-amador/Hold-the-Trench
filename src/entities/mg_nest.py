"""
Machine gun nest building.

Auto-fires a rapid small-damage stream at the nearest enemy inside a
circular range. The battle state steps these on its simulated frame
and passes the correct side's bullet/unit lists.
"""

import math
import pygame

from config import TILE_SIZE, GREY
from entities.bullet import Bullet
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from systems.factions import building_filename
from utils.image_loader import load_image


class MGNest:

    def __init__(self, tile_x, tile_y, is_enemy=False, faction="allies"):
        # type strings match the map spot_types keys.
        self.type = "enemy_mg" if is_enemy else "mg"
        self.is_enemy = is_enemy
        self.faction = faction

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Firing stats: circular engagement range in pixels, fixed
        # damage per bullet, and a short cooldown between shots (the
        # cooldown is subtracted in update, hence starts at 0).
        self.range = 220
        self.damage = 8
        self.fire_rate = 0.2
        self.cooldown = 0

        # Art side: random per-building from the faction's pool, same
        # rule as the other buildings (axis = ger, allies = brit/fr).
        self.image = load_image(
            building_filename(faction, "mg_nest"),
            alpha=True,
            size=(TILE_SIZE, TILE_SIZE),
        )

        # Mirror enemy art so it faces the battlefield like its units.
        # Flipping copies the cached surface: the cache is never mutated.
        if is_enemy:
            self.image = pygame.transform.flip(self.image, True, False)

    def update(self, dt, enemies, bullets):
        """Fire at the nearest enemy in range into the list `bullets`.

        `bullets` must be the side-appropriate list the battle state
        simulates (player-side bullets or enemy_bullets).
        """
        # Cooldown keeps ticking down; fire only after it reaches 0.
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
        """Sprite in SPRITES mode; flat grey block in BLOCK mode.

        Block mode must show no textures at all: the tile-sized grey
        square matches the other buildings' block look.
        """
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE

        if not render_mode.is_sprite():
            draw_unit_block(
                screen,
                px,
                py,
                TILE_SIZE,
                TILE_SIZE,
                -1 if self.is_enemy else 1,
                GREY,
            )
            return

        screen.blit(self.image, (px, py))
