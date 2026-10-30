"""
Static, marker-placed buildings: air field and tank factory.

Placed FREE from map markers (F = air field, K = tank factory for the
player; f/k for the enemy side) at battle start — nobody pays for
them and the build prompt never touches them (they are not in
BUILDING_CLASSES). The tank factory rolls out armored vehicles on the
shared FACTORY_UNIT_INTERVAL timeline, producing per its rolled
COUNTRY; the AIR FIELD produces PLANES into the side's plane list on
the same cadence (user: "generate planes at the same rate as tanks").

Art follows the battle scene like every other building: the variant
chain (scene file -> _a file -> base) picks summer/winter art per the
shared scene roll. Static art gets the SEMI-ALPHA FIX (user: "tank
factory transparent background is shown"): the german factory art
paints its whole backdrop at partial alpha, which reads as a milky
translucent overlay — hardening snaps every pixel fully opaque or
fully transparent (utils/image_loader). Block mode (or missing art) =
one uniform BROWN footprint rect.
Static footprints come from the config table (7x7), and the statics
are SOLID (player.BLOCKING_BUILDINGS + the enemy_ types).
"""

import pygame

from config import TILE_SIZE, BROWN, BUILD_FOOTPRINTS, BUILDING_HP, FACTORY_UNIT_INTERVAL
from entities.airplane import AirplaneUnit
from entities.armor import roll_armor_unit
from graphics import render_mode
from systems.factions import (
    building_variant_filenames,
    armor_factory_nation,
    plane_filename,
    spawn_plane_nation,
)
from utils.image_loader import (
    load_image_semi_alpha_fixed,
    load_first_image_named,
)


class StaticBuilding:
    """Shared body of the free-placed static buildings."""

    # canonical asset stem (building_<stem>_<nation>[_variant].png)
    STEM = None

    def __init__(self, tile_x, tile_y, faction="allies", is_enemy=False):
        assert self.STEM is not None, "subclass must set STEM"
        # type strings stay the bare stem (collision keys off the
        # is_enemy flag + the enemy_ prefix handling in player.py).
        self.type = self.STEM
        self.is_enemy = is_enemy
        self.faction = faction

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Footprint from the config table (statics are 7x7 per the
        # user); sprite/block/collision scale with it like every
        # other building.
        self.footprint_tiles = BUILD_FOOTPRINTS[self.STEM]
        fw_px, fh_px = (TILE_SIZE * n for n in self.footprint_tiles)
        self.width, self.height = fw_px, fh_px

        # World coerce for targeting/bombs: anchored like every
        # multi-tile building.
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE

        # Objective hp (destructible building, config table).
        self.hp = BUILDING_HP[self.STEM]
        self.dead = False

        # Scene-variant art across the full footprint (same chain as
        # mg_nest/bunker). The SEMI-ALPHA FIX comes free: the world
        # art is scaled from the hardened native copy, so both
        # resolutions share the same opaque cut-out.
        self.image = None
        self.image_native = None
        self.image, image_file = load_first_image_named(
            building_variant_filenames(faction, self.STEM),
            alpha=True,
            size=(fw_px, fh_px),
        )
        if image_file is not None:
            try:
                self.image_native = load_image_semi_alpha_fixed(image_file)
                if fw_px != self.image_native.get_width():
                    self.image = pygame.transform.scale(
                        self.image_native,
                        (fw_px, fh_px),
                    )
            except FileNotFoundError:
                self.image_native = None

        # NO ENEMY FLIP (user: "air fields and tank factory SAME
        # orientation regardless if enemy or not" — and "my side is
        # currently correct"): both sides draw the art exactly as the
        # file paints it. This differs from units/mg/bunker/barracks,
        # which still mirror their enemy copies.

    # ---- shared destructible-building body ----

    def take_damage(self, dmg):
        """Apply damage; hp floors at 0 so `is_destroyed` reads true once."""
        if self.dead:
            return
        self.hp = max(0, self.hp - dmg)
        self.dead = self.hp <= 0

    def is_destroyed(self):
        return self.hp <= 0

    def get_hitbox(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, dt, units):
        """No combat behavior yet — a static structure."""
        return

    def draw(self, screen, camera_x):
        """SPRITES: art blitted straight onto the ground (no underlay:
        PNG transparency shows the battlefield floor, never a painted
        square behind it). BLOCK mode / no art: one solid BROWN rect
        over the full footprint, no facing marker."""
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        fw_px, fh_px = self.width, self.height

        if not render_mode.is_sprite() or self.image is None:
            pygame.draw.rect(screen, BROWN, (px, py, fw_px, fh_px))
            return

        screen.blit(self.image, (px, py))


class AirField(StaticBuilding):
    """Free-placed air field (markers 'F'/'f'): rolls out PLANES on
    the same cadence as tank factories (user rule), into the side's
    plane list."""

    STEM = "air_field"

    def __init__(self, tile_x, tile_y, faction="allies", is_enemy=False):
        super().__init__(tile_x, tile_y, faction, is_enemy)

        # The field produces per COUNTRY (factory rule): allies mix
        # brit/fr randomly, axis fields are always german (austria
        # flies german-built planes — plane_filename fallback).
        self.nation = spawn_plane_nation(faction)

        # Production clock: one plane every FACTORY_UNIT_INTERVAL
        # seconds ("generate planes at the same rate as tanks").
        self.spawn_timer = 0.0

    def update(self, dt, planes):
        """Roll out a plane of this field's country into `planes` (the
        side's PLANE list owned by the battle state)."""
        if self.dead:
            return

        self.spawn_timer += dt / 1000
        if self.spawn_timer < FACTORY_UNIT_INTERVAL:
            return

        # Subtract (rather than zero) so slow frames never lose time.
        self.spawn_timer -= FACTORY_UNIT_INTERVAL

        planes.append(AirplaneUnit(
            self.x,
            self.y,
            is_enemy=self.is_enemy,
            filename=plane_filename(self.nation),
            nation=self.nation,
        ))


class TankFactory(StaticBuilding):
    """Free-placed tank factory (markers 'K'/'k'): rolls out armored
    vehicles — tanks for every country; British factories also mix
    in the machine-gun car ("a random of available units")."""

    STEM = "tank_factory"

    def __init__(self, tile_x, tile_y, faction="allies", is_enemy=False):
        super().__init__(tile_x, tile_y, faction, is_enemy)

        # The factory produces per COUNTRY (user rule): allies
        # factories roll brit or fr once at placement (same 50/50 as
        # building art); axis factories are always german.
        self.nation = armor_factory_nation(faction)

        # Production clock: one vehicle every FACTORY_UNIT_INTERVAL
        # seconds (user ratio "1 tank per 3 infantry" on the shared
        # timeline: infantry deploys every 5 s, a vehicle every 15).
        self.spawn_timer = 0.0

    def update(self, dt, units):
        """Roll out a random vehicle of this factory's country into
        `units` (the side's unit list owned by the battle state)."""
        if self.dead:
            return

        self.spawn_timer += dt / 1000
        if self.spawn_timer < FACTORY_UNIT_INTERVAL:
            return

        # Subtract (rather than zero) so slow frames never lose time.
        self.spawn_timer -= FACTORY_UNIT_INTERVAL

        unit = roll_armor_unit(
            self.nation,
            self.is_enemy,
            self.tile_x * TILE_SIZE,
            self.tile_y * TILE_SIZE,
        )
        if unit is not None:
            units.append(unit)
