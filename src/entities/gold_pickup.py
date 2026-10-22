"""
Gold dropped by defeated enemies.

The pickup bobs in place until the player walks within range. The
battle state polls update() every frame and, when it returns True,
credits the amount to EconomySystem.gold and drops the pickup from
its list.

Art: defeated AXIS soldiers (ger/aust) drop coin_ger.png; defeated
ALLIES soldiers drop coin_brit.png / coin_fr.png. The dying unit
passes the filename; missing files fall back to the plain gold square
(the gold square is also the whole look in block mode terms — a coin
that cannot load must never crash the game).
"""

import math
import pygame

from utils.image_loader import load_image

# Draw size for coin art; scaled copy, the cache is never mutated.
COIN_SIZE = (12, 12)


class GoldPickup:
    def __init__(self, x, y, amount, texture=None):
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

        # Nation coin art: loaded once here (image cache holds the
        # scaled copy separately from the raw asset). None means the
        # art is missing and draw() falls back to the gold square.
        self.texture = None

        if texture is not None:
            try:
                image = load_image(texture, alpha=True)
                self.texture = pygame.transform.scale(image, COIN_SIZE)
            except FileNotFoundError:
                self.texture = None

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

        draw_x = self.x - camera_x
        draw_y = self.y + self.y_offset

        if self.texture is not None:
            screen.blit(self.texture, (draw_x, draw_y))
            return

        # Fallback: plain gold square (asset missing or no coin named).
        pygame.draw.rect(
            screen,
            (255, 215, 0),
            (draw_x, draw_y, self.width, self.height),
        )
