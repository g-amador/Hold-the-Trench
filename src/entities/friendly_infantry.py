"""
Friendly infantry spawned from barracks.
Moves toward nearest enemy, engages in melee.
Kills exactly one enemy and dies.
"""

import math
import pygame
import random

from graphics.sprite_generator import SpriteGenerator

class FriendlyInfantry:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.speed = 120
        self.hp = 40
        self.width = 24
        self.height = 24
        self.dead = False
        self.kill_count = 0

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
        self.upper_idle = self.sprite_generator.load(f"{prefix}_d.png")
        self.upper_aim = self.sprite_generator.load(f"{prefix}_e.png")

        # Animation state
        self.facing = 1 
        self.run_frame = 0
        self.run_timer = 0.0
        self.run_frame_duration = 0.12
        self.is_moving = False
        self.shoot_animation_timer = 0.0
        self.shoot_animation_duration = 0.18

    def update(self, dt, enemies, bullets=None):
        if self.dead:
            return

        target = None
        best_dist = None

        for enemy in enemies:
            if enemy.dead:
                continue
            dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                target = enemy

        if target is None:
            self.is_moving = False
            return

        dx = target.x - self.x
        dy = target.y - self.y
        length = math.hypot(dx, dy)

        if length > 0:
            self.facing = 1 if dx > 0 else -1
            self.is_moving = True
            
            # Move toward enemy
            self.x += (dx / length) * self.speed * dt / 1000
            self.y += (dy / length) * self.speed * dt / 1000

            # Shooting Logic (Range: 200px, Cone: 90 deg)
            if length < 200:
                # Normalize and check dot product for 90 degree cone
                nx, ny = dx / length, dy / length
                if (nx * self.facing) >= 0.707:
                    self.shoot_animation_timer = self.shoot_animation_duration
                    # If your game handles bullets via a list:
                    # bullets.append(Bullet(self.x, self.y, nx, ny))
            else:
                self.shoot_animation_timer = 0

        # Animation update
        if self.is_moving:
            self.run_timer += dt / 1000
            while self.run_timer >= self.run_frame_duration:
                self.run_timer -= self.run_frame_duration
                self.run_frame = (self.run_frame + 1) % len(self.legs_run)
        else:
            self.run_frame = 0

        self.shoot_animation_timer = max(0, self.shoot_animation_timer - dt / 1000)

        # Melee Collision
        friendly_rect = self.get_hitbox()
        enemy_rect = target.get_hitbox() if hasattr(target, "get_hitbox") else pygame.Rect(
            round(target.x), round(target.y), target.width, target.height
        )

        if friendly_rect.colliderect(enemy_rect):
            if self.kill_count == 0:
                target.take_damage(target.hp)
                self.kill_count = 1
            self.hp = 0
            self.dead = True

    def get_hitbox(self):
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def draw(self, screen, camera_x):
        if self.dead: return
        screen_x = round(self.x - camera_x)
        screen_y = round(self.y)
        
        legs = self.legs_run[self.run_frame] if self.is_moving else self.legs_idle
        upper = self.upper_aim if self.shoot_animation_timer > 0 else self.upper_idle
        
        pos = (screen_x, screen_y)
        self.sprite_generator.draw(screen, legs, pos, self.facing)
        self.sprite_generator.draw(screen, upper, pos, self.facing)
