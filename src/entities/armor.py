"""
Factory-produced armor: tanks and the British machine-gun car.

Both classes share the ArmorUnit machinery (user spec):
- steady FORWARD advance toward the enemy base, STOPPING whenever an
  enemy building is within shooting range (user: "tanks and car
  should stop when in shooting range of a building") — tanks then
  shell that building; cars only park (they keep their infantry-only
  MG rule from the previous batch);
- an on-board machine gun that auto-fires at the nearest VALID
  target in range without ever needing to stop ("shoot as machine
  guns") — tanks hurt infantry AND other tanks, cars only infantry;
- the armor damage rule: armor is ONLY damaged by other tanks' shots
  and artillery splash (the battle state's bullet loops enforce it);
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
    CAR_HP,
    TANK_SPEED,
    CAR_SPEED,
    TANK_MG_RANGE,
    TANK_MG_DAMAGE,
    TANK_MG_FIRE_RATE,
    CAR_MG_RANGE,
    CAR_MG_DAMAGE,
    CAR_MG_FIRE_RATE,
)
from entities.bullet import Bullet
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from utils.image_loader import load_first_image
from systems.factions import scaled_damage, scaled_hp
from world.trench_generator import STATIC_MAP


def _world_width():
    """World pixel width from the ASCII map (edge stop for armor)."""
    return len(STATIC_MAP[0]) * TILE_SIZE


class ArmorUnit:
    """Shared vehicle behavior: advance, hull MG, hp, death."""

    # Vehicle identity for the MG targeting rules and the battle
    # state's force counts; infantry classes read as "infantry"
    # through the same getattr fallback.
    unit_kind = "vehicle"

    # Which target kinds this vehicle's MG can hurt: tanks shoot
    # infantry AND other tanks; cars shoot infantry only (user rule:
    # a car "cannot damage other tanks"). BUILDINGS are handled
    # separately via the buildings list passed to update().
    MG_TARGETS = ()

    # Buildings targeting (user spec): TANKS target enemy buildings;
    # cars only ever stop in building range (no building fire).
    CAN_SHELL_BUILDINGS = False

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
        self.speed = speed
        self.width = width
        self.height = height
        self.dead = False

        # Armor never feeds the gold economy: the flag stays True so
        # the state's gold loop (dead and not gold_spawned) skips
        # armored bodies without any spawn_gold method needed.
        self.gold_spawned = True

        # Hull machine gun: MG-nest-style auto-fire on cooldown.
        self.range = mg_range
        self.damage = mg_damage
        self.fire_rate = mg_fire_rate
        self.cooldown = 0

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

    def take_damage(self, dmg):
        """Subtract hp; hp <= 0 flips dead (unit lists re-filter)."""
        self.hp -= dmg
        if self.hp <= 0:
            self.dead = True

    def get_hitbox(self):
        """Collision rectangle in world coordinates."""
        return pygame.Rect(
            round(self.x), round(self.y), self.width, self.height,
        )

    # ---- behavior ----

    def update(self, dt, targets, bullets, buildings=None):
        """Advance forward, stop in building range, fire the hull MG.

        `targets` is the OPPOSING unit list; only kinds listed in
        MG_TARGETS are engaged (cars ignore armor, tanks shoot both
        infantry and tanks). `bullets` is the side-appropriate list
        the battle state simulates. `buildings` is the OPPOSING
        BUILDING list (user spec): a tank stops and SHELLS the
        nearest building in shooting range; a car stops the advance
        the same way but parks (its MG can never hurt buildings).
        """
        if self.dead:
            return

        world_w = _world_width()

        # Building stop rule (user): "tanks and car should stop when
        # in shooting range of a building". Nearest ALIVE enemy
        # building whose center is inside the gun range halts the
        # advance this frame.
        building = self._nearest_building(buildings)

        if building is not None and self.CAN_SHELL_BUILDINGS:
            # Tanks: park here and shell the building on the gun's
            # cadence. Their armor_damage shots work on all enemy
            # buildings (MG nests, artillery, barracks, factories,
            # air fields, bunkers — destructible since BUILDING_HP).
            self._fire_building_shot(dt, building, bullets)
            return

        if building is not None:
            # Cars: stop the advance but keep the hull MG (infantry
            # in range is still engaged; the building never hurts).
            self._fire_nearest_target(dt, targets, bullets)
            return

        # Steady forward advance; stop at the world edges.
        self.x += self.dir_x * self.speed * dt / 1000
        self.x = max(0, min(self.x, world_w - self.width))

        # Hull MG: nearest valid target inside the range circle.
        self._fire_nearest_target(dt, targets, bullets)

    def _nearest_building(self, buildings):
        """Nearest ALIVE enemy building within the gun's range circle.

        buildings=None means the state passed no list (back-compat):
        no building rule applies. Distance is center-to-center, the
        same measure the hull MG uses for units.
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
            dist = math.hypot(hb.centerx - cx, hb.centery - cy)
            if dist <= self.range and (
                best_dist is None or dist < best_dist
            ):
                best_dist = dist
                nearest = build
        return nearest

    def _fire_nearest_target(self, dt, targets, bullets):
        """Auto-fire the MG at the nearest valid target, on cooldown."""
        self.cooldown -= dt / 1000
        if self.cooldown > 0:
            return

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        target = None
        best_dist = None
        for t in targets:
            if t.dead:
                continue
            # MG targeting rule: cars skip armor, tanks shoot both.
            if getattr(t, "unit_kind", "infantry") not in self.MG_TARGETS:
                continue
            dist = math.hypot(t.x - cx, t.y - cy)
            if dist <= self.range and (best_dist is None or dist < best_dist):
                best_dist = dist
                target = t

        if target is None:
            return

        dx = target.x - cx
        dy = target.y - cy
        length = math.hypot(dx, dy)
        if length == 0:
            return

        # Tank shells can kill other tanks (Bullet.armor_damage);
        # car bullets are regular (pass through armor harmlessly —
        # the battle state's bullet loops handle the skip rule).
        # Damage carries the producing nation's handicap.
        armor = "tank" in self.MG_TARGETS
        bullet = Bullet(cx, cy, dx / length, dy / length, armor_damage=armor)
        bullet.damage = scaled_damage(
            self.nation, self.unit_kind, self.damage,
        )
        bullets.append(bullet)
        self.cooldown = self.fire_rate

    def _fire_building_shot(self, dt, building, bullets):
        """Shell an enemy building while parked inside shooting range."""
        self.cooldown -= dt / 1000
        if self.cooldown > 0:
            return

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        hx, hy = building.get_hitbox().center
        dx, dy = hx - cx, hy - cy
        length = math.hypot(dx, dy) or 1.0

        bullet = Bullet(cx, cy, dx / length, dy / length, armor_damage=True)
        bullet.damage = scaled_damage(
            self.nation, self.unit_kind, self.damage,
        )
        bullets.append(bullet)
        self.cooldown = self.fire_rate

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
    """Factory tank: 100 hp, slow, MG hurts infantry AND tanks; stops
    in range of an enemy building and shells it."""

    unit_kind = "tank"
    MG_TARGETS = ("infantry", "tank")
    CAN_SHELL_BUILDINGS = True

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


class CarUnit(ArmorUnit):
    """British mobile machine gun (MG nest on wheels): 80 hp, quick,
    can ONLY damage infantry — its MG never engages armor. It still
    STOPS when an enemy building is inside shooting range (user rule)
    but never fires at it."""

    unit_kind = "car"
    MG_TARGETS = ("infantry",)
    CAN_SHELL_BUILDINGS = False

    def __init__(self, x, y, is_enemy=False, filename=None, nation=None):
        # Cars are lighter than tanks: 3 tiles across.
        super().__init__(
            x, y, is_enemy,
            filename,
            nation=nation,
            hp=CAR_HP,
            speed=CAR_SPEED,
            width=96, height=44,
            mg_range=CAR_MG_RANGE,
            mg_damage=CAR_MG_DAMAGE,
            mg_fire_rate=CAR_MG_FIRE_RATE,
        )


def roll_armor_unit(nation, is_enemy, x, y):
    """Build ONE random factory unit of `nation` at (x, y).

    A British factory mixes tanks and cars randomly (per the user:
    "a random of available units"); French/German factories only
    field tanks. Nations without table entries yield None (the
    factory simply stands empty).
    """
    from systems.factions import armor_unit_options

    options = armor_unit_options(nation)
    if not options:
        return None

    kind, filename = random.choice(options)
    unit_class = CarUnit if kind == "car" else TankUnit
    # The producing nation is passed INTO the ctor so the WWI
    # balance handicaps (hp resistance) apply at spawn directly.
    return unit_class(x, y, is_enemy, filename, nation)
