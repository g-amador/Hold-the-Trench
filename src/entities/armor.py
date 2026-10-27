"""
Factory-produced armor: tanks and the British machine-gun car.

Both classes share the ArmorUnit machinery (user spec):
- steady FORWARD advance toward the enemy base (the enemy bunker
  when one is on the map — tanks stop there and shell it; cars
  drive on past, they can never damage a bunker);
- an on-board machine gun that auto-fires at the nearest VALID
  target in range without ever stopping the advance ("shoot as
  machine guns");
- the armor damage rule: armor is ONLY damaged by artillery splash
  and tank shots. Every infantry/ MG-nest/ car bullet lacks
  Bullet.armor_damage, and the battle state's bullet loops skip
  armored targets those bullets reach. Tanks fire armor_damage
  bullets: they can also kill other tanks. Cars only ever hurt
  infantry (their bullets are regular).
- armor never drops gold (gold_spawned stays True so the state's
  gold loop skips them).

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
    # a car "cannot damage other tanks"). Read by _pick_target.
    MG_TARGETS = ()

    def __init__(self, x, y, is_enemy, filename,
                 hp, speed, width, height,
                 mg_range, mg_damage, mg_fire_rate):
        # Top-left world position; vehicles use free float positions
        # like all other units (no tile collision).
        self.x = x
        self.y = y

        self.is_enemy = is_enemy
        self.nation = None

        self.hp = hp
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

    def update(self, dt, targets, bullets, enemy_bunker=None):
        """Advance forward and fire the hull MG at valid targets.

        `targets` is the OPPOSING unit list; only kinds listed in
        MG_TARGETS are engaged (cars ignore armor, tanks shoot both
        infantry and tanks). `bullets` is the side-appropriate list
        the battle state simulates. `enemy_bunker` (tanks only use
        it) stops the advance at the enemy bunker and shells it.
        """
        if self.dead:
            return

        world_w = _world_width()
        bunker_hit = (
            enemy_bunker is not None
            and not enemy_bunker.is_destroyed()
            and self.get_hitbox().colliderect(enemy_bunker.get_hitbox())
        )

        if bunker_hit and "bunker" in self.MG_TARGETS:
            # Tanks press against the wall and fire on the gun's
            # cadence (their shells work on buildings like on
            # units). Cars have no "bunker" in MG_TARGETS: they
            # simply keep driving (units do not collide with
            # buildings, so they pass the objective by).
            self._fire_bunker_shot(dt, enemy_bunker, bullets)
            # MG cooldown also gates bunker shots: no double-firing.
            return

        # Steady forward advance; stop at the world edges.
        self.x += self.dir_x * self.speed * dt / 1000
        self.x = max(0, min(self.x, world_w - self.width))

        # Hull MG: nearest valid target inside the range circle.
        self._fire_nearest_target(dt, targets, bullets)

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
        armor = "tank" in self.MG_TARGETS
        bullets.append(Bullet(
            cx, cy, dx / length, dy / length, armor_damage=armor,
        ))
        self.cooldown = self.fire_rate

    def _fire_bunker_shot(self, dt, bunker, bullets):
        """Shell the enemy bunker while pressed against it."""
        self.cooldown -= dt / 1000
        if self.cooldown > 0:
            return

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        bx = bunker.x + bunker.width / 2
        by = bunker.y + bunker.height / 2
        dx, dy = bx - cx, by - cy
        length = math.hypot(dx, dy) or 1.0

        bullets.append(Bullet(
            cx, cy, dx / length, dy / length, armor_damage=True,
        ))
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
    """Factory tank: 100 hp, slow, MG hurts infantry AND tanks."""

    unit_kind = "tank"
    MG_TARGETS = ("infantry", "tank", "bunker")

    def __init__(self, x, y, is_enemy=False, filename=None):
        # All tank source files scale to one 128x58 world box
        # (4 tiles across: a wide low silhouette like the art).
        super().__init__(
            x, y, is_enemy,
            filename,
            hp=TANK_HP,
            speed=TANK_SPEED,
            width=128, height=58,
            mg_range=TANK_MG_RANGE,
            mg_damage=TANK_MG_DAMAGE,
            mg_fire_rate=TANK_MG_FIRE_RATE,
        )


class CarUnit(ArmorUnit):
    """British mobile machine gun (MG nest on wheels): 80 hp, quick,
    can ONLY damage infantry — its MG never engages armor."""

    unit_kind = "car"
    MG_TARGETS = ("infantry",)

    def __init__(self, x, y, is_enemy=False, filename=None):
        # Cars are lighter than tanks: 3 tiles across.
        super().__init__(
            x, y, is_enemy,
            filename,
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
    unit = unit_class(x, y, is_enemy, filename)
    # Remember the nation (art source/debugging) on the unit.
    unit.nation = nation
    return unit
