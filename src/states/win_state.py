"""
Win state: shown when every enemy bunker is destroyed.

Background keys off the played faction (victory shows the winner's
banner). R replays the same side, S switches faction for the next
battle, Q quits. All three restart through a fresh TileMap so no
buildings or wage bookkeeping leak between fights.
"""

from systems.factions import VICTORY_BACKGROUND
from states.end_screen import EndScreenState


class WinState(EndScreenState):
    """Victory screen. Per-faction art: allies win under the french
    banner, axis under the german one (single source table)."""

    TITLE = "YOU WIN!"
    BACKGROUND_TABLE = VICTORY_BACKGROUND
