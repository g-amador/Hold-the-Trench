"""
Static, marker-placed buildings: air field and tank factory.

Placed FREE from uppercase map markers (F = air field, K = tank
factory) at battle start — the player never pays for them and the
build prompt never touches them (they are not in BUILDING_CLASSES).
No combat behavior yet: update() is a deliberate no-op; their game
role (spawning tanks/planes) comes later.

Art follows the battle scene like every other building: the variant
chain (scene _a/_c file -> _a file -> base) picks summer/winter art
per the shared scene roll, scaled across the whole footprint. Block
mode (or missing art) = one uniform BROWN footprint rect (the user's
MG rule: sprites blit without underlay; blocks uniform, no marker).
Footprint is 6x6 ("like the MGs but bigger", user-directed), and the
statics are SOLID: their type strings are in player.BLOCKING_BUILDINGS,
so the whole footprint blocks the player through the config table.
"""

import pygame

from config import TILE_SIZE, BROWN, BUILD_FOOTPRINTS
from graphics import render_mode
from systems.factions import building_variant_filenames
from utils.image_loader import load_first_image


class StaticBuilding:
    """Shared body of the free-placed static buildings."""

    # canonical asset stem (building_<stem>_<nation>[_variant].png)
    STEM = None

    def __init__(self, tile_x, tile_y, faction="allies"):
        assert self.STEM is not None, "subclass must set STEM"
        self.type = self.STEM
        self.is_enemy = False
        self.faction = faction

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Footprint from the config table (statics are 6x6 like
        # barracks/bunker, user-directed); sprite/block/collision scale
        # with it like every other building.
        self.footprint_tiles = BUILD_FOOTPRINTS[self.STEM]
        fw_px, fh_px = (TILE_SIZE * n for n in self.footprint_tiles)

        # Scene-variant art across the full footprint (same chain as
        # mg_nest/bunker: scene file -> _a file -> base art, None if
        # nothing exists -> block drawing).
        self.image = load_first_image(
            building_variant_filenames(faction, self.STEM),
            alpha=True,
            size=(fw_px, fh_px),
        )

    def update(self, dt, enemies, bullets):
        """No combat behavior yet — a static structure."""
        return

    def draw(self, screen, camera_x):
        """SPRITES: art blitted straight onto the ground (no underlay:
        PNG transparency shows the battlefield floor, never a painted
        square behind it). BLOCK mode / no art: one solid BROWN rect
        over the full footprint, no facing marker."""
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        fw_px, fh_px = (TILE_SIZE * n for n in self.footprint_tiles)

        if not render_mode.is_sprite() or self.image is None:
            pygame.draw.rect(screen, BROWN, (px, py, fw_px, fh_px))
            return

        screen.blit(self.image, (px, py))


class AirField(StaticBuilding):
    """Free-placed air field (map marker 'F'); planes later."""

    STEM = "air_field"


class TankFactory(StaticBuilding):
    """Free-placed tank factory (map marker 'K'); production later."""

    STEM = "tank_factory"
