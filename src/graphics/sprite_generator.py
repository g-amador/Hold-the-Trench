"""
Sprite utilities for loading and animating character sprites.
"""

import pygame

from utils.image_loader import load_first_image, load_image


class SpriteGenerator:
    """Loads and prepares sprite frames for a character.

    Cheap wrappers around utils/image_loader because the real caching
    lives there: repeated loads here are free.
    """

    # Class-level: every instance shares flipped frames, and the loaded
    # surfaces live forever in the image cache, so surface ids stay valid.
    _flip_cache = {}

    # Extensions tried per frame, in order: the infantry art pack
    # mixes lossless .png cut-outs with .jpeg poses (same letters,
    # different extensions per nation).
    FRAME_EXTENSIONS = (".png", ".jpeg", ".jpg")

    def load(self, filename):
        """Load a sprite with transparency."""
        return load_image(filename, alpha=True)

    def load_animation(self, filenames):
        """Load a list of animation frames."""
        return [self.load(filename) for filename in filenames]

    def load_unit_frames(self, prefix, size=None):
        """Load the standard infantry frame set (full-body poses).

        USER ART RULE (single-layer art): the old legs/upper composite
        is RETIRED — every file is ONE full-body pose now:
          _a.._f  running cycle (six frames, played while moving)
          _g      at rest
          _h      at rest (second pose — stands in for the retired
                  aim pose on the per-shot blip while standing)
        Each letter tries the FRAME_EXTENSIONS in order. `size`
        smoothscales every frame to the unit's world box at load
        (the sources are 1088x976; the scaled surface is cached, so
        spawns stay cheap) — art and hitbox then match 1:1 and
        collision needs no adjustments. Opaque (jpeg) frames get
        their near-white studio background keyed out at load
        (image_loader._key_white_background); alpha-carrying .png
        cut-outs pass through untouched. Returns None when any file
        is missing so callers can fall back to block rendering.
        """
        def frame(letter):
            return load_first_image(
                [f"{prefix}_{letter}{ext}" for ext in self.FRAME_EXTENSIONS],
                alpha=True,
                size=size,
                smooth=True,
                key_white=True,
            )

        frames = {
            "rest": frame("g"),
            "rest_alt": frame("h"),
            "run": [frame(letter) for letter in "abcdef"],
        }
        if (frames["rest"] is None
                or frames["rest_alt"] is None
                or any(f is None for f in frames["run"])):
            return None
        return frames

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
