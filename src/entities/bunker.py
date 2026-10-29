"""
Bunker building: the win/lose anchor of a battle.

The player's bunker must survive; destroying every enemy bunker wins
the battle. Bunkers do not shoot: they are pure objectives with hp
that other buildings and the player protect or attack.
"""

import pygame

from config import TILE_SIZE, GREY, BUILD_FOOTPRINTS, BUILDING_HP
from graphics import render_mode
from systems.factions import building_variant_filenames
from utils.image_loader import load_image, load_first_image_named


class Bunker:
    def __init__(self, tile_x, tile_y, is_enemy=False, faction="allies"):
        self.is_enemy = is_enemy
        self.faction = faction
        # type strings match the map spot_types keys.
        self.type = "enemy_bunker" if is_enemy else "bunker"

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Bunkers are the tankiest entity; hp only ever decreases here.
        # (config.BUILDING_HP table — the objective entry — user rule:
        # every stat centralized in config.py.)
        self.hp = BUILDING_HP["bunker"]
        self.dead = False

        # Footprint/table-driven like the MG (user set the config to
        # 6x6): the drawn sprite/block, the collision rect, and the
        # spot outline all read BUILD_FOOTPRINTS — one anchor, growing
        # right + down from the marker tile. No more legacy 2x3
        # up-sticking hitbox: block == collision == drawn footprint.
        self.footprint_tiles = BUILD_FOOTPRINTS.get("bunker", (1, 1))
        self.width, self.height = (
            TILE_SIZE * n for n in self.footprint_tiles
        )

        # World coordinates used for targeting and collision: anchored
        # at the marker tile like every other multi-tile building.
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE

        # Art side: random per-building from the faction's pool, same
        # rule as the other buildings (axis = ger, allies = brit/fr) —
        # scene-variant chain loader (a/b/c/d with summer-day fallback)
        # per the user's letter mapping: a summer day, b summer night,
        # c winter day, d winter night. Scaled across the footprint.
        fw_px, fh_px = self.width, self.height
        self.image, image_file = load_first_image_named(
            building_variant_filenames(faction, "bunker"),
            alpha=True,
            size=(fw_px, fh_px),
        )

        # Native-resolution copy of the SAME art file for the CLOSE
        # view's hires blit (None when nothing loaded).
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

    def get_hitbox(self):
        """Return the bunker's collision rectangle in world coordinates."""
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )

    def update(self):
        # Passive objective: nothing to simulate.
        pass

    def take_damage(self, dmg):
        """Apply damage; hp floors at 0 so `is_destroyed` reads true once."""
        self.hp = max(0, self.hp - dmg)
        self.dead = self.hp <= 0

    def is_destroyed(self):
        """Win/lose checks test hp directly (hp == 0 = collapsed)."""
        return self.hp <= 0

    def draw(self, screen, camera_x):
        """Sprite in SPRITES mode; uniform flat grey block in BLOCK mode.

        The MG draw rules apply (user request): SPRITES blits the art
        straight over the battlefield floor (no underlay), BLOCK mode
        paints ONE plain solid rect over the whole footprint — no
        facing marker, no textures — but keeps the bunker's GREY
        color (the MG uses BROWN; the bunker stays grey).
        """
        if not render_mode.is_sprite() or self.image is None:
            # Anchor on the hitbox so the block lines up with the
            # bunker's real collision area.
            rect = self.get_hitbox()
            rect.x -= round(camera_x)
            pygame.draw.rect(screen, GREY, rect)
            return

        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        screen.blit(self.image, (px, py))
