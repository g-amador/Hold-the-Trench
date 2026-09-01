"""
WW1 enemies: Infantry, Cavalry, Tank.
Move leftward across no man's land and drop gold once on death.
"""

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
        super().__init__(x, y, speed=60, hp=40, gold_drop=1)


class Cavalry(EnemyBase):
    def __init__(self, x, y):
        super().__init__(x, y, speed=120, hp=80, gold_drop=2)
        self.width = 32
        self.height = 32


class Tank(EnemyBase):
    def __init__(self, x, y):
        super().__init__(x, y, speed=30, hp=300, gold_drop=5)
        self.width = 48
        self.height = 32
