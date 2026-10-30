"""
Main gameplay state: the battle screen.

Owns one complete simulation frame of fighting: it steps the player,
barracks, bunkers, MG nests, and artillery; resolves both bullet
lists; runs gold pickups; handles automatic building with partial
payments; and switches to GameOverState / WinState when a terminal
condition is reached. The engine Game delegates handle_event / update
/ render here, so this class is the heart of the game loop.
"""

import pygame
import math

from collections import Counter, deque

from states.game_over import GameOverState
from states.win_state import WinState

from systems.economy_system import EconomySystem, BUILD_COSTS
from systems.building_query import BuildingQuery

from ui.hud import HUD

from graphics import render_mode

from entities.player import Player
from entities.mg_nest import MGNest
from entities.bunker import Bunker
from entities.artillery import Artillery
from entities.armor import ArmorUnit
from entities.airplane import AirplaneUnit
from entities.barracks import Barracks
from entities.static_building import AirField, TankFactory
from entities.gold_pickup import COIN_SIZE

from systems.factions import other, roll_scene

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TILE_SIZE,
    HUD_BAR_HEIGHT,
    WHITE,
    RED,
    YELLOW,
    BUILD_FOOTPRINTS,
    footprint_for,
    VIEW_FULL,
    VIEW_CLOSE,
    CLOSE_VIEW_TILES,
)


# Map spot_type string -> player-purchasable building class
# (spot_types comes from the ASCII map's uppercase markers).
# Statics are player-buildable TOO (user: "for collisions in the
# tiles that a non-placed building occupies, if i touch either of the
# tiles it should be placed if I have cash to place them" — this was
# broken for F/K because they were not in the payable set at all):
# cost > 0 in BUILD_COSTS -> touch-and-pay; cost 0 -> free at start
# (place_zero_cost_buildings), same rules as mg/barracks/artillery.
BUILDING_CLASSES = {
    "mg": MGNest,
    "barracks": Barracks,
    "artillery": Artillery,
    "air_field": AirField,
    "tank_factory": TankFactory,
}

# Map spot_type string -> enemy building class; these are placed free
# at battle start from the map's lowercase markers (no gold involved).
ENEMY_BUILDING_CLASSES = {
    "enemy_bunker": Bunker,
    "enemy_mg": MGNest,
    "enemy_barracks": Barracks,
    "enemy_artillery": Artillery,
}

# Map spot_type string -> free ENEMY-side static classes (f/k
# markers): placed without cost when BUILD_COSTS allows (0) and never
# purchasable — NOT in BUILDING_CLASSES, so the build prompt/paying
# logic ignores them (the enemy has no payment path; the BUILD COSTS
# DEBUG GATE removes them entirely at cost > 0). The playerside
# statics moved into BUILDING_CLASSES (payable) above.
STATIC_BUILDING_CLASSES = {
    "enemy_air_field": AirField,
    "enemy_tank_factory": TankFactory,
}

# Entity cull margin in world px: entities up to a big sprite's size
# may poke into the CLOSE window from outside its rect, so draws are
# kept for anything within one footstep of the visible window.
CULL_MARGIN = 128


class AssaultPhase:
    def __init__(self, game):
        self.game = game
        # Shared world: the menu rebuilt this TileMap so the battle
        # always starts from the pristine ASCII layout.
        self.tilemap = game.tilemap

        # Sides come from the menu-selected faction: both spawners and
        # every entity read these to pick art and coin drops.
        self.player_faction = getattr(game, "selected_faction", "allies")
        self.enemy_faction = other(self.player_faction)

        # Faction-aware EMPTY-spot footprints: the axis artillery spot
        # is a 3x2 plot while the allies' stays 4x2 (config overrides;
        # placed buildings carry their own footprint either way).
        self.tilemap.set_factions(self.player_faction, self.enemy_faction)

        # One scene roll per battle. Everything scene-linked then
        # shares the same letter: the ground texture (map1_a/map1_c is
        # rebound below) and every building's art (mg nest, bunker,
        # barracks load their suffix from the rolled scene). "If _a
        # then all 3 must be _a" — one roll guarantees it.
        roll_scene()
        self.tilemap.reload_ground()

        self.hud = HUD()
        self.economy = EconomySystem()

        # Pause is battle-state-owned: SPACE (ESC as secondary) flips
        # it, rendering keeps running, and the simulation (update)
        # skips while paused.
        self.paused = False

        # Pause overlay assets, built once: translucent dim surface and
        # the two fonts (no surface/scale churn per paused frame).
        self.pause_font = pygame.font.SysFont("arial", 46)
        self.pause_hint_font = pygame.font.SysFont("arial", 20)
        self.pause_overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        self.pause_overlay.fill((0, 0, 0, 140))

        # Offscreen world view sized to the FULL map strip: the whole
        # battlefield is drawn here 1:1 (world pixels are always
        # TILE_SIZE px), then uniformly zoomed below the HUD bar in
        # render(). The zoom fits the map with ONE factor so tiles
        # always render square (never a per-axis stretch).
        # SRCALPHA: in CLOSE view the ground is NOT baked into this
        # surface (it is drawn straight from the native 4K image at
        # screen resolution), so the zoom can blit this surface's
        # leftover content (buildings, units, bullets) as a transparent
        # ENTITY layer on top of that hi-res ground. Undrawn pixels
        # must stay fully transparent instead of black.
        self.world_w_px = self.tilemap.width * TILE_SIZE
        self.world_h_px = self.tilemap.height * TILE_SIZE
        self.world_surface = pygame.Surface(
            (self.world_w_px, self.world_h_px),
            pygame.SRCALPHA,
        )

        # UNIFORM zoom state: fit_width vs fit_height, take the min so
        # nothing is cropped. The survivors afterwards (view size and
        # side-band offset) precompute every-frame math away; the map
        # aspect is rarely 1280:728 exactly, so the leftover columns
        # are centered as dark bands.
        visible_h = SCREEN_HEIGHT - HUD_BAR_HEIGHT
        self.world_zoom = min(
            SCREEN_WIDTH / self.world_w_px,
            visible_h / self.world_h_px,
        )
        self.world_view = (
            int(round(self.world_w_px * self.world_zoom)),
            int(round(self.world_h_px * self.world_zoom)),
        )
        self.world_offset_x = (SCREEN_WIDTH - self.world_view[0]) // 2

        # CLOSE view geometry ('+'/'-' keys, two views only per user):
        # a screen-wide 10-tile window around the player scaled at one
        # uniform factor so it OCCUPIES the full visible strip (no
        # side bands; 4x at 1280x768 -> 128px screen tiles).
        self.view_mode = VIEW_FULL
        self.close_window_w = CLOSE_VIEW_TILES * TILE_SIZE
        self.close_scale = SCREEN_WIDTH / self.close_window_w
        self.close_window_h = int(
            round((SCREEN_HEIGHT - HUD_BAR_HEIGHT) / self.close_scale)
        )
        self.close_view = (SCREEN_WIDTH, SCREEN_HEIGHT - HUD_BAR_HEIGHT)

        # Find the first player bunker build spot. A map without one
        # (e.g. the blank all-'.' canvas) simply has no bunker: the
        # battle then runs bunkerless — no defeat condition, no siege
        # target for enemies, and the HUD shows a flat 0 HP. The
        # bunkerless path also removes the old trench_y-based
        # fallback, which referenced a TileMap attribute that no
        # longer exists (latent crash on any markerless map).
        bunker_pos = None
        for (x, y), spot_type in self.tilemap.spot_types.items():
            if spot_type == "bunker":
                bunker_pos = (x, y)
                break

        # DEBUG COST GATE (user rule): the player bunker obeys the
        # same cost table as every other free placement — cost 0
        # (the table value today) places it, a nonzero cost turns the
        # marker back into "no bunker" and the battle runs through the
        # supported bunkerless path (no defeat condition, enemies have
        # no siege target, HUD shows a flat 0 HP).
        if bunker_pos is not None and BUILD_COSTS.get("bunker", 10**9) != 0:
            bunker_pos = None

        if bunker_pos is not None:
            bunker_x, bunker_y = bunker_pos

            # Place the bunker (faction-keyed art for both objectives).
            bunker_tile = self.tilemap.get_tile(bunker_x, bunker_y)
            if bunker_tile:
                bunker_tile.building = Bunker(
                    bunker_x,
                    bunker_y,
                    faction=self.player_faction,
                )

        # Friendly boundary.
        boundary = self.tilemap.friendly_boundary

        # Spawn search anchor: the bunker tile when one exists,
        # otherwise a middle-row tile on the map's left edge.
        anchor = bunker_pos if bunker_pos is not None else (
            0,
            self.tilemap.height // 2,
        )

        # Spawn safety (user rule: start OUTSIDE the bunker, not on
        # top of anything): walkable terrain alone is not enough —
        # the 4x4 bunker footprint, built buildings, and empty/paid
        # spot footprints (statics included) all block a spawn tile.
        def spawn_ok(x, y):
            if not self.tilemap.is_walkable(x, y):
                return False
            if self.tilemap.building_covering(x, y) is not None:
                return False
            return self.tilemap.empty_spot_covering(x, y) is None

        queue = deque([anchor])
        visited = {anchor}
        spawn_tile = None

        while queue:
            x, y = queue.popleft()

            if x < boundary and spawn_ok(x, y):
                spawn_tile = (x, y)
                break

            # Left first: the friendly side reads as "outside" the
            # bunker (the bunker grows right/down from its marker).
            for nx, ny in (
                (x - 1, y),
                (x, y - 1),
                (x, y + 1),
                (x + 1, y),
            ):
                if (
                    (nx, ny) not in visited
                    and self.tilemap.get_tile(nx, ny)
                ):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        if spawn_tile is None:
            spawn_x = 3 * TILE_SIZE
            spawn_y = (self.tilemap.height // 2) * TILE_SIZE
        else:
            spawn_x = spawn_tile[0] * TILE_SIZE
            spawn_y = spawn_tile[1] * TILE_SIZE

        self.player = Player(spawn_x, spawn_y, faction=self.player_faction)

        self.camera_x = 0

        self.gold_pickups = []
        self.bullets = []
        self.enemy_bullets = []
        self.friendlies = []
        self.enemy_barracks_units = []
        # Planes fly in their OWN per-side lists (not mixed into the
        # infantry lists): their update signature, damage rules, and
        # air-vs-ground targeting differ too much to share the loops.
        self.friendly_planes = []
        self.enemy_planes = []

        self.build_prompt_radius = 72
        self.place_enemy_buildings()
        self.place_static_buildings()
        self.place_zero_cost_buildings()

        # FPS for the HUD: smoothed frames-per-second, measured from
        # the engine's per-frame dt (ms). Engine calls update() every
        # frame, so this updates even while paused.
        self.fps = 0.0

    def handle_event(self, event):
        """Key routing: SPACE/ESC pause, G toggles art, +/- switch view.

        SPACE is THE pause key, event-based toggle per AI.md. Player
        fire is automatic (update() calls auto_fire), so there is no
        manual fire key anymore.
        """
        if event.type != pygame.KEYDOWN:
            return

        # SPACE is the pause key; ESC stays an accessible secondary.
        # Toggling on the keydown event exactly once prevents the
        # held-key repeat storm.
        if event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
            self.paused = not self.paused
            return

        # View zoom works live AND paused (it is a viewing aid, not a
        # sim action): '+' zooms IN to the CLOSE view, '-' zooms OUT
        # to FULL. Only these two views exist (config), so each key
        # sets an absolute state (idempotent, no toggle flip-flop on
        # key autorepeat). K_EQUALS covers laptops where '+' needs
        # SHIFT (it shares the '=' key).
        if event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.view_mode = VIEW_CLOSE
            return
        if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.view_mode = VIEW_FULL
            return

        # Paused: only the graphics toggle is honored while frozen;
        # any other stray keydown is ignored so nothing misfires.
        if self.paused:
            if event.key == pygame.K_g:
                render_mode.toggle()
            return

        # Live gameplay keys (event-driven only).
        if event.key == pygame.K_g:
            render_mode.toggle()

    def place_enemy_buildings(self):
        """Place enemy defenses from lowercase map markers without charging gold."""
        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            building_class = ENEMY_BUILDING_CLASSES.get(spot_type)
            if building_class is None:
                continue

            # DEBUG COST GATE (user rule, applies to BOTH sides): a
            # spot kind with a nonzero BUILD_COSTS entry is never
            # placed free. The enemy has no payment path at all, so
            # the cost table is the lever: cost 0 = exists at battle
            # start, cost > 0 = removed from the battle entirely.
            if BUILD_COSTS.get(spot_type, 10**9) != 0:
                continue

            tile = self.tilemap.get_tile(tile_x, tile_y)
            # An occupied tile is skipped: first marker wins, so hand
            # edits to the map never silently overwrite a building.
            if tile is None or tile.building is not None:
                continue

            if spot_type == "enemy_bunker":
                tile.building = Bunker(
                    tile_x,
                    tile_y,
                    is_enemy=True,
                    faction=self.enemy_faction,
                )
            else:
                tile.building = building_class(
                    tile_x,
                    tile_y,
                    is_enemy=True,
                    faction=self.enemy_faction,
                )

    def place_static_buildings(self):
        """Place free statics from the enemy f/k markers.

        Same placement as enemy defenses: free at battle start (when
        BUILD_COSTS allows — see the DEBUG COST GATE below), open
        tiles only, no payment. The PLAYER-side statics (F/K markers)
        live in BUILDING_CLASSES since the user made them payable:
        cost 0 -> place_zero_cost_buildings, cost > 0 -> touch-and-pay.
        Enemy-side statics get the enemy faction for art behavior
        (german buildings/planes) and spawn into the enemy's lists
        via their own is_enemy flag.
        """
        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            building_class = STATIC_BUILDING_CLASSES.get(spot_type)
            if building_class is None:
                continue

            # DEBUG COST GATE (user rule, applies to BOTH sides):
            # statics are never purchasable either, so a nonzero
            # BUILD_COSTS entry means the static does not exist in
            # this battle — on the player side (F/K) as well as the
            # enemy side (f/k). Cost 0 keeps the free placement.
            if BUILD_COSTS.get(spot_type, 10**9) != 0:
                continue

            tile = self.tilemap.get_tile(tile_x, tile_y)
            if tile is None or tile.building is not None:
                continue

            is_enemy = spot_type.startswith("enemy_")
            tile.building = building_class(
                tile_x,
                tile_y,
                faction=(
                    self.enemy_faction if is_enemy else self.player_faction
                ),
                is_enemy=is_enemy,
            )

    def place_zero_cost_buildings(self):
        """Auto-place every purchasable spot whose BUILD_COSTS entry is 0.

        Cost 0 means FREE per the user's tuning: the building is placed
        at battle start exactly like the statics/enemy markers — NO
        gold, NO prompt, NO contact needed. Spots with a real price
        still go through the touch-and-pay path (auto_place_if_possible),
        so this pass must run BEFORE the player can reach anything.
        """
        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            building_class = BUILDING_CLASSES.get(spot_type)
            if building_class is None:
                continue

            if BUILD_COSTS.get(spot_type, 10**9) != 0:
                continue

            tile = self.tilemap.get_tile(tile_x, tile_y)
            # Same first-marker-wins rule: an occupied tile is skipped
            # (e.g. a static or enemy defense already placed there).
            if tile is None or tile.building is not None:
                continue

            tile.building = building_class(
                tile_x,
                tile_y,
                faction=self.player_faction,
            )

    def auto_place_if_possible(self):
        """Pay toward a building when touching its spot; build when fully paid."""
        # Contact = the player's hitbox, slightly inflated for
        # forgiveness while brushing past a spot marker.
        player_rect = self.player.get_hitbox().inflate(2, 2)

        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            building_class = BUILDING_CLASSES.get(spot_type)
            if building_class is None:
                continue

            tile = self.tilemap.get_tile(tile_x, tile_y)
            if tile is None or tile.building is not None:
                continue

            # Contact against the spot's FULL footprint: touching ANY
            # tile of the MG's 4x4 pays into it, not only the marker.
            # Faction-aware: the allies/axis artillery spot differs
            # (axis 3x2; player spots use the player's side).
            fw, fh = footprint_for(spot_type, self.player_faction)
            spot_rect = pygame.Rect(
                tile_x * TILE_SIZE,
                tile_y * TILE_SIZE,
                fw * TILE_SIZE,
                fh * TILE_SIZE,
            )

            if not player_rect.colliderect(spot_rect):
                continue

            cost = BUILD_COSTS[spot_type]
            key = (tile_x, tile_y)

            # Remember payments even while the spot is still empty.
            paid = self.tilemap.paid_amount.get(key, 0)
            remaining = max(0, cost - paid)
            payment = min(remaining, max(0, self.economy.gold))

            # Brick-by-brick economics: touch a spot and available gold
            # goes into it; a building only appears once the FULL cost
            # is covered, so the player can fund work over several trips.
            if payment > 0:
                self.economy.spend(payment)
                paid += payment
                self.tilemap.paid_amount[key] = paid

            # Only construct the building once its full cost is paid.
            if paid >= cost:
                tile.building = building_class(
                    tile_x,
                    tile_y,
                    faction=self.player_faction,
                )
                # One construction per pass: the next spot waits a frame,
                # which keeps placement readable.
                return

    def _collect_gold_and_pay_debts(self):
        """Collect gold and apply available gold to unpaid buildings."""
        remaining_gold = []

        for gold in self.gold_pickups:
            collected = gold.update(0, self.player)

            if collected:
                # dt=0 freezes the bob animation for this instant check:
                # it answers "would the player collect this right now"
                # without simulating the pickup.
                self.economy.gold += gold.amount
            else:
                remaining_gold.append(gold)

        self.gold_pickups = remaining_gold

        # Pay existing debts using available gold.
        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            if spot_type not in BUILDING_CLASSES:
                continue

            tile = self.tilemap.get_tile(tile_x, tile_y)
            if tile is None or tile.building is None:
                continue

            cost = BUILD_COSTS[spot_type]
            paid = self.tilemap.paid_amount.get((tile_x, tile_y), 0)
            debt = max(0, cost - paid)

            payment = min(debt, max(0, self.economy.gold))
            if payment > 0:
                self.economy.spend(payment)
                self.tilemap.paid_amount[(tile_x, tile_y)] = paid + payment

    def update(self, dt):
        """One simulation step of the whole battle.

        Order matters: buildings spawn units first, then the player +
        bullets fight, then infantry melee resolves, then supporting
        buildings fire, then gold/payments, then win/lose checks.

        While paused this method returns before simulating anything:
        the engine keeps calling update + render, so the window stays
        responsive and the frozen battle keeps being drawn under the
        overlay.
        """
        # FPS metering happens even while paused (the engine still
        # calls update every frame): dt IS the last frame's duration
        # in ms (clock.tick return), so frames-per-second is 1000/dt.
        # A short exponential smoothing keeps the HUD number stable.
        if dt > 0:
            instant = 1000.0 / dt
            self.fps = (
                instant if self.fps <= 0
                else 0.9 * self.fps + 0.1 * instant
            )

        # Paused: freeze the whole simulation (render still runs).
        if self.paused:
            return

        # Retrieve all buildings from the tilemap.
        buildings = BuildingQuery.get_all_buildings(self.tilemap)

        # Split the building roster by side, ALIVE only: destructible
        # buildings (all of them, since BUILDING_HP) take damage from
        # tank shells, plane bombs, and bunker-bound bullets; the dead
        # ones stop firing, spawning, and being targeted.
        enemy_buildings = [
            b for b in buildings
            if b.is_enemy and not b.is_destroyed()
        ]
        player_buildings = [
            b for b in buildings
            if not b.is_enemy and not b.is_destroyed()
        ]

        player_bunkers = [
            b for b in buildings
            if isinstance(b, Bunker) and not b.is_enemy
        ]
        enemy_bunkers = [
            b for b in buildings
            if isinstance(b, Bunker) and b.is_enemy
        ]

        # Update the player.
        self.player.update(
            dt,
            self.tilemap,
            self.enemy_barracks_units,
        )

        # Update barracks and spawn infantry.
        for building in buildings:
            if not isinstance(building, Barracks):
                continue

            if building.is_enemy:
                building.update(dt, self.enemy_barracks_units)
            else:
                building.update(dt, self.friendlies)

        # Update bunkers.
        for bunker in player_bunkers + enemy_bunkers:
            bunker.update()

        # Player targets enemy infantry and enemy bunkers.
        player_targets = [
            enemy for enemy in self.enemy_barracks_units
            if not enemy.dead
        ]
        player_targets.extend(
            bunker for bunker in enemy_bunkers
            if not bunker.dead
        )

        # Temporarily disabled player shooting.
        self.player.auto_fire(dt, player_targets, self.bullets)

        # Automatically build when close to a valid build spot.
        self.auto_place_if_possible()

        # Camera: pinned to the map origin. The uniform-zoom view fits
        # the ENTIRE battlefield below the HUD bar, so any pan would
        # only crop parts the player is already seeing in full.
        self.camera_x = 0
        
        # Player bullets damage enemy infantry or enemy bunkers.
        # Resolution is a filter loop: every surviving bullet is either
        # re-listed, or a hit/removal is folded into remaining_bullets.
        remaining_bullets = []

        for bullet in self.bullets:
            bullet.update(dt)

            # Self-destructed (out of world) shots are simply dropped.
            if getattr(bullet, "dead", False):
                continue

            hit = False

            for enemy in self.enemy_barracks_units:
                if enemy.dead:
                    continue

                # ARMOR RULE: infantry/player/MG shots can never hurt
                # armored units — they pass through (only artillery
                # splash and tank shells damage armor). Bullets keep
                # flying on armor contact so they can still hit an
                # infantry unit behind the tank.
                if isinstance(enemy, ArmorUnit) and not bullet.armor_damage:
                    continue

                if bullet.get_hitbox().colliderect(enemy.get_hitbox()):
                    enemy.take_damage(bullet.damage)
                    hit = True
                    break

            # Fallback to objectives when no unit was hit. Buildings
            # are destructible: armor_damage bullets (tank shells)
            # hurt ANY enemy building; plane MG bullets never touch
            # buildings (bombs only); other shots keep the old
            # bunker-only rule (shooting bunkers is a core win route).
            if not hit and bullet.armor_damage:
                for building in enemy_buildings:
                    if bullet.get_hitbox().colliderect(
                        building.get_hitbox()
                    ):
                        building.take_damage(bullet.damage)
                        hit = True
                        break
            elif not hit and getattr(bullet, "can_damage_buildings", True):
                for bunker in enemy_bunkers:
                    if bunker.dead:
                        continue

                    if bullet.get_hitbox().colliderect(
                        bunker.get_hitbox()
                    ):
                        bunker.take_damage(bullet.damage)
                        hit = True
                        break

            # Enemy planes: player-side bullets (and plane MG fire)
            # reach the opposing planes in the air (bullets with no
            # armor damage chip planes like infantry; plane bullets
            # are armorless by design, dogfights stay infantry-like).
            if not hit:
                for plane in self.enemy_planes:
                    if plane.dead:
                        continue

                    if bullet.get_hitbox().colliderect(
                        plane.get_hitbox()
                    ):
                        plane.take_damage(bullet.damage)
                        hit = True
                        break

            # Unhit bullets survive to the next frame.
            if not hit:
                remaining_bullets.append(bullet)

        self.bullets = remaining_bullets

        # Enemy infantry fights friendly infantry in melee. When no
        # friendlies remain, EnemyInfantry sieges player_bunker instead.
        player_bunker = player_bunkers[0] if player_bunkers else None

        for enemy in self.enemy_barracks_units:
            # ArmorUnit is updated in its OWN loop below (stop-at-
            # building rule): the infantry call signature would feed
            # it the player bunker as a BUILDINGS list. Skip here.
            if isinstance(enemy, ArmorUnit):
                continue
            enemy.update(dt, self.friendlies, self.enemy_bullets, player_bunker)

        # Spawn gold before removing dead enemy infantry: spawn_gold
        # guards double drops, and the filter below must not eat the
        # drop chance this frame.
        for enemy in self.enemy_barracks_units:
            if enemy.dead and not enemy.gold_spawned:
                gold = enemy.spawn_gold()
                if gold is not None:
                    self.gold_pickups.append(gold)

        self.enemy_barracks_units = [
            enemy for enemy in self.enemy_barracks_units
            if not enemy.dead
        ]

        # Friendly infantry fights enemy infantry in melee + ranged.
        for friendly in self.friendlies:
            friendly.update(dt, self.enemy_barracks_units, self.bullets)

        self.friendlies = [
            friendly for friendly in self.friendlies
            if not friendly.dead
        ]

        # Update production and combat buildings. Barracks spawn
        # infantry on their cadence, the tank factory rolls out
        # armor, AIR FIELDS roll out planes; machine guns and
        # artillery share the same classes on both sides — only the
        # lists swapped in differ, so which side shoots at whom is
        # the state's choice (buildings aim at the opposing unit
        # list). Destroyed buildings stand down entirely.
        for building in buildings:
            if getattr(building, "is_destroyed", lambda: False)():
                continue

            if not isinstance(
                building,
                (Barracks, TankFactory, MGNest, Artillery, AirField),
            ):
                continue

            if building.is_enemy:
                if isinstance(building, (Barracks, TankFactory)):
                    building.update(dt, self.enemy_barracks_units)
                elif isinstance(building, AirField):
                    building.update(dt, self.enemy_planes)
                else:
                    building.update(dt, self.friendlies, self.enemy_bullets)
            else:
                if isinstance(building, (Barracks, TankFactory)):
                    building.update(dt, self.friendlies)
                elif isinstance(building, AirField):
                    building.update(dt, self.friendly_planes)
                else:
                    building.update(dt, self.enemy_barracks_units, self.bullets)

        # Factory armor: vehicles drive toward the enemy base and
        # hunt with their hull MG. Both stop when an enemy building
        # is inside shooting range (user rule); tanks shell it, cars
        # park (their MG never hits buildings).
        for vehicle in list(self.friendlies):
            if isinstance(vehicle, ArmorUnit):
                vehicle.update(
                    dt, self.enemy_barracks_units, self.bullets,
                    enemy_buildings,
                )

        for vehicle in list(self.enemy_barracks_units):
            if isinstance(vehicle, ArmorUnit):
                vehicle.update(
                    dt, self.friendlies, self.enemy_bullets,
                    player_buildings,
                )

        # Planes fly (no ground logic): friendly planes hunt the
        # enemy's armor + buildings + planes; enemy planes mirror.
        # Ground target list = enemy armor (tanks/cars) + enemy
        # buildings, nearest-first inside the plane itself.
        enemy_ground = [
            unit for unit in self.enemy_barracks_units
            if isinstance(unit, ArmorUnit) and not unit.dead
        ] + enemy_buildings
        friendly_ground = [
            unit for unit in self.friendlies
            if isinstance(unit, ArmorUnit) and not unit.dead
        ] + player_buildings

        for plane in list(self.friendly_planes):
            plane.update(
                dt, enemy_ground, self.enemy_planes, self.bullets,
            )

        for plane in list(self.enemy_planes):
            plane.update(
                dt, friendly_ground, self.friendly_planes,
                self.enemy_bullets,
            )

        # Dead planes out this frame (no gold drops: gold_spawned is
        # True on planes, so the gold loop below skips them too).
        self.friendly_planes = [
            plane for plane in self.friendly_planes if not plane.dead
        ]
        self.enemy_planes = [
            plane for plane in self.enemy_planes if not plane.dead
        ]

        # Enemy bullets can damage friendly infantry; armor passes
        # through; friendly BUILDINGS rule mirrors the bullets above
        # (tank shells hit any building, others only bunkers); and
        # friendly PLANES get hit by anything in the air.
        remaining_enemy_bullets = []

        for bullet in self.enemy_bullets:
            bullet.update(dt)

            if getattr(bullet, "dead", False):
                continue

            hit = False

            for friendly in self.friendlies:
                if friendly.dead:
                    continue

                # ARMOR RULE (mirrored): plain enemy bullets pass
                # through friendly armor; only tank shots/artillery
                # hurt armored units on this side too.
                if isinstance(friendly, ArmorUnit) and not bullet.armor_damage:
                    continue

                if bullet.get_hitbox().colliderect(
                    friendly.get_hitbox()
                ):
                    # Direct hp subtraction: friendlies take raw bullet
                    # damage instead of a take_damage call (they have
                    # no armor or special death handling here).
                    friendly.hp -= bullet.damage

                    if friendly.hp <= 0:
                        friendly.dead = True

                    hit = True
                    break

            if not hit and bullet.armor_damage:
                for building in player_buildings:
                    if bullet.get_hitbox().colliderect(
                        building.get_hitbox()
                    ):
                        building.take_damage(bullet.damage)
                        hit = True
                        break
            elif not hit and getattr(bullet, "can_damage_buildings", True):
                for bunker in player_bunkers:
                    if bunker.dead:
                        continue

                    if bullet.get_hitbox().colliderect(
                        bunker.get_hitbox()
                    ):
                        bunker.take_damage(bullet.damage)
                        hit = True
                        break

            if not hit:
                for plane in self.friendly_planes:
                    if plane.dead:
                        continue

                    if bullet.get_hitbox().colliderect(
                        plane.get_hitbox()
                    ):
                        plane.take_damage(bullet.damage)
                        hit = True
                        break

            if not hit:
                remaining_enemy_bullets.append(bullet)

        self.enemy_bullets = remaining_enemy_bullets

        self.friendlies = [
            friendly for friendly in self.friendlies
            if not friendly.dead
        ]

        # Collect gold pickups and add their full value to gold.
        remaining_gold = []

        for gold in self.gold_pickups:
            if gold.update(dt, self.player):
                self.economy.gold += gold.amount
            else:
                remaining_gold.append(gold)

        self.gold_pickups = remaining_gold

        # Lose if the player's bunker is destroyed. Checking at the END
        # of update (not the start) means the frame that destroys it
        # still fully simulates and draws before the switch, avoiding a
        # half-updated final frame.
        if player_bunkers and all(
            bunker.is_destroyed() for bunker in player_bunkers
        ):            
            self.game.state = GameOverState(self.game)
            return

        # Win when all enemy bunkers are destroyed. Guarded by
        # enemy_bunkers existing, so a map without enemy bunkers never
        # auto-wins.
        if enemy_bunkers and all(
            bunker.is_destroyed() for bunker in enemy_bunkers
        ):            
            self.game.state = WinState(self.game)
            return

    def get_nearby_build_spot(self):
        """Return the nearest EMPTY PLAYER build spot within range.

        Only player-purchasable spot types (mg/barracks/artillery) can
        prompt: enemy defenses are pre-placed free at battle start, so
        standing near one shows nothing. Also skipped: any spot that
        already holds a building (nothing left to buy there — finished
        player spots included). Range is circular (build_prompt_radius
        pixels around the player's center); ties break in favor of the
        first closest spot.
        """
        player_x = self.player.x + self.player.width / 2
        player_y = self.player.y + self.player.height / 2

        nearest_spot = None
        nearest_distance = float("inf")

        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            # Promptable = empty player-purchasable spots only.
            if spot_type not in BUILDING_CLASSES:
                continue

            tile = self.tilemap.get_tile(tile_x, tile_y)
            if tile is None or tile.building is not None:
                continue

            # Distance from the player to the FOOTPRINT RECT (nearest
            # edge; 0 anywhere on/inside). At 4x4, a center-based
            # radius left the prompt blind while standing on the far
            # corner tiles (90px > the 72px radius) — edge distance
            # keeps "near the spot" true for its whole footprint.
            # Faction-aware (axis artillery 3x2 override etc.).
            fw, fh = footprint_for(spot_type, self.player_faction)
            rect = pygame.Rect(
                tile_x * TILE_SIZE,
                tile_y * TILE_SIZE,
                fw * TILE_SIZE,
                fh * TILE_SIZE,
            )
            edge_x = max(rect.left, min(player_x, rect.right))
            edge_y = max(rect.top, min(player_y, rect.bottom))
            distance = math.hypot(player_x - edge_x, player_y - edge_y)

            if (
                distance <= self.build_prompt_radius
                and distance < nearest_distance
            ):
                nearest_spot = (tile_x, tile_y, spot_type)
                nearest_distance = distance

        return nearest_spot

    def _collect_force_rows(self):
        """Build the HUD force-count rows for both sides.

        Infantry rows count live units (both role lists are dead-
        filtered every update, so len() is the standing count).
        Buildable defenses show X/Y: X = build spots already holding a
        building, Y = total build spots of that type on the map (one
        building per spot, so X is always <= Y). Enemy buildings are
        placed free at battle start on their own markers and have no
        build limit, so they display as plain counts.
        """
        # Player buildable spots: per-type totals and occupied counts.
        totals = {"barracks": 0, "mg": 0, "artillery": 0}
        placed = {"barracks": 0, "mg": 0, "artillery": 0}

        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            if spot_type not in totals:
                continue

            totals[spot_type] += 1

            tile = self.tilemap.get_tile(tile_x, tile_y)
            if tile and tile.building is not None:
                placed[spot_type] += 1

        # Enemy standing buildings, grouped by class; the class naming
        # (MGNest) is translated to the display name in the rows below.
        enemy_placed = Counter()
        for building in BuildingQuery.get_all_buildings(self.tilemap):
            if building.is_enemy:
                enemy_placed[type(building).__name__] += 1

        # One tuple per row: (name, player display, enemy display).
        # Infantry counts exclude factory armor (planes live in their
        # OWN lists); armored vehicles (tanks + cars) get their own
        # row and the air forces another.
        infantry_player = sum(
            1 for u in self.friendlies if not isinstance(u, ArmorUnit)
        )
        infantry_enemy = sum(
            1 for u in self.enemy_barracks_units if not isinstance(u, ArmorUnit)
        )
        armor_player = sum(
            1 for u in self.friendlies if isinstance(u, ArmorUnit)
        )
        armor_enemy = sum(
            1 for u in self.enemy_barracks_units if isinstance(u, ArmorUnit)
        )
        return [
            (
                "Infantry",
                str(infantry_player),
                str(infantry_enemy),
            ),
            (
                "Armor",
                str(armor_player),
                str(armor_enemy),
            ),
            (
                "Planes",
                str(len(self.friendly_planes)),
                str(len(self.enemy_planes)),
            ),
            (
                "Barracks",
                f"{placed['barracks']}/{totals['barracks']}",
                str(enemy_placed["Barracks"]),
            ),
            (
                "MG Nest",
                f"{placed['mg']}/{totals['mg']}",
                str(enemy_placed["MGNest"]),
            ),
            (
                "Artillery",
                f"{placed['artillery']}/{totals['artillery']}",
                str(enemy_placed["Artillery"]),
            ),
        ]

    def draw_build_prompt(self, screen):
        """Show the cost ledger of the nearby EMPTY player spot.

        get_nearby_build_spot already filters to empty player-purchasable
        spots, so the prompt is always an unpaid or partially paid plot:
        PAID X / COST | OWES | HAVE gold. Enemy buildings and finished
        player buildings show nothing at all.
        """
        nearby = self.get_nearby_build_spot()
        if nearby is None:
            return

        tile_x, tile_y, spot_type = nearby

        cost = BUILD_COSTS.get(spot_type, 0)
        paid = self.tilemap.paid_amount.get((tile_x, tile_y), 0)
        gold = self.economy.gold

        remaining = max(0, cost - paid)
        message = (
            f"{spot_type.upper()}: PAID {paid}/{cost} | "
            f"OWES {remaining} | HAVE {gold}"
        )

        text = self.hud.font.render(
            message,
            True,
            (255, 255, 255),
        )

        padding = 8
        panel = pygame.Rect(
            0,
            0,
            text.get_width() + padding * 2,
            text.get_height() + padding * 2,
        )
        panel.centerx = screen.get_width() // 2
        panel.bottom = screen.get_height() - 12

        pygame.draw.rect(
            screen,
            (25, 25, 30),
            panel,
            border_radius=5,
        )
        pygame.draw.rect(
            screen,
            (220, 200, 120),
            panel,
            width=1,
            border_radius=5,
        )

        screen.blit(
            text,
            (panel.x + padding, panel.y + padding),
        )

    def render(self, screen):
        """Draw the battle back-to-front: world, zoom, entities, HUD.

        The world (map, units, pickups, bullets, player) is drawn 1:1
        onto the pre-allocated FULL-map world surface, then uniformly
        zoomed below the HUD top bar: ONE factor for both axes so
        tiles and units stay square (no per-axis squash). If the map
        aspect differs from 1280:728 the extra horizontal columns
        become centered dark side bands (FULL view only; CLOSE fills
        the whole strip). HUD overlays draw after, in screen space.

        Viewport culling (user rule: don't render what is not on
        screen — it matters when zoomed in): in CLOSE view only the
        player-window region of the world is redrawn and only entities
        near that window get draw() calls; stale pixels elsewhere on
        the world surface are never read, because the CLOSE zoom
        subsamples exactly the window. In FULL view everything maps
        to screen, so nothing is culled (view_rect=None).
        """
        world = self.world_surface

        # Viewport crop for this frame, computed BEFORE drawing:
        # FULL view = whole map (None disables culling), CLOSE view =
        # the clamped player window in world pixels.
        cx = cy = 0
        view_rect = None
        if self.view_mode == VIEW_CLOSE:
            cx = int(max(0, min(
                self.player.x - self.close_window_w / 2,
                self.world_w_px - self.close_window_w,
            )))
            cy = int(max(0, min(
                self.player.y - self.close_window_h / 2,
                self.world_h_px - self.close_window_h,
            )))
            view_rect = pygame.Rect(
                cx,
                cy,
                self.close_window_w,
                self.close_window_h,
            )

        # Cull test for entity draws: anything with a world position
        # near the visible window (CULL_MARGIN covers sprite sizes;
        # bullets are tiny) is drawn. None view = always visible.
        def in_view(x, y):
            return view_rect is None or (
                view_rect.left - CULL_MARGIN <= x
                <= view_rect.right + CULL_MARGIN
                and view_rect.top - CULL_MARGIN <= y
                <= view_rect.bottom + CULL_MARGIN
            )

        # Ground layering decision for this frame: in CLOSE view, when
        # the native-resolution ground is available AND we are in
        # SPRITES mode, the ground is rendered straight from native
        # 4K detail at screen resolution (no ground on the world
        # surface — see the zoom block below). Everything else keeps
        # the classic ground-on-world-surface path.
        close_native_ground = (
            self.view_mode == VIEW_CLOSE
            and self.tilemap.ground_texture_native is not None
            and render_mode.is_sprite()
        )

        # No-ground frames no longer overwrite the window region with
        # the JPEG every frame, so the ENTITIES' canvas must be cleared
        # here — stale pixels (unit trails, ghost sprites, stale block
        # tiles after a live G toggle) would otherwise persist forever
        # under the native ground.
        if close_native_ground:
            world.fill(
                (0, 0, 0, 0),
                (cx, cy, self.close_window_w, self.close_window_h),
            )

        self.tilemap.draw(
            world,
            self.camera_x,
            view_rect,
            skip_ground=close_native_ground,
            skip_native_hires=close_native_ground,
        )

        # Artillery firing/impact markers, measured on the marker's
        # world position (NOT the gun's) so they show even when the
        # gun that fired them is culled:
        # - muzzle: SMALL yellow flash just in front of the gun while
        #   the shell flies (user: "a little yellow", not a square);
        # - blast: red flash where the shell landed.
        for building in BuildingQuery.get_all_buildings(self.tilemap):
            if not isinstance(building, Artillery):
                continue
            for mx, my, _ttl in building.muzzles:
                if in_view(mx, my):
                    pygame.draw.circle(
                        world,
                        YELLOW,
                        (int(mx + TILE_SIZE / 2 - self.camera_x),
                         int(my + TILE_SIZE / 2)),
                        7,
                    )
            for ix, iy, _ttl in building.impacts:
                if in_view(ix, iy):
                    pygame.draw.circle(
                        world,
                        RED,
                        (int(ix - self.camera_x), int(iy)),
                        8,
                    )

        for enemy_unit in self.enemy_barracks_units:
            if in_view(enemy_unit.x, enemy_unit.y):
                enemy_unit.draw(world, self.camera_x)

        for gold in self.gold_pickups:
            if close_native_ground:
                # CLOSE SPRITES view: coins blit straight from their
                # native art in the hires pass below — the world
                # layer would only show a 4x-upscaled 12px copy
                # (user: "coin images with good quality").
                continue
            if in_view(gold.x, gold.y):
                gold.draw(world, self.camera_x)

        for bullet in self.bullets:
            if in_view(bullet.x, bullet.y):
                bullet.draw(world, self.camera_x)

        for bullet in self.enemy_bullets:
            if in_view(bullet.x, bullet.y):
                bullet.draw(world, self.camera_x)

        for friendly in self.friendlies:
            if in_view(friendly.x, friendly.y):
                friendly.draw(world, self.camera_x)

        # Planes fly ABOVE everything on the world layer (their own
        # draw already offsets them up for the flight illusion).
        for plane in self.enemy_planes:
            if in_view(plane.x, plane.y):
                plane.draw(world, self.camera_x)

        for plane in self.friendly_planes:
            if in_view(plane.x, plane.y):
                plane.draw(world, self.camera_x)

        self.player.draw(world, self.camera_x)

        # Uniform zoom into the visible strip: single-factor scale
        # keeps every tile square; smoothscale avoids downscale
        # aliasing on the photo-like ground texture. Bands: fill the
        # visible strip first so leftover columns don't accumulate
        # stale frame pixels.
        screen.fill((20, 20, 20), (0, HUD_BAR_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - HUD_BAR_HEIGHT))
        if self.view_mode == VIEW_CLOSE:
            # CLOSE view ('+'): subsample the full-res world in a
            # screen-wide ~10-tile window centered (and map-clamped)
            # on the player, upscaled so it occupies the WHOLE visible
            # strip (no side bands). cx/cy were computed before the
            # crop pass above (culling and zoom share one window).
            #
            # ground pass (SPRITES mode + native 4K asset): the
            # user's 5504x3072 map art holds ~2.15x more pixels per
            # world px than the world strip — sampling THIS window
            # from the native image means one true source pixel per
            # screen pixel at 4x zoom (the old path upscaled the
            # pre-downscaled 2560x1472 texture 4x, the "blurry when
            # zoomed" complaint). The entity layer (buildings, units,
            # bullets, markers) rides on top from the SRCALPHA world
            # surface, whose ground was skipped this frame.
            native = self.tilemap.ground_texture_native
            if close_native_ground:
                src_rect = self.tilemap.native_ground_rect(view_rect)
                if src_rect is not None:
                    screen.blit(
                        # Native was already edge-sharpened once at
                        # load (graphics/ground_sharpen.py via
                        # tilemap.reload_ground) — the zoom just
                        # resamples that crisp source per frame.
                        pygame.transform.smoothscale(
                            native.subsurface(src_rect),
                            self.close_view,
                        ),
                        (0, HUD_BAR_HEIGHT),
                    )
            region = world.subsurface(
                (cx, cy, self.close_window_w, self.close_window_h),
            )
            screen.blit(
                pygame.transform.smoothscale(region, self.close_view),
                (0, HUD_BAR_HEIGHT),
            )

            # Building hires pass (user: "images zoom in or zoom out
            # should have the same high quality"): static buildings
            # usually ship native art much bigger than the world box,
            # so those with image_native blit straight here at SCREEN
            # resolution (4x sharper than the world surface could
            # ever show). Buildings without native art keep their
            # normal low-res draw under the entity layer above.
            if close_native_ground:
                self._blit_building_hires(screen, cx, cy, view_rect)
                self._blit_coin_hires(screen, cx, cy, view_rect)
        else:
            # FULL view (default/'-'): whole battlefield at once.
            screen.blit(
                pygame.transform.smoothscale(world, self.world_view),
                (self.world_offset_x, HUD_BAR_HEIGHT),
            )

        # Bunker HP bar: the first bunker found is the one tracked.
        buildings = BuildingQuery.get_all_buildings(self.tilemap)
        bunkers = [b for b in buildings if isinstance(b, Bunker)]
        bunker_hp = bunkers[0].hp if bunkers else 0

        self.hud.draw(
            screen,
            bunker_hp,
            self.economy.gold,
            render_mode.label(),
            self.view_mode,
            fps=round(self.fps),
        )

        self.draw_build_prompt(screen)

        # Force counts panel: paused-only so live play keeps a clean
        # view; drawn after the dim overlay so the numbers stay crisp.
        if self.paused:
            self._draw_pause_overlay(screen)
            self.hud.draw_force_counts(screen, self._collect_force_rows())

    def _blit_building_hires(self, screen, cx, cy, view_rect):
        """CLOSE view: buildings blit straight to screen from native art.

        For every building with an image_native surface (the SAME art
        file at its true resolution, sized per instance in the entity
        constructors), the battle caches ONE smoothscaled copy at the
        CLOSE zoom (native -> footprint * close_scale world px, i.e.
        ~4x) and blits it at its window-relative screen position.
        Buildings whose art would upscale beyond its source or missing
        files (image_native None) stay on the low-res world path —
        nothing disappears, quality only stays where it can improve.
        """
        scale = self.close_scale
        for building in BuildingQuery.get_all_buildings(self.tilemap):
            native = getattr(building, "image_native", None)
            if native is None:
                continue

            # PROPORTIONAL art (user fix): buildings that draw
            # aspect-true inside their footprint carry draw_size +
            # draw_offset (bunker bottom-center); others draw the full
            # footprint box (no attrs = unchanged behavior).
            fw, fh = getattr(
                building, "draw_size",
                tuple(TILE_SIZE * n for n in building.footprint_tiles),
            )
            ox, oy = getattr(building, "draw_offset", (0, 0))
            target = (
                int(round(fw * scale)),
                int(round(fh * scale)),
            )

            cache = building.__dict__.get("_hires_cache")
            if cache is None or cache.get_size() != target:
                cache = pygame.transform.smoothscale(native, target)
                building._hires_cache = cache

            screen_x = (building.tile_x * TILE_SIZE + ox - cx) * scale
            screen_y = HUD_BAR_HEIGHT + (
                building.tile_y * TILE_SIZE + oy - cy
            ) * scale

            # Cull: FOOTPRINT fully outside the CLOSE window is skipped
            # (wider than the drawn art for proportional buildings).
            cfp_w, cfp_h = (
                TILE_SIZE * n for n in building.footprint_tiles
            )
            world_rect = pygame.Rect(
                building.tile_x * TILE_SIZE,
                building.tile_y * TILE_SIZE,
                cfp_w,
                cfp_h,
            )
            if not world_rect.colliderect(view_rect):
                continue

            screen.blit(cache, (int(round(screen_x)), int(round(screen_y))))

    def _blit_coin_hires(self, screen, cx, cy, view_rect):
        """CLOSE view: coin pickups blit straight from native art.

        Mirror of the building hires pass for the gold coins (user:
        "coin images with good quality"): each uncollected pickup
        carries image_native (the coin's 256x256 source); in CLOSE
        SPRITES mode it is smoothscaled ONCE per instance to
        COIN_SIZE * close_scale (~48x48 screen px) — far sharper than
        the 4x-upscaled 12px world copy — and blitted at its
        bob-animated position. Pickups without native art (missing
        asset) stay on the low-res world path (and pickups hidden by
        this pass keep it only in FULL / BLOCKS mode).
        """
        scale = self.close_scale
        # Same edge forgiveness as the unit cull so coins bobbing at
        # the window edge don't pop in/out.
        margin_rect = view_rect.inflate(CULL_MARGIN, CULL_MARGIN)

        for gold in self.gold_pickups:
            if gold.collected or gold.image_native is None:
                continue

            coin_rect = pygame.Rect(
                gold.x,
                gold.y + gold.y_offset,
                COIN_SIZE[0],
                COIN_SIZE[1],
            )
            if not coin_rect.colliderect(margin_rect):
                continue

            target = (
                int(round(COIN_SIZE[0] * scale)),
                int(round(COIN_SIZE[1] * scale)),
            )
            cache = gold.__dict__.get("_hires_cache")
            if cache is None or cache.get_size() != target:
                cache = pygame.transform.smoothscale(
                    gold.image_native, target,
                )
                gold._hires_cache = cache

            screen_x = (gold.x - cx) * scale
            screen_y = HUD_BAR_HEIGHT + (gold.y + gold.y_offset - cy) * scale
            screen.blit(cache, (int(round(screen_x)), int(round(screen_y))))

    def _draw_pause_overlay(self, screen):
        """Draw the dim + centered PAUSED panel with resume instructions."""
        # Dim the frozen battle scene; the surface was built once in
        # __init__ so pausing costs nothing per frame.
        screen.blit(self.pause_overlay, (0, 0))

        screen_w, screen_h = screen.get_size()

        # Centered text stack: title, resume hint, hard-coded controls
        # so the player always knows what is usable while frozen.
        title = self.pause_font.render("PAUSED", True, WHITE)
        title_rect = title.get_rect(centerx=screen_w // 2, y=screen_h // 3)
        screen.blit(title, title_rect)

        hint = self.pause_hint_font.render(
            "Press SPACE (or ESC) to resume",
            True,
            WHITE,
        )
        hint_rect = hint.get_rect(
            centerx=screen_w // 2,
            y=screen_h // 3 + 60,
        )
        screen.blit(hint, hint_rect)

        # Live player tile position while frozen, 1-BASED per tile
        # (floor divide; the NW-most tile is X=1, Y=1 since world x
        # in [0, TILE_SIZE) belongs to tile 1). Enables distance
        # reading against the hand-edited map markers.
        tile_x = int(self.player.x // TILE_SIZE) + 1
        tile_y = int(self.player.y // TILE_SIZE) + 1
        pos = self.pause_hint_font.render(
            f"Player tile: X {tile_x} | Y {tile_y}",
            True,
            WHITE,
        )
        pos_rect = pos.get_rect(
            centerx=screen_w // 2,
            y=screen_h // 3 + 96,
        )
        screen.blit(pos, pos_rect)

        # Control reference while frozen: the help the user reads
        # whenever the battle is paused.
        controls = self.pause_hint_font.render(
            "SPACE: pause/resume | +: zoom in | -: zoom out | G: graphics toggle | WASD: move",
            True,
            WHITE,
        )
        controls_rect = controls.get_rect(
            centerx=screen_w // 2,
            y=screen_h - 60,
        )
        screen.blit(controls, controls_rect)
