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

from collections import deque

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
from entities.barracks import Barracks

from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, WHITE


# Map spot_type string -> player-purchasable building class
# (spot_types comes from the ASCII map's uppercase markers).
BUILDING_CLASSES = {
    "mg": MGNest,
    "barracks": Barracks,
    "artillery": Artillery,
}

# Map spot_type string -> enemy building class; these are placed free
# at battle start from the map's lowercase markers (no gold involved).
ENEMY_BUILDING_CLASSES = {
    "enemy_bunker": Bunker,
    "enemy_mg": MGNest,
    "enemy_barracks": Barracks,
    "enemy_artillery": Artillery,
}


class AssaultPhase:
    def __init__(self, game):
        self.game = game
        # Shared world: the menu rebuilt this TileMap so the battle
        # always starts from the pristine ASCII layout.
        self.tilemap = game.tilemap

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

        # Find the first bunker build spot.
        bunker_pos = None
        for (x, y), spot_type in self.tilemap.spot_types.items():
            if spot_type == "bunker":
                bunker_pos = (x, y)
                break

        if bunker_pos is None:
            bunker_x = 2
            bunker_y = self.tilemap.trench_y + 1
        else:
            bunker_x, bunker_y = bunker_pos

        # Place the bunker.
        bunker_tile = self.tilemap.get_tile(bunker_x, bunker_y)
        if bunker_tile:
            bunker_tile.building = Bunker(bunker_x, bunker_y)

        # Friendly boundary.
        boundary = self.tilemap.friendly_boundary

        # Find a walkable spawn tile on the friendly side.
        queue = deque([(bunker_x, bunker_y)])
        visited = {(bunker_x, bunker_y)}
        spawn_tile = None

        while queue:
            x, y = queue.popleft()

            if x < boundary and self.tilemap.is_walkable(x, y):
                spawn_tile = (x, y)
                break

            for nx, ny in (
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1),
            ):
                if (
                    (nx, ny) not in visited
                    and self.tilemap.get_tile(nx, ny)
                ):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        if spawn_tile is None:
            spawn_x = 3 * TILE_SIZE
            spawn_y = (self.tilemap.trench_y + 1) * TILE_SIZE
        else:
            spawn_x = spawn_tile[0] * TILE_SIZE
            spawn_y = spawn_tile[1] * TILE_SIZE

        self.player = Player(spawn_x, spawn_y)
        self.player.max_world_x = (
            self.tilemap.width * TILE_SIZE - self.player.width
        )

        self.camera_x = 0

        self.gold_pickups = []
        self.bullets = []
        self.enemy_bullets = []
        self.friendlies = []
        self.enemy_barracks_units = []

        self.build_prompt_radius = 72
        self.place_enemy_buildings()

    def handle_event(self, event):
        """Key routing: SPACE (or ESC) pauses/resumes, G toggles graphics.

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

            tile = self.tilemap.get_tile(tile_x, tile_y)
            # An occupied tile is skipped: first marker wins, so hand
            # edits to the map never silently overwrite a building.
            if tile is None or tile.building is not None:
                continue

            if spot_type == "enemy_bunker":
                tile.building = Bunker(tile_x, tile_y, is_enemy=True)
            else:
                tile.building = building_class(
                    tile_x,
                    tile_y,
                    is_enemy=True,
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

            spot_rect = pygame.Rect(
                tile_x * TILE_SIZE,
                tile_y * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
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
                tile.building = building_class(tile_x, tile_y)
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
        # Paused: freeze the whole simulation (render still runs).
        if self.paused:
            return

        # Retrieve all buildings from the tilemap.
        buildings = BuildingQuery.get_all_buildings(self.tilemap)

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

        # Camera follows the player.
        world_width = self.tilemap.width * TILE_SIZE
        max_camera_x = max(0, world_width - SCREEN_WIDTH)

        self.camera_x = max(
            0,
            min(
                self.player.x - SCREEN_WIDTH // 2,
                max_camera_x,
            ),
        )
        
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

                if bullet.get_hitbox().colliderect(enemy.get_hitbox()):
                    enemy.take_damage(bullet.damage)
                    hit = True
                    break

            # Fallback to objectives when no unit was hit: shooting
            # bunkers is a core win route.
            if not hit:
                for bunker in enemy_bunkers:
                    if bunker.dead:
                        continue

                    if bullet.get_hitbox().colliderect(
                        bunker.get_hitbox()
                    ):
                        bunker.take_damage(bullet.damage)
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

        # Update machine guns and artillery.
        # Both sides share the same classes; only the lists swapped in
        # differ, so which side shoots at whom is the state's choice
        # (buildings aim at the opposing unit list).
        for building in buildings:
            if not isinstance(building, (MGNest, Artillery)):
                continue

            if building.is_enemy:
                building.update(
                    dt,
                    self.friendlies,
                    self.enemy_bullets,
                )
            else:
                building.update(
                    dt,
                    self.enemy_barracks_units,
                    self.bullets,
                )

        # Enemy bullets can damage friendly infantry only.
        remaining_enemy_bullets = []

        for bullet in self.enemy_bullets:
            bullet.update(dt)

            if getattr(bullet, "dead", False):
                continue

            hit = False

            for friendly in self.friendlies:
                if friendly.dead:
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
        """Return the nearest build spot within interaction range.

        Range is circular (build_prompt_radius pixels around the
        player's center); ties break in favor of the first closest spot.
        """
        player_x = self.player.x + self.player.width / 2
        player_y = self.player.y + self.player.height / 2

        nearest_spot = None
        nearest_distance = float("inf")

        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            # Spot center in pixel coordinates for the radial compare.
            center_x = tile_x * TILE_SIZE + TILE_SIZE / 2
            center_y = tile_y * TILE_SIZE + TILE_SIZE / 2

            distance = math.hypot(
                center_x - player_x,
                center_y - player_y,
            )

            if (
                distance <= self.build_prompt_radius
                and distance < nearest_distance
            ):
                nearest_spot = (tile_x, tile_y, spot_type)
                nearest_distance = distance

        return nearest_spot

    def draw_build_prompt(self, screen):
        """Show building cost, payment, and outstanding debt."""
        nearby = self.get_nearby_build_spot()
        if nearby is None:
            return

        tile_x, tile_y, spot_type = nearby
        tile = self.tilemap.get_tile(tile_x, tile_y)

        cost = BUILD_COSTS.get(spot_type, 0)
        paid = self.tilemap.paid_amount.get((tile_x, tile_y), 0)
        gold = self.economy.gold

        if tile and tile.building is not None:
            # Built spots keep showing the ledger: cheap reassurance
            # that a finished building owes nothing.
            message = f"{spot_type.upper()}: BUILT | PAID {paid}/{cost}"
        else:
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
        """Draw the battle back-to-front: world, swap, entities, HUD.

        Draw order mimics depth: ground first, then ground-level units
        and pickups, bullets come later so they read over units, the
        player on top of everything walked over, then the HUD above.
        """
        self.tilemap.draw(screen, self.camera_x)

        for enemy_unit in self.enemy_barracks_units:
            enemy_unit.draw(screen, self.camera_x)

        for gold in self.gold_pickups:
            gold.draw(screen, self.camera_x)

        for bullet in self.bullets:
            bullet.draw(screen, self.camera_x)

        for bullet in self.enemy_bullets:
            bullet.draw(screen, self.camera_x)

        for friendly in self.friendlies:
            friendly.draw(screen, self.camera_x)

        self.player.draw(screen, self.camera_x)

        # Bunker HP bar: the first bunker found is the one tracked.
        buildings = BuildingQuery.get_all_buildings(self.tilemap)
        bunkers = [b for b in buildings if isinstance(b, Bunker)]
        bunker_hp = bunkers[0].hp if bunkers else 0

        self.hud.draw(
            screen,
            bunker_hp,
            self.economy.gold,
            render_mode.label(),
        )

        self.draw_build_prompt(screen)

        # Building counts table rendered under the main bar.
        counts = BuildingQuery.count_buildings(self.tilemap)
        self.hud.draw_building_counts(screen, counts)

        # Pause overlay goes last so it dims everything drawn above.
        if self.paused:
            self._draw_pause_overlay(screen)

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

        # Control reference while frozen: the help the user reads
        # whenever the battle is paused.
        controls = self.pause_hint_font.render(
            "SPACE: pause/resume | G: graphics toggle | WASD: move",
            True,
            WHITE,
        )
        controls_rect = controls.get_rect(
            centerx=screen_w // 2,
            y=screen_h - 60,
        )
        screen.blit(controls, controls_rect)
