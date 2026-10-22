"""
Central faction table: the only place faction/nation art rules live.

The player picks a side in the main menu ("allies" or "axis"); the
opposite side fights as the enemy. Every texture decision in the game
derives from this table so no file hardcodes nation names:

- Soldier textures are random per unit from the side's nation pool.
- Building textures: the Axis pool holds only Germany's (there are no
  austrian *_building* assets), so axis buildings are always ger; the
  allies pool mixes brit/fr randomly per building.
- Coin drops key off the DYING unit's nation: germans and austrians
  share coin_ger.png (no dedicated austrian coin asset exists).
"""

import random


FACTIONS = {
    "allies": {
        "label": "PLAY AS ALLIES (A / 1)",
        "unit_nations": ["brit", "fr"],
        "building_nations": ["brit", "fr"],
    },
    "axis": {
        "label": "PLAY AS AXIS  (X / 2)",
        "unit_nations": ["ger", "aust"],
        "building_nations": ["ger"],
    },
}

# Coin art keyed by the DYING unit's nation; germans and austrians
# both drop the german coin (single aust/ger coin asset exists).
COIN_BY_NATION = {
    "brit": "coin_brit.png",
    "fr": "coin_fr.png",
    "ger": "coin_ger.png",
    "aust": "coin_ger.png",
}

# Faction-keyed static screens. Allies victory/defeat show allied /
# central-powers banners respectively; axis mirrors it.
MENU_BACKGROUND = "Menu_2_Start.jpeg"
VICTORY_BACKGROUND = {
    "allies": "Menu_2_Victory_fr.jpeg",
    "axis": "Menu_2_Victory_ger.jpeg",
}
DEFEAT_BACKGROUND = {
    "allies": "Menu_2_Victory_ger.jpeg",
    "axis": "Menu_2_Victory_fr.jpeg",
}


def is_valid(faction):
    """True for every selectable faction string."""
    return faction in FACTIONS


def other(faction):
    """Return the battlefield's opposite side of `faction`."""
    return "axis" if faction == "allies" else "allies"


def unit_prefix(faction):
    """Random infantry frame prefix + nation for a side.

    Returns (prefix, nation) — the nation is needed again at death
    time for the coin drop, so units remember what they rolled.
    """
    nation = random.choice(FACTIONS[faction]["unit_nations"])
    return f"infantry_unit_{nation}_1", nation


def building_filename(faction, kind):
    """Random building art filename from the side's pool.

    kind is the canonical asset stem ("barraks" — misspelling is part
    of the asset filename — "mg_nest", "bunker").
    """
    nation = random.choice(FACTIONS[faction]["building_nations"])
    return f"building_{kind}_{nation}.png"


def coin_texture(nation):
    """Coin art for a fallen soldier's nation (defaults to german)."""
    return COIN_BY_NATION.get(nation, "coin_ger.png")
