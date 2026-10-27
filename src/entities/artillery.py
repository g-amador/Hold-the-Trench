"""
Artillery building.

No-man's-land bombardment (user design): shells do NOT target units.
Each shot lands on a random UNUSED tile in a strip 14-18 tiles AHEAD
of the gun (player guns fire east, enemy guns west) spread over the
gun's row +- 5. Each impact leaves a brief red dot and damages any
standing unit on the tile + its 8 neighbours for 20 (half of an
infantry unit's 40 hp). A gun never hits the same tile twice; when
its band is exhausted it stands down.

Art by FACTION (factions.ARTILLERY_IMAGE: allies = unit_cannon_fr,
axis = unit_heavy_howitzer_ger), drawn across the footprint; missing
art falls back to the grey block (never crash).
"""

import random

import pygame

from config import TILE_SIZE, GREY, BUILD_FOOTPRINTS
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from systems.factions import artillery_filename
from utils.image_loader import load_first_image
from world.trench_generator import STATIC_MAP


class Artillery:

    # Barrage pattern (user-tuned): impact column = gun center 14-18
    # tiles toward the front; impact row = gun center row +-5. 20
    # damage = half of one infantry unit (infantry hp = 40).
    AHEAD_MIN = 14
    AHEAD_MAX = 18
    ROW_SPREAD = 5
    SPLASH_DAMAGE = 20
    DOT_TIME = 0.5  # seconds a red impact dot stays visible

    def __init__(self, tile_x, tile_y, is_enemy=False, faction="allies"):
        # type strings match the map spot_types keys.
        self.type = "enemy_artillery" if is_enemy else "artillery"
        self.is_enemy = is_enemy
        self.faction = faction

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Footprint/table-driven (user set artillery to 4x2): the
        # drawn sprite/block, fire origin, and TileMap viewport
        # culling all read footprint_tiles (collision comes from the
        # same table via tilemap._footprint_covered).
        self.footprint_tiles = BUILD_FOOTPRINTS.get("artillery", (1, 1))
        self.width, self.height = (
            TILE_SIZE * n for n in self.footprint_tiles
        )

        # Firing stats: steady barrage cadence; cooldown is subtracted
        # in update, hence starts at 0.
        self.fire_rate = 1.5
        self.cooldown = 0

        # Barrage bookkeeping: never hit the same tile twice (per gun),
        # and remember live red-dot impact markers.
        self.used_tiles = set()
        self.impacts = []  # [x_px, y_px, ttl_seconds] live dots

        # Art by FACTION (allies = french cannon, axis = heavy
        # howitzer), scaled across the footprint (4x2 = 128x64).
        # Missing file -> None: draw() falls back to the grey block
        # instead of crashing.
        self.image = load_first_image(
            [artillery_filename(faction)],
            alpha=True,
            size=(self.width, self.height),
        )

    def update(self, dt, enemies, bullets):
        """Shell one random unused tile in the no-man's-land band.

        `enemies` is the opposing unit list passed by the battle
        state; anything standing on the impact tile or its 8
        neighbours takes the splash damage. `bullets` is kept for
        signature compatibility (shells are instant, none are flown).
        """
        # Red-dot markers tick down; expired ones are dropped.
        if self.impacts:
            for imp in self.impacts:
                imp[2] -= dt / 1000
            self.impacts = [imp for imp in self.impacts if imp[2] > 0]

        # Reload gate: no shots until the cooldown drains to 0.
        self.cooldown -= dt / 1000
        if self.cooldown > 0:
            return

        tile = self._pick_impact_tile()
        if tile is None:
            # Every tile in this gun's band was already shelled: the
            # gun stands down rather than repeating ground.
            return
        col, row = tile
        self.used_tiles.add((col, row))

        # Impact marker: brief red dot at the tile's center.
        ix = col * TILE_SIZE + TILE_SIZE / 2
        iy = row * TILE_SIZE + TILE_SIZE / 2
        self.impacts.append([ix, iy, self.DOT_TIME])

        # Splash: hit tile + its 8 neighbours; damage any standing
        # unit regardless of side ("any unit", user choice).
        for unit in enemies:
            if unit.dead:
                continue
            uc = int(unit.x // TILE_SIZE)
            ur = int(unit.y // TILE_SIZE)
            if abs(uc - col) <= 1 and abs(ur - row) <= 1:
                unit.take_damage(self.SPLASH_DAMAGE)

        self.cooldown = self.fire_rate

    def _pick_impact_tile(self):
        """Pick a random unused (col, row) in this gun's barrage band.

        Front = toward the enemy side (player guns anchored on the
        west half fire EAST). Band: center column +14..+18 ahead,
        rows = center row +- ROW_SPREAD, clipped to the map.
        """
        cx_tile = round(self.tile_x + self.footprint_tiles[0] / 2)
        cy_tile = round(self.tile_y + self.footprint_tiles[1] / 2)
        dir_x = -1 if self.is_enemy else 1

        map_w = len(STATIC_MAP[0])
        map_h = len(STATIC_MAP)
        candidates = [
            (col, row)
            for advance in range(self.AHEAD_MIN, self.AHEAD_MAX + 1)
            for row in range(cy_tile - self.ROW_SPREAD,
                             cy_tile + self.ROW_SPREAD + 1)
            for col in (cx_tile + dir_x * advance,)
            if 0 <= col < map_w and 0 <= row < map_h
            and (col, row) not in self.used_tiles
        ]
        if not candidates:
            return None
        return random.choice(candidates)

    def draw(self, screen, camera_x):
        """Faction art in SPRITES mode; flat grey block otherwise.

        The artillery image is keyed by FACTION (allied nations share
        the french cannon; axis = heavy howitzer), scaled across the
        footprint (4x2) and blitted directly on the ground (sprite
        rule: no underlay). Block mode / missing art keeps the grey
        block, now covering the full footprint.
        """
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE

        if render_mode.is_sprite() and self.image is not None:
            screen.blit(self.image, (px, py))
            return

        draw_unit_block(
            screen,
            px,
            py,
            self.width,
            self.height,
            -1 if self.is_enemy else 1,
            GREY,
        )
