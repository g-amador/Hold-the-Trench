"""
Central faction table: the only place faction/nation art rules live.

The player picks a side in the main menu ("allies" or "axis"); the
opposite side fights as the enemy. Every texture decision in the game
derives from this table so no file hardcodes nation names.

CURRENT PLAYABLE RULE (user): the game is FR vs GER (or GER vs FR,
depending on the chosen side) — the pools below are SINGLE-NATION, so
every per-unit/per-building roll resolves deterministically and the
two sides never mix nations. The pools keep their LIST shape on
purpose: further nations can be added later purely by dropping in
their art and widening these lists (plus their table rows) — no code
change anywhere else.
"""

import random


FACTIONS = {
    "allies": {
        "label": "PLAY AS ALLIES (W)",
        # FR only right now (user: FR vs GER). A nation rejoins this
        # pool when its art returns from assets/images/temp.
        "unit_nations": ["fr"],
        "building_nations": ["fr"],
    },
    "axis": {
        "label": "PLAY AS AXIS  (S)",
        # GER only right now (user: GER vs FR). A nation rejoins this
        # pool when its art returns from assets/images/temp.
        "unit_nations": ["ger"],
        "building_nations": ["ger"],
    },
}

# Coin drops depend on the SIDE the player chose (user: coins depend
# on the side I choose): the drops are the OPPOSING side's currency.
# Playing allies -> every axis soldier drops the german coin; playing
# axis -> every ALLIED soldier drops the french coin. Coin art for
# other nations stays unused for drops (drops key off the dying side,
# never the nation). Only enemy units ever drop gold (the player's
# own side pays nothing), so keying by the dying side is the whole
# rule.
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


def other(faction):
    """Return the battlefield's opposite side of `faction`."""
    return "axis" if faction == "allies" else "allies"


def unit_prefix(faction, nation=None):
    """Random infantry frame prefix + nation for a side.

    Returns (prefix, nation) — the nation is needed again at death
    time for the coin drop, so units remember what they rolled.

    nation=None keeps the historical PER-MAN random roll from the
    faction's unit-nation pool (callers with no parent building).
    A FORCED nation keeps a barracks uniform with its own rolled
    building nation — a building never deploys mixed-nation
    divisions.
    """
    if nation is None:
        nation = random.choice(FACTIONS[faction]["unit_nations"])
    return f"infantry_unit_{nation}_1", nation


def side_coin(faction):
    """The coin art a faction's soldiers drop (see COIN_BY_SIDE)."""
    return COIN_BY_SIDE.get(faction, "coin_ger.png")


def dominant_unit_nation(units, faction):
    """The nation most of `units` belong to (duck-typed .nation attr).

    Decides WHICH theme the DEFEAT screen plays (the anthem of the
    enemy nation that held the map). Counts the ALIVE units' nations
    and returns the most common one; ties resolve by the faction's
    unit_nations pool order, and an empty field (no alive unit
    carries a nation) falls back to that pool's first entry.
    """
    pool = FACTIONS[faction]["unit_nations"]
    counts = {}
    for unit in units:
        if getattr(unit, "dead", False):
            continue
        nation = getattr(unit, "nation", None)
        if nation is not None:
            counts[nation] = counts.get(nation, 0) + 1
    best = None
    best_count = -1
    for nation in pool:  # pool order = deterministic tie-break
        count = counts.get(nation, 0)
        if count > best_count:
            best, best_count = nation, count
    return best if best is not None else pool[0]


# ---------------- Battle scene (building art variants) ----------------
# Every building kind gets scene images that share one base filename
# and differ by a scene suffix:
#   a = day, b = night.
# One scene is rolled ONCE PER BATTLE (roll_scene, called at
# AssaultPhase start) and EVERYTHING scene-linked reads it — the
# ground texture (ground_texture_candidates) and every building
# (building_variant_filenames) — so the whole battlefield always
# shares one scene letter: a day battle shows day buildings on the
# day map, a night battle night buildings on the night map (user:
# "all buildings and map should match — map in day shows buildings
# in day"). The pool is deliberately just these two letters; the
# building chain still falls back to _a/base art for a kind missing
# its variant file.
# TEST MODE is OFF: set SCENE_VARIANT_TEST to "a" or "b" to pin the
# roll while debugging artworks.
SCENE_VARIANT_TEST = None
SCENE_VARIANTS = ("a", "b")

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
    """Ground texture for the current battle scene: map1_<letter>.jpg."""
    return f"map1_{scene_variant()}.jpg"


# Ground-map safety net: if the rolled scene's map file is missing
# from assets/images, the chain falls back to the base map instead of
# degrading the battle to tile rendering.
GROUND_TEXTURE_FALLBACK = "map1_a.jpg"


def ground_texture_candidates():
    """Ground files to try for the current battle's scene, in order.

    First the rolled scene's own file, then the base map — a missing
    scene map silently degrades to the fallback.
    """
    return [ground_texture_filename(), GROUND_TEXTURE_FALLBACK]


# Artillery art keyed by FACTION (not nation), per the user: allied
# guns are the french 75s, axis artillery the heavy howitzer. (No
# scene-variant suffixes exist for these unit images.)
ARTILLERY_IMAGE = {
    "allies": "artillery_fr.png",
    "axis": "artillery_ger.png",
}


def artillery_filename(faction):
    """Artillery art file for a battlefield side."""
    return ARTILLERY_IMAGE.get(faction, "artillery_fr.png")


def artillery_nation_for_side(faction):
    """Nation whose artillery stats a battlefield side fires with.

    Modifiers are keyed by NATION (user handicaps per nation), but
    artillery buildings roll by SIDE: allied guns read as
    the french 75s, axis guns as the german heavy howitzers.
    """
    return "fr" if faction == "allies" else "ger"


# ---------------- WWI balance modifiers (user handicaps) ----------------
# USER SPEC: each nation gets an edge in some units' damage and
# resistance, historically flavored, balanced in 0.9-1.1 so no side
# overwhelms another. Keys are the UNIT kind; values (damage, hp)
# multipliers applied at fire/spawn time. The table carries the two
# playable nations; further countries rejoin by adding a row.
#   fr:   quick-firing 75mm guns + SPAD fighters, reliable FT light tank
#   ger:  stormtroopers + heavy howitzers + early air aces; clumsy A7V
FACTION_MODIFIERS = {
    "fr":   {"infantry": (1.00, 1.00), "plane": (1.10, 1.00),
             "tank": (1.00, 1.05), "artillery": (1.10, 1.00)},
    "ger":  {"infantry": (1.05, 1.05), "plane": (1.05, 1.05),
             "tank": (0.90, 0.90), "artillery": (1.10, 1.05)},
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
# Per COUNTRY art; airfields roll their producing COUNTRY like
# factories do. Unknown nations fall back to the german plane art
# (generic default, never crash).
PLANE_IMAGE = {
    "ger": "airplane_ger.png",
    "fr": "airplane_fr.png",
}


def plane_filename(nation):
    """Plane art file for a producing nation (unknown -> german)."""
    return PLANE_IMAGE.get(nation, PLANE_IMAGE["ger"])


def spawn_plane_nation(faction):
    """Roll the COUNTRY one air field produces for (factory rule)."""
    return random.choice(FACTIONS[faction]["building_nations"])


# ---------------- Armor (tank factory units) ----------------
# Per COUNTRY (user spec), not faction: tanks key off the nation that
# factory rolled. Each image file exists in assets/images (sizes:
# 1518x699 — ArmorUnit scales everything to one box). The pool is
# deliberately just the two playable nations; further countries
# rejoin by adding their art plus a row here (list-driven, no code
# change).
TANK_UNIT_TABLE = {
    "fr": [
        ("tank", "tank_fr_male.png"),
        ("tank", "tank_fr_female.png"),
    ],
    "ger": [
        ("tank", "tank_ger.png"),
    ],
}


def armor_factory_nation(faction):
    """Roll the COUNTRY one tank factory produces for.

    Single-nation pools right now (FR vs GER): allies factories are
    french, axis factories german. Multi-nation pools would mix per
    factory again with no code change.
    """
    return random.choice(FACTIONS[faction]["building_nations"])


def armor_unit_options(nation):
    """(kind, filename) variants one factory of `nation` rolls from.

    Unknown nations yield no units (the factory simply stands
    empty) — never crash.
    """
    return TANK_UNIT_TABLE.get(nation, [])


def nation_from_building_filename(filename):
    """The art nation ("ger"/"fr") from a building file stem.

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
        # suffix is always a single scene letter (a/b) and can be
        # absent.
        if len(parts[-1]) == 1:
            return parts[-2]
        return parts[-1]
    return None


def building_variant_filenames(faction, kind):
    """Ordered image candidates for one building, scene-aware.

    kind is the canonical asset stem ("barracks", "mg_nest", "bunker").
    Trial order: the scene's own suffix file, then the '_a' (day)
    file, then the unsuffixed base art — so a building missing
    its variant image silently keeps day art instead of
    crashing. (The active SCENE_VARIANTS pool covers the day/night
    letters "a"/"b" — a missing variant file falls back to
    the paths above.)
    """
    nation = random.choice(FACTIONS[faction]["building_nations"])
    stem = f"building_{kind}_{nation}"
    variant = scene_variant()

    candidates = [f"{stem}_{variant}.png"]
    if variant != "a":
        candidates.append(f"{stem}_a.png")
    candidates.append(f"{stem}.png")
    return candidates
