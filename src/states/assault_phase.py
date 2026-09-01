"""
Main gameplay state: player, camera, waves, combat, structured defenses, bunker castle, autofire, auto-placement.
"""

import pygame

from systems.wave_director import WaveDirector
from systems.combat_system import CombatSystem
from systems.economy_system import EconomySystem
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
        self.wave_director = WaveDirector(self.tilemap, 3, 5)
        self.combat = CombatSystem()

        self.player = Player(3 * 32, (self.tilemap.trench_y + 1) * 32)
        self.player.max_world_x = self.tilemap.width * 32 - self.player.width

        bunker_x = 2
        bunker_y = self.tilemap.trench_y + 1
        bunker_tile = self.tilemap.get_tile(bunker_x, bunker_y)
        bunker_tile.building = Bunker(bunker_x, bunker_y)

        self.camera_x = 0
        self.gold_pickups = []
        self.bullets = []
        self.friendlies = []

        self.economy.register_cost(20)   # MG
        self.economy.register_cost(30)   # Barracks
        self.economy.register_cost(60)   # Artillery

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bullet = self.player.shoot()
                if bullet:
                    self.bullets.append(bullet)

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
            cost = 20
        elif spot_type == "barracks":
            building_class = Barracks
            cost = 30
        elif spot_type == "artillery":
            building_class = Artillery
            cost = 60
        else:
            return

        if self.economy.supplies < cost:
            return

        self.economy.spend(cost)
        tile.building = building_class(tile_x, tile_y)

    def update(self, dt):
        self.player.update(dt)

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
                from states.main_menu import MainMenu
                self.game.change_state(MainMenu(self.game))

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

        counts = BuildingQuery.count_buildings(self.tilemap)
        self.hud.draw_building_counts(screen, counts)
