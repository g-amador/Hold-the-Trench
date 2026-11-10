"""
Air plane unit (user spec batch): produced by air fields on the SAME
cadence as tank factories.

Behavior:
- living in its side's dedicated PLANE list, it FLYS: no ground
  collision, no tile logic — it steers straight toward its target
  and NEVER stops while one is alive (user: continuous movement);
- target selection = nearest enemy among ARMOR UNITS (tanks),
  infantry, BUILDINGS, and PLANES. No preference but proximity
  (user: "no particular preference aside proximity");
- WEAPON by body class (user adjustments): the MACHINE GUN fires at
  INFANTRY and at enemy PLANES (dogfight, in MC range); BOMBS go to
  TANKS and BUILDINGS (artillery — a building — included), dropped
  when the plane is OVER them — center distance at most
  PLANE_BOMB_TRIGGER_PX. The bomb is a small YELLOW dot that flies
  for PLANE_BOMB_FLIGHT_TIME; it detonates at the pinned point —
  brief RED flash (markers, like artillery's), damage lands ON
  IMPACT on the pinned entity if it is still alive there;
  buildings take damage through their own take_damage (destructible
  since BUILDING_HP);
- bombs ONCE per pass (user reports, v2): a bomb-on-cooldown makes
  tanks/buildings drop out of selection ENTIRELY (ready gate in
  _pick_target) — the plane cruises straight past instead of
  circling/chasing on top of the struck body, and re-engages (same
  or nearest) once the bomb is ready or a dogfight walks into MG
  range. Nothing attackable but enemies alive = straight cruise
  along the last flight vector (bounced at the map edges).
- machine gun: PLANE_MG bullets fly; the battle state's bullet loops
  hit infantry and enemy planes with them (and never armored bodies
  — plane MG fire skips armor, bombs do the anti-armor work). Only
  confirmed bullet hits reduce hp; the cyclic rate per WWI armament
  (Vickers ~450-600 rpm French, Spandau ~400-500 rpm German) lives
  in config.PLANE_MG_ROUNDS_PER_MIN keyed by NATION;
- FACING (user rule): the art's nose points the way the plane
  travels, exactly like the controlled player's facing flip — the
  horizontal heading decides, base nose east / mirrored copy west
  (draw picks per frame; no spawn-side flip anymore);
- when one plane dies mid-dogfight the survivor just re-picks the
  nearest target next frame (proximity selection is per frame);
- when NO target remains ANYWHERE the plane flies to the NEAREST map
  edge and out, then dies (the state's dead-filter removes it).

The WWI balance handicaps (systems/factions.py) scale spawn hp and
both weapon damages per the producing nation.
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
    PLANE_MG_ROUNDS_PER_MIN,
    PLANE_BOMB_DAMAGE,
    PLANE_BOMB_COOLDOWN,
    PLANE_BOMB_TRIGGER_PX,
    PLANE_BOMB_FLIGHT_TIME,
    PLANE_BOMB_IMPACT_TIME,
    RED,
    BLUE,
)
from entities.bullet import Bullet
from entities.damage import GuardedRawDamage
from entities.tank import ArmorUnit
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from utils.image_loader import load_first_image
from systems.factions import scaled_damage, scaled_hp
from world.trench_generator import STATIC_MAP


class AirplaneUnit(GuardedRawDamage):
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
        # WWI cyclic rate per NATION (config table, rpm -> seconds);
        # an unlisted nation keeps the generic rate.
        rpm = PLANE_MG_ROUNDS_PER_MIN.get(nation)
        self.mg_fire_rate = (60.0 / rpm) if rpm else PLANE_MG_FIRE_RATE
        self.mg_cooldown = 0.0

        self.bomb_damage = PLANE_BOMB_DAMAGE
        self.bomb_cooldown_time = PLANE_BOMB_COOLDOWN
        self.bomb_cooldown = 0.0
        self.bomb_trigger = PLANE_BOMB_TRIGGER_PX

        # Bomb bookkeeping (artillery's marker pattern): pending bombs
        # [x_px, y_px, ttl_seconds, pinned entity] in flight, and live
        # red impact markers [x_px, y_px, ttl_seconds].
        self.pending_bombs = []
        self.impacts = []

        # Cruise vector (UNIT length): the LAST flown direction.
        # Straight cruising reuses it when nothing is attackable (bomb
        # clock running, no dogfight) — see _pick_target/_cruise.
        self.flight_vx = -1.0 if is_enemy else 1.0
        self.flight_vy = 0.0

        # Initial horizontal heading: EAST for player planes, WEST for
        # enemy planes (the nose will follow this and every change of
        # heading, like the player's facing flip).
        self.dir_x = -1 if is_enemy else 1

        # Per-country art scaled to the world box. FACING follows
        # flight (user rule: the front points the way the plane goes,
        # exactly like the controlled player): BOTH horizontal
        # orientations are kept — the base file's nose points east,
        # the mirrored copy points west — and draw() picks per frame
        # from dir_x. The old spawn-side enemy flip is retired: a
        # plane chasing or retreating toward the west must show the
        # nose west too (it used to keep flying "backwards").
        self.image = load_first_image([filename], alpha=True,
                                      size=self.width_and_height())
        self.image_flipped = None
        if self.image is not None:
            self.image_flipped = pygame.transform.flip(
                self.image, True, False,
            )

    def width_and_height(self):
        return self.width, self.height

    # ---- housekeeping ----

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
        machine-gun enemy planes in range, leave the map otherwise."""

        if self.dead:
            return

        dt_s = dt / 1000

        # Weapon clocks tick every frame.
        self.mg_cooldown = max(0.0, self.mg_cooldown - dt_s)
        self.bomb_cooldown = max(0.0, self.bomb_cooldown - dt_s)

        # Red impact markers tick down; expired ones are dropped.
        if self.impacts:
            for imp in self.impacts:
                imp[2] -= dt_s
            self.impacts = [imp for imp in self.impacts if imp[2] > 0]

        # Bomb flight: pending bombs land after PLANE_BOMB_FLIGHT_TIME
        # and damage the PINNED entity at that moment (release only
        # launches the yellow dot). Render reads pending/impacts for
        # the yellow-in-flight / red-blast markers.
        if self.pending_bombs:
            for bomb in self.pending_bombs:
                bomb[2] -= dt_s
            landed = [b for b in self.pending_bombs if b[2] <= 0]
            self.pending_bombs = [
                b for b in self.pending_bombs if b[2] > 0
            ]
            for bx, by, _t, entity in landed:
                self._bomb_impact(bx, by, entity)

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        # READY-GATED selection (user fix for hovering + tank-chasing):
        # MG bodies (infantry, enemy planes) are always attackable;
        # BOMB bodies (tanks, buildings) only while the bomb is READY.
        # On cooldown they are skipped ENTIRELY — the plane never
        # steers at a body it cannot strike yet, so it cruises
        # straight past instead of circling on top (bomb once, then
        # move on; selection re-runs every frame).
        target, kind = self._pick_target(
            ground_targets, air_targets, self.bomb_cooldown == 0.0,
        )

        if target is None:
            allies_alive = self._pick_target(
                ground_targets, air_targets, True,
            )[0] is not None

            if allies_alive:
                # Enemies are ALIVE but none is attackable yet (bomb
                # clock running, no dogfight in range): straight
                # cruise along the last flight vector — never a hover,
                # never a chase over a cooldown target.
                self._cruise(dt_s)
                return

            # Nothing left to fight anywhere: leave the battlefield
            # through the nearest edge (user rule — no endless patrol).
            self._leave_map(dt_s)
            return

        tgx, tgy, entity = target
        dx, dy = tgx - cx, tgy - cy
        length = math.hypot(dx, dy) or 1.0

        # Steer directly at the target (planes ignore the ground).
        # Movement NEVER stops — over, past, or in a dogfight, the
        # plane keeps flying (user rule).
        self.x += (dx / length) * self.speed * dt_s
        self.y += (dy / length) * self.speed * dt_s
        self.flight_vx = dx / length
        self.flight_vy = dy / length

        # FACING (user rule): the nose points the way the plane goes,
        # exactly like the controlled player's facing flip. The
        # horizontal component of the flown vector decides; a purely
        # vertical move keeps the last heading (no jitter at dx ~ 0).
        if abs(dx) > 1e-6:
            self.dir_x = 1 if dx > 0 else -1

        # Weapon by BODY CLASS (user adjustment): the machine gun
        # fires at INFANTRY and enemy PLANES; BOMBS go to TANKS and
        # BUILDINGS (artillery — a building — included). Class here is
        # duck-typed: only buildings carry is_destroyed; armor is the
        # ArmorUnit base (bombs do the anti-armor work per project
        # rule); everything else on the ground list is infantry.
        if kind == "air" or (
            not isinstance(entity, ArmorUnit)
            and not hasattr(entity, "is_destroyed")
        ):
            # MG body (enemy plane or infantry): fire inside range.
            if length <= self.mg_range:
                self._fire_mg(cx, cy, tgx, tgy, bullets)
        else:
            # Bomb body (tank or building): bomb when OVER it. The
            # selection gate guarantees the bomb is ready right now.
            if length <= self.bomb_trigger:
                self._drop_bomb(entity)

    def _pick_target(self, ground_targets, air_targets, bomb_ready=True):
        """Nearest ALIVE attackable enemy across both lists.

        Returns (target, kind) or (None, None); kind is "ground" or
        "air" matching the list the winner came from. The READY GATE
        (user fix): BOMB bodies (tanks via ArmorUnit, buildings via
        is_destroyed) qualify only while `bomb_ready`; MG bodies
        (infantry, enemy planes) always qualify. Dead/destroyed
        bodies never qualify either way.
        """
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        best = None
        target = None
        kind = None
        for t in ground_targets:
            if getattr(t, "dead", False) or getattr(t, "is_destroyed", bool)():
                continue
            bomb_body = (
                isinstance(t, ArmorUnit) or hasattr(t, "is_destroyed")
            )
            if bomb_body and not bomb_ready:
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
        return target, kind

    def _cruise(self, dt_s):
        """Nothing attackable right now: straight cruise (user rule).

        All bomb targets sit on the bomb clock and no MG body is in
        range: the plane keeps flying along its LAST flight vector —
        bouncing off the left/right world edges, clamped to the
        map's vertical bounds. Steering resumes the frame a weapon
        becomes ready again; hovering over a previously bombed body
        (the reported back-and-forth) can no longer happen.
        """
        world_w = len(STATIC_MAP[0]) * TILE_SIZE
        world_h = len(STATIC_MAP) * TILE_SIZE

        self.x += self.flight_vx * self.speed * dt_s
        self.y += self.flight_vy * self.speed * dt_s

        # Horizontal bounce: heading (+ nose art) mirrors with it.
        if self.x <= 0:
            self.x = 0
            self.flight_vx = abs(self.flight_vx) or 1.0
            self.dir_x = 1
        elif self.x >= world_w - self.width:
            self.x = world_w - self.width
            self.flight_vx = -abs(self.flight_vx) or -1.0
            self.dir_x = -1

        # Vertical clamp: slide along the ceiling/floor line instead
        # of leaving the strip; the vertical component dies there so
        # the cruise stays horizontal.
        max_y = world_h - self.height
        if self.y < 0:
            self.y = 0
            self.flight_vy = 0.0
        elif self.y > max_y:
            self.y = max_y
            self.flight_vy = 0.0

    def _leave_map(self, dt_s):
        """No target left: fly to the NEAREST edge and out (user rule).

        The plane measures its center against the four world
        boundaries, steers straight at the closest one, and keeps
        going; once fully outside the world it dies, which the battle
        state's dead-filter uses to remove it from the plane lists.

        Marching order is the OLD patrol-echo: LEFT, RIGHT, TOP,
        BOTTOM — an equidistant tie resolves to the first candidate,
        so planes never jitter between edges.
        """
        world_w = len(STATIC_MAP[0]) * TILE_SIZE
        world_h = len(STATIC_MAP) * TILE_SIZE
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        candidates = (
            (cx,             -1.0, 0.0),   # west edge
            (world_w - cx,    1.0, 0.0),   # east edge
            (cy,              0.0, -1.0),  # north edge
            (world_h - cy,    0.0, 1.0),   # south edge
        )
        _dist, vx, vy = min(candidates, key=lambda c: c[0])

        self.x += vx * self.speed * dt_s
        self.y += vy * self.speed * dt_s
        if vx:
            self.dir_x = int(vx)

        if (
            self.x + self.width <= 0 or self.x >= world_w
            or self.y + self.height <= 0 or self.y >= world_h
        ):
            self.dead = True

    def _drop_bomb(self, target):
        """Bomb release: a YELLOW dot flies to the pinned point.

        Damage is NOT instant anymore: the bomb lands after
        PLANE_BOMB_FLIGHT_TIME and _bomb_impact applies it then.
        The cooldown starts at release (artillery's fire-clock echo).
        While that clock runs, tank/building targets drop out of
        selection entirely (READY GATE), so the plane keeps moving
        away instead of circling the body it just struck.
        """
        bx, by = _target_center(target)
        self.pending_bombs.append(
            [bx, by, PLANE_BOMB_FLIGHT_TIME, target],
        )
        self.bomb_cooldown = self.bomb_cooldown_time

    def _bomb_impact(self, bx, by, entity):
        """Bomb touchdown: brief RED flash + damage on the pinned body.

        The pinned entity may already be gone by touch-down (faster
        hands also fired between release and impact): only a still-
        alive/undestroyed body takes the hit, at the bomb's own
        coordinates — the impact position is fixed at release.
        """
        self.impacts.append([bx, by, PLANE_BOMB_IMPACT_TIME])

        if getattr(entity, "dead", False):
            return
        if getattr(entity, "is_destroyed", bool)():
            return
        entity.take_damage(
            scaled_damage(self.nation, "plane", self.bomb_damage),
        )

    def _fire_mg(self, cx, cy, tx, ty, bullets):
        """One machine-gun burst at an INFANTRY body or an enemy
        plane, on cooldown.

        Bullets are real projectiles (only confirmed hits reduce hp).
        They never touch buildings (can_damage_buildings False) and
        pass through armor — the bomb does that work — so the burst
        only ever matters against infantry and other planes.
        """
        if self.mg_cooldown > 0:
            return

        length = math.hypot(tx - cx, ty - cy) or 1.0
        bullet = Bullet(cx, cy, (tx - cx) / length, (ty - cy) / length)
        bullet.can_damage_buildings = False
        bullet.damage = scaled_damage(self.nation, "plane", self.mg_damage)
        bullets.append(bullet)
        self.mg_cooldown = self.mg_fire_rate

    # ---- rendering ----

    def draw(self, screen, camera_x):
        """Country art (blitted above the ground, offset up) or side
        block fallback: BLUE player planes / RED enemy planes. The
        nose points the FLIGHT direction: dir_x < 0 shows the mirrored
        art, dir_x >= 0 the base file (player-facing flip behavior)."""
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

        img = self.image_flipped if self.dir_x < 0 else self.image
        screen.blit(img, (px, py))


def _target_center(t):
    """Center point of a target unit or building (world px)."""
    if hasattr(t, "get_hitbox"):
        return t.get_hitbox().center
    return (
        t.x + getattr(t, "width", 0) / 2,
        t.y + getattr(t, "height", 0) / 2,
    )
