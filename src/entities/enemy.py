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
    
class EnemyInfantry(EnemyBase):
    def __init__(self, x, y):
        super().__init__(
            x,
            y,
            speed=120,
            hp=40,
            gold_drop=5,
        )
        
        self.width = 24
        self.height = 24
        self.is_barracks_unit = True
    
    
    def update(self, dt, friendlies, player_bunker=None):
        if self.dead:
            return

        move_amount = self.speed * dt / 1000

        # Priority 1: attack living friendly infantry.
        living_friendlies = [
            friendly for friendly in friendlies if not friendly.dead
        ]

        if living_friendlies:
            target = min(
                living_friendlies,
                key=lambda friendly: math.hypot(
                    friendly.x - self.x,
                    friendly.y - self.y
                )
            )

            dx = target.x - self.x
            dy = target.y - self.y
            distance = math.hypot(dx, dy)

            if distance > 0:
                self.x += dx / distance * move_amount
                self.y += dy / distance * move_amount

            if self.get_hitbox().colliderect(target.get_hitbox()):
                target.hp -= self.hp
                target.dead = target.hp <= 0
                self.take_damage(self.hp)

            return

        # Priority 2: charge toward the player's bunker.
        if player_bunker is None or player_bunker.dead:
            return

        bunker_rect = player_bunker.get_hitbox()
        enemy_rect = self.get_hitbox()

        # If touching the bunker, explode and deal damage.
        if enemy_rect.colliderect(bunker_rect):
            player_bunker.take_damage(self.hp)
            self.take_damage(self.hp)
            return

        # Move toward the bunker center in both axes.
        enemy_cx = self.x + self.width / 2
        enemy_cy = self.y + self.height / 2
        bunker_cx = bunker_rect.centerx
        bunker_cy = bunker_rect.centery

        dx = bunker_cx - enemy_cx
        dy = bunker_cy - enemy_cy
        distance = math.hypot(dx, dy)

        if distance > 0:
            self.x += dx / distance * move_amount
            self.y += dy / distance * move_amount

        # Check collision again after moving, so contact triggers immediately.
        if self.get_hitbox().colliderect(bunker_rect):
            player_bunker.take_damage(self.hp)
            self.take_damage(self.hp)
    
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