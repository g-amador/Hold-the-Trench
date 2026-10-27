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
        "label": "PLAY AS ALLIES (W)",
        "unit_nations": ["brit", "fr"],
        "building_nations": ["brit", "fr"],
    },
    "axis": {
        "label": "PLAY AS AXIS  (S)",
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
MENU_BACKGROUND = "Menu_Start.jpeg"
VICTORY_BACKGROUND = {
    "allies": "Menu_Victory_fr.jpeg",
    "axis": "Menu_Victory_ger.jpeg",
}
DEFEAT_BACKGROUND = {
    "allies": "Menu_Victory_ger.jpeg",
    "axis": "Menu_Victory_fr.jpeg",
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


# ---------------- Battle scene (building art variants) ----------------
# Every building kind gets (or will get) four scene images that share
# one base filename and differ by a suffix letter:
#   a = summer day, b = summer night, c = winter day, d = winter night.
# One scene is rolled ONCE PER BATTLE (roll_scene, called at
# AssaultPhase start) and EVERYTHING scene-linked reads it — the
# ground texture (map1a/map1c) via ground_texture_filename() and every
# building via building_variant_filenames — so the whole battlefield
# always shares one scene letter ("If _a then all 3 must be _a").
# ACTIVE POOL = a (summer day) + c (winter day): the variants with
# complete map + mg_nest + bunker art. b (summer night) / d (winter
# night) rejoin the tuple when their art lands.
# TEST MODE is OFF: set SCENE_VARIANT_TEST to "a" (or "c") to pin the
# roll while debugging artworks.
SCENE_VARIANT_TEST = None
SCENE_VARIANTS = ("a", "c")

# Process-wide scene state: rolled per battle, read everywhere.
_scene_variant = "a"


def roll_scene():
    """Roll this battle's scene variant; call once per battle start."""
    global _scene_variant
    if SCENE_VARIANT_TEST is not None:
        _scene_variant = SCENE_VARIANT_TEST
    else:
        _scene_variant = random.choice(SCENE_VARIANTS)
    return _scene_variant


def scene_variant():
    """The current battle's scene suffix for building art."""
    return _scene_variant


def ground_texture_filename():
    """Ground texture for the current scene: map1a -> map1c."""
    return f"map1{scene_variant()}.jpg"


# Artillery art keyed by FACTION (not nation), per the user: both
# allied nations share the french cannon; axis artillery is the heavy
# howitzer. (No scene-variant suffixes exist for these unit images.)
ARTILLERY_IMAGE = {
    "allies": "unit_cannon_fr.png",
    "axis": "unit_heavy_howitzer_ger.png",
}


def artillery_filename(faction):
    """Artillery art file for a battlefield side."""
    return ARTILLERY_IMAGE.get(faction, "unit_cannon_fr.png")


# ---------------- Armor (tank factory units) ----------------
# Per COUNTRY (user spec), not faction: tanks and cars key off the
# nation that factory rolled. British factories may also produce
# cars (mobile MG nests); the French and Germans only field tanks.
# Each image file exists in assets/images (sizes: 176x80, the
# german tank 256x116 — ArmorUnit scales everything to one box).
TANK_UNIT_TABLE = {
    "fr": [
        ("tank", "tank_unit_fr_tank1.png"),
        ("tank", "tank_unit_fr_tank2.png"),
        ("tank", "tank_unit_fr_tank3.png"),
    ],
    "ger": [
        ("tank", "tank_unit_ger_tank.png"),
    ],
    "brit": [
        ("tank", "tank_unit_brit_tank1.png"),
        ("tank", "tank_unit_brit_tank2.png"),
        ("car", "car_unit_brit_car1.png"),
        ("car", "car_unit_brit_car2.png"),
    ],
}


def armor_factory_nation(faction):
    """Roll the COUNTRY one tank factory produces for.

    Matches the building-art rule: allies factories mix brit/fr
    randomly, axis factories are always german (no austrian armor
    is in the table).
    """
    return random.choice(FACTIONS[faction]["building_nations"])


def armor_unit_options(nation):
    """(kind, filename) variants one factory of `nation` rolls from.

    Unknown nations yield no units (the factory simply stands
    empty) — never crash.
    """
    return TANK_UNIT_TABLE.get(nation, [])


def building_variant_filenames(faction, kind):
    """Ordered image candidates for one building, scene-aware.

    kind is the canonical asset stem ("barraks", "mg_nest", "bunker").
    Trial order: the scene's own suffix file, then the '_a' (summer
    day) file, then the unsuffixed base art — so a building missing
    its variant image silently keeps summer-day art instead of
    crashing. (The pool only rolls art-complete letters: "a"/"c".)
    """
    nation = random.choice(FACTIONS[faction]["building_nations"])
    stem = f"building_{kind}_{nation}"
    variant = scene_variant()

    candidates = [f"{stem}_{variant}.png"]
    if variant != "a":
        candidates.append(f"{stem}_a.png")
    candidates.append(f"{stem}.png")
    return candidates
