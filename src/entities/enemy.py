"""
WW1 enemies: Infantry, Cavalry, Tank.
Move leftward across no man's land and drop gold once on death.
"""

import math
import pygame
import random

from entities.gold_pickup import GoldPickup
from graphics.sprite_generator import SpriteGenerator


class EnemyBase:
    def __init__(self, x, y, speed, hp, gold_drop):
        self.x = x
        self.y = y

        self.speed = speed
        self.hp = hp
        self.gold_drop = gold_drop

        self.width = 24
        self.height = 32

        self.dead = False
        self.gold_spawned = False

    def update(self, dt):
        if self.dead:
            return

        self.x -= self.speed * dt / 1000

        if self.hp <= 0:
            self.dead = True

    def get_hitbox(self):
        """Return the enemy's collision rectangle in world coordinates."""
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )

    def draw(self, screen, camera_x):
        if self.dead:
            return

        pygame.draw.rect(
            screen,
            (200, 50, 50),
            (self.x - camera_x, self.y, self.width, self.height)
        )

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.dead = True

    def spawn_gold(self):
        if self.dead and not self.gold_spawned and self.gold_drop > 0:
            self.gold_spawned = True
            return GoldPickup(self.x, self.y, self.gold_drop)
        return None
    
class EnemyInfantry(EnemyBase):
    def __init__(self, x, y):
        super().__init__(x, y, speed=120, hp=40, gold_drop=5)
        self.width = 24
        self.height = 24
        self.is_barracks_unit = True

        # Randomly choose between German and Austrian assets
        faction = random.choice(["ger", "aust"])
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

        self.facing = -1
        self.run_frame = 0
        self.run_timer = 0.0
        self.run_frame_duration = 0.12
        self.is_moving = False
        self.shoot_animation_timer = 0.0
        self.shoot_animation_duration = 0.18

    def update(self, dt, friendlies, player_bunker=None):
        if self.dead: return

        move_amount = self.speed * dt / 1000
        self.is_moving = True

        living_friendlies = [f for f in friendlies if not f.dead]

        if living_friendlies:
            target = min(living_friendlies, key=lambda f: math.hypot(f.x - self.x, f.y - self.y))
            dx, dy = target.x - self.x, target.y - self.y
            dist = math.hypot(dx, dy)

            if dist > 0:
                self.facing = 1 if dx > 0 else -1
                self.x += (dx / dist) * move_amount
                self.y += (dy / dist) * move_amount

                # Shooting check (90 deg cone)
                if dist < 200:
                    if (dx / dist * self.facing) >= 0.707:
                        self.shoot_animation_timer = self.shoot_animation_duration
                else:
                    self.shoot_animation_timer = 0

            if self.get_hitbox().colliderect(target.get_hitbox()):
                target.hp -= self.hp
                target.dead = target.hp <= 0
                self.take_damage(self.hp)
            return

        # Charge Bunker logic (remaining same as your provided code...)
        # [Insert your existing bunker charging code here]

        # Animation logic
        self.run_timer += dt / 1000
        while self.run_timer >= self.run_frame_duration:
            self.run_timer -= self.run_frame_duration
            self.run_frame = (self.run_frame + 1) % len(self.legs_run)
        self.shoot_animation_timer = max(0, self.shoot_animation_timer - dt / 1000)

    def draw(self, screen, camera_x):
        if self.dead: return
        screen_x = round(self.x - camera_x)
        screen_y = round(self.y)
        
        legs = self.legs_run[self.run_frame] if self.is_moving else self.legs_idle
        upper = self.upper_aim if self.shoot_animation_timer > 0 else self.upper_idle
        
        pos = (screen_x, screen_y)
        self.sprite_generator.draw(screen, legs, pos, self.facing)
        self.sprite_generator.draw(screen, upper, pos, self.facing)
    
class Cavalry(EnemyBase):
    def __init__(self, x, y):
        super().__init__(x, y, speed=120, hp=80, gold_drop=10)
        self.width = 32
        self.height = 32

class Tank(EnemyBase):
    def __init__(self, x, y):
        super().__init__(x, y, speed=30, hp=300, gold_drop=20)
        self.width = 48
        self.height = 32