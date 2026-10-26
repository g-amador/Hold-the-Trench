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

        # Ground floor texture for SPRITES mode: map1<scene>.jpeg
        # scaled ONCE to the whole battlefield strip (tiles are then
        # skipped at draw time — the texture IS the ground). The scene
        # letter comes from the shared battle roll, so ground and
        # buildings always match (map1a summer / map1c winter).
        self.ground_texture = None
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

        The map tilemap is built before the battle (the menu creates
        it), i.e. before roll_scene() — so AssaultPhase calls this
        right after rolling to re-pick the ground alongside the
        buildings (map1a.jpeg summer day / map1c.jpeg winter day).
        Loaded through utils/image_loader (cached, pre-scaled to the
        world strip); a missing file keeps ground_texture None and
        draw() falls back to tile rendering instead of crashing.
        """
        try:
            self.ground_texture = load_image(
                ground_texture_filename(),
                alpha=False,
                size=(self.width * TILE_SIZE, self.height * TILE_SIZE),
            )
        except FileNotFoundError:
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

    def _draw_buildings(self, screen, camera_x):
        """Draw every anchored building once (grid scan); shared by
        both graphics modes so buildings always sit on top of the
        ground, never under neighboring tiles."""
        for row in self.tiles:
            for tile in row:
                if tile.building:
                    tile.building.draw(screen, camera_x)

    def draw(self, screen, camera_x):
        """Draw the battlefield, then outline build spots for the player.

        SPRITES mode: the ground is the scaled map.png floor texture —
        one blit sized to the whole map strip, buildings drawn over
        it (tiles themselves are skipped: the texture IS the ground).
        BLOCKS mode: per-tile flat colors exactly as before, no
        textures at all (block toggle contract).

        The mode is queried EVERY frame (single source: render_mode;
        never cached), so G flips textured floor <-> tile palette live.
        """
        if self.ground_texture and render_mode.is_sprite():
            screen.blit(self.ground_texture, (-camera_x, 0))

            # Buildings ride on tiles, so draw them here over the
            # texture (units/bullets/pickups are drawn later, on top
            # of the whole tilemap, by the battle state).
            self._draw_buildings(screen, camera_x)
        else:
            # Tile grid first, buildings second: a multi-tile building
            # (2x2 MG) must never have its right/bottom footprint
            # overpainted by the fill of its neighbor tiles.
            for y in range(self.height):
                for x in range(self.width):
                    self.tiles[y][x].draw(screen, camera_x)

            self._draw_buildings(screen, camera_x)

        # Debug/assist overlay: ONE green outline spanning each EMPTY
        # build spot's FULL footprint (the MG's 2x2 reads as a single
        # square to place into, in both graphics modes). Placed spots
        # draw nothing: once the building exists the guide line is
        # removed and the occupied space speaks for itself.
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
            pygame.draw.rect(
                screen,
                (0, 255, 0),
                (px + 4, py + 4, fw * TILE_SIZE - 8, fh * TILE_SIZE - 8),
                1,
            )
