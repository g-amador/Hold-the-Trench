"""
Main gameplay state: player, camera, waves, combat, building placement, gold pickups, player shooting.
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

from config import SCREEN_WIDTH


class AssaultPhase:
    def __init__(self, game):
        self.game = game
        self.tilemap = game.tilemap

        self.hud = HUD()
        self.economy = EconomySystem()
        self.wave_director = WaveDirector(self.tilemap, 3, 5)
        self.combat = CombatSystem()

        self.player = Player(3 * 32, 5 * 32)
        self.player.max_world_x = self.tilemap.width * 32 - self.player.width

        self.camera_x = 0
        self.gold_pickups = []
        self.bullets = []

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bullet = self.player.shoot()
                if bullet:
                    self.bullets.append(bullet)

            if event.key == pygame.K_1:
                self.place_building(Trench)
            if event.key == pygame.K_2:
                self.place_building(MGNest)
            if event.key == pygame.K_3:
                self.place_building(Bunker)
            if event.key == pygame.K_4:
                self.place_building(Artillery)

    def place_building(self, building_class):
        tile_x = int(self.player.x / 32)
        tile_y = int(self.player.y / 32)

        tile = self.tilemap.get_tile(tile_x, tile_y)
        if not tile:
            return

        if not self.tilemap.is_build_spot(tile_x, tile_y):
            return

        if tile.building:
            return

        cost = {
            Trench: 0,
            MGNest: 20,
            Bunker: 40,
            Artillery: 60
        }[building_class]

        if self.economy.supplies < cost:
            return

        self.economy.supplies -= cost
        tile.building = building_class(tile_x, tile_y)

    def update(self, dt):
        self.player.update(dt)

        # Camera clamped to map
        self.camera_x = self.player.x - 200
        max_camera = self.tilemap.width * 32 - SCREEN_WIDTH
        if self.camera_x < 0:
            self.camera_x = 0
        if self.camera_x > max_camera:
            self.camera_x = max_camera

        self.wave_director.update()
        enemies = self.wave_director.get_enemies()

        # Bullets
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

        # Enemies + gold
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

        # Buildings
        buildings = BuildingQuery.get_all_buildings(self.tilemap)
        for b in buildings:
            b.update()

        # Combat
        self.combat.update(buildings, enemies)

        # Bunker loss condition: if any enemy reaches trench line, damage bunker
        bunkers = [b for b in buildings if isinstance(b, Bunker)]
        if bunkers:
            bunker = bunkers[0]
            for enemy in enemies:
                if not enemy.dead and enemy.x < 50:
                    enemy.dead = True
                    bunker.take_damage(20)

            if bunker.is_destroyed():
                # Simple "lose" behavior: back to main menu
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

        self.player.draw(screen, self.camera_x)

        self.hud.draw(
            screen,
            self.economy.supplies,
            self.wave_director.wave_number,
            self.wave_director.total_waves
        )

        counts = BuildingQuery.count_buildings(self.tilemap)
        self.hud.draw_building_counts(screen, counts)
