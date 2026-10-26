"""
Reusable image loader with a module-level cache.

This is the ONLY place the game reads image files. Results are cached
per (filename, alpha, size) so repeated loads return the same surface
object, which is why loaded surfaces must never be mutated (flip or
scale into a NEW surface instead).
"""

from pathlib import Path

import pygame


# Project assets root, resolved from this file so it works no matter
# where the game is launched from: repo/assets/images.
IMAGE_DIR = Path(__file__).resolve().parents[2] / "assets" / "images"

# Cache storage, filled lazily on first request of each unique key.
_image_cache = {}


def load_image(filename, *, alpha=False, size=None):
    """Load an image from the project's assets/images directory.

    alpha=True converts for per-pixel transparency (units, building
    sprites); alpha=False is faster for opaque art. size rescales
    before caching, so differently-sized loads are cached separately.

    Raises FileNotFoundError for missing files; callers that can go
    without the art should catch it and fall back (see block_drawer).
    """
    key = (filename, alpha, size)

    if key not in _image_cache:
        path = IMAGE_DIR / filename

        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")

        image = pygame.image.load(str(path))
        image = image.convert_alpha() if alpha else image.convert()

        if size is not None:
            image = pygame.transform.scale(image, size)

        _image_cache[key] = image

    return _image_cache[key]


def load_first_image(filenames, *, alpha=False, size=None):
    """Load the first candidate that exists; None when none do.

    Candidates are tried in order, every hit served from the shared
    cache. Callers that can live without art check for None and draw
    a block instead (never crash on missing art).
    """
    for filename in filenames:
        try:
            return load_image(filename, alpha=alpha, size=size)
        except FileNotFoundError:
            continue
    return None
