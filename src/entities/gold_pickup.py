"""
Gold dropped by defeated enemies.

The pickup bobs in place; when the player gets close enough the coin
is MAGNETICALLY pulled toward them (user request: "the player is a
magnet attracting the coins") until it reaches the pickup radius and
pays out. The battle state polls update() every frame and, when it
returns True, credits the amount to EconomySystem.gold and drops the
pickup from its list.

Art: the coin side follows the player's choice (user rule): playing
ALLIES, axis soldiers (ger/aust) drop coin_ger.png; playing AXIS,
every allied soldier (fr units AND brit units) drops coin_fr.png
(factions.side_coin). The dying unit passes the filename; missing
files fall back to the plain gold square (the gold square is also the
whole look in block mode terms — a coin that cannot load must never
crash the game).
"""

import math
import pygame

from config import (
    GOLD,
    GOLD_PICKUP_RADIUS_PX,
    GOLD_MAGNET_RADIUS_PX,
    GOLD_MAGNET_SPEED_PX_S,
)
from utils.image_loader import load_image

# Draw size for coin art in the world layer; scaled copy, the cache is
# never mutated. The OPEN quality comes from three places (user:
# "coin images with good quality"):
#   1. the world copy uses smoothscale — the 256x256 source art is
#      NOT nearest-squeezed into 12x12 anymore,
#   2. the FULL view's uniform zoom then downscales that smoothly,
#   3. in the CLOSE view the coin skips the upscaled world layer
#      entirely and AssaultPhase._blit_coin_hires smoothscales the
#      NATIVE art straight to screen (more pixels per world px than
#      the ~3.1x CLOSE zoom could show on the world copy).
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
        # raw source, never mutated). None means the art is missing
        # and draw() falls back to the gold square.
        self.texture = None
        self.image_native = None   # CLOSE hires source (256x256)

        if texture is not None:
            try:
                native = load_image(texture, alpha=True)
                self.texture = pygame.transform.smoothscale(
                    native,
                    COIN_SIZE,
                )
                self.image_native = native
            except FileNotFoundError:
                self.texture = None
                self.image_native = None

    def update(self, dt, player):
        """Advance the bob animation; magnet-pull and collect vs the player.

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
        if dist < GOLD_PICKUP_RADIUS_PX:
            self.collected = True
            return True

        # MAGNETISM: the player attracts coins (user request). Inside
        # the magnet radius the coin slides toward the player at a
        # fixed px/s read from config, so coin hunting becomes
        # automatic once the player is close; the pull happens over a
        # few frames at normal speed (never a teleport — a step is
        # capped at the remaining distance). Coins keep their pulled
        # position if the player moves on, and still bob while they
        # fly (force_fly visual charm).
        if dist < GOLD_MAGNET_RADIUS_PX:
            # dt is in milliseconds: convert to seconds for the px/s
            # pull speed.
            step = min(dist, GOLD_MAGNET_SPEED_PX_S * dt / 1000.0)
            if step > 0 and dist > 0:
                self.x += (player.x - self.x) / dist * step
                self.y += (player.y - self.y) / dist * step

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
            GOLD,
            (draw_x, draw_y, self.width, self.height),
        )
