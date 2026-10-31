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

# Coin art by the DYING unit's nation — SUPERSEDED for drops (see
# COIN_BY_SIDE below; kept as art bookkeeping / potential future use).
# Germans and austrians both drop the german coin (single aust/ger
# coin asset exists).
COIN_BY_NATION = {
    "brit": "coin_brit.png",
    "fr": "coin_fr.png",
    "ger": "coin_ger.png",
    "aust": "coin_ger.png",
}

# Coin drops depend on the SIDE the player chose (user: coins depend
# on the side I choose): the drops are the OPPOSING side's currency.
# Playing allies -> every axis soldier (ger/aust) drops the german
# coin; playing axis -> every ALLIED soldier drops the french coin —
# fr units AND brit units alike (the british coin asset stays unused
# for drops). Only enemy units ever drop gold (the player's own side
# pays nothing), so keying by the dying side is the whole rule.
COIN_BY_SIDE = {
    "axis": "coin_ger.png",
    "allies": "coin_fr.png",
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
    """Coin art for a fallen soldier's nation (defaults to german).

    Art bookkeeping only — gold DROPS go through side_coin() since the
    coins follow the side the player chose, not the unit's nation.
    """
    return COIN_BY_NATION.get(nation, "coin_ger.png")


def side_coin(faction):
    """The coin art a faction's soldiers drop (see COIN_BY_SIDE)."""
    return COIN_BY_SIDE.get(faction, "coin_ger.png")


# ---------------- Battle scene (building art variants) ----------------
# Every building kind gets (or will get) four scene images that share
# one base filename and differ by a suffix letter:
#   a = summer day, b = summer night, c = winter day, d = winter night.
# One scene is rolled ONCE PER BATTLE (roll_scene, called at
# AssaultPhase start) and EVERYTHING scene-linked reads it — the
# ground texture (map1_a/map1_c) via ground_texture_filename() and every
# building via building_variant_filenames — so the whole battlefield
# always shares one scene letter ("If _a then all 3 must be _a").
# ACTIVE POOL = ALL FOUR variants (user: "can use all 4 variations" —
# the scene art landed for every letter): a summer day, b summer
# night, c winter day, d winter night. The building chain still falls
# back to _a/base art for a kind missing its variant file.
# TEST MODE is OFF: set SCENE_VARIANT_TEST to "a".."d" to pin the
# roll while debugging artworks.
SCENE_VARIANT_TEST = None
SCENE_VARIANTS = ("a", "b", "c", "d")

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
    """Ground texture for the current battle scene: map1_a/b/c/d."""
    return f"map1_{scene_variant()}.png"


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


def artillery_nation_for_side(faction):
    """Nation whose artillery stats a battlefield side fires with.

    Modifiers are keyed by NATION (user handicaps per Ger/Brit/Fr/
    Aust), but artillery buildings roll by SIDE: allied guns read as
    the french 75s, axis guns as the german heavy howitzers.
    """
    return "fr" if faction == "allies" else "ger"


# ---------------- WWI balance modifiers (user handicaps) ----------------
# USER SPEC: each nation gets an edge in some units' damage and
# resistance, historically flavored, balanced in 0.9-1.1 so no side
# overwhelms another. Keys are the UNIT kind; values (damage, hp)
# multipliers applied at fire/spawn time.
#   fr:   quick-firing 75mm guns + SPAD fighters, reliable FT light tank
#   brit: first tanks + creeping barrage doctrine, solid all-round
#   ger:  stormtroopers + heavy howitzers + early air aces; clumsy A7V
#   aust: polyglot conscript army, weak planes/company armor; Skoda guns
FACTION_MODIFIERS = {
    "fr":   {"infantry": (1.00, 1.00), "plane": (1.10, 1.00),
             "tank": (1.00, 1.05), "artillery": (1.10, 1.00)},
    "brit": {"infantry": (1.00, 1.00), "plane": (1.05, 1.00),
             "tank": (1.10, 1.10), "artillery": (1.05, 1.00)},
    "ger":  {"infantry": (1.05, 1.05), "plane": (1.05, 1.05),
             "tank": (0.90, 0.90), "artillery": (1.10, 1.05)},
    "aust": {"infantry": (0.90, 0.90), "plane": (0.95, 0.90),
             "tank": (0.90, 0.90), "artillery": (1.00, 0.95)},
}


def unit_modifiers(nation, kind):
    """(damage, resistance) multipliers for a nation's unit kind.

    Unknown nations/kinds read (1.0, 1.0) — never crash.
    """
    return FACTION_MODIFIERS.get(nation, {}).get(kind, (1.0, 1.0))


def scaled_damage(nation, kind, damage):
    """Outgoing damage of `damage` scaled by the nation's handicap."""
    return round(damage * unit_modifiers(nation, kind)[0])


def scaled_hp(nation, kind, hp):
    """Spawn hp of `hp` scaled by the nation's resistance handicap."""
    return round(hp * unit_modifiers(nation, kind)[1])


# ---------------- Planes (air field production) ----------------
# Per COUNTRY art; the french SPAD drops nothing to france alone —
# airfields roll their producing COUNTRY like factories do. Austria
# flew german-built Albatros types: no dedicated austrian plane asset
# exists, so austrian fields hand out german planes.
PLANE_IMAGE = {
    "ger": "airplane_unit_ger_plane.png",
    "brit": "airplane_unit_brit_plane.png",
    "fr": "airplane_unit_fr_plane.png",
}


def plane_filename(nation):
    """Plane art file for a producing nation (aust falls back to ger)."""
    return PLANE_IMAGE.get(nation, PLANE_IMAGE["ger"])


def spawn_plane_nation(faction):
    """Roll the COUNTRY one air field produces for (factory rule)."""
    return random.choice(FACTIONS[faction]["building_nations"])


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


def nation_from_building_filename(filename):
    """The art nation ("ger"/"fr"/"brit") from a building file stem.

    File convention: building_<kind>_<nation>[_<variant>][.png] —
    the third underscore token is the nation. Unknown shapes return
    None (the caller falls back to its default footprint/table).
    """
    stem = str(filename).rsplit(".", 1)[0]
    parts = stem.split("_")
    if len(parts) >= 3 and parts[0] == "building":
        # File convention: building_<kind>_<nation>[_variant].png —
        # kind may itself contain underscores (tank_factory), so the
        # nation is the token BEFORE the scene-variant suffix; the
        # suffix is always a single letter a/b/c/d and can be absent.
        if len(parts[-1]) == 1:
            return parts[-2]
        return parts[-1]
    return None


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
