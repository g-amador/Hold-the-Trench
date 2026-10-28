"""
Tilemap for static ASCII battlefield.

Loads STATIC_MAP from TrenchGenerator and turns it into a Tile grid.
Everything is exactly as written in ASCII: the map is the level
editor. Buildings attach to tiles (tile.building), which makes the
map the authority on layout, occupancy, and (with spot_types) build
locations.
"""

import pygame

from config import TILE_SIZE, BUILD_FOOTPRINTS
from graphics import render_mode
from utils.image_loader import load_image
from systems.factions import ground_texture_filename
from world.trench_generator import (
    TrenchGenerator,
    TILE_EMPTY,
    TILE_TRENCH,
    TILE_CRATER,
    TILE_WIRE,
    TILE_MUD,
)


class Tile:
    """One world cell: terrain type plus an optional building anchor."""

    def __init__(self, x, y, tile_type):
        self.x = x
        self.y = y
        self.type = tile_type
        # Buildings live on tiles: collision, queries, and drawing all
        # walk the tile grid instead of a second entity list.
        self.building = None

        # Convert numeric tile type -> ASCII character: chars double as
        # the tokens game logic tests against (player.py keeps sets of
        # them); keep TileMap and TrenchGenerator in sync on these.
        if tile_type == TILE_TRENCH:
            self.type_char = "#"
        elif tile_type == TILE_CRATER:
            self.type_char = "C"
        elif tile_type == TILE_WIRE:
            self.type_char = "W"
        elif tile_type == TILE_MUD:
            self.type_char = "~"        
        else:
            self.type_char = "."

    def draw(self, screen, camera_x):
        """Paint this tile as terrain.

        Flat palette per terrain type plus a 1px grid outline; camera
        only shifts x because the battlefield is a horizontal strip.
        Buildings are NOT drawn here: TileMap paints EVERY tile grid
        first and every building after, so multi-tile footprints (e.g.
        the 2x2 MG) are never overpainted by neighboring tiles.
        """
        px = self.x * TILE_SIZE - camera_x
        py = self.y * TILE_SIZE

        colors = {
            TILE_EMPTY: (50, 50, 50),
            TILE_TRENCH: (90, 60, 40),
            TILE_CRATER: (70, 50, 50),
            TILE_WIRE: (150, 150, 150),
            TILE_MUD: (80, 70, 50)
        }

        pygame.draw.rect(screen, colors[self.type], (px, py, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(screen, (20, 20, 20), (px, py, TILE_SIZE, TILE_SIZE), 1)


class TileMap:
    """Grid of tiles from the ASCII map, plus build-spot bookkeeping."""

    def __init__(self):
        # The generator is the single level source; rebuilding it gives
        # a pristine battlefield (menu does this once per battle).
        generator = TrenchGenerator()
        result = generator.generate_sector()

        layout = result["tiles"]
        self.build_candidates = result["build_candidates"]

        self.width = len(layout[0])
        self.height = len(layout)

        # Row-major tile grid; x grows right, y grows down.
        self.tiles = [
            [Tile(x, y, layout[y][x]) for x in range(self.width)]
            for y in range(self.height)
        ]

        # Ground floor texture for SPRITES mode: map1<scene>.jpg
        # scaled ONCE to the whole battlefield strip (tiles are then
        # skipped at draw time — the texture IS the ground). The scene
        # letter comes from the shared battle roll, so ground and
        # buildings always match (map1a summer / map1c winter).
        # ground_texture_native keeps the file's own resolution for
        # the CLOSE view to sample 4K detail from (see reload_ground).
        self.ground_texture = None
        self.ground_texture_native = None
        self.reload_ground()

        # Build spot types (mg, bunker, barracks, artillery, enemy
        # versions), keyed by tile coordinate for O(1) lookups.
        self.spot_types = {(c["x"], c["y"]): c["type"] for c in self.build_candidates}

        # Partial payments: key (x, y) -> gold already paid by the
        # player toward that spot. The battle state tops these up each
        # frame; the building appears when payments cover the cost.
        self.paid_amount = {(x, y): 0 for (x, y) in self.spot_types}

        # Friendly boundary = first '|' in row 0 (S1 rule): the player
        # side ends at this tile column. A map without any separator
        # (e.g. the blank all-'.' canvas) counts its WHOLE width as
        # the friendly side instead of crashing on a missing '|'.
        row0 = generator.ascii_map[0]
        separator = row0.find("|")
        self.friendly_boundary = separator if separator != -1 else self.width

    def reload_ground(self):
        """Bind the ground texture to the CURRENT scene variant.

        Two resolution caches, BOTH from the same file (the user's
        5504x3072 map1a/map1c 4K art):

        - ground_texture: pre-scaled down to the world strip
          (width*TILE_SIZE x height*TILE_SIZE) for the FULL view,
          which smoothscales it to ~half world size anyway — cheap
          and detail-sufficient there.
        - ground_texture_native: the image's OWN pixel size, kept so
          the CLOSE zoom (4x upscale of a ~10-tile window) can sample
          per-screen-pixel from true 4K detail instead of the
          pre-downscaled texture (the 4x-upscaled result of that was
          the user's "blurry when zoomed" complaint).

        The map tilemap is built before the battle (the menu creates
        it), i.e. before roll_scene() — so AssaultPhase calls this
        right after rolling to re-pick the ground alongside the
        buildings (map1a.jpg summer day / map1c.jpg winter day).
        Loaded through utils/image_loader (cached per size);
        a missing file keeps both None and draw() falls back to tile
        rendering instead of crashing.
        """
        try:
            filename = ground_texture_filename()
            # Full-res first: the pre-scale below renders FROM the
            # cached native surface (transform.scale reads it once),
            # then both live in the image cache under their own keys.
            self.ground_texture_native = load_image(filename, alpha=False)
            self.ground_texture = load_image(
                filename,
                alpha=False,
                size=(self.width * TILE_SIZE, self.height * TILE_SIZE),
            )
        except FileNotFoundError:
            self.ground_texture_native = None
            self.ground_texture = None

    # WaveDirector expects this to exist
    def configure_build_spots(self, *args, **kwargs):
        # KNOWN ISSUE (AI.md #5): dead compatibility stub; build spots
        # already come from TrenchGenerator.
        return

    def is_build_spot(self, x, y):
        """True when this tile is a player/enemy build spot marker."""
        return (x, y) in self.spot_types

    def get_tile(self, x, y):
        """Return the tile, or None for any out-of-grid coordinate."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def is_walkable(self, x, y):
        """Strict spawn-walkability: only '.' counts as empty ground.

        Deliberately excludes trenches, mud, craters, wire, and hills:
        units and spawn searches treat everything else as blocked.
        """
        tile = self.get_tile(x, y)
        if not tile:
            return False

        # Only '.' counts as empty for spawning (Option B)
        return tile.type_char == "."

    def _footprint_covered(self, tile_x, tile_y):
        """Yield (anchor_x, anchor_y, fw, fh) for every anchor whose
        footprint could reach (tile_x, tile_y).

        Footprints anchor at their UPPER-LEFT tile and grow right and
        down, so an anchor sits within (footprint_side - 1) tiles up-
        left. The probe radius derives from the footprint table (its
        biggest side covers e.g. the 4x4 MG), staying correct
        automatically as kinds grow. Stateless probing means direct
        `tile.building = ...` assignment needs no extra bookkeeping
        anywhere.
        """
        probe_reach = max(
            max(fw, fh) for fw, fh in BUILD_FOOTPRINTS.values()
        )
        for dy in range(probe_reach):
            for dx in range(probe_reach):
                tile = self.get_tile(tile_x - dx, tile_y - dy)
                if tile is None:
                    continue

                kind = self.spot_types.get((tile_x - dx, tile_y - dy))
                if kind is not None:
                    # Spot-marker footprints come from the config table
                    # (enemy kinds lose their prefix).
                    build_kind = (
                        kind[len("enemy_"):]
                        if kind.startswith("enemy_")
                        else kind
                    )
                    fw, fh = BUILD_FOOTPRINTS.get(build_kind, (1, 1))
                else:
                    fw, fh = 1, 1

                # A real building on the anchor tile overrides the
                # table guess with its own footprint.
                if tile.building is not None:
                    fw, fh = getattr(
                        tile.building,
                        "footprint_tiles",
                        (fw, fh),
                    )

                if dx < fw and dy < fh:
                    yield (tile_x - dx, tile_y - dy, fw, fh)

    def building_covering(self, tile_x, tile_y):
        """Return the building whose footprint covers a tile, or None.

        Used by collision so multi-tile buildings block every tile
        they visually occupy, not just their anchor tile.
        """
        for anchor_x, anchor_y, fw, fh in self._footprint_covered(
            tile_x,
            tile_y,
        ):
            tile = self.get_tile(anchor_x, anchor_y)
            if tile is not None and tile.building is not None:
                return tile.building
        return None

    def empty_spot_covering(self, tile_x, tile_y):
        """Return (kind, anchor_x, anchor_y) of an EMPTY build spot
        whose footprint covers a tile, or None.

        Empty = the anchor tile still holds no building. Lets collision
        treat unbuilt multi-tile spots as solid over their whole
        footprint (buildings can't be walked into existence).
        """
        for anchor_x, anchor_y, fw, fh in self._footprint_covered(
            tile_x,
            tile_y,
        ):
            tile = self.get_tile(anchor_x, anchor_y)
            if (
                tile is not None
                and tile.building is None
                and (anchor_x, anchor_y) in self.spot_types
            ):
                # The spot's own footprint bound is already enforced by
                # _footprint_covered (fw/fh from the marker).
                return (
                    self.spot_types[(anchor_x, anchor_y)],
                    anchor_x,
                    anchor_y,
                )
        return None

    def native_ground_rect(self, world_rect):
        """The given world-px region as a source rect into
        ground_texture_native (its OWN resolution, not the world's).

        The native image is stretched to the full world strip in both
        axes, so the mapping is a plain proportional fit (separate
        factors for x and y keep any image/strip aspect mismatch
        identical to the pre-scaled texture's stretch); the rect is
        clamped inside the image. Callers subsurface() this crop and
        smoothscale it to the CLOSE window — per-screen-pixel 4K
        detail instead of the 4x-upscaled pre-scaled texture.
        """
        native = self.ground_texture_native
        if native is None:
            return None
        world_w = self.width * TILE_SIZE
        world_h = self.height * TILE_SIZE
        kx = native.get_width() / world_w
        ky = native.get_height() / world_h
        left = max(0, min(native.get_width() - 1, int(round(world_rect.left * kx))))
        top = max(0, min(native.get_height() - 1, int(round(world_rect.top * ky))))
        right = max(left + 1, min(
            native.get_width(),
            int(round((world_rect.left + world_rect.width) * kx)),
        ))
        bottom = max(top + 1, min(
            native.get_height(),
            int(round((world_rect.top + world_rect.height) * ky)),
        ))
        return pygame.Rect(left, top, right - left, bottom - top)

    def _draw_buildings(self, screen, camera_x, view_rect=None):
        """Draw every anchored building once (grid scan); shared by
        both graphics modes so buildings always sit on top of the
        ground, never under neighboring tiles. A building is skipped
        when its footprint lies fully outside the culled viewport."""
        for row in self.tiles:
            for tile in row:
                if tile.building:
                    build = tile.building
                    if view_rect is not None:
                        # Culled: build the footprint rect from the
                        # building's own table-driven footprint sizes
                        # (all building classes set footprint_tiles).
                        fw_px, fh_px = (
                            TILE_SIZE * n
                            for n in getattr(build, "footprint_tiles", (1, 1))
                        )
                        footprint = pygame.Rect(
                            build.tile_x * TILE_SIZE,
                            build.tile_y * TILE_SIZE,
                            fw_px,
                            fh_px,
                        )
                        if not footprint.colliderect(view_rect):
                            continue
                    build.draw(screen, camera_x)

    def draw(self, screen, camera_x, view_rect=None, skip_ground=False):
        """Draw the battlefield, then outline build spots for the player.

        SPRITES mode: the ground is the scaled map floor texture —
        one blit sized to the whole map strip, buildings drawn over
        it (tiles themselves are skipped: the texture IS the ground).
        BLOCKS mode: per-tile flat colors exactly as before, no
        textures at all (block toggle contract).

        skip_ground (CLOSE view only): draw buildings but NOT the
        ground texture. AssaultPhase renders the CLOSE window's
        ground straight from the NATIVE 4K image at screen
        resolution (its 4x zoom needs more detail than the
        world-resolution strip contains), so the caller then blits
        only this surface's ENTITY content over that ground; ground
        must not be baked in underneath. Ignored in BLOCKS mode.

        The mode is queried EVERY frame (single source: render_mode;
        never cached), so G flips textured floor <-> tile palette live.

        view_rect (world px, optional) = viewport culling: when given
        (CLOSE zoom), only the ground region, tiles, buildings, and
        spot outlines intersecting the rect are drawn; pixels outside
        stay stale on the offscreen surface, which is invisible
        because the CLOSE zoom subsamples exactly this window.
        """
        if self.ground_texture and render_mode.is_sprite():
            if not skip_ground:
                if view_rect is None:
                    screen.blit(self.ground_texture, (-camera_x, 0))
                else:
                    # Culled ground: blit ONLY the visible world region —
                    # the clipped blit area is the window's intersection
                    # with the texture, placed at its own world coords.
                    clip = view_rect.clip(
                        pygame.Rect(
                            0, 0,
                            self.width * TILE_SIZE,
                            self.height * TILE_SIZE,
                        ),
                    )
                    if clip.width > 0 and clip.height > 0:
                        screen.blit(
                            self.ground_texture,
                            (clip.x - camera_x, clip.y),
                            clip,
                        )

            # Buildings ride on tiles, so draw them here over the
            # texture (units/bullets/pickups are drawn later, on top
            # of the whole tilemap, by the battle state).
            self._draw_buildings(screen, camera_x, view_rect)
        else:
            # Tile grid first, buildings second: a multi-tile building
            # (2x2 MG) must never have its right/bottom footprint
            # overpainted by the fill of its neighbor tiles. The row/
            # column range is sliced to the visible window when culled.
            if view_rect is None:
                x_lo, x_hi, y_lo, y_hi = 0, self.width, 0, self.height
            else:
                x_lo = max(0, view_rect.left // TILE_SIZE)
                x_hi = min(self.width, view_rect.right // TILE_SIZE + 1)
                y_lo = max(0, view_rect.top // TILE_SIZE)
                y_hi = min(self.height, view_rect.bottom // TILE_SIZE + 1)

            for y in range(y_lo, y_hi):
                for x in range(x_lo, x_hi):
                    self.tiles[y][x].draw(screen, camera_x)

            self._draw_buildings(screen, camera_x, view_rect)

        # Debug/assist overlay: ONE green outline spanning each EMPTY
        # build spot's FULL footprint (the MG's 2x2 reads as a single
        # square to place into, in both graphics modes). Placed spots
        # draw nothing: once the building exists the guide line is
        # removed and the occupied space speaks for itself. Culled to
        # the viewport like everything else.
        for (x, y), spot_kind in self.spot_types.items():
            tile = self.tiles[y][x]
            if tile.building is not None:
                continue

            build_kind = (
                spot_kind[len("enemy_"):]
                if spot_kind.startswith("enemy_")
                else spot_kind
            )
            fw, fh = BUILD_FOOTPRINTS.get(build_kind, (1, 1))

            px = x * TILE_SIZE - camera_x
            py = y * TILE_SIZE
            if (
                view_rect is not None
                and not pygame.Rect(
                    px + camera_x, py, fw * TILE_SIZE, fh * TILE_SIZE,
                ).colliderect(view_rect)
            ):
                continue

            pygame.draw.rect(
                screen,
                (0, 255, 0),
                (px + 4, py + 4, fw * TILE_SIZE - 8, fh * TILE_SIZE - 8),
                1,
            )
