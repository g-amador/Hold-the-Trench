"""
Sprite utilities for loading and animating character sprites.
"""

import pygame

from utils.image_loader import load_image


class SpriteGenerator:
    """Loads and prepares sprite frames for a character.

    Cheap wrappers around utils/image_loader because the real caching
    lives there: repeated loads here are free.
    """

    # Class-level: every instance shares flipped frames, and the loaded
    # surfaces live forever in the image cache, so surface ids stay valid.
    _flip_cache = {}

    def load(self, filename):
        """Load a sprite with transparency."""
        return load_image(filename, alpha=True)

    def load_animation(self, filenames):
        """Load a list of animation frames."""
        return [self.load(filename) for filename in filenames]

    def load_unit_frames(self, prefix):
        """Load the standard infantry frame set.

        Frames: {prefix}_a/_b/_c legs, {prefix}_d upper idle,
        {prefix}_e upper aim. Returns None when any file is missing so
        callers can fall back to block rendering.
        """
        try:
            return {
                "legs_idle": self.load(f"{prefix}_a.png"),
                "legs_run": self.load_animation([
                    f"{prefix}_a.png",
                    f"{prefix}_b.png",
                    f"{prefix}_c.png",
                ]),
                "upper_idle": self.load(f"{prefix}_d.png"),
                "upper_aim": self.load(f"{prefix}_e.png"),
            }
        except FileNotFoundError:
            return None

    def get_facing_sprite(self, sprite, facing):
        """
        Return a sprite facing the requested direction.
        facing: 1 = right, -1 = left.
        """
        if facing == 1:
            return sprite

        key = id(sprite)
        cached = self._flip_cache.get(key)

        if cached is None or cached[0] is not sprite:
            flipped = pygame.transform.flip(sprite, True, False)
            self._flip_cache[key] = (sprite, flipped)
            return flipped

        return cached[1]

    def draw(self, screen, sprite, position, facing=1):
        """Draw a sprite facing the requested direction."""
        image = self.get_facing_sprite(sprite, facing)
        screen.blit(image, position)
