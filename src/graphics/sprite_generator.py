"""
Sprite utilities for loading and animating character sprites.
"""

import pygame

from utils.image_loader import load_image


class SpriteGenerator:
    """Loads and prepares sprite frames for a character."""

    def __init__(self):
        self._flip_cache = {}

    def load(self, filename):
        """Load a sprite with transparency."""
        return load_image(filename, alpha=True)

    def load_animation(self, filenames):
        """Load a list of animation frames."""
        return [self.load(filename) for filename in filenames]

    def get_facing_sprite(self, sprite, facing):
        """
        Return a sprite facing the requested direction.
        facing: 1 = right, -1 = left.
        """
        if facing == 1:
            return sprite

        key = id(sprite)

        if key not in self._flip_cache:
            self._flip_cache[key] = pygame.transform.flip(
                sprite, True, False
            )

        return self._flip_cache[key]

    def draw(self, screen, sprite, position, facing=1):
        """Draw a sprite facing the requested direction."""
        image = self.get_facing_sprite(sprite, facing)
        screen.blit(image, position)