"""
Audio system: menu music, faction-select sting, national end themes.

The first audio wiring in the project (nothing else touches the
mixer). Three behaviors, all user requests:

- The START menu loops `Menu_Loop.wav` for as long as it shows; the
  loop is cut when a battle starts (see stop_menu_audio callers).
- Every faction-selection key press plays the `menu_select.wav` sting
  once; a press mid-sting restarts it (never polyphonic stacking).
- End screens play ONE national theme: victory plays the PLAYER's
  rolled nation anthem, defeat plays the anthem of the enemy nation
  that held the field (nation picked by the battle state — see
  assault_phase's transitions and factions.dominant_unit_nation).

Everything is a safe no-op when the mixer is unavailable (no audio
device, exotic sandboxes): the game never crashes on sound. Music and
themes go through pygame.mixer.music (one stream, mp3 capable); the
select sting uses a dedicated Sound channel so a rapid re-press cuts
the previous sting instead of stacking on a new one.
"""

import os

import pygame

from config import (
    MENU_MUSIC,
    MENU_SELECT_SOUND,
    NATION_VICTORY_THEMES,
)

# Asset roots (config stores bare filenames).
_MUSIC_DIR = os.path.join("assets", "music")
_SOUNDS_DIR = os.path.join("assets", "sounds")

# One-time mixer readiness probe (None init = no usable audio device).
_mixer_checked = False
_mixer_ok = False

# Select-sting state (module-level because the sting is a global
# singleton — one dedicated channel owns it for the whole session).
_select_channel = None
_select_sound = None  # the menu_select.wav Sound, lazy-loaded


def _ensure_mixer():
    """Probe the mixer once; return True when audio can actually play."""
    global _mixer_checked, _mixer_ok
    if not _mixer_checked:
        _mixer_checked = True
        try:
            _mixer_ok = pygame.mixer.get_init() is not None
        except pygame.error:
            _mixer_ok = False
    return _mixer_ok


def _music_path(filename):
    return os.path.join(_MUSIC_DIR, filename)


def _sound_path(filename):
    return os.path.join(_SOUNDS_DIR, filename)


def play_menu_music():
    """Loop Menu_Loop.wav while the start menu shows (user request).

    Restarting the load on every menu entry is intentional: whatever
    music ran before (a victory theme from a previous battle) must be
    replaced by the loop.
    """
    if not _ensure_mixer():
        return
    try:
        pygame.mixer.music.load(_music_path(MENU_MUSIC))
        # loops=-1: loop until stop_menu_audio cuts it at battle start.
        pygame.mixer.music.play(-1)
    except (pygame.error, FileNotFoundError):
        pass


def stop_menu_audio():
    """Cut menu music AND any running select sting (battle start).

    Called at every battle-entry point (menu ENTER, end-screen
    restarts): without it the looping menu music would keep playing
    under the battle.
    """
    if not _ensure_mixer():
        return
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass
    if _select_channel is not None:
        _select_channel.stop()


def play_nation_theme(nation):
    """Play the nation's victory theme ONCE (end screens, user rule).

    nation is a unit nation ("ger"/"fr" right now — the playable
    nations) chosen by the
    battle state: victory = the player's own rolled nation, defeat =
    the enemy nation that held the map. Unknown/None nations stay
    silent rather than falling back to a wrong anthem.
    """
    if not _ensure_mixer():
        return
    filename = NATION_VICTORY_THEMES.get(nation)
    if filename is None:
        return
    try:
        # Replaces the menu loop (or the previous theme) in the single
        # music stream; loops=0 plays exactly once.
        pygame.mixer.music.load(_music_path(filename))
        pygame.mixer.music.play(0)
    except (pygame.error, FileNotFoundError):
        pass


def play_menu_select_sound():
    """Play the faction-selection sting once (user: menu_select.wav).

    Fired on EVERY faction-selection key press (menu side keys, the
    end screen's faction switch). One sound per press: the dedicated
    channel is stopped first, so pressing mid-sting restarts the sting
    instead of overlapping copies of it.
    """
    global _select_channel, _select_sound
    if not _ensure_mixer():
        return
    try:
        if _select_sound is None:
            _select_sound = pygame.mixer.Sound(_sound_path(MENU_SELECT_SOUND))
        if _select_channel is None:
            # Channel 0: never used by anything else in the project.
            _select_channel = pygame.mixer.Channel(0)
        _select_channel.stop()  # re-press: restart, never stack
        _select_channel.play(_select_sound)
    except (pygame.error, FileNotFoundError):
        pass
