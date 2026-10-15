"""
Reusable image loader.
"""

from pathlib import Path

import pygame


IMAGE_DIR = Path(__file__).resolve().parents[2] / "assets" / "images"


def load_image(filename, *, alpha=False, size=None):
    """Load an image from the project's assets/images directory."""
    path = IMAGE_DIR / filename

    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    image = pygame.image.load(str(path))
    image = image.convert_alpha() if alpha else image.convert()    

    if size is not None:
        image = pygame.transform.scale(image, size)

    return image

