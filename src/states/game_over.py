"""
Game Over state: shown when the player's bunker is destroyed.

Background keys off the played faction (defeat shows the enemy's
banner — you annexed by the central powers as allies and vice versa).
R replays the same side, S switches faction for the next battle, Q
quits. All three restart through a fresh TileMap so no buildings or
wage bookkeeping leak between fights.
"""

from systems.factions import DEFEAT_BACKGROUND
from states.end_screen import EndScreenState


class GameOverState(EndScreenState):
    """Defeat screen. Per-faction art: allies lose under the german
    banner, axis under the french one (single source table). Plays the
    enemy nation's anthem (theme_nation picked by
    factions.dominant_unit_nation at the transition)."""

    TITLE = "GAME OVER"
    BACKGROUND_TABLE = DEFEAT_BACKGROUND
