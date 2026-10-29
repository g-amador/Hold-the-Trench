"""
Air plane unit (user spec batch): produced by air fields on the SAME
cadence as tank factories.

Behavior:
- living in its side's dedicated PLANE list, it FLYS: no ground
  collision, no tile logic — it steers straight toward its target;
- target selection = nearest enemy among ARMOR UNITS (tanks/cars),
  BUILDINGS, and PLANES. No preference but proximity (user: "no
  particular preference aside proximity");
- ground targets (tank/car/building): the plane bombs it when it is
  OVER it — center distance at most PLANE_BOMB_TRIGGER_PX — dropping
  bomb damage on cooldown (direct damage, like artillery splash:
  no bullet, no armor rule); buildings take damage through their
  own take_damage (destructible since BUILDING_HP);
- air targets (planes): machine gun in range, "like infantry vs
  infantry" — PLANE_MG bullets fly; the battle state's bullet loops
  hit their own side's planes with them (and never armored bodies —
  plane MG fire skips armor, bombs do the anti-armor work);
- when no target exists the plane keeps flying on its heading and
  bounces at the world edges (endless patrol).

The WWI balance handicaps (systems/factions.py) scale spawn hp and
both weapon damages per the producing nation. Art per country
(file); enemy planes mirror horizontally like every other unit.
"""

import math

import pygame

from config import (
    TILE_SIZE,
    PLANE_HP,
    PLANE_SPEED,
    PLANE_SIZE,
    PLANE_MG_RANGE,
    PLANE_MG_DAMAGE,
    PLANE_MG_FIRE_RATE,
    PLANE_BOMB_DAMAGE,
    PLANE_BOMB_COOLDOWN,
    PLANE_BOMB_TRIGGER_PX,
    RED,
    BLUE,
)
from entities.bullet import Bullet
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from utils.image_loader import load_first_image
from systems.factions import scaled_damage, scaled_hp
from world.trench_generator import STATIC_MAP


class AirplaneUnit:
    """A flying plane: proximity targets, bombs over targets, air MG."""

    # Identity for the battle state's force counts and targeting
    # rules ("plane" — unlike ground vehicle kinds).
    unit_kind = "plane"

    # A draw offset for the FLIGHT illusion: the plane paints a few
    # pixels above its logical position so it reads as air, not as a
    # ground unit. All hit/bomb math uses the logical position.
    FLIGHT_Y_OFFSET = 24

    def __init__(self, x, y, is_enemy=False, filename=None, nation=None):
        # World position as float; the plane flies free over
        # everything.
        self.x = float(x)
        self.y = float(y)

        self.is_enemy = is_enemy
        self.nation = nation

        # Spawn hp scaled by the producing nation's resistance.
        self.hp = scaled_hp(nation, "plane", PLANE_HP)
        self.speed = PLANE_SPEED
        self.width, self.height = PLANE_SIZE
        self.dead = False

        # Planes never feed the gold economy (armor-like: the state's
        # gold loop sees gold_spawned True and skips them).
        self.gold_spawned = True

        # Weapons: machine gun vs enemy planes (in range), bombs vs
        # whatever ground target the plane is over. Both cooldowns
        # start drained so the first contact strikes immediately.
        self.mg_range = PLANE_MG_RANGE
        self.mg_damage = PLANE_MG_DAMAGE
        self.mg_fire_rate = PLANE_MG_FIRE_RATE
        self.mg_cooldown = 0.0

        self.bomb_damage = PLANE_BOMB_DAMAGE
        self.bomb_cooldown_time = PLANE_BOMB_COOLDOWN
        self.bomb_cooldown = 0.0
        self.bomb_trigger = PLANE_BOMB_TRIGGER_PX

        # Patrol heading steady EAST (enemy planes WEST), like every
        # other unit's advance direction.
        self.dir_x = -1 if is_enemy else 1

        # Per-country art scaled to the world box; enemy planes flip
        # horizontally so their nose points at the player side.
        self.image = load_first_image([filename], alpha=True,
                                      size=self.width_and_height())
        if is_enemy and self.image is not None:
            self.image = pygame.transform.flip(self.image, True, False)

    def width_and_height(self):
        return self.width, self.height

    # ---- housekeeping ----

    def take_damage(self, dmg):
        """Subtract hp; hp <= 0 flips dead (the plane list re-filters)."""
        if self.dead:
            return
        self.hp -= dmg
        if self.hp <= 0:
            self.dead = True

    def get_hitbox(self):
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )

    # ---- behavior ----

    def update(self, dt, ground_targets, air_targets, bullets):
        """Fly toward the nearest enemy; bomb over ground targets,
        machine-gun enemy planes in range, patrol when nothing picks."""

        if self.dead:
            return

        dt_s = dt / 1000

        # Weapon clocks tick every frame.
        self.mg_cooldown = max(0.0, self.mg_cooldown - dt_s)
        self.bomb_cooldown = max(0.0, self.bomb_cooldown - dt_s)

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        # Nearest target, AIR or GROUND mixed (proximity only).
        target = None
        kind = None       # "ground" or "air"
        best = None
        for t in ground_targets:
            if getattr(t, "dead", False) or getattr(t, "is_destroyed", bool)():
                continue
            tgx, tgy = _target_center(t)
            dist = math.hypot(tgx - cx, tgy - cy)
            if best is None or dist < best:
                best = dist
                target = (tgx, tgy, t)
                kind = "ground"
        for t in air_targets:
            if getattr(t, "dead", False):
                continue
            ttx, tty = _target_center(t)
            dist = math.hypot(ttx - cx, tty - cy)
            if best is None or dist < best:
                best = dist
                target = (ttx, tty, t)
                kind = "air"

        if target is None:
            # Patrol: keep the heading, bounce at the world edges.
            self._patrol(dt_s)
            return

        tgx, tgy, entity = target
        dx, dy = tgx - cx, tgy - cy
        length = math.hypot(dx, dy) or 1.0

        # Steer directly at the target (planes ignore the ground).
        self.x += (dx / length) * self.speed * dt_s
        self.y += (dy / length) * self.speed * dt_s

        # Ground target: bomb when OVER it (proximity gate + cooldown).
        if kind == "ground":
            if length <= self.bomb_trigger and self.bomb_cooldown == 0:
                self._drop_bomb(entity)

        # Air target: machine gun inside the MG range ("like infantry
        # vs infantry") — a real bullet into the side's bullet list.
        elif kind == "air" and length <= self.mg_range:
            self._fire_mg(cx, cy, tgx, tgy, bullets)

    def _patrol(self, dt_s):
        """No target: fly the heading; bounce off the left/right edges.

        No vertical motion keeps the plane on its altitude track —
        bounces only reset horizontal heading.
        """
        world_w = len(STATIC_MAP[0]) * TILE_SIZE
        self.x += self.dir_x * self.speed * dt_s
        if self.x <= 0:
            self.x = 0
            self.dir_x = 1
        elif self.x >= world_w - self.width:
            self.x = world_w - self.width
            self.dir_x = -1

    def _drop_bomb(self, target):
        """Bomb release: direct damage on the target under the plane."""
        damage = scaled_damage(self.nation, "plane", self.bomb_damage)
        target.take_damage(damage)
        self.bomb_cooldown = self.bomb_cooldown_time

    def _fire_mg(self, cx, cy, tx, ty, bullets):
        """One machine-gun bullet at an enemy plane, on cooldown."""
        if self.mg_cooldown > 0:
            return

        length = math.hypot(tx - cx, ty - cy) or 1.0
        bullet = Bullet(cx, cy, (tx - cx) / length, (ty - cy) / length)
        # Plane MG fires only at PLANES: no armor damage (the state's
        # loops skip armored bodies without this flag), and no
        # building hits either — only BOMBS touch buildings.
        bullet.can_damage_buildings = False
        bullet.damage = scaled_damage(self.nation, "plane", self.mg_damage)
        bullets.append(bullet)
        self.mg_cooldown = self.mg_fire_rate

    # ---- rendering ----

    def draw(self, screen, camera_x):
        """Country art (blitted above the ground, offset up) or side
        block fallback: BLUE player planes / RED enemy planes."""
        if self.dead:
            return

        px = round(self.x - camera_x)
        py = round(self.y - self.FLIGHT_Y_OFFSET)

        if not render_mode.is_sprite() or self.image is None:
            draw_unit_block(
                screen, px, py, self.width, self.height,
                self.dir_x,
                RED if self.is_enemy else BLUE,
            )
            return

        screen.blit(self.image, (px, py))


def _target_center(t):
    """Center point of a target unit or building (world px)."""
    if hasattr(t, "get_hitbox"):
        return t.get_hitbox().center
    return (
        t.x + getattr(t, "width", 0) / 2,
        t.y + getattr(t, "height", 0) / 2,
    )
