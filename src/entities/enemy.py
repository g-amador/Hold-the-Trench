"""
WW1 enemies: Infantry, Cavalry, Tank.
Move leftward across no man's land and drop gold once on death.
"""

import math
import pygame

from entities.gold_pickup import GoldPickup


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
    

class Infantry(EnemyBase):
    def __init__(self, x, y):
        super().__init__(x, y, speed=60, hp=40, gold_drop=5)


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

class EnemyInfantry(Infantry):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.is_barracks_unit = True
    
    def update(self, dt, friendlies):
        if self.dead:
            return

        target = None
        best_dist = None

        for friendly in friendlies:
            if friendly.dead:
                continue

            dist = math.hypot(
                friendly.x + friendly.width / 2
                - (self.x + self.width / 2),
                friendly.y + friendly.height / 2
                - (self.y + self.height / 2),
            )

            if best_dist is None or dist < best_dist:
                best_dist = dist
                target = friendly

        # No friendly infantry nearby: advance toward the player's side.
        if target is None:
            self.x -= self.speed * dt / 1000
            return

        dx = (
            target.x + target.width / 2
            - (self.x + self.width / 2)
        )
        dy = (
            target.y + target.height / 2
            - (self.y + self.height / 2)
        )

        length = math.hypot(dx, dy)

        if length > 0:
            dx /= length
            dy /= length
            self.x += dx * self.speed * dt / 1000
            self.y += dy * self.speed * dt / 1000

        enemy_rect = self.get_hitbox()
        friendly_rect = pygame.Rect(
            round(target.x),
            round(target.y),
            target.width,
            target.height,
        )

        if enemy_rect.colliderect(friendly_rect):
            target.hp -= self.hp
            target.dead = True
            self.take_damage(self.hp)
