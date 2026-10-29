"""
Artillery building.

No-man's-land bombardment (user design): shells do NOT target units.
Each shot lands on a random UNUSED tile in no-man's-land — strictly
between the row-0 '|' markers (full-height wall in STATIC_MAP) when the
map has the pair, so impacts stay solely between the two MG nest lines;
maps without the pair fall back to a 14-18-tiles-ahead strip. Columns
are center-weighted near the field's middle; rows swing UNIFORMLY over
the strip's full height ("not always center — sometimes more up, more
down"). Each impact leaves a brief red dot and damages any standing
unit on the tile + its 8 neighbours for 20 (half of an infantry unit's
40 hp). A gun never hits the same tile twice; when the band is
exhausted it stands down.

Art by FACTION (factions.ARTILLERY_IMAGE: allies = unit_cannon_fr,
axis = unit_heavy_howitzer_ger), drawn across the footprint; missing
art falls back to the grey block (never crash).
"""

import random

import pygame

from config import TILE_SIZE, GREY, BUILDING_HP, footprint_for
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from systems.factions import (
    artillery_filename,
    artillery_nation_for_side,
    scaled_damage,
)
from utils.image_loader import load_image, load_first_image_named
from world.trench_generator import STATIC_MAP, no_mans_land_bounds


class Artillery:

    # Barrage pattern (user-tuned): impacts land in the no-man's-land
    # strip between the row-0 '|' markers when a map HAS the pair
    # (" Solely between my and the enemy MG nests"); without the
    # markers the fallback band spans 14-18 tiles toward the front.
    # Columns are center-weighted (the window's own middle); rows span
    # the strip's FULL height uniformly (see CENTER_ROW). 20 damage =
    # half of an infantry unit (hp 40).
    AHEAD_MIN = 14
    AHEAD_MAX = 18
    ROW_SPREAD = 5
    SPLASH_DAMAGE = 20
    DOT_TIME = 0.5      # seconds the red blast stays visible
    SHELL_DELAY = 1.0   # seconds the shell takes to land (quick-dirty)
    MUZZLE_TIME = 1.0   # seconds the yellow muzzle flash stays visible
    # Vertical pin of the impact rows, in tiles: None (DEFAULT) = no
    # pin — rows UNIFORM over the strip's full height (user: shells
    # should swing up AND down the field, not cluster mid-field).
    # Set a number to confine rows to that row +- ROW_SPREAD instead.
    CENTER_ROW = None

    def __init__(self, tile_x, tile_y, is_enemy=False, faction="allies"):
        # type strings match the map spot_types keys.
        self.type = "enemy_artillery" if is_enemy else "artillery"
        self.is_enemy = is_enemy
        self.faction = faction

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Footprint: faction-aware (user rule — the GERMAN howitzer is
        # a 3x2 plot, the allied cannon line stays 4x2; config's
        # FACTION_FOOTPRINT_OVERRIDES via footprint_for). The drawn
        # sprite/block, fire origin, and TileMap viewport culling all
        # read footprint_tiles (collision comes from the same call
        # through tilemap._footprint_covered).
        self.footprint_tiles = footprint_for("artillery", faction)
        self.width, self.height = (
            TILE_SIZE * n for n in self.footprint_tiles
        )

        # Nation whose ARTILLERY handicap this gun fires with (allies
        # read as french 75s, axis as german howitzers).
        self.nation = artillery_nation_for_side(faction)

        # Objective hp (destructible building, config table).
        self.hp = BUILDING_HP["artillery"]
        self.dead = False

        # Firing stats: steady barrage cadence; cooldown is subtracted
        # in update, hence starts at 0.
        self.fire_rate = 1.5
        self.cooldown = 0

        # Barrage bookkeeping: never hit the same tile twice (per gun),
        # and remember live red-dot impact markers.
        self.used_tiles = set()  # impact tiles already committed
        self.impacts = []        # [x_px, y_px, ttl_seconds] live blasts
        self.muzzles = []        # [x_px, y_px, ttl_seconds] yellow flashes
        # Pending shells: [col, row, ttl_seconds] — fired, not landed.
        self.pending = []

        # Art by FACTION (allies = french cannon, axis = heavy
        # howitzer), scaled across the footprint. Enemy art flips so
        # the gun barrel points WEST into no-man's-land (user: "enemy
        # artillery should be pointing to the west and image
        # flipped"). Missing file -> None: draw() falls back to the
        # grey block instead of crashing.
        self.image, image_file = load_first_image_named(
            [artillery_filename(faction)],
            alpha=True,
            size=(self.width, self.height),
        )
        if self.is_enemy and self.image is not None:
            self.image = pygame.transform.flip(self.image, True, False)

        # Native-resolution copy of the SAME art file for the CLOSE
        # view's hires blit (flipped for enemies, like the world art).
        self.image_native = None
        if image_file is not None:
            try:
                self.image_native = load_image(image_file, alpha=True)
            except FileNotFoundError:
                self.image_native = None
            if self.image_native is not None and self.is_enemy:
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
        return pygame.Rect(
            self.tile_x * TILE_SIZE,
            self.tile_y * TILE_SIZE,
            self.width,
            self.height,
        )

    def update(self, dt, enemies, bullets):
        """Shell one random unused tile in the no-man's-land band.

        Sequence (user quick-dirty illustration): the shot lights a
        small YELLOW muzzle flash in front of the gun; the shell flies for
        `SHELL_DELAY` seconds; then the red blast pops on the impact
        tile and the splash applies. `enemies` is the opposing unit
        list passed by the battle state; anything standing on the
        impact tile or its 8 neighbours takes the splash damage at
        LANDING time (the live list — never a stale snapshot).
        `bullets` is kept for signature compatibility (shells are
        instant, none are flown). A destroyed gun stands down
        entirely.
        """
        if self.dead:
            return

        # Red blast markers tick down; expired ones are dropped.
        if self.impacts:
            for imp in self.impacts:
                imp[2] -= dt / 1000
            self.impacts = [imp for imp in self.impacts if imp[2] > 0]

        # Yellow muzzle squares tick down; expired ones are dropped.
        if self.muzzles:
            for m in self.muzzles:
                m[2] -= dt / 1000
            self.muzzles = [m for m in self.muzzles if m[2] > 0]

        # Shell flight: pending shells land after SHELL_DELAY; the
        # blast + splash use THIS frame's opposing list (the state
        # rebinds its unit lists every frame, so store only the
        # tile — never the list — at fire time).
        if self.pending:
            for entry in self.pending:
                entry[2] -= dt / 1000
            landed = [e for e in self.pending if e[2] <= 0]
            self.pending = [e for e in self.pending if e[2] > 0]
            for col, row, _t in landed:
                self._land_shell(col, row, enemies)

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

        # Muzzle flash marker (USER: "a little yellow in front of the
        # artillery", not a square; user choice: flash on the TOP ROW,
        # beside the barrel tip). The marker sits on the tile directly
        # in front of the footprint's leading edge on the FIRST
        # footprint row — the old version offset down half a tile,
        # which straddled the 2-row boundary and read as sitting on
        # the y+1 cell (user report: "yellow dot on the x=4 and y=1
        # cell"); the render pass draws it as a SMALL yellow circle
        # fully inside that top-row tile. Enemies mirror to the west.
        dir_x = -1 if self.is_enemy else 1
        if dir_x > 0:
            mx = (self.tile_x + self.footprint_tiles[0]) * TILE_SIZE
        else:
            mx = (self.tile_x - 1) * TILE_SIZE
        my = self.tile_y * TILE_SIZE
        self.muzzles.append([mx, my, self.MUZZLE_TIME])

        # The shell is in flight: the blast lands after SHELL_DELAY.
        self.pending.append([col, row, self.SHELL_DELAY])

        self.cooldown = self.fire_rate

    def _land_shell(self, col, row, enemies):
        """Shell touchdown: red blast marker + splash damage."""
        # Blast marker: brief red flash at the tile's center.
        ix = col * TILE_SIZE + TILE_SIZE / 2
        iy = row * TILE_SIZE + TILE_SIZE / 2
        self.impacts.append([ix, iy, self.DOT_TIME])

        # Damage per shell, scaled by this gun's nation's ARTILLERY
        # handicap (fr 1.1 / ger 1.1 / brit 1.05 / aust 1.0 — factions
        # table).
        damage = scaled_damage(self.nation, "artillery", self.SPLASH_DAMAGE)

        # Splash: hit tile + its 8 neighbours; damage any standing
        # unit regardless of side ("any unit", user choice).
        for unit in enemies:
            if unit.dead:
                continue
            uc = int(unit.x // TILE_SIZE)
            ur = int(unit.y // TILE_SIZE)
            if abs(uc - col) <= 1 and abs(ur - row) <= 1:
                unit.take_damage(damage)

    def _pick_impact_tile(self):
        """Pick a random UNUSED (col, row) in this gun's barrage band.

        Front/bounds: when the map carries the row-0 '|' pair both
        sides sample strictly between the markers (solely the field);
        otherwise the band is center column +14..+18 toward the
        enemy side. COLUMNS are CENTER-WEIGHTED (triangular, peaked
        on the field window's middle); ROWS span the field's FULL
        height UNIFORMLY (user: "not always center — sometimes more
        up, more down") unless CENTER_ROW pins them to a
        +-ROW_SPREAD band. The random pick never repeats a tile and
        stands down (None) when every band tile is already shelled;
        the exhausted band = window interior x full map height
        (e.g. 9 cols x 46 rows = 414 tiles for the wall map).
        """
        cx_tile = round(self.tile_x + self.footprint_tiles[0] / 2)
        dir_x = -1 if self.is_enemy else 1

        map_w = len(STATIC_MAP[0])
        map_h = len(STATIC_MAP)

        # Impact columns: when the map carries the '|' pair (user rule:
        # shells hit SOLELY in no-man's-land, between MY and the enemy
        # MG lines), both sides sample the SAME strip strictly between
        # the markers. Maps without the pair keep the legacy
        # 14-18-tiles-ahead band. Columns keep the triangular
        # center-weighting, now peaked on the window's own middle.        
        bounds = no_mans_land_bounds()
        if bounds is not None:
            col_low, col_high = bounds[0] + 1, bounds[1] - 1
        else:
            col_low, col_high = (
                cx_tile + dir_x * self.AHEAD_MIN,
                cx_tile + dir_x * self.AHEAD_MAX,
            )
            col_low, col_high = min(col_low, col_high), max(col_low, col_high)
        col_low = max(0, col_low)
        col_high = min(map_w - 1, col_high)
        if col_low > col_high:
            return None
        mid_col = (col_low + col_high) / 2
        col_half = (col_high - col_low) / 2

        # Impact rows (user tuning v3: "not ALWAYS center — sometimes
        # more up, more down"): UNIFORM over the no-man's-land strip's
        # FULL height. The old triangular peak on the field's center
        # row made nearly every shell land mid-field. An explicit
        # CENTER_ROW pin (subclass/testing override) keeps a
        # +-ROW_SPREAD uniform band instead.
        if self.CENTER_ROW is not None:
            row_lo = max(0, self.CENTER_ROW - self.ROW_SPREAD)
            row_hi = min(map_h - 1, self.CENTER_ROW + self.ROW_SPREAD)
        else:
            row_lo, row_hi = 0, map_h - 1

        def triangular():
            # Sum of two uniforms: peaks at 0, thins out toward +-1.
            return random.random() - random.random()

        # Sampling: columns CENTER-WEIGHTED (triangular on the window's
        # middle), rows UNIFORM across the strip. Retries land on
        # unused tiles.
        for _ in range(12):
            col = round(mid_col + triangular() * col_half)
            col = max(col_low, min(col_high, col))
            row = random.randint(row_lo, row_hi)
            if (col, row) not in self.used_tiles:
                return col, row

        # Fallback: uniform over all remaining unused field tiles so
        # the gun still exhausts its band exactly like before.
        candidates = [
            (col, row)
            for col in range(col_low, col_high + 1)
            for row in range(row_lo, row_hi + 1)
            if (col, row) not in self.used_tiles
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
