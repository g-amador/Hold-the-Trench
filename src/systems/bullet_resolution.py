"""
Battle bullet resolution: one unified collision pass for both sides.

The player-bullet pass and the enemy-bullet pass in the battle state
are MIRROR copies of the same filter loop (code-review finding): move
every bullet, drop self-destructed shots, then try collisions in a
fixed priority — live opposing units first, then buildings, then
planes. The side-specific parts are just the four target lists and
ONE damage callback, so the loop lives here once and
AssaultPhase.update() calls it exactly twice per frame.

The caller re-lists whatever this function returns, so surviving
bullets flow through unchanged — resolution never mutates the input
list itself.
"""

from entities.armor import ArmorUnit


def apply_enemy_damage(unit, damage):
    """Enemy-side unit hit: route through the unit's own handler.

    Enemies' take_damage carries their armor/death bookkeeping; the
    pass calls it whenever a bullet lands on a live enemy unit.
    """
    unit.take_damage(damage)


def apply_friendly_damage(unit, damage):
    """Friendly-side unit hit: direct hp subtraction.

    Kept raw on purpose (historical enemy-pass behavior): friendlies
    take the bullet straight to hp and die at <= 0, bypassing their
    take_damage (friendlies have no armor or special death handling
    inside the bullet pass here).
    """
    unit.hp -= damage
    if unit.hp <= 0:
        unit.dead = True


def resolve_bullets(bullets, units, buildings, bunkers, planes,
                    dt, apply_damage):
    """Run one bullets-vs-battlefield collision pass; return survivors.

    bullets  — incoming shots (updated in place, filter-scanned)
    units    — live opposing infantry + armor of the other side
    buildings— destructible buildings of the other side
    bunkers  — the two BUNKER lists shrink one side (see caller)
    planes   — the other side's airborne planes
    apply_damage — how a landed UNIT hit hurts the unit (per side
      callbacks above; building/bunker/plane hits always go through
      the victim's take_damage in all modes)

    Priority matters: units take hits first so an infantry standing
    in front of a bunker still blocks the shot; planes are checked
    LAST because ground hits must not be blocked by air traffic.
    """
    remaining = []

    for bullet in bullets:
        bullet.update(dt)

        # Self-destructed (out of world) shots are simply dropped.
        if getattr(bullet, "dead", False):
            continue

        hit = False

        # Opposing UNITS first. ARMOR RULE (both directions): plain
        # shots can never hurt armored units — they pass through
        # (only artillery splash and tank shells damage armor).
        # On armor contact the bullet keeps flying so it can still
        # hit an infantry unit behind the tank.
        for unit in units:
            if unit.dead:
                continue

            if isinstance(unit, ArmorUnit) and not bullet.armor_damage:
                continue

            if bullet.get_hitbox().colliderect(unit.get_hitbox()):
                apply_damage(unit, bullet.damage)
                hit = True
                break

        # Fallback to objectives when no unit was hit. Buildings
        # are destructible: armor_damage bullets (tank shells)
        # hurt ANY building; plane MG bullets never touch
        # buildings (bombs only); other shots keep the old
        # bunker-only rule (shooting bunkers is a core win route).
        if not hit and bullet.armor_damage:
            for building in buildings:
                if bullet.get_hitbox().colliderect(
                    building.get_hitbox()
                ):
                    building.take_damage(bullet.damage)
                    hit = True
                    break
        elif not hit and getattr(bullet, "can_damage_buildings", True):
            for bunker in bunkers:
                if bunker.dead:
                    continue

                if bullet.get_hitbox().colliderect(
                    bunker.get_hitbox()
                ):
                    bunker.take_damage(bullet.damage)
                    hit = True
                    break

        # PLANES: player-side bullets (and plane MG fire) reach the
        # opposing planes in the air (bullets with no armor damage
        # chip planes like infantry; plane bullets are armorless
        # by design, dogfights stay infantry-like).
        if not hit:
            for plane in planes:
                if plane.dead:
                    continue

                if bullet.get_hitbox().colliderect(
                    plane.get_hitbox()
                ):
                    plane.take_damage(bullet.damage)
                    hit = True
                    break

        # Unhit bullets survive to the next frame.
        if not hit:
            remaining.append(bullet)

    return remaining
