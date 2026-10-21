"""
Gold dropped by defeated enemies.

The pickup bobs in place until the player walks within range. The
battle state polls update() every frame and, when it returns True,
credits the amount to EconomySystem.gold and drops the pickup from
its list.
"""

import math
import pygame


class GoldPickup:
    def __init__(self, x, y, amount):
        # World position (where the dying enemy stood).
        self.x = x
        self.y = y

        # Gold credited to the economy exactly once on collection.
        self.amount = amount

        # Guard flag: prevents crediting twice and stops future drawing.
        self.collected = False

        # Sine-wave phase driving the floating bob animation; advances
        # with dt so the animation is framerate independent.
        self.float_phase = 0
        # Pixel-height offset applied only at draw time (never affects
        # pickup logic).
        self.y_offset = 0

        # Small square drawn shape; collection is distance based, not
        # rectangle based, so these are purely visual.
        self.width = 12
        self.height = 12

    def update(self, dt, player):
        """Advance the bob animation; collect when the player is near.

        Returns True exactly once (the collect frame) so the caller
        knows to credit the amount and remove this pickup.
        """
        # Already credited: no double payment possible.
        if self.collected:
            return False

        # dt is milliseconds, hence the small divisor to advance the phase.
        self.float_phase += dt / 200
        self.y_offset = math.sin(self.float_phase) * 3

        # Radial pickup range instead of a collision rect: friendlier
        # and simpler; the player collects by walking roughly near it.
        dist = math.hypot(player.x - self.x, player.y - self.y)
        if dist < 64:
            self.collected = True
            return True

        return False

    def draw(self, screen, camera_x):
        # Collected pickups vanish the same frame they pay out.
        if self.collected:
            return

        # Draw at the bobbed position; camera only offsets horizontally.
        pygame.draw.rect(
            screen,
            (255, 215, 0),
            (self.x - camera_x, self.y + self.y_offset, self.width, self.height)
        )
