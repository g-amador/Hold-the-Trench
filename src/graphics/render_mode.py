"""
Global graphics toggle state: sprite mode vs block mode.

Press G in the battle state to toggle. Any other module that needs to
know the current mode must call is_sprite()/label() — no other module
may store render-mode state (see AI.md single-source rules).
"""

MODES = ("SPRITES", "BLOCKS")

# Process-wide toggle; battle state flips it, renderers only read it.
_mode = "SPRITES"


def toggle():
    """Switch between sprite mode and block mode."""
    global _mode
    _mode = "BLOCKS" if _mode == "SPRITES" else "SPRITES"


def is_sprite():
    """True when sprite/animated rendering should be used."""
    return _mode == "SPRITES"


def label():
    """Current mode name for HUD display."""
    return _mode
