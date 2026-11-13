"""
Factory-produced tanks.

The ArmorUnit machinery (Beta user spec):
- spawn OUTSIDE the factory on the battle-facing side (user rule):
  player armor rolls out EAST of the factory, enemy armor WEST of it
  (roll_armor_unit offsets the unit off the factory's battle-facing
  edge);
- movement SCALES TO MAP SIZE (config.TANK_SPEED_REF_TILES) and is
  FULL 2D — the tank drives back/forward and up/down toward its
  COMMITTED target (user rule). The commit is picked per variant
  (cannon tanks: the nearest enemy TANK/BUILDING/MG-nest/artillery;
  french female: the nearest enemy INFANTRY — she is the sole
  infantry pursuer) and is re-picked — possibly turning the tank —
  ONLY when the committed target is destroyed. A target in gun
  range halts the tank: it shoots the committed target until the
  target falls or the tank dies, then rolls to the next nearest.
  No target left: the tank stops where it stands. Infantry are
  NEVER a reason to stop — they are squished when driven over and
  machine-gunned in range;
- tanks NEVER collide with buildings (user rule): the movement step
  probes ahead and STEERS AROUND any building in the path (a slide
  along the building's edge on the shortest-detour side);
- armor_damage cannon shells work on all enemy buildings (MG nests,
  artillery, barracks, factories, air fields, bunkers — destructible
  since BUILDING_HP) AND on enemy tanks caught in front of the gun;
  tank MG rounds NEVER damage buildings or tanks (the cannon is the
  only anti-armor/anti-building weapon);
- cannon and machine guns fire SIMULTANEOUSLY (separate cooldowns)
  when their targets are in range;
- weapon layout per SPRITE VARIANT (user spec):
    tank_ger        5.7 cm Maxim-Nordenfelt cannon (FRONT hull
                    muzzle) vs tanks/buildings/MG-nests/artillery
                    IN FRONT + MGs vs infantry only, ONE column per
                    position simultaneously — one above, one below,
                    one behind (never two columns in the same
                    position), fired from their rear/roof/belly
                    mounts;
    tank_fr_male    37 mm gun in the ROTATING turret (fires from
                    the hull center in ANY direction); targets
                    tanks/buildings/MG-nests/artillery (no MG —
                    infantry are engaged only by being run over);
    tank_fr_female  Hotchkiss/Reibel MGs only — targets INFANTRY
                    only (her rounds never hurt tanks or
                    buildings), ONE column at a time; a column
                    directly ahead of her facing is RUN OVER, not
                    shot (she never stops for it); the turret
                    ROTATES, so she shoots in ANY direction while
                    the fixed german hull is restricted (MGs never
                    fire into the front arc — only behind or
                    steeply above/below);
- the armor damage rule: armor is ONLY damaged by other tanks'
  cannon shots and artillery splash (the battle state's bullet
  loops enforce it);
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
    PINK,
    TANK_HP,
    TANK_SPEED,
    TANK_SPEED_REF_TILES,
    TANK_BUILDING_STANDOFF_PX,
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

    # Which target kinds this vehicle's MG can hurt: tanks machine-gun
    # INFANTRY only — enemy armor is a CANNON target. BUILDINGS are
    # handled separately via the buildings list passed to update().
    MG_TARGETS = ()

    # Weapon layout per VARIANT (user spec, assigned by sprite
    # variant — see the subclasses below):
    # cannon           the tank shells its committed target (buildings,
    #                  MG nests, artillery AND enemy tanks in front of
    #                  a fixed hull) once it halts in gun range;
    # mg_gun_count     guns fired per MG volley (the german hull
    #                  caps the volley at ONE column per position:
    #                  above/below/behind);
    # turret_rotates   False = fixed hull (german): the cannon only
    #                  fires FORWARD and the MGs never fire into the
    #                  front arc; True (french rotating turret) = any
    #                  direction;
    # pursues_infantry False = the ADVANCE commits to the nearest
    #                  body that is NOT infantry (enemy tanks,
    #                  buildings, MG nests, artillery); infantry are
    #                  only squished en route and machine-gunned in
    #                  range, never pursued. The french female
    #                  variant is the SOLE pursuer of infantry — the
    #                  only body her guns can hurt.
    cannon = True
    mg_gun_count = 1
    turret_rotates = True
    pursues_infantry = False

    # Block-mode look (user rule): the french female tank renders
    # with a PINK body and the side color on its facing marker; all
    # other variants keep the plain side-color block.
    block_accented = False

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

        # COMMIT slot (user movement rules): the body the tank is
        # driving to / shooting at. It is re-picked — possibly with a
        # direction change — ONLY when it is destroyed; with no
        # valid target left the tank halts where it stands.
        self.move_target = None

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
        """Drive to the committed target, halt in range, shoot.

        `targets` is the OPPOSING unit list (infantry + armor).
        `bullets` is the side-appropriate list the battle state
        simulates. `buildings` is the building list of BOTH SIDES
        (user rule: tanks never touch any building border — the
        stand-off avoidance needs the allied buildings too; commit
        targets filter to the OPPOSING side's buildings only).

        Movement model (user rules): the tank drives in FULL 2D
        (back/forward, up/down) toward its COMMITTED target — the
        nearest enemy tank/building/MG-nest/artillery for cannon
        tanks, the nearest enemy infantry for the french female.
        The commit is re-picked (with a possible direction change)
        ONLY when the committed target is destroyed. A target in
        gun range halts the tank: it shoots the committed target
        until the target falls or the tank dies, then rolls to the
        next nearest target. With no valid target left the tank
        stops where it stands. Infantry are NEVER a reason to stop:
        bodies driven over are squished outright, and the machine
        guns keep firing in range whatever the tank is doing.
        Buildings are never collided with — the movement step
        STEERS AROUND them.
        """
        if self.dead:
            return

        # STAND-OFF INVARIANT (user rule: a tank NEVER touches a
        # building border — allied or enemy): any hull that somehow
        # ended up inside a building's stand-off zone is shoved back
        # out before anything else runs.
        self._push_out_of_buildings(buildings)

        # COMMITTED TARGET: the nearest valid target (per variant).
        # Re-picked — with a possible direction change — ONLY when
        # the committed target is destroyed (user rule). No target
        # left: the tank halts where it stands.
        target = self.move_target
        if target is not None and self._target_gone(target):
            target = None
            self.move_target = None
        if target is None:
            target = self._pick_move_target(targets, buildings)
            if target is not None:
                self.move_target = target

        if target is not None:
            tx, ty = self._body_center(target)
            if self._in_stop_range(target, tx, ty):
                # IN RANGE: halt here and shoot the committed target
                # until it is destroyed or the tank dies (user
                # rule). The hull keeps facing the target so the
                # fixed german cannon stays cone-legal.
                self._face_towards(tx, ty)
                if self.cannon:
                    self._fire_cannon_shot(dt, target, bullets)
            else:
                # Out of range (or a french female with the target
                # column directly ahead of her facing — she keeps
                # driving to RUN OVER it): drive toward the target
                # in 2D, steering around buildings (never colliding).
                self._advance_step(dt, tx, ty, buildings)
                self._face_towards(tx, ty)
                # The step probe already keeps the stand-off, but the
                # slide blend is not probed itself — re-assert the
                # invariant after the move.
                self._push_out_of_buildings(buildings)

        # Infantry are NEVER a reason to stop (user rule): enemy
        # infantry under the hull die outright ("killed as if
        # squished") and the MG volley keeps firing on the move,
        # while halted, and while standing targetless. The list is
        # the OPPOSING side only, so same-side infantry is never
        # squished — no extra faction check needed.
        self._squish_infantry(targets)
        self._fire_mg_volley(dt, targets, bullets)

    def _target_gone(self, target):
        """Committed-target death test: units die, buildings fall."""
        if getattr(target, "dead", False):
            return True
        return bool(getattr(target, "is_destroyed", bool)())

    def _body_center(self, body):
        """Center point of a unit or building (world px)."""
        if hasattr(body, "get_hitbox"):
            return body.get_hitbox().center
        return (
            body.x + getattr(body, "width", 0) / 2,
            body.y + getattr(body, "height", 0) / 2,
        )

    def _face_towards(self, tx, ty):
        """Turn east/west toward the committed target.

        The hull's horizontal facing follows the target; up/down
        movement keeps the heading. A direction change therefore
        only happens when a fresh commit sits on the other side —
        which, per the commit rule, only occurs after the previous
        target was destroyed.
        """
        cx = self.x + self.width / 2
        if tx > cx:
            self.dir_x = 1
        elif tx < cx:
            self.dir_x = -1

    def _in_stop_range(self, target, tx, ty):
        """True when the committed target should HALT the tank.

        Cannon tanks (german, french male) halt once the target is
        inside gun range and shoot it until it falls or they die
        (user rule). The french female halts to gun an infantry
        column EXCEPT when the column stands directly ahead of her
        facing — there she never stops: she keeps driving and runs
        the column over instead (user rule).
        """
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        dist = math.hypot(tx - cx, ty - cy)
        if dist > self.range:
            return False
        if self.pursues_infantry:
            ahead = (
                (tx - cx) * self.dir_x > 0
                and abs(ty - cy) <= self.height
            )
            return not ahead
        return True

    def _pick_move_target(self, targets, buildings):
        """Nearest valid COMMIT target for the ADVANCE.

        (user rule) Cannon tanks (german, french male) commit to the
        nearest body that is NOT infantry: enemy tanks, buildings,
        MG nests and artillery. The french female variant commits
        to enemy INFANTRY only — the only body her guns can hurt.
        Returns the OBJECT so the tank can track its death for the
        turn rule.
        """
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        best = None
        best_dist = None

        if self.pursues_infantry:
            # Female variant: infantry targets ONLY.
            for t in targets:
                if getattr(t, "dead", False):
                    continue
                if getattr(t, "unit_kind", "infantry") != "infantry":
                    continue
                tx, ty = self._body_center(t)
                dist = math.hypot(tx - cx, ty - cy)
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best = t
            return best

        # Cannon tanks: enemy TANKS (user rule) plus the OPPOSING
        # side's BUILDINGS (MG nests and artillery are buildings
        # too). The buildings list carries BOTH sides — same-side
        # buildings are never commit targets.
        for t in targets:
            if getattr(t, "dead", False):
                continue
            if getattr(t, "unit_kind", "infantry") == "infantry":
                continue
            tx, ty = self._body_center(t)
            dist = math.hypot(tx - cx, ty - cy)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = t

        for build in buildings or ():
            if build.is_destroyed():
                continue
            if build.is_enemy == self.is_enemy:
                continue
            hb = build.get_hitbox()
            dist = math.hypot(hb.centerx - cx, hb.centery - cy)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = build
        return best

    def _standoff_zone(self, build):
        """A building's collision zone: its footprint grown by the
        stand-off margin on every side (user rule: tanks never touch
        a building border — the margin IS the no-touch radius)."""
        return build.get_hitbox().inflate(
            TANK_BUILDING_STANDOFF_PX * 2,
            TANK_BUILDING_STANDOFF_PX * 2,
        )

    def _push_out_of_buildings(self, buildings):
        """Shove the hull out of any building stand-off zone.

        The user rule is absolute: a tank NEVER touches a building
        border. If the hull somehow ends up inside a zone (map-edge
        spawn clamp, a slide blend, anything), it is pushed out
        along the axis with the smaller penetration, away from the
        building's center.
        """
        moved = False
        for build in buildings or ():
            if build.is_destroyed():
                continue
            zone = self._standoff_zone(build)
            hull = self.get_hitbox()
            if not hull.colliderect(zone):
                continue

            bcx, bcy = zone.center
            hcx, hcy = hull.center
            # Axis with the smaller penetration wins; the push
            # direction follows the hull's side of the zone.
            if hcx >= bcx:
                px = zone.right - hull.left + 1      # push east
            else:
                px = -(hull.right - zone.left + 1)   # push west
            if hcy >= bcy:
                py = zone.bottom - hull.top + 1      # push south
            else:
                py = -(hull.bottom - zone.top + 1)   # push north
            if abs(px) <= abs(py):
                self.x += px
            else:
                self.y += py
            moved = True

        if moved:
            world_w = _world_width()
            world_h = len(STATIC_MAP) * TILE_SIZE
            self.x = max(0, min(self.x, world_w - self.width))
            self.y = max(0, min(self.y, world_h - self.height))

    def _advance_step(self, dt, tx, ty, buildings):
        """One frame of movement toward (tx, ty).

        Movement is FULL 2D (user: back and forward, up and down).
        Buildings are the only obstacle — BOTH sides' buildings:
        each step probes the hull one step ahead against the
        buildings' stand-off zones and, when one blocks it, slides
        along the zone's edge on the shortest-detour side — tanks go
        AROUND buildings and never touch their borders (user rule).
        """
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        dx, dy = tx - cx, ty - cy
        dist = math.hypot(dx, dy) or 1.0
        ux, uy = dx / dist, dy / dist
        step = self.speed * dt / 1000

        # Desired straight step: probe the hull translated one step
        # along the travel line.
        probe = pygame.Rect(
            round(self.x + ux * step), round(self.y + uy * step),
            self.width, self.height,
        )
        blocked = None
        blocked_zone = None
        for build in buildings or ():
            if build.is_destroyed():
                continue
            zone = self._standoff_zone(build)
            if probe.colliderect(zone):
                blocked = build
                blocked_zone = zone
                break

        if blocked is None:
            self.x += ux * step
            self.y += uy * step
        else:
            # GO AROUND (user rule): steer along the zone's edge
            # toward the side the travel line does NOT pass — the
            # shorter detour — keeping a little forward progress so
            # the tank flows around the corner instead of hugging
            # the wall.
            bx, by = blocked_zone.center
            cross = ux * (by - cy) - uy * (bx - cx)
            side = -1 if cross > 0 else 1
            px, py = -uy * side, ux * side
            plen = math.hypot(px, py) or 1.0
            self.x += (px / plen * 0.7 + ux * 0.3) * step
            self.y += (py / plen * 0.7 + uy * 0.3) * step

        # In-world clamp on BOTH axes (full 2D movement).
        world_w = _world_width()
        world_h = len(STATIC_MAP) * TILE_SIZE
        self.x = max(0, min(self.x, world_w - self.width))
        self.y = max(0, min(self.y, world_h - self.height))

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

    def _fire_mg_volley(self, dt, targets, bullets):
        """Fire the machine guns at the nearest valid infantry.

        The volley shares ONE clock (fire_rate). Valid = alive, kind
        in MG_TARGETS (infantry only), inside the range circle,
        inside the MG facing cone. VOLLEY RULE per hull (user spec):
        a ROTATING turret (french variants) engages the mg_gun_count
        nearest infantry columns, any direction. The FIXED german
        hull engages at most ONE column per POSITION — one above,
        one below, one behind, simultaneously; never two columns in
        the same position ("can't shoot 3 columns below"). MOUNT
        RULE: shots originate at the mount covering each column's
        position (turret center for rotating turrets; rear/roof/
        belly mounts for the german hull).
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

        # MOUNT RULE + VOLLEY RULE: pick the shot list (muzzle, target)
        # per hull type.
        if self.turret_rotates:
            # Rotating turret: nearest-first, mg_gun_count columns,
            # every shot from the turret at the hull center.
            candidates.sort(key=lambda c: c[0])
            shots = [
                (cx, cy, c[3]) for c in candidates[: self.mg_gun_count]
            ]
        else:
            # Fixed german hull: ONE column per position — the
            # nearest BEHIND, the nearest ABOVE, the nearest BELOW —
            # fired from that position's mount (user rule: up to 3
            # columns at once, never two from the same position).
            buckets = {"behind": None, "above": None, "below": None}
            for dist, dx, dy, t in candidates:
                if dx * self.dir_x < 0:
                    key = "behind"
                elif dy < 0:
                    key = "above"
                else:
                    key = "below"
                cur = buckets[key]
                if cur is None or dist < cur[0]:
                    buckets[key] = (dist, t)

            shots = []
            if buckets["behind"] is not None:
                shots.append((
                    cx - self.dir_x * (self.width / 2), cy,
                    buckets["behind"][1],
                ))
            if buckets["above"] is not None:
                shots.append((
                    cx, cy - self.height / 2,
                    buckets["above"][1],
                ))
            if buckets["below"] is not None:
                shots.append((
                    cx, cy + self.height / 2,
                    buckets["below"][1],
                ))

        for muzzle_x, muzzle_y, t in shots:
            vdx = t.x + t.width / 2 - muzzle_x
            vdy = t.y + t.height / 2 - muzzle_y
            length = math.hypot(vdx, vdy) or 1.0
            bullet = Bullet(
                muzzle_x, muzzle_y, vdx / length, vdy / length,
            )
            # MG rounds are ANTI-INFANTRY only (user rule): they pass
            # through armor harmlessly (cannons kill tanks) and never
            # scratch buildings (the cannon is the only anti-building
            # weapon).
            bullet.armor_damage = False
            bullet.can_damage_buildings = False
            bullet.damage = scaled_damage(
                self.nation, self.unit_kind, self.damage,
            )
            bullets.append(bullet)
        self.mg_cooldown = self.fire_rate

    def _fire_cannon_shot(self, dt, target, bullets):
        """Shell the COMMITTED target while halted in gun range.

        Cannon targets (user rule): enemy buildings (MG nests and
        artillery are buildings) AND enemy tanks — for the fixed
        german hull only when the target sits in front of it. MOUNT
        RULE (user): a hull-mounted cannon (tank_ger) fires from the
        FRONT of the tank — the muzzle sits on the front face, so
        the shot physically comes "from the part where the front of
        the tank is"; a rotating-turret cannon (tank_fr_male) fires
        from the turret at the hull center. The facing cone applies
        either way (tank_ger fires FORWARD only): the halted tank
        keeps its hull faced at the target, so the shot is
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

        hx, hy = target.get_hitbox().center
        dx, dy = hx - muzzle_x, hy - muzzle_y
        length = math.hypot(dx, dy) or 1.0
        if not self._cannon_can_hit(hx - cx, hy - cy):
            return

        # Cannon shells carry armor damage: they kill enemy tanks
        # AND scratch every enemy building (armor_damage branch).
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
            # FEMALE TANK BLOCK (user rule): her block body is PINK —
            # the side color moves onto the facing marker (BLUE for
            # the player's side, RED for the enemy side) so the side
            # AND the direction stay readable. All other variants
            # keep the plain side-color block with the dark marker.
            color = RED if self.is_enemy else BLUE
            marker_color = None
            if self.block_accented:
                color = PINK
                marker_color = RED if self.is_enemy else BLUE
            draw_unit_block(
                screen, px, py, self.width, self.height,
                self.dir_x, color, marker_color=marker_color,
            )
            return

        screen.blit(self.image, (px, py))


class TankUnit(ArmorUnit):
    """Factory tank base: 100 hp, slow. The ADVANCE commits to the
    nearest body that is NOT infantry (enemy tanks, buildings, MG
    nests, artillery — user rule); infantry are never pursued, only
    squished when driven over and machine-gunned in range. The
    VARIANT subclasses below assign the per-variant weapon
    layouts."""

    unit_kind = "tank"
    MG_TARGETS = ("infantry",)

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
    the FRONT hull only — it fires at enemy tanks/buildings/MG-nests/
    artillery IN FRONT of the tank; the six 7.9 mm machine guns
    engage INFANTRY only, from BEHIND, ABOVE or BELOW the tank — at
    most ONE column per position simultaneously (never two columns
    in the same position: the hull has no second gun facing any one
    of them)."""

    turret_rotates = False
    mg_gun_count = 6


class FrenchMaleTank(TankUnit):
    """tank_fr_male: 37 mm gun ONLY (no machine guns) — it targets
    enemy TANKS/BUILDINGS/MG-nests/artillery (user rule): it halts
    once near a target (rotating turret: no facing needed) and
    shells it until it falls. No MG, so infantry are engaged only
    by being run over (squished)."""

    mg_gun_count = 0


class FrenchFemaleTank(TankUnit):
    """tank_fr_female: Hotchkiss/Reibel machine guns ONLY — she
    targets ONLY enemy infantry (user rule): her MG rounds carry
    neither armor damage nor building damage, so tanks and
    buildings are immune to her fire. She is the SOLE tank that
    pursues infantry (pursues_infantry), one column at a time; a
    column directly ahead of her facing is RUN OVER, not shot (she
    never stops for it); any other column in range is shot from the
    rotating turret, any direction. No cannon, so she never shells
    buildings — they are steered around instead."""

    cannon = False
    mg_gun_count = 1
    MG_TARGETS = ("infantry",)
    pursues_infantry = True

    # User rule: in block mode the female tank is the PINK tank —
    # pink body, side color on the facing marker (blue player side,
    # red enemy side).
    block_accented = True


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


def roll_armor_unit(nation, is_enemy, x, y, factory_width=0,
                    force_filename=None):
    """Build ONE random factory unit of `nation` at (x, y).

    A factory mixes its nation's available kinds randomly (per the
    user: "a random of available units"); under the current table
    every nation fields only tanks. Nations without table entries
    yield None (the factory simply stands empty).

    force_filename pins the VARIANT (the factory's coverage pass —
    male AND female both appear in a battle): the file must exist in
    the nation's option pool or the roll yields None.

    SPAWN NORTH OF THE FACTORY, OUTSIDE IT (user rule): every tank
    factory — BOTH sides — rolls its armor out of the NORTH edge.
    The hull aligns to the CENTER of the factory's width and sits
    one hull height + the building STAND-OFF margin of clear air
    ABOVE the footprint — it NEVER starts inside its own factory —
    clamped in-world. `x` is the factory anchor tile's left edge;
    `y` is the factory anchor tile's top edge; `factory_width` is
    the factory footprint in px.
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

    # NORTH of the factory (user rule): both sides roll out of the
    # north edge now — one hull height + stand-off margin of clear
    # air above the footprint's top edge, horizontally centered on
    # the factory's width, clamped in-world.
    world_w = _world_width()
    unit.x = x + (factory_width - unit.width) / 2
    unit.y = y - unit.height - TANK_BUILDING_STANDOFF_PX
    unit.x = max(0, min(unit.x, world_w - unit.width))
    unit.y = max(0, unit.y)
    return unit
