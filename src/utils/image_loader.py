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
        if filename is None:
            raise FileNotFoundError("No image filename given")

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


def load_first_image_named(filenames, *, alpha=False, size=None):
    """load_first_image, but ALSO returns the winning filename.

    Returns (surface_or_None, filename_or_None). Buildings store the
    chosen name so they can later load the SAME file at NATIVE
    resolution for the CLOSE-view hires pass. load_first_image cannot
    do this (its return is just a surface), so effects and hires both
    key off this helper.
    """
    for filename in filenames:
        try:
            return load_image(filename, alpha=alpha, size=size), filename
        except FileNotFoundError:
            continue
    return None, None


_OPQ_BBOX_CACHE = {}


def opaque_bbox(filename, *, alpha_min=20, step=2, pad=8):
    """(minx, miny, maxx, maxy) opaque-content box of an art file.

    USER RULE (proportional bunker art): some building art canvases
    carry large transparent margins, so scaling the FULL canvas into
    a footprint box distorts the building. This finds the opaque
    content box (alpha >= alpha_min, sampled every `step` px for
    speed, widened by `pad`, clamped to the canvas). Cached per
    filename — the per-pixel python scan costs a few seconds once per
    file per process. Empty canvases fall back to the full canvas.
    """
    if filename not in _OPQ_BBOX_CACHE:
        img = load_image(filename, alpha=True)
        w, h = img.get_size()
        minx, miny, maxx, maxy = w, h, -1, -1
        for y in range(0, h, step):
            for x in range(0, w, step):
                if img.get_at((x, y)).a >= alpha_min:
                    if x < minx: minx = x
                    if x > maxx: maxx = x
                    if y < miny: miny = y
                    if y > maxy: maxy = y
        if maxy < 0:
            box = (0, 0, w, h)
        else:
            box = (
                max(0, minx - pad),
                max(0, miny - pad),
                min(w, maxx + step + pad),
                min(h, maxy + step + pad),
            )
        _OPQ_BBOX_CACHE[filename] = box

    return _OPQ_BBOX_CACHE[filename]


def aspect_fit_contain(src_w, src_h, box_w, box_h):
    """Largest (w, h) <= box with the source's exact aspect ratio.

    Never distorts: the single scale factor is min of both axes.
    """
    scale = min(box_w / max(src_w, 1), box_h / max(src_h, 1))
    return max(1, round(src_w * scale)), max(1, round(src_h * scale))


_SEMI_ALPHA_FIXED = {}


# numpy availability for the fast alpha sweep (pygame.surfarray is a
# numpy-backed module; pygame raises lazily when numpy is missing).
# The Python fallback sweep runs whenever numpy is unavailable.
try:
    import numpy as _numpy
    from pygame import surfarray as _surfarray
except ImportError:
    _numpy = None
    _surfarray = None


def _sweep_alpha(surface, cutoff):
    """Per-pixel Python sweep: semi-alpha pixels go hard 0 or 255.

    Only ever used for the handful of static art files when numpy is
    unavailable.
    """
    for y in range(surface.get_height()):
        for x in range(surface.get_width()):
            color = surface.get_at((x, y))
            a = color.a
            hard_a = 0 if a <= cutoff else 255
            if hard_a != a:
                surface.set_at(
                    (x, y),
                    (color.r, color.g, color.b, hard_a),
                )


def load_image_semi_alpha_fixed(filename, *, cutoff=128):
    """Native-res load with semi-transparent pixels hardened.

    USER FIX ("tank factory transparent background is shown"): some
    static art packs an ENTIRE backdrop at partial alpha (the german
    tank factory paints ~30% of its pixels at ~alpha 128, no a=0 at
    all), so the picture shows as a milky translucent overlay over
    the battlefield. Hardening: alpha <= cutoff snaps to 0 (clean
    cut-out like the other buildings), the rest snaps to 255 (solid
    paint). One-time per filename (cached); the world-size art can
    then be scaled from this opaque base so both resolutions agree.
    """
    if filename not in _SEMI_ALPHA_FIXED:
        base = load_image(filename, alpha=True)

        flattened = base.copy()
        width, height = base.get_size()

        if _surfarray is not None and _numpy is not None:
            try:
                alpha = _surfarray.pixels_alpha(flattened)
                alpha[alpha <= cutoff] = 0
                alpha[alpha > cutoff] = 255
                del alpha
            except (NotImplementedError, ModuleNotFoundError):
                _sweep_alpha(flattened, cutoff)
        else:
            _sweep_alpha(flattened, cutoff)

        _SEMI_ALPHA_FIXED[filename] = flattened

    return _SEMI_ALPHA_FIXED[filename]
