"""
WW1 infantry player with WASD movement, collision, sliding, snapping,
and wire slow-down.
"""

import math
import pygame

from config import SCREEN_HEIGHT, TILE_SIZE
from entities.bullet import Bullet

BLOCKING_TILES = {"#", "H"}
BLOCKING_BUILDINGS = {"mg", "bunker", "barracks", "artillery"}
BUILDABLE_SPOTS = {"mg", "barracks", "artillery"}
SLOW_TILES = {"W"}


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

        self.speed = 120
        self.width = 24
        self.height = 24

        self.shoot_cooldown = 0.25
        self.shoot_timer = 0

        self.max_world_x = 2000

    def get_hitbox(self):
        """Return the player's hitbox in world coordinates."""
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )

    def _is_blocked_at(self, x, y, tilemap, enemies=None):
        """Check terrain, build spots, buildings, and enemy collisions."""
        rect = pygame.Rect(
            round(x),
            round(y),
            self.width,
            self.height,
        )

        min_tile_x = rect.left // TILE_SIZE
        max_tile_x = (rect.right - 1) // TILE_SIZE
        min_tile_y = rect.top // TILE_SIZE
        max_tile_y = (rect.bottom - 1) // TILE_SIZE

        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                tile = tilemap.get_tile(tile_x, tile_y)

                if tile is None:
                    return True

                if tile.type_char in BLOCKING_TILES:
                    return True

                spot_type = tilemap.spot_types.get((tile_x, tile_y))

                # An empty build spot is solid until construction occurs.
                if (
                    spot_type in BUILDABLE_SPOTS
                    and tile.building is None
                ):
                    return True

                building = tile.building
                if (
                    building is not None
                    and getattr(building, "type", None)
                    in BLOCKING_BUILDINGS
                ):
                    return True

        if enemies:
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

                if rect.colliderect(enemy_rect):
                    return True

        return False

    def _move_axis(self, amount, axis, tilemap, enemies=None):
        """Move along one axis without crossing blocking geometry."""
        if amount == 0:
            return

        direction = 1 if amount > 0 else -1
        remaining = abs(amount)
        max_step = 1.0

        while remaining > 0:
            step_size = min(remaining, max_step)
            step = direction * step_size

            test_x = self.x + step if axis == "x" else self.x
            test_y = self.y + step if axis == "y" else self.y

            if self._is_blocked_at(test_x, test_y, tilemap, enemies):
                break

            if axis == "x":
                self.x = test_x
            else:
                self.y = test_y

            remaining -= step_size

    def handle_input(self, dt, tilemap, enemies=None):
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        # Normalize diagonal movement.
        if dx and dy:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length

        tile_x = int(self.x // TILE_SIZE)
        tile_y = int(self.y // TILE_SIZE)
        tile = tilemap.get_tile(tile_x, tile_y)

        move_speed = self.speed
        if tile and tile.type_char in SLOW_TILES:
            move_speed *= 0.45

        move_x = dx * move_speed * dt / 1000
        move_y = dy * move_speed * dt / 1000

        # Resolve axes separately to preserve wall sliding.
        self._move_axis(move_x, "x", tilemap, enemies)
        self._move_axis(move_y, "y", tilemap, enemies)

    def _clamp_to_bounds(self):
        self.x = max(0, min(self.x, self.max_world_x))
        self.y = max(40, min(self.y, SCREEN_HEIGHT - self.height))

    def update(self, dt, tilemap, enemies=None):
        self.handle_input(dt, tilemap, enemies)
        self._clamp_to_bounds()

        self.shoot_timer -= dt / 1000
        if self.shoot_timer < 0:
            self.shoot_timer = 0

    def shoot_toward(self, target, bullets):
        if self.shoot_timer > 0:
            return

        start_x = self.x + self.width / 2
        start_y = self.y + self.height / 2

        target_x = target.x + target.width / 2
        target_y = target.y + target.height / 2

        dx = target_x - start_x
        dy = target_y - start_y

        distance = math.hypot(dx, dy)
        if distance == 0:
            return

        dx /= distance
        dy /= distance

        bullets.append(Bullet(start_x, start_y, dx, dy))
        self.shoot_timer = self.shoot_cooldown

    def auto_fire(self, dt, enemies, bullets):
        if self.shoot_timer > 0:
            return

        player_x = self.x + self.width / 2
        player_y = self.y + self.height / 2

        nearest_enemy = None
        nearest_distance = float("inf")

        for enemy in enemies:
            if enemy.dead:
                continue

            enemy_x = enemy.x + enemy.width / 2
            enemy_y = enemy.y + enemy.height / 2

            distance = math.hypot(
                enemy_x - player_x,
                enemy_y - player_y,
            )

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_enemy = enemy

        if nearest_enemy and nearest_distance <= 300:
            self.shoot_toward(nearest_enemy, bullets)

    def draw(self, screen, camera_x):
        rect = self.get_hitbox()
        rect.x -= round(camera_x)
        pygame.draw.rect(screen, (0, 200, 255), rect)
