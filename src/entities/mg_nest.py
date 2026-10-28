"""
Machine gun nest building.

Auto-fires a rapid small-damage stream at the nearest enemy inside a
circular range. The battle state steps these on its simulated frame
and passes the correct side's bullet/unit lists.
"""

import math
import pygame

from config import TILE_SIZE, BROWN, BUILD_FOOTPRINTS
from entities.bullet import Bullet
from graphics import render_mode
from systems.factions import building_variant_filenames
from utils.image_loader import load_first_image


class MGNest:

    def __init__(self, tile_x, tile_y, is_enemy=False, faction="allies"):
        # type strings match the map spot_types keys.
        self.type = "enemy_mg" if is_enemy else "mg"
        self.is_enemy = is_enemy
        self.faction = faction

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Footprint in tiles (MG = 4x4, config single source). The
        # anchor tile is the TOP-LEFT: sprite, block mode, collision,
        # and spot outlines all scale with this footprint.
        self.footprint_tiles = BUILD_FOOTPRINTS["mg"]
        fw_px, fh_px = (TILE_SIZE * n for n in self.footprint_tiles)

        # Firing stats: circular engagement range in pixels, fixed
        # damage per bullet, and a short cooldown between shots (the
        # cooldown is subtracted in update, hence starts at 0).
        self.range = 220
        self.damage = 8
        self.fire_rate = 0.2
        self.cooldown = 0

        # Art side: scene-variant chain loader (a summer day / b summer
        # night / c winter day / d winter night, with base-art
        # fallback), drawn across the FULL footprint.
        self.image = load_first_image(
            building_variant_filenames(faction, "mg_nest"),
            alpha=True,
            size=(fw_px, fh_px),
        )

        # Mirror enemy art so it faces the battlefield like its units.
        # Flipping copies the cached surface: the cache is never mutated.
        # A None image (no art at all) is left flipped-free: draw()
        # falls back to the block mode instead.
        if is_enemy and self.image is not None:
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

        # Aim origin: the CENTER of the whole footprint in pixel
        # coordinates (a 2x2 nest fires from between its four tiles).
        fw_px, fh_px = (TILE_SIZE * n for n in self.footprint_tiles)
        cx = self.tile_x * TILE_SIZE + fw_px / 2
        cy = self.tile_y * TILE_SIZE + fh_px / 2

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
        """Art DIRECTLY on the ground; brown block only without textures.

        SPRITES (texture) mode: the art is blitted straight over the
        map ground — PNG transparency reveals the real battlefield
        floor, never a painted square behind it (a grey underlay here
        made the art "show background"; bunkers already drew this way).
        BLOCK mode (or no art at all): one solid BROWN square over the
        full 2x2 — no textures, uniform color, no facing marker.
        """
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        fw_px, fh_px = (TILE_SIZE * n for n in self.footprint_tiles)

        if not render_mode.is_sprite() or self.image is None:
            pygame.draw.rect(screen, BROWN, (px, py, fw_px, fh_px))
            return

        # Sprites blit WITHOUT an underlay: PNG transparency reveals the
        # real battlefield ground (map1_a/map1_c), same as the bunker.
        # An opaque grey square here was painting the "background" the
        # user saw through the art.
        screen.blit(self.image, (px, py))
