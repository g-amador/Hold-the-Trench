"""
Machine gun nest building.

Auto-fires a rapid small-damage stream at the nearest enemy inside a
circular range from a FIXED MUZZLE CELL outside the footprint (user
spec: the bullet starts at cell x+4, y+1 for the player side — the
first column EAST of the 4x4 nest, second row — and at x-1, y+1 for
the enemy side, mirroring into the first column WEST). Aim vector and
engagement range are both measured from that muzzle cell. The battle
state steps these on its simulated frame and passes the correct side's
bullet/unit lists.

Buildings are destructible now (bunker-style hp + take_damage driven
by config.BUILDING_HP): tank shells and plane bombs can wear a nest
down.
"""

import math
import pygame

from config import (
    TILE_SIZE,
    BROWN,
    BUILD_FOOTPRINTS,
    BUILDING_HP,
    MG_NEST_RANGE,
    MG_NEST_DAMAGE,
    MG_NEST_FIRE_RATE,
)
from entities.bullet import Bullet
from graphics import render_mode
from systems.factions import building_variant_filenames
from utils.image_loader import (
    load_image,
    load_first_image_named,
)


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
        self.width, self.height = fw_px, fh_px

        # Objective hp (destructible building, config table).
        self.hp = BUILDING_HP["mg"]
        self.dead = False

        # Firing stats: circular engagement range in pixels (measured
        # from the muzzle cell), fixed damage per bullet, and a short
        # cooldown between shots (the cooldown is subtracted in
        # update, hence starts at 0).
        self.range = MG_NEST_RANGE
        self.damage = MG_NEST_DAMAGE
        self.fire_rate = MG_NEST_FIRE_RATE
        self.cooldown = 0

        # Art side: scene-variant chain loader (a summer day / b summer
        # night / c winter day / d winter night, with base-art
        # fallback), drawn across the FULL footprint.
        self.image, image_file = load_first_image_named(
            building_variant_filenames(faction, "mg_nest"),
            alpha=True,
            size=(fw_px, fh_px),
        )

        # Native-resolution copy of the SAME art file for the CLOSE
        # view's hires blit (None when the file is missing entirely:
        # the building keeps its normal low-res or block drawing).
        self.image_native = None
        if image_file is not None:
            try:
                self.image_native = load_image(image_file, alpha=True)
            except FileNotFoundError:
                self.image_native = None

        # Mirror enemy art so it faces the battlefield like its units.
        # Flipping copies the cached surface: the cache is never mutated.
        # A None image (no art at all) is left flipped-free: draw()
        # falls back to the block mode instead.
        if is_enemy and self.image is not None:
            self.image = pygame.transform.flip(self.image, True, False)
        if is_enemy and self.image_native is not None:
            self.image_native = pygame.transform.flip(
                self.image_native,
                True,
                False,
            )

    def take_damage(self, dmg):
        """Apply damage; hp floors at 0 so `is_destroyed` reads true once."""
        if self.dead:
            return
        self.hp = max(0, self.hp - dmg)
        self.dead = self.hp <= 0

    def is_destroyed(self):
        return self.hp <= 0

    def get_hitbox(self):
        """Return the nest's collision rectangle in world coordinates."""
        return pygame.Rect(
            self.tile_x * TILE_SIZE,
            self.tile_y * TILE_SIZE,
            self.width,
            self.height,
        )

    def _muzzle_px(self):
        """Fixed muzzle cell OUTSIDE the footprint (user spec).

        Player side: cell (x + fw, y + 1) — the first column EAST of
        the 4x4 footprint, second row. Enemy side mirrors WEST: cell
        (x - 1, y + 1). The returned pixel point is the CELL CENTER:
        bullets spawn there and the aim/range math runs from it.
        """
        if self.is_enemy:
            cell_x = self.tile_x - 1
        else:
            cell_x = self.tile_x + self.footprint_tiles[0]
        cell_y = self.tile_y + 1
        return (
            (cell_x + 0.5) * TILE_SIZE,
            (cell_y + 0.5) * TILE_SIZE,
        )

    def update(self, dt, enemies, bullets):
        """Fire at the nearest enemy in range from the muzzle cell.

        `bullets` must be the side-appropriate list the battle state
        simulates (player-side bullets or enemy_bullets). Destroyed
        nests stop firing.
        """
        if self.dead:
            return

        # Cooldown keeps ticking down; fire only after it reaches 0.
        self.cooldown -= dt / 1000
        if self.cooldown > 0:
            return

        # Fire origin: the muzzle cell center (outside the footprint).
        cx, cy = self._muzzle_px()

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
            bullet.damage = self.damage
            bullets.append(bullet)

            self.cooldown = self.fire_rate

    def draw(self, screen, camera_x):
        """Art DIRECTLY on the ground; brown block only without textures.

        SPRITES (texture) mode: the art is blitted straight over the
        map ground — PNG transparency reveals the real battlefield
        floor, never a painted square behind it (a grey underlay here
        made the art "show background"; bunkers already drew this way).
        BLOCK mode (or no art at all): one solid BROWN square over the
        full 4x4 — no textures, uniform color, no facing marker.
        """
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        fw_px, fh_px = self.width, self.height

        if not render_mode.is_sprite() or self.image is None:
            pygame.draw.rect(screen, BROWN, (px, py, fw_px, fh_px))
            return

        # Sprites blit WITHOUT an underlay: PNG transparency reveals the
        # real battlefield ground (map1_a/map1_c), same as the bunker.
        # An opaque grey square here was painting the "background" the
        # user saw through the art.
        screen.blit(self.image, (px, py))
