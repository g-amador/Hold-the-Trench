"""
Main gameplay state: player, camera, waves, combat, structured defenses, bunker castle,
autofire, auto-placement, dynamic gold budget, game over and win states.
"""

import pygame
from collections import deque

from systems.wave_director import WaveDirector
from systems.combat_system import CombatSystem
from systems.economy_system import EconomySystem, BUILD_COSTS
from systems.building_query import BuildingQuery

from ui.hud import HUD

from entities.player import Player
from entities.enemy import Infantry, Cavalry, Tank
from entities.gold_pickup import GoldPickup
from entities.bullet import Bullet

from entities.trench import Trench
from entities.mg_nest import MGNest
from entities.bunker import Bunker
from entities.artillery import Artillery
from entities.barracks import Barracks
from entities.friendly_infantry import FriendlyInfantry

from config import SCREEN_WIDTH


class AssaultPhase:
    def __init__(self, game):
        self.game = game
        self.tilemap = game.tilemap

        self.hud = HUD()
        self.economy = EconomySystem()
        self.wave_director = WaveDirector(self.tilemap, self.economy, 5)
        self.combat = CombatSystem()

        # --- Spawn logic: B1 + P1 + S1 ---

        # Find first bunker build spot (B1 rule)
        bunker_pos = None
        for (x, y), t in self.tilemap.spot_types.items():
            if t == "bunker":
                bunker_pos = (x, y)
                break

        if bunker_pos is None:
            # Fallback: original hardcoded position if no bunker spot exists
            bunker_x = 2
            bunker_y = self.tilemap.trench_y + 1
        else:
            bunker_x, bunker_y = bunker_pos

        # Place bunker building at its tile
        bunker_tile = self.tilemap.get_tile(bunker_x, bunker_y)
        if bunker_tile:
            bunker_tile.building = Bunker(bunker_x, bunker_y)

        # Friendly boundary (S1 rule): first '|' in row 0
        boundary = self.tilemap.friendly_boundary

        # BFS search for nearest '.' tile on friendly side (P1 rule)
        queue = deque([(bunker_x, bunker_y)])
        visited = set([(bunker_x, bunker_y)])
        spawn_tile = None

        while queue:
            x, y = queue.popleft()

            if x < boundary and self.tilemap.is_walkable(x, y):
                spawn_tile = (x, y)
                break

            for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                if (nx, ny) not in visited and self.tilemap.get_tile(nx, ny):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        if spawn_tile is None:
            # Fallback: original spawn if no valid tile found
            spawn_x = 3 * 32
            spawn_y = (self.tilemap.trench_y + 1) * 32
        else:
            spawn_x = spawn_tile[0] * 32
            spawn_y = spawn_tile[1] * 32

        self.player = Player(spawn_x, spawn_y)
        self.player.max_world_x = self.tilemap.width * 32 - self.player.width

        self.camera_x = 0
        self.gold_pickups = []
        self.bullets = []
        self.friendlies = []

        # Register defense costs (for HUD stats)
        self.economy.register_cost(BUILD_COSTS["mg"])
        self.economy.register_cost(BUILD_COSTS["barracks"])
        self.economy.register_cost(BUILD_COSTS["artillery"])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                enemies = self.wave_director.get_enemies()
                self.player.auto_fire(0, enemies, self.bullets)

    def auto_place_if_possible(self):
        tile_x = int(self.player.x / 32)
        tile_y = int(self.player.y / 32)

        tile = self.tilemap.get_tile(tile_x, tile_y)
        if not tile:
            return

        if not self.tilemap.is_build_spot(tile_x, tile_y):
            return

        if tile.building:
            return

        spot_type = self.tilemap.spot_types.get((tile_x, tile_y))

        if spot_type == "mg":
            building_class = MGNest
        elif spot_type == "barracks":
            building_class = Barracks
        elif spot_type == "artillery":
            building_class = Artillery
        else:
            return

        cost = BUILD_COSTS.get(spot_type, 0)

        if self.economy.supplies < cost:
            return

        self.economy.spend(cost)
        tile.building = building_class(tile_x, tile_y)
        self.tilemap.paid_amount[(tile_x, tile_y)] = cost

    def update(self, dt):
        self.player.update(dt, self.tilemap)

        enemies = self.wave_director.get_enemies()
        self.player.auto_fire(dt, enemies, self.bullets)

        self.auto_place_if_possible()

        self.camera_x = self.player.x - 200
        max_camera = self.tilemap.width * 32 - SCREEN_WIDTH
        if max_camera < 0:
            max_camera = 0
        if self.camera_x < 0:
            self.camera_x = 0
        if self.camera_x > max_camera:
            self.camera_x = max_camera

        self.wave_director.update()
        enemies = self.wave_director.get_enemies()

        remaining_bullets = []
        for bullet in self.bullets:
            bullet.update(dt)

            hit = False
            for enemy in enemies:
                if enemy.dead:
                    continue

                if (bullet.x > enemy.x and
                    bullet.x < enemy.x + enemy.width and
                    bullet.y > enemy.y and
                    bullet.y < enemy.y + enemy.height):

                    enemy.take_damage(bullet.damage)
                    bullet.dead = True
                    hit = True
                    break

            if not bullet.dead:
                remaining_bullets.append(bullet)

        self.bullets = remaining_bullets

        new_gold = []
        for enemy in enemies:
            enemy.update(dt)
            gold = enemy.spawn_gold()
            if gold:
                new_gold.append(gold)

        self.gold_pickups.extend(new_gold)

        remaining_gold = []
        for gold in self.gold_pickups:
            collected = gold.update(dt, self.player)
            if collected:
                self.economy.supplies += gold.amount
            else:
                remaining_gold.append(gold)

        self.gold_pickups = remaining_gold

        buildings = BuildingQuery.get_all_buildings(self.tilemap)
        bunkers = [b for b in buildings if isinstance(b, Bunker)]

        for b in buildings:
            if isinstance(b, Barracks):
                b.update(dt, self.friendlies)
            elif isinstance(b, MGNest):
                b.update(dt, enemies, self.bullets)
            elif isinstance(b, Artillery):
                b.update(dt, enemies, self.bullets)
            else:
                b.update()

        remaining_friendlies = []
        for f in self.friendlies:
            f.update(dt, enemies)
            if not f.dead:
                remaining_friendlies.append(f)
        self.friendlies = remaining_friendlies

        self.combat.update(buildings, enemies)

        if bunkers:
            bunker = bunkers[0]
            for enemy in enemies:
                if not enemy.dead and enemy.x < 50:
                    enemy.dead = True
                    bunker.take_damage(10)

            if bunker.is_destroyed():
                from states.game_over import GameOverState
                self.game.change_state(GameOverState(self.game))

        if self.wave_director.wave_number == self.wave_director.total_waves and not enemies:
            from states.win_state import WinState
            self.game.change_state(WinState(self.game))

    def render(self, screen):
        self.tilemap.draw(screen, self.camera_x)

        for enemy in self.wave_director.get_enemies():
            enemy.draw(screen, self.camera_x)

        for gold in self.gold_pickups:
            gold.draw(screen, self.camera_x)

        for bullet in self.bullets:
            bullet.draw(screen, self.camera_x)

        for f in self.friendlies:
            f.draw(screen, self.camera_x)

        self.player.draw(screen, self.camera_x)

        buildings = BuildingQuery.get_all_buildings(self.tilemap)
        bunkers = [b for b in buildings if isinstance(b, Bunker)]
        bunker_hp = bunkers[0].hp if bunkers else 0

        self.hud.draw(
            screen,
            self.economy.supplies,
            self.wave_director.wave_number,
            self.wave_director.total_waves,
            bunker_hp,
            self.economy.total_defense_cost,
            self.economy.spent_defense_cost
        )

        # Show cost info above the build spot
        tile_x = int(self.player.x / 32)
        tile_y = int(self.player.y / 32)

        if self.tilemap.is_build_spot(tile_x, tile_y):
            spot_type = self.tilemap.spot_types[(tile_x, tile_y)]
            cost = BUILD_COSTS.get(spot_type, 0)
            paid = self.tilemap.paid_amount[(tile_x, tile_y)]
            coins = self.economy.supplies

            if paid >= cost:
                text = f"{spot_type.upper()}: BUILT"
            else:
                text = f"{spot_type.upper()}: {cost}/{coins}"

            px = tile_x * 32 - self.camera_x
            py = tile_y * 32 - 20

            surf = self.hud.font.render(text, True, (255, 255, 255))
            screen.blit(surf, (px, py))

        counts = BuildingQuery.count_buildings(self.tilemap)
        self.hud.draw_building_counts(screen, counts)
