"""
Bunker building: the win/lose anchor of a battle.

The player's bunker must survive; destroying every enemy bunker wins
the battle. Bunkers do not shoot: they are pure objectives with hp
that other buildings and the player protect or attack.
"""

import pygame

from config import (
    TILE_SIZE,
    GREY,
    BUILD_FOOTPRINTS,
    BUILDING_HP,
    BUNKER_FOOTPRINTS_BY_NATION,
)
from graphics import render_mode
from systems.factions import (
    building_variant_filenames,
    nation_from_building_filename,
)
from utils.image_loader import (
    aspect_fit_contain,
    load_image,
    opaque_bbox,
)


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

        # Default footprint before the art resolves (missing-art
        # fallback): the kind's table entry, 6x6 today.
        self.footprint_tiles = BUILD_FOOTPRINTS.get("bunker", (1, 1))

        # World coordinates used for targeting and collision: anchored
        # at the marker tile like every other multi-tile building.
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE

        # Per-nation footprint (user: "brit and ger bunkers can be
        # only 6x4 tiles"): the rolled art file decides the footprint
        # for THIS instance — brit/ger art sits in the squat 6x4 box,
        # fr (and the no-art fallback) keeps the 6x6 table default.
        # Handled per instance because the allies bunker rolls brit OR
        # fr art per battle.
        self.art_nation = None

        # ---- art: PROPORTIONAL DRAW (user fix) ----
        # The bunker art is now:
        #   1. cropped to its OPAQUE content (native bbox, cached per
        #      file — applies to every scene variant a/b/c/d),
        #   2. fitted CONTAIN into the footprint box aspect-true
        #      (never stretched), BOTTOM-CENTER anchored (a cutaway
        #      building stands on its ground line).
        # `draw_size`/`draw_offset` are honored by the CLOSE-hires
        # pass and the world blit; collision uses the per-nation
        # footprint above.
        self.draw_size = None
        self.draw_offset = (0, 0)
        self.image_native = None
        self.image = None
        for filename in building_variant_filenames(faction, "bunker"):
            try:
                bbox = opaque_bbox(filename)
                native_full = load_image(filename, alpha=True)
            except FileNotFoundError:
                continue

            bbox_w = bbox[2] - bbox[0]
            bbox_h = bbox[3] - bbox[1]
            if bbox_w <= 0 or bbox_h <= 0:
                continue

            # NOTE: opaque_bbox returns (left, top, RIGHT, BOTTOM)
            # edges — build the rect with explicit w/h, never
            # Rect(box) (that would read them as width/height and
            # overshoot the canvas).
            crop = native_full.subsurface(
                pygame.Rect(bbox[0], bbox[1], bbox_w, bbox_h),
            )

            self.art_nation = nation_from_building_filename(filename)
            self.footprint_tiles = BUNKER_FOOTPRINTS_BY_NATION.get(
                self.art_nation,
                BUILD_FOOTPRINTS.get("bunker", (1, 1)),
            )
            self.width, self.height = (
                TILE_SIZE * n for n in self.footprint_tiles
            )

            draw_w, draw_h = aspect_fit_contain(
                bbox_w, bbox_h, self.width, self.height,
            )
            self.draw_size = (draw_w, draw_h)
            self.draw_offset = (
                (self.width - draw_w) // 2,    # centered horizontally
                self.height - draw_h,          # on the ground line
            )

            # Native copy = the opaque CROP (CLOSE hires scales THIS);
            # world copy = the crop aspect-fit into the footprint box
            # (smoothscale — the user wants quality, not nearest).
            self.image_native = crop
            self.image = pygame.transform.smoothscale(
                crop,
                (draw_w, draw_h),
            )

            # Mirror enemy art so it faces the battlefield like its
            # units. Flipping makes a copy: the cache is never mutated.
            if is_enemy:
                self.image = pygame.transform.flip(self.image, True, False)
                self.image_native = pygame.transform.flip(
                    crop, True, False,
                )
            break

        # No art anywhere (missing files): full default footprint and
        # full-footprint draw defaults; draw() shows the block mode.
        if self.image is None:
            self.footprint_tiles = BUILD_FOOTPRINTS.get("bunker", (1, 1))
            self.width, self.height = (
                TILE_SIZE * n for n in self.footprint_tiles
            )
            self.draw_size = (self.width, self.height)

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
        color (the MG uses BROWN; the bunker stays grey). The sprite
        is blitted at draw_offset so the aspect-true art sits
        bottom-center inside its footprint (transparent footprint
        edges reveal the ground, like every other building).
        """
        if not render_mode.is_sprite() or self.image is None:
            # Anchor on the hitbox so the block lines up with the
            # bunker's real collision area.
            rect = self.get_hitbox()
            rect.x -= round(camera_x)
            pygame.draw.rect(screen, GREY, rect)
            return

        px = self.tile_x * TILE_SIZE - camera_x + self.draw_offset[0]
        py = self.tile_y * TILE_SIZE + self.draw_offset[1]
        screen.blit(self.image, (px, py))
