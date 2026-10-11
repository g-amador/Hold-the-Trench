"""
Main gameplay state: player, camera, waves, combat, structured defenses,
bunker, autofire, automatic building, partial payments, and HUD.
"""

import pygame
import math

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

from config import SCREEN_WIDTH, TILE_SIZE


BUILDING_CLASSES = {
    "mg": MGNest,
    "barracks": Barracks,
    "artillery": Artillery,
}

ENEMY_BUILDING_CLASSES = {
    "enemy_bunker": Bunker,
    "enemy_mg": MGNest,
    "enemy_barracks": Barracks,
    "enemy_artillery": Artillery,
}


class AssaultPhase:
    def __init__(self, game):
        self.game = game
        self.tilemap = game.tilemap

        self.hud = HUD()
        self.economy = EconomySystem()
        self.wave_director = WaveDirector(
            self.tilemap,
            self.economy,
            5,
        )
        self.combat = CombatSystem()

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

        # Register defense costs for HUD statistics.
        self.economy.register_cost(BUILD_COSTS["mg"])
        self.economy.register_cost(BUILD_COSTS["barracks"])
        self.economy.register_cost(BUILD_COSTS["artillery"])

        self.build_prompt_radius = 72
        self.place_enemy_buildings()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                targets = list(self.enemy_barracks_units)
                targets.extend(
                    building
                    for building in BuildingQuery.get_all_buildings(self.tilemap)
                    if isinstance(building, Bunker)
                    and getattr(building, "is_enemy", False)
                )
                self.player.auto_fire(0, targets, self.bullets)

    def place_enemy_buildings(self):
        """Place enemy defenses from lowercase map markers without charging supplies."""
        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            building_class = ENEMY_BUILDING_CLASSES.get(spot_type)
            if building_class is None:
                continue

            tile = self.tilemap.get_tile(tile_x, tile_y)
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
            payment = min(remaining, max(0, self.economy.supplies))

            if payment > 0:
                self.economy.spend(payment)
                paid += payment
                self.tilemap.paid_amount[key] = paid

            # Only construct the building once its full cost is paid.
            if paid >= cost:
                tile.building = building_class(tile_x, tile_y)
                return

    def _collect_gold_and_pay_debts(self):
        """Collect gold and apply available supplies to unpaid buildings."""
        remaining_gold = []

        for gold in self.gold_pickups:
            collected = gold.update(0, self.player)

            if collected:
                self.economy.supplies += gold.amount
            else:
                remaining_gold.append(gold)

        self.gold_pickups = remaining_gold

        # Pay existing debts using available supplies.
        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            if spot_type not in BUILDING_CLASSES:
                continue

            tile = self.tilemap.get_tile(tile_x, tile_y)
            if tile is None or tile.building is None:
                continue

            cost = BUILD_COSTS[spot_type]
            paid = self.tilemap.paid_amount.get((tile_x, tile_y), 0)
            debt = max(0, cost - paid)

            payment = min(debt, max(0, self.economy.supplies))
            if payment > 0:
                self.economy.spend(payment)
                self.tilemap.paid_amount[(tile_x, tile_y)] = paid + payment

    def update(self, dt):
        # The wave director is intentionally not updated.
        # All combatants now come from barracks.
        self.player.update(dt, self.tilemap, self.enemy_barracks_units)

        buildings = BuildingQuery.get_all_buildings(self.tilemap)
        bunkers = [b for b in buildings if isinstance(b, Bunker)]
        player_bunkers = [
            b for b in bunkers if not getattr(b, "is_enemy", False)
        ]
        enemy_bunkers = [
            b for b in bunkers if getattr(b, "is_enemy", False)
        ]

        # Spawn infantry from both sides' barracks.
        for building in buildings:
            if isinstance(building, Barracks):
                if getattr(building, "is_enemy", False):
                    building.update(dt, self.enemy_barracks_units)
                else:
                    building.update(dt, self.friendlies)

        # Player automatic fire can target enemy infantry and the enemy bunker.
        targets = list(self.enemy_barracks_units)
        targets.extend(
            bunker for bunker in enemy_bunkers
            if not bunker.is_destroyed()
        )
        self.player.auto_fire(dt, targets, self.bullets)

        self.auto_place_if_possible()

        # Keep the camera inside the map.
        self.camera_x = self.player.x - 200
        max_camera = max(
            0,
            self.tilemap.width * TILE_SIZE - SCREEN_WIDTH,
        )
        self.camera_x = max(0, min(self.camera_x, max_camera))

        # Update player bullets and hit only enemy infantry or enemy bunker.
        remaining_bullets = []
        for bullet in self.bullets:
            bullet.update(dt)
            bullet_rect = bullet.get_hitbox()
            hit = False

            for unit in self.enemy_barracks_units:
                if unit.dead:
                    continue
                if bullet_rect.colliderect(unit.get_hitbox()):
                    unit.take_damage(bullet.damage)
                    bullet.dead = True
                    hit = True
                    break

            if not hit:
                for bunker in enemy_bunkers:
                    if (
                        not bunker.is_destroyed()
                        and bullet_rect.colliderect(bunker.get_hitbox())
                    ):
                        bunker.take_damage(bullet.damage)
                        bullet.dead = True
                        hit = True
                        break

            if not bullet.dead and not hit:
                remaining_bullets.append(bullet)

        self.bullets = remaining_bullets

        # Update enemy infantry. They fight friendly infantry in melee.
        remaining_enemy_units = []
        for unit in self.enemy_barracks_units:
            unit.update(dt, self.friendlies)
            if not unit.dead:
                remaining_enemy_units.append(unit)
        self.enemy_barracks_units = remaining_enemy_units

        # Friendly infantry fight enemy barracks infantry in melee.
        remaining_friendlies = []
        for friendly in self.friendlies:
            friendly.update(dt, self.enemy_barracks_units)
            if not friendly.dead:
                remaining_friendlies.append(friendly)
        self.friendlies = remaining_friendlies

        # Friendly MGs and artillery shoot enemy barracks infantry.
        # Enemy MGs and artillery shoot friendly infantry.
        for building in buildings:
            if isinstance(building, MGNest):
                if getattr(building, "is_enemy", False):
                    building.update(
                        dt, self.friendlies, self.enemy_bullets
                    )
                else:
                    building.update(
                        dt, self.enemy_barracks_units, self.bullets
                    )
            elif isinstance(building, Artillery):
                if getattr(building, "is_enemy", False):
                    building.update(
                        dt, self.friendlies, self.enemy_bullets
                    )
                else:
                    building.update(
                        dt, self.enemy_barracks_units, self.bullets
                    )

        # Enemy bullets can damage only friendly infantry.
        remaining_enemy_bullets = []
        for bullet in self.enemy_bullets:
            bullet.update(dt)
            bullet_rect = bullet.get_hitbox()

            for friendly in self.friendlies:
                if friendly.dead:
                    continue
                friendly_rect = pygame.Rect(
                    round(friendly.x),
                    round(friendly.y),
                    friendly.width,
                    friendly.height,
                )
                if bullet_rect.colliderect(friendly_rect):
                    friendly.hp -= bullet.damage
                    if friendly.hp <= 0:
                        friendly.dead = True
                    bullet.dead = True
                    break

            if not bullet.dead:
                remaining_enemy_bullets.append(bullet)

        self.enemy_bullets = remaining_enemy_bullets
        self.friendlies = [
            friendly for friendly in self.friendlies
            if not friendly.dead
        ]

        # Keep gold pickups if existing gameplay uses them.
        remaining_gold = []
        for gold in self.gold_pickups:
            if gold.update(dt, self.player):
                self.economy.supplies += gold.amount
            else:
                remaining_gold.append(gold)
        self.gold_pickups = remaining_gold

        # Lose if your bunker is destroyed.
        if player_bunkers and player_bunkers[0].is_destroyed():
            from states.game_over import GameOverState
            self.game.change_state(GameOverState(self.game))
            return

        # Win only when the enemy bunker is destroyed.
        if enemy_bunkers and all(
            bunker.is_destroyed() for bunker in enemy_bunkers
        ):
            from states.win_state import WinState
            self.game.change_state(WinState(self.game))
            return

        enemies = self.wave_director.get_enemies()
        self.player.update(dt, self.tilemap, enemies)

        enemies = self.wave_director.get_enemies()
        self.player.auto_fire(dt, enemies, self.bullets)

        self.auto_place_if_possible()

        # Camera follows the player and remains inside the map.
        self.camera_x = self.player.x - 200
        max_camera = max(
            0,
            self.tilemap.width * TILE_SIZE - SCREEN_WIDTH,
        )
        self.camera_x = max(0, min(self.camera_x, max_camera))

        self.wave_director.update()
        enemies = self.wave_director.get_enemies()

        # Update bullets and check full hitboxes.
        remaining_bullets = []

        for bullet in self.bullets:
            bullet.update(dt)

            bullet_rect = pygame.Rect(
                round(bullet.x),
                round(bullet.y),
                getattr(bullet, "width", 6),
                getattr(bullet, "height", 3),
            )

            hit = False

            for enemy in enemies:
                if enemy.dead:
                    continue

                if hasattr(enemy, "get_hitbox"):
                    enemy_rect = enemy.get_hitbox()
                else:
                    enemy_rect = pygame.Rect(
                        round(enemy.x),
                        round(enemy.y),
                        enemy.width,
                        enemy.height,
                    )

                if bullet_rect.colliderect(enemy_rect):
                    enemy.take_damage(bullet.damage)
                    bullet.dead = True
                    hit = True
                    break

            if not getattr(bullet, "dead", False) and not hit:
                remaining_bullets.append(bullet)

        self.bullets = remaining_bullets

        # Update enemies and collect gold drops.
        new_gold = []

        for enemy in enemies:
            enemy.update(dt)
            gold = enemy.spawn_gold()

            if gold:
                new_gold.append(gold)

        self.gold_pickups.extend(new_gold)

        # Keep the original GoldPickup API and pass the frame delta.
        remaining_gold = []

        for gold in self.gold_pickups:
            collected = gold.update(dt, self.player)

            if collected:
                self.economy.supplies += gold.amount
            else:
                remaining_gold.append(gold)

        self.gold_pickups = remaining_gold

        # Pay outstanding building costs after collecting supplies.
        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
            if spot_type not in BUILDING_CLASSES:
                continue

            tile = self.tilemap.get_tile(tile_x, tile_y)
            if tile is None or tile.building is None:
                continue

            cost = BUILD_COSTS[spot_type]
            paid = self.tilemap.paid_amount.get((tile_x, tile_y), 0)
            debt = max(0, cost - paid)
            payment = min(debt, max(0, self.economy.supplies))

            if payment > 0:
                self.economy.spend(payment)
                self.tilemap.paid_amount[(tile_x, tile_y)] = paid + payment

        # Update buildings.
        buildings = BuildingQuery.get_all_buildings(self.tilemap)
        bunkers = [b for b in buildings if isinstance(b, Bunker)]
        
        for building in buildings:
            if isinstance(building, Barracks):
                if getattr(building, "is_enemy", False):
                    building.update(dt, self.enemy_barracks_units)
                else:
                    building.update(dt, self.friendlies)
            elif isinstance(building, MGNest):
                if getattr(building, "is_enemy", False):
                    building.update(dt, self.friendlies, self.enemy_bullets)
                else:
                    building.update(dt, enemies, self.bullets)
            elif isinstance(building, Artillery):
                if getattr(building, "is_enemy", False):
                    building.update(dt, self.friendlies, self.enemy_bullets)
                else:
                    building.update(dt, enemies, self.bullets)
            else:
                building.update()

        # Update enemy barracks infantry separately.
        remaining_enemy_barracks_units = []

        for unit in self.enemy_barracks_units:
            unit.update(dt, self.friendlies)

            if not unit.dead:
                remaining_enemy_barracks_units.append(unit)

        self.enemy_barracks_units = remaining_enemy_barracks_units

        # Update friendly infantry.
        remaining_friendlies = []

        for friendly in self.friendlies:
            friendly.update(dt, enemies)

            if not friendly.dead:
                remaining_friendlies.append(friendly)

        self.friendlies = remaining_friendlies

        remaining_enemy_bullets = []

        for bullet in self.enemy_bullets:
            bullet.update(dt)
            bullet_rect = bullet.get_hitbox()

            for friendly in self.friendlies:
                if friendly.dead:
                    continue

                friendly_rect = pygame.Rect(
                    round(friendly.x),
                    round(friendly.y),
                    friendly.width,
                    friendly.height,
                )

                if bullet_rect.colliderect(friendly_rect):
                    friendly.hp -= bullet.damage

                    if friendly.hp <= 0:
                        friendly.dead = True

                    bullet.dead = True
                    break

            if not bullet.dead:
                remaining_enemy_bullets.append(bullet)

        self.enemy_bullets = remaining_enemy_bullets

        self.combat.update(buildings, enemies)

        # Enemies reaching the defensive line damage the bunker.
        if bunkers:
            bunker = bunkers[0]

            for enemy in enemies:
                if not enemy.dead and enemy.x < 50:
                    enemy.dead = True
                    bunker.take_damage(10)

            if bunker.is_destroyed():
                from states.game_over import GameOverState
                self.game.change_state(GameOverState(self.game))
                return

        # Preserve the original win condition.
        if (
            self.wave_director.wave_number
            == self.wave_director.total_waves
            and not enemies
        ):
            from states.win_state import WinState
            self.game.change_state(WinState(self.game))

    def get_nearby_build_spot(self):
        """Return the nearest build spot within interaction range."""
        player_x = self.player.x + self.player.width / 2
        player_y = self.player.y + self.player.height / 2

        nearest_spot = None
        nearest_distance = float("inf")

        for (tile_x, tile_y), spot_type in self.tilemap.spot_types.items():
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
        supplies = self.economy.supplies
        debt = max(0, cost - paid)
        
        if tile and tile.building is not None:
            message = f"{spot_type.upper()}: BUILT | PAID {paid}/{cost}"
        else:
            remaining = max(0, cost - paid)
            message = (
                f"{spot_type.upper()}: PAID {paid}/{cost} | "
                f"OWES {remaining} | HAVE {supplies}"
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

        buildings = BuildingQuery.get_all_buildings(self.tilemap)
        bunkers = [b for b in buildings if isinstance(b, Bunker)]
        bunker_hp = bunkers[0].hp if bunkers else 0

        self.hud.draw(
            screen,
            self.economy.supplies,
            0,
            0,
            bunker_hp,
            self.economy.total_defense_cost,
            self.economy.spent_defense_cost,
        )

        self.draw_build_prompt(screen)

        counts = BuildingQuery.count_buildings(self.tilemap)
        self.hud.draw_building_counts(screen, counts)
