"""
Factory-produced tanks.

The ArmorUnit machinery (Beta user spec):
- spawn WEST of the factory, heading toward the enemy trenches
  (roll_armor_unit offsets the unit off the factory's west edge);
- movement SCALES TO MAP SIZE (config.TANK_SPEED_REF_TILES) and the
  advance targets the nearest enemy infantry/MG/building: the tank
  stops ONLY to shell a building/MG with its cannon when one is
  inside gun range (and inside the gun's facing cone), never for
  infantry — those are machine-gunned on the move, "stop only when
  none remain";
- cannon and machine guns fire SIMULTANEOUSLY (separate cooldowns)
  when suitable targets are in range; several guns may engage
  several targets in one volley (mg_gun_count);
- weapon layout per SPRITE VARIANT (user spec):
    tank_ger        5.7 cm Maxim-Nordenfelt cannon (FRONT hull
                    muzzle, forward shots only) + six 7.9 mm MGs
                    (two each behind/below/above, fired from their
                    rear/roof/belly mounts);
    tank_fr_male    37 mm gun in the ROTATING turret (fires from
                    the hull center in ANY direction);
    tank_fr_female  Hotchkiss/Reibel MGs only; the turret ROTATES,
                    so french tanks shoot in ANY direction while the
                    fixed german hull is restricted (MGs never fire
                    into the front arc — only behind or steeply
                    above/below);
- the armor damage rule: armor is ONLY damaged by other tanks' shots
  and artillery splash (the battle state's bullet loops enforce it);
- tanks NEVER collide with buildings: the stop rule halts the tank
  inside gun range, long before any footprint contact;
- a tank passing over OPPOSING infantry squishes it (dead outright);
  same-side infantry is never touched (the state passes only the
  opposing list);
- armor never drops gold (gold_spawned stays True).

Stats come from config (user rule: speed/hp centralized here), and
the WWI balance handicaps (systems/factions.py) scale both spawn hp
and outgoing damage per the producing nation.

Art is per COUNTRY via factions.TANK_UNIT_TABLE; a factory rolls a
variant file for each unit and this module scales any of them to
the class's world size (source files differ per nation). Missing
files fall back to the block colors (never crash).
"""

import math
import random

import pygame

from config import (
    TILE_SIZE,
    RED,
    BLUE,
    TANK_HP,
    TANK_SPEED,
    TANK_SPEED_REF_TILES,
    TANK_MG_RANGE,
    TANK_MG_DAMAGE,
    TANK_MG_FIRE_RATE,
)
from entities.bullet import Bullet
from entities.damage import RawSubtractDamage
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from utils.image_loader import load_first_image
from systems.factions import scaled_damage, scaled_hp
from world.trench_generator import STATIC_MAP


def _world_width():
    """World pixel width from the ASCII map (edge stop for armor)."""
    return len(STATIC_MAP[0]) * TILE_SIZE


class ArmorUnit(RawSubtractDamage):
    """Shared vehicle behavior: advance, hull MG, hp, death."""

    # Vehicle identity for the MG targeting rules and the battle
    # state's force counts; infantry classes read as "infantry"
    # through the same getattr fallback.
    unit_kind = "vehicle"

    # Which target kinds this vehicle's MG can hurt: tanks shoot
    # infantry AND other tanks. BUILDINGS are handled separately via
    # the buildings list passed to update().
    MG_TARGETS = ()

    # Weapon layout per VARIANT (user spec, assigned by sprite
    # variant — see the subclasses below):
    # cannon         stops for buildings/MGs and shells them; a
    #                cannon-less tank never parks for buildings;
    # mg_gun_count   guns fired per MG volley (several guns may
    #                engage several infantry targets);
    # turret_rotates False = fixed hull (german): the cannon only
    #                fires FORWARD and the MGs never fire into the
    #                front arc; True (french rotating turret) = any
    #                direction.
    cannon = True
    mg_gun_count = 1
    turret_rotates = True

    def __init__(self, x, y, is_enemy, filename, nation,
                 hp, speed, width, height,
                 mg_range, mg_damage, mg_fire_rate):
        # Top-left world position; vehicles use free float positions
        # like all other units (no tile collision).
        self.x = x
        self.y = y

        self.is_enemy = is_enemy
        # Producing nation, set by the factory BEFORE ctor: the WWI
        # balance handicaps scale spawn hp (resistance) and outgoing
        # gun damage at fire time.
        self.nation = nation

        self.hp = scaled_hp(nation, self.unit_kind, hp)
        # Movement SCALES TO MAP SIZE (user rule): the config speed
        # is referenced to TANK_SPEED_REF_TILES tiles — wider maps
        # speed tanks up proportionally, narrower slow them.
        world_w = _world_width()
        reference_w = TANK_SPEED_REF_TILES * TILE_SIZE
        self.speed = speed * world_w / reference_w
        self.width = width
        self.height = height
        self.dead = False

        # Armor never feeds the gold economy: the flag stays True so
        # the state's gold loop (dead and not gold_spawned) skips
        # armored bodies without any spawn_gold method needed.
        self.gold_spawned = True

        # On-board guns: the machine-gun volley (MG-nest-style
        # auto-fire) and the main cannon each keep their OWN clock —
        # both fire in the same frame when their targets are in
        # range (user: simultaneous cannon + MG fire).
        self.range = mg_range
        self.damage = mg_damage
        self.fire_rate = mg_fire_rate
        self.mg_cooldown = 0
        self.gun_cooldown = 0

        # Advance direction: friendly armor drives EAST toward the
        # enemy base; enemy armor would drive WEST. Mirrors the
        # buildings' facing convention.
        self.dir_x = -1 if is_enemy else 1

        # Per-country art, scaled to this class's world size. A
        # missing file (like the factory art chain) falls back to
        # the block color instead of crashing.
        self.image = load_first_image([filename], alpha=True,
                                      size=(width, height))
        if is_enemy and self.image is not None:
            # Mirror enemy art so it faces the battlefield the same
            # way its units do (never mutates the shared cache).
            self.image = pygame.transform.flip(self.image, True, False)

    # ---- housekeeping shared with the other units ----

    def get_hitbox(self):
        """Collision rectangle in world coordinates."""
        return pygame.Rect(
            round(self.x), round(self.y), self.width, self.height,
        )

    # ---- facing cones (nation weapon handicaps) ----

    def _cannon_can_hit(self, dx, dy):
        """Main-gun facing rule for the body at offset (dx, dy)."""
        if self.turret_rotates:
            return True
        # Fixed hull (tank_ger): the cannon only fires FORWARD.
        return dx * self.dir_x > 0

    def _mg_can_hit(self, dx, dy):
        """Machine-gun facing rule for the body at offset (dx, dy)."""
        if self.turret_rotates:
            return True
        # German hull MGs sit behind/roof/belly (user: two each
        # targeting behind, below, and above): they engage bodies
        # BEHIND or STEEPLY above/below — never the shallow front
        # arc (the cannon owns the front).
        if dx * self.dir_x < 0:
            return True
        return abs(dy) > abs(dx)

    # ---- behavior ----

    def update(self, dt, targets, bullets, buildings=None):
        """Advance toward the enemy, shell buildings, volley the MGs.

        `targets` is the OPPOSING unit list (infantry + armor).
        `bullets` is the side-appropriate list the battle state
        simulates. `buildings` is the OPPOSING BUILDING list: a
        cannon tank stops and SHELLS the nearest alive building in
        gun range (and inside the facing cone) — the ONLY thing the
        tank stops for ("stop only when none remain"); infantry are
        machine-gunned on the move or while parked (simultaneous
        fire), and bodies run over are squished.
        """
        if self.dead:
            return

        world_w = _world_width()
        world_h = len(STATIC_MAP) * TILE_SIZE

        # Building stop rule (cannon tanks only — a cannon-less
        # variant never parks): nearest ALIVE enemy building whose
        # center is inside gun range AND the gun's facing cone halts
        # the advance this frame; the tank parks here and shells it
        # on the cannon's cadence. armor_damage shots work on ALL
        # enemy buildings (MG nests, artillery, barracks, factories,
        # air fields, bunkers — destructible since BUILDING_HP). The
        # stop range sits far outside any footprint, so the tank
        # NEVER collides with the building it shells (user rule).
        building = None
        if self.cannon:
            building = self._nearest_building(buildings)
        parked = building is not None
        if parked:
            self._fire_building_shot(dt, building, bullets)

        if not parked:
            # Movement TARGET (user: "target the nearest enemy
            # infantry, MG, or building; turn toward a closer valid
            # target; stop only when none remain"): steer at the
            # nearest opposing infantry or building; enemy tanks are
            # NOT pursued (the MGs duel armor while advancing). No
            # target left = straight advance to the enemy edge.
            cx = self.x + self.width / 2
            cy = self.y + self.height / 2
            move_to = self._nearest_move_target(targets, buildings)

            if move_to is not None:
                dx = move_to[0] - cx
                dy = move_to[1] - cy
                length = math.hypot(dx, dy) or 1.0
                self.x += dx / length * self.speed * dt / 1000
                self.y += dy / length * self.speed * dt / 1000

                # FACING follows the pursuit, like the player's.
                if abs(dx) > 1e-6:
                    self.dir_x = 1 if dx > 0 else -1
            else:
                self.x += self.dir_x * self.speed * dt / 1000

            # In-world clamp on BOTH axes.
            self.x = max(0, min(self.x, world_w - self.width))
            self.y = max(0, min(self.y, world_h - self.height))

            # SQUISH (user rule): enemy infantry under the hull die
            # outright ("killed as if squished"). The list is the
            # OPPOSING side only, so same-side infantry is never
            # squished — no extra faction check needed.
            self._squish_infantry(targets)

        # MG volley: fires while parked AND advancing (simultaneous
        # cannon + MG fire, user rule).
        self._fire_mg_volley(dt, targets, bullets)

    def _nearest_move_target(self, targets, buildings):
        """Nearest enemy body the tank should DRIVE toward.

        Candidates (user spec): enemy INFANTRY and enemy BUILDINGS
        (MG nests included — they are buildings). Enemy TANKS are not
        pursued: armor duels happen through the MGs while advancing.
        Returns the target's center as (x, y), or None.
        """
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        best = None
        best_dist = None
        for t in targets:
            if getattr(t, "dead", False):
                continue
            if getattr(t, "unit_kind", "infantry") != "infantry":
                continue
            tx = t.x + t.width / 2
            ty = t.y + t.height / 2
            dist = math.hypot(tx - cx, ty - cy)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = (tx, ty)

        if buildings:
            for build in buildings:
                if build.is_destroyed():
                    continue
                hb = build.get_hitbox()
                dist = math.hypot(hb.centerx - cx, hb.centery - cy)
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best = (hb.centerx, hb.centery)

        return best

    def _squish_infantry(self, targets):
        """Run over opposing infantry: squished, dead outright."""
        hull = self.get_hitbox()
        for t in targets:
            if getattr(t, "dead", False):
                continue
            if getattr(t, "unit_kind", "infantry") != "infantry":
                continue
            if hull.colliderect(t.get_hitbox()):
                t.hp = 0
                t.dead = True

    def _nearest_building(self, buildings):
        """Nearest ALIVE enemy building in gun range AND facing cone.

        buildings=None means the state passed no list (back-compat):
        no building rule applies. Distance is center-to-center.
        """
        if not buildings:
            return None

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        nearest = None
        best_dist = None
        for build in buildings:
            if build.is_destroyed():
                continue
            hb = build.get_hitbox()
            dx = hb.centerx - cx
            dy = hb.centery - cy
            if not self._cannon_can_hit(dx, dy):
                continue
            dist = math.hypot(dx, dy)
            if dist <= self.range and (
                best_dist is None or dist < best_dist
            ):
                best_dist = dist
                nearest = build
        return nearest

    def _fire_mg_volley(self, dt, targets, bullets):
        """Fire up to mg_gun_count guns at the nearest valid targets.

        One bullet per gun per volley; the volley shares ONE clock
        (fire_rate). Valid = alive, kind in MG_TARGETS, inside the
        range circle, inside the MG facing cone. Distance-sorted so
        the closest bodies get the guns ("targets in rotation" reads
        as the nearest-first pass). MOUNT RULE: shots originate at
        the mount covering the target's arc (turret center for
        rotating turrets; rear/roof/belly mounts for the german
        hull — see the loop below).
        """
        self.mg_cooldown -= dt / 1000
        if self.mg_cooldown > 0:
            return
        if self.mg_gun_count <= 0:
            return

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        candidates = []
        for t in targets:
            if t.dead:
                continue
            # MG targeting rule: only the kinds in MG_TARGETS are
            # engaged.
            if getattr(t, "unit_kind", "infantry") not in self.MG_TARGETS:
                continue
            dx = t.x + t.width / 2 - cx
            dy = t.y + t.height / 2 - cy
            dist = math.hypot(dx, dy)
            if dist <= self.range and self._mg_can_hit(dx, dy):
                candidates.append((dist, dx, dy, t))

        if not candidates:
            return
        candidates.sort(key=lambda c: c[0])

        # Tank shells can kill other tanks (Bullet.armor_damage);
        # regular shots pass through armor harmlessly — the battle
        # state's bullet loops handle the skip rule. Damage carries
        # the producing nation's handicap.
        armor = "tank" in self.MG_TARGETS
        for _dist, dx, dy, t in candidates[: self.mg_gun_count]:
            # MOUNT RULE (user): every shot comes from the mount that
            # covers the target's arc. Rotating-turret MGs (fr female)
            # fire from the turret at the hull center; the german
            # hull PAIRS fire from their fixed positions — rear
            # mounts for bodies BEHIND, roof mounts for bodies ABOVE
            # (north), belly mounts for bodies BELOW (south).
            if self.turret_rotates:
                muzzle_x, muzzle_y = cx, cy
            elif dx * self.dir_x < 0:
                muzzle_x = cx - self.dir_x * (self.width / 2)
                muzzle_y = cy
            elif dy < 0:
                muzzle_x, muzzle_y = cx, cy - self.height / 2
            else:
                muzzle_x, muzzle_y = cx, cy + self.height / 2

            vdx = t.x + t.width / 2 - muzzle_x
            vdy = t.y + t.height / 2 - muzzle_y
            length = math.hypot(vdx, vdy) or 1.0
            bullet = Bullet(
                muzzle_x, muzzle_y, vdx / length, vdy / length,
                armor_damage=armor,
            )
            bullet.damage = scaled_damage(
                self.nation, self.unit_kind, self.damage,
            )
            bullets.append(bullet)
        self.mg_cooldown = self.fire_rate

    def _fire_building_shot(self, dt, building, bullets):
        """Shell an enemy building while parked inside shooting range.

        MOUNT RULE (user): a hull-mounted cannon (tank_ger) fires from
        the FRONT of the tank — the muzzle sits on the front face, so
        the shot physically comes "from the part where the front of
        the tank is"; a rotating-turret cannon (tank_fr_male) fires
        from the turret at the hull center. The facing cone applies
        either way (tank_ger fires FORWARD only): a building outside
        the cone never triggers the stop rule, so this shot is always
        cone-legal when it fires.
        """
        self.gun_cooldown -= dt / 1000
        if self.gun_cooldown > 0:
            return

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        if self.turret_rotates:
            muzzle_x, muzzle_y = cx, cy
        else:
            muzzle_x = cx + self.dir_x * (self.width / 2)
            muzzle_y = cy

        hx, hy = building.get_hitbox().center
        dx, dy = hx - muzzle_x, hy - muzzle_y
        length = math.hypot(dx, dy) or 1.0
        if not self._cannon_can_hit(hx - cx, hy - cy):
            return

        bullet = Bullet(
            muzzle_x, muzzle_y, dx / length, dy / length,
            armor_damage=True,
        )
        bullet.damage = scaled_damage(
            self.nation, self.unit_kind, self.damage,
        )
        bullets.append(bullet)
        self.gun_cooldown = self.fire_rate

    # ---- rendering ----

    def draw(self, screen, camera_x):
        """Country art per unit (blitted over the ground) or side
        block (BLUE player armor / RED enemy armor) with a facing
        marker when sprites are missing."""
        if self.dead:
            return

        px = round(self.x - camera_x)
        py = round(self.y)

        if not render_mode.is_sprite() or self.image is None:
            draw_unit_block(
                screen, px, py, self.width, self.height,
                self.dir_x,
                RED if self.is_enemy else BLUE,
            )
            return

        screen.blit(self.image, (px, py))


class TankUnit(ArmorUnit):
    """Factory tank base: 100 hp, slow; MG hurts infantry AND tanks;
    stops in range of an enemy building and shells it. The VARIANT
    subclasses below assign the per-variant weapon layouts."""

    unit_kind = "tank"
    MG_TARGETS = ("infantry", "tank")

    def __init__(self, x, y, is_enemy=False, filename=None, nation=None):
        # All tank source files scale to one 128x58 world box
        # (4 tiles across: a wide low silhouette like the art).
        super().__init__(
            x, y, is_enemy,
            filename,
            nation=nation,
            hp=TANK_HP,
            speed=TANK_SPEED,
            width=128, height=58,
            mg_range=TANK_MG_RANGE,
            mg_damage=TANK_MG_DAMAGE,
            mg_fire_rate=TANK_MG_FIRE_RATE,
        )


class GermanTank(TankUnit):
    """tank_ger (A7V-style hull): 5.7 cm Maxim-Nordenfelt cannon in
    the FRONT hull only; six 7.9 mm machine guns (two each targeting
    behind, below, and above) fire as a 6-gun volley — never into the
    shallow front arc, which the cannon owns."""

    turret_rotates = False
    mg_gun_count = 6


class FrenchMaleTank(TankUnit):
    """tank_fr_male: 37 mm guns ONLY (no machine guns) — it stops for
    buildings/MGs and shells them, rotating turret: any direction."""

    mg_gun_count = 0


class FrenchFemaleTank(TankUnit):
    """tank_fr_female: Hotchkiss/Reibel machine guns ONLY — no
    cannon, so it NEVER stops for buildings (it keeps advancing and
    strafing); the rotating turret engages any direction."""

    cannon = False
    mg_gun_count = 2


# Sprite-variant -> weapon class (user: "assign weapons by sprite
# variant"); unknown files fall back to the generic TankUnit.
VARIANT_CLASSES = {
    "tank_ger.png": GermanTank,
    "tank_fr_male.png": FrenchMaleTank,
    "tank_fr_female.png": FrenchFemaleTank,
}


# Kind -> class for the factory roll (list-driven: a future vehicle
# kind rejoins by adding a row here plus its table entries).
UNIT_CLASSES = {
    "tank": TankUnit,
}


def roll_armor_unit(nation, is_enemy, x, y, force_filename=None):
    """Build ONE random factory unit of `nation` at (x, y).

    A factory mixes its nation's available kinds randomly (per the
    user: "a random of available units"); under the current table
    every nation fields only tanks. Nations without table entries
    yield None (the factory simply stands empty).

    force_filename pins the VARIANT (the factory's coverage pass —
    male AND female both appear in a battle): the file must exist in
    the nation's option pool or the roll yields None.

    SPAWN WEST OF THE FACTORY (user rule): the unit is placed just
    outside the anchor's west edge and moves toward the trenches
    from there — never overlapping the factory building.
    """
    from systems.factions import armor_unit_options

    options = armor_unit_options(nation)
    if not options:
        return None

    if force_filename is not None:
        matches = [
            (kind, file) for kind, file in options
            if file == force_filename
        ]
        if not matches:
            return None
        kind, filename = matches[0]
    else:
        kind, filename = random.choice(options)

    unit_class = (
        VARIANT_CLASSES.get(filename) or UNIT_CLASSES.get(kind)
    )
    if unit_class is None:
        return None
    # The producing nation is passed INTO the ctor so the WWI
    # balance handicaps (hp resistance) apply at spawn directly.
    unit = unit_class(x, y, is_enemy, filename, nation)

    # West of the anchor (the factory's top-left tile): one hull
    # width + a small gap clear of the building, clamped in-world.
    unit.x = max(0, x - unit.width - 4)
    return unit
