"""
Bullet projectile: a straight-flying shot fired by the player,
machine gun nests, artillery, and infantry.

A bullet stores its own direction vector, moves on every update, and
leaves hit detection to the battle state: the state walks its bullet
lists each frame, checks overlap against targets, and drops dead
bullets. A bullet dies via `dead` either from impact or after flying
its configured range (config.BULLET_RANGE_PX).
"""

import pygame

from config import BULLET_RANGE_PX


class Bullet:
    def __init__(self, x, y, dx, dy, armor_damage=False):
        # Spawn position in world coordinates (usually the shooter's
        # muzzle/center point).
        self.x = x
        self.y = y

        # Movement and damage: speed is pixels per second; damage is
        # subtracted from a target's hp in one hit.
        self.speed = 400
        self.damage = 20

        # Armor rule (user spec): only artillery splash and tank shots
        # can hurt armored units. Bullets default to False (infantry,
        # player, MG-nest and car shots pass through armor harmlessly
        # — the hit loop skips armored targets they reach); only tank
        # shots set this True.
        self.armor_damage = armor_damage

        # Small rectangular hit box. Every shooter passes a NORMALIZED
        # direction vector (unit length), so direction values are
        # typically -1..1.
        self.width = 6
        self.height = 3

        # Set True once the bullet impacts, expires at max range, or
        # leaves the world; the caller's list filter then removes it.
        self.dead = False

        # Normalized direction vector; movement scales it by speed*dt.
        self.dx = dx
        self.dy = dy

        # Range flight: distance measured along the actual path so a
        # diagonal shot expires exactly like a straight one. BULLET_RANGE_PX
        # sits above every engagement range in config (see there).
        self.traveled = 0.0
        self.max_distance = BULLET_RANGE_PX

    def update(self, dt):
        """Move along the direction vector; die at impact or max range."""
        # dt is milliseconds in this project, hence the /1000 to seconds.
        step = self.speed * dt / 1000
        self.x += self.dx * step
        self.y += self.dy * step
        self.traveled += step

        # Range cap: the bullet disappears after flying BULLET_RANGE_PX
        # — shots never streak across the whole map to fizzle at some
        # arbitrary far edge.
        if self.traveled >= self.max_distance:
            self.dead = True

    def get_hitbox(self):
        """Return the bullet's collision rectangle in world coordinates."""
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )

    def draw(self, screen, camera_x):
        # Only horizontal camera offset: the battlefield is a horizontal
        # strip, so world y maps 1:1 to screen y.
        pygame.draw.rect(
            screen,
            (255, 255, 0),
            (self.x - camera_x, self.y, self.width, self.height)
        )
