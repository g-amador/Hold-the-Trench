"""
WW1 infantry player with WASD movement, collision, sliding,
snapping, wire slow-down, sprite animation, and shooting.
"""

import math
import pygame
import random

from config import SCREEN_HEIGHT, TILE_SIZE
from entities.bullet import Bullet
from graphics.sprite_generator import SpriteGenerator


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

        # Randomly choose between German and Austrian assets
        faction = random.choice(["brit", "fr"])
        prefix = f"infantry_unit_{faction}_1"
        
        # Sprites (Enemy Assets)
        self.sprite_generator = SpriteGenerator()

        # Use the prefix to load the random faction's sprites
        self.legs_idle = self.sprite_generator.load(f"{prefix}_a.png")
        self.legs_run = self.sprite_generator.load_animation([
            f"{prefix}_a.png",
            f"{prefix}_b.png",
            f"{prefix}_c.png"
        ])

        # Upper body: weapon lowered and raised.
        self.upper_idle = self.sprite_generator.load(f"{prefix}_d.png")
        self.upper_aim = self.sprite_generator.load(f"{prefix}_e.png")

        # Animation timing.
        self.run_frame = 0
        self.run_timer = 0.0
        self.run_frame_duration = 0.12

        self.shoot_animation_timer = 0.0
        self.shoot_animation_duration = 0.18

        self.is_moving = False
        self.facing = 1  # 1 = right, -1 = left

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

                # An empty build spot is solid until construction.
                if spot_type in BUILDABLE_SPOTS and tile.building is None:
                    return True

                building = tile.building

                if (
                    building is not None
                    and getattr(building, "type", None) in BLOCKING_BUILDINGS
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
        """Handle movement input and preserve wall sliding."""
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

        # Face the direction of horizontal movement.
        if dx > 0:
            self.facing = 1
        elif dx < 0:
            self.facing = -1

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
        """Keep the player within the playable area."""
        self.x = max(0, min(self.x, self.max_world_x))
        self.y = max(40, min(self.y, SCREEN_HEIGHT - self.height))

    def update(self, dt, tilemap, enemies=None):
        """Update movement, running animation, and shot timers."""
        old_x = self.x
        old_y = self.y

        self.handle_input(dt, tilemap, enemies)
        self._clamp_to_bounds()

        self.is_moving = (
            abs(self.x - old_x) > 0.01
            or abs(self.y - old_y) > 0.01
        )

        if self.is_moving:
            self.run_timer += dt / 1000

            while self.run_timer >= self.run_frame_duration:
                self.run_timer -= self.run_frame_duration
                self.run_frame = (self.run_frame + 1) % len(self.legs_run)
        else:
            self.run_frame = 0
            self.run_timer = 0.0

        self.shoot_timer = max(0.0, self.shoot_timer - dt / 1000)
        self.shoot_animation_timer = max(
            0.0,
            self.shoot_animation_timer - dt / 1000,
        )

    def shoot_toward(self, target, bullets):
        """Fire at a target within a 90-degree cone in front of the player."""
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

        # Normalize target vector
        nx, ny = dx / distance, dy / distance

        # Facing vector: (1, 0) if right, (-1, 0) if left
        fx, fy = (self.facing, 0)

        # Dot product of normalized vectors = cos(theta)
        # cos(45 degrees) is approx 0.707
        dot_product = nx * fx + ny * fy

        if dot_product < 0.707:
            return

        bullets.append(Bullet(start_x, start_y, nx, ny))

        self.shoot_timer = self.shoot_cooldown
        self.shoot_animation_timer = self.shoot_animation_duration

    def auto_fire(self, dt, enemies, bullets):
        """Shoot the nearest enemy within a 90-degree cone in front, within 300 pixels."""
        if self.shoot_timer > 0:
            return

        player_x = self.x + self.width / 2
        player_y = self.y + self.height / 2

        nearest_enemy = None
        nearest_distance = float("inf")

        for enemy in enemies:
            if getattr(enemy, "dead", False):
                continue

            enemy_x = enemy.x + enemy.width / 2
            enemy_y = enemy.y + enemy.height / 2
            dx = enemy_x - player_x
            dy = enemy_y - player_y
            distance = math.hypot(dx, dy)

            if distance == 0 or distance > 300:
                continue

            # Normalize target vector
            nx, ny = dx / distance, dy / distance
            
            # Dot product with facing vector (self.facing, 0)
            dot_product = nx * self.facing

            # Only consider enemies within 45 degrees up/down (total 90 deg cone)
            if dot_product < 0.707:
                continue

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_enemy = enemy

        if nearest_enemy:
            self.shoot_toward(nearest_enemy, bullets)

    def draw(self, screen, camera_x):
        """Draw animated legs and upper body facing the correct direction."""
        screen_x = round(self.x - camera_x)
        screen_y = round(self.y)

        if self.is_moving:
            legs = self.legs_run[self.run_frame]
        else:
            legs = self.legs_idle

        if self.shoot_animation_timer > 0:
            upper = self.upper_aim
        else:
            upper = self.upper_idle

        position = (screen_x, screen_y)
        self.sprite_generator.draw(
            screen, legs, position, self.facing
        )
        self.sprite_generator.draw(
            screen, upper, position, self.facing
        )
