"""
Barracks building: spawns infantry on a fixed timer.

Player barracks spawn friendly infantry; enemy barracks spawn enemy
infantry. `is_enemy` selects both behavior and art side; spawn
frequency is shared (spawn_cooldown).
"""

import pygame
import random

from config import TILE_SIZE, GREY
from entities.enemy import EnemyInfantry
from entities.friendly_infantry import FriendlyInfantry
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from utils.image_loader import load_image


class Barracks:

    def __init__(self, tile_x, tile_y, is_enemy=False):
        # type strings match the map spot_types keys (building_query
        # and TileMap spot bookkeeping read these prefixes).
        self.type = "enemy_barracks" if is_enemy else "barracks"
        self.is_enemy = is_enemy

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Spawn clock: infantry deploy every spawn_cooldown milliseconds.
        self.spawn_cooldown = 5.0
        self.timer = 0

        # 1 = right, -1 = left: enemies face the player side.
        self.facing = -1 if is_enemy else 1

        # Art side: allies use Central Powers art, enemies use Entente
        # art (placeholder faction logic until the faction table lands).
        prefix = f"building_barraks"

        filename = random.choice([f"{prefix}_fr.png", f"{prefix}_brit.png"]) if is_enemy else random.choice([f"{prefix}_ger.png"])
        self.image = load_image(
            filename,
            alpha=True,
            size=(TILE_SIZE, TILE_SIZE),
        )

        # Mirror enemy art so it faces the battlefield the same way as
        # its units (the shared image cache is never mutated: flip
        # produces a new surface).
        if is_enemy:
            self.image = pygame.transform.flip(self.image, True, False)

    def update(self, dt, units):
        """Count down the spawn clock; deploy a unit into `units`.

        `units` is the side's unit list owned by the battle state
        (friendlies or enemy_barracks_units there).
        """
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
            units.append(EnemyInfantry(x, y))
        else:
            units.append(FriendlyInfantry(x, y))

    def draw(self, screen, camera_x):
        # Block mode: flat block with the facing marker on its leading
        # edge; whole-tile footprint.
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE

        if not render_mode.is_sprite():
            draw_unit_block(
                screen,
                px,
                py,
                TILE_SIZE,
                TILE_SIZE,
                self.facing,
                GREY,
            )
            return

        screen.blit(self.image, (px, py))
