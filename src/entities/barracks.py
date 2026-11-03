"""
Barracks building: spawns infantry on a fixed timer.

Player barracks spawn friendly infantry; enemy barracks spawn enemy
infantry. `is_enemy` selects both behavior and art side; spawn
frequency is shared (spawn_cooldown).
"""

import pygame

from config import (
    TILE_SIZE,
    GREY,
    BUILD_FOOTPRINTS,
    BUILDING_HP,
    BARRACKS_SPAWN_INTERVAL,
)
from entities.damage import FlooredDamage
from entities.enemy import EnemyInfantry
from entities.friendly_infantry import FriendlyInfantry
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from systems.factions import building_variant_filenames
from utils.image_loader import load_image, load_first_image_named


class Barracks(FlooredDamage):

    def __init__(self, tile_x, tile_y, is_enemy=False, faction="allies"):
        # type strings match the map spot_types keys (building_query
        # and TileMap spot bookkeeping read these prefixes).
        self.type = "enemy_barracks" if is_enemy else "barracks"
        self.is_enemy = is_enemy
        self.faction = faction

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Footprint/table-driven like the other buildings (config sets
        # barracks to 4x4): the drawn sprite/block, and TileMap's
        # viewport culling, all read footprint_tiles. Collision comes
        # from the same table via tilemap._footprint_covered.
        self.footprint_tiles = BUILD_FOOTPRINTS.get("barracks", (1, 1))
        self.width, self.height = (
            TILE_SIZE * n for n in self.footprint_tiles
        )

        # Objective hp (destructible building, config table).
        self.hp = BUILDING_HP["barracks"]
        self.dead = False
        self.x = self.tile_x * TILE_SIZE
        self.y = self.tile_y * TILE_SIZE

        # Spawn clock: infantry deploy every BARRACKS_SPAWN_INTERVAL
        # seconds (the anchor the factory cadence multiplies off).
        self.spawn_cooldown = BARRACKS_SPAWN_INTERVAL
        self.timer = 0

        # 1 = right, -1 = left: enemies face the player side.
        self.facing = -1 if is_enemy else 1

        # Art side: random per-building from the faction's pool (axis
        # buildings are always ger; allies mix brit/fr randomly) —
        # scene-variant chain loader (a/b/c/d with summer-day fallback)
        # per the user's letter mapping: a summer day, b summer night,
        # c winter day, d winter night. Scaled across the footprint.
        self.image, image_file = load_first_image_named(
            building_variant_filenames(faction, "barraks"),
            alpha=True,
            size=(self.width, self.height),
        )

        # Native-resolution copy of the SAME art file for the CLOSE
        # view's hires blit (None when nothing loaded).
        self.image_native = None
        if image_file is not None:
            try:
                self.image_native = load_image(image_file, alpha=True)
            except FileNotFoundError:
                self.image_native = None

        # Mirror enemy art so it faces the battlefield the same way as
        # its units (the shared image cache is never mutated: flip
        # produces a new surface). A None image (no art at all) is left
        # flipped-free: draw() falls back to the block mode instead.
        if is_enemy and self.image is not None:
            self.image = pygame.transform.flip(self.image, True, False)

    def is_destroyed(self):
        return self.hp <= 0

    def get_hitbox(self):
        """Return the barracks' collision rectangle in world coordinates."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, dt, units):
        """Count down the spawn clock; deploy a unit into `units`.

        `units` is the side's unit list owned by the battle state
        (friendlies or enemy_barracks_units there). Destroyed
        barracks stop spawning.
        """
        if self.dead:
            return

        self.timer += dt / 1000

        if self.timer < self.spawn_cooldown:
            return

        # Subtract (instead of zeroing) so slow frames never lose time.
        self.timer -= self.spawn_cooldown

        # Spawn at the tile's top-left in pixel coordinates; the unit's
        # own AI walks it out of the building.
        x = self.tile_x * TILE_SIZE
        y = self.tile_y * TILE_SIZE

        if self.is_enemy:
            units.append(EnemyInfantry(x, y, faction=self.faction))
        else:
            units.append(FriendlyInfantry(x, y, faction=self.faction))

    def draw(self, screen, camera_x):
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        fw_px, fh_px = self.width, self.height

        if not render_mode.is_sprite() or self.image is None:
            # Block mode: flat grey block over the FULL footprint
            # with the facing marker on its leading edge (infantry side
            # hint). Also the no-art fallback (never crash).
            draw_unit_block(
                screen,
                px,
                py,
                fw_px,
                fh_px,
                self.facing,
                GREY,
            )
            return

        screen.blit(self.image, (px, py))
