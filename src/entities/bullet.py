"""
Bullet projectile: a straight-flying shot fired by the player,
machine gun nests, and artillery.

A bullet stores its own direction vector, moves on every update, and
leaves hit detection to the battle state: the state walks its bullet
lists each frame, checks overlap against targets, and drops dead
bullets. A bullet that leaves the world self-destructs via `dead`.
"""

import pygame


class Bullet:
    def __init__(self, x, y, dx, dy):
        # Spawn position in world coordinates (usually the shooter's
        # muzzle/center point).
        self.x = x
        self.y = y

        # Movement and damage: speed is pixels per second; damage is
        # subtracted from a target's hp in one hit.
        self.speed = 400
        self.damage = 20

        # Small rectangular hit box. Every shooter passes a NORMALIZED
        # direction vector (unit length), so direction values are
        # typically -1..1.
        self.width = 6
        self.height = 3

        # Set True once the bullet leaves the world; the caller's list
        # filter then removes it.
        self.dead = False

        # Normalized direction vector; movement scales it by speed*dt.
        self.dx = dx
        self.dy = dy

    def update(self, dt):
        """Move along the direction vector; die when far outside the world."""
        # dt is milliseconds in this project, hence the /1000 to seconds.
        self.x += self.dx * self.speed * dt / 1000
        self.y += self.dy * self.speed * dt / 1000

        # Bounds are generous: bullets die from leaving the playable
        # area, never from true walls, so long-range artillery shots exist.
        if self.x > 5000 or self.x < -500 or self.y < -500 or self.y > 5000:
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
