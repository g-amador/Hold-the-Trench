"""
Friendly infantry spawned from barracks.

Homes onto the nearest target — enemy infantry and the enemy bunker
compete by PROXIMITY (user rule: infantry prioritize enemy infantry,
the bunker only when it is nearer than any enemy infantry), engages
in melee with infantry, sieges the bunker. The one-kill design keeps
infantry fights perfectly symmetrical with enemy melee (both sides
lose one unit per clash).
"""

import math
import pygame

from config import (
    BLUE,
    TILE_SIZE,
    INFANTRY_SPEED,
    INFANTRY_HP,
    INFANTRY_SHOOT_RANGE_PX,
    INFANTRY_BULLET_DAMAGE,
    FRIENDLY_SIEGE_DAMAGE,
    FRIENDLY_SIEGE_COOLDOWN,
    INFANTRY_BUNKER_SHOOT_TILES,
    rifle_shoot_cooldown,
    INFANTRY_ANIM_FRAME_S,
    INFANTRY_AIM_POSE_S,
)
from utils.geometry import distance_to_rect
from entities.tank import ArmorUnit
from entities.bullet import Bullet
from entities.damage import FlooredDamage
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from graphics.sprite_generator import SpriteGenerator
from systems.factions import unit_prefix, scaled_damage, scaled_hp

class FriendlyInfantry(FlooredDamage):
    """Ally rifle infantry: one charge, one kill, one death."""

    def __init__(self, x, y, faction="allies", nation=None):
        # Spawn at the barracks' tile origin in pixel coordinates.
        self.x = x
        self.y = y

        # Side-picked soldier art: nation comes from the faction pool
        # (fr for allies right now — FR vs GER; systems/factions.py)
        # unless the caller forces one. Rolled FIRST so the WWI
        # balance handicaps scale
        # this unit's stats at spawn; barracks pass THEIR rolled
        # nation so a building deploys only its own kind of soldier.
        prefix, self.nation = unit_prefix(faction, nation)

        # Baseline stats mirror EnemyInfantry so melee is a fair trade
        # (all from config; hp carries the nation's resistance handicap).
        self.speed = INFANTRY_SPEED
        self.hp = scaled_hp(self.nation, "infantry", INFANTRY_HP)
        self.width = 24
        self.height = 24
        self.dead = False
        # One-kill guard: a charging friendly may kill exactly one
        # enemy, then dies. Without it, both sides could farm kills
        # off a single clash.
        self.kill_count = 0

        # Ranged fire: cooldown gates shots (the nation's WWI rifle
        # rate from config — fr Lebel 43 rpm, ger Gewehr 98 15 rpm);
        # the aim-pose timer plays on every pull (see update).
        self.shoot_cooldown = rifle_shoot_cooldown(self.nation)
        self.shoot_timer = 0.0

        # Siege stats (used when the enemy BUNKER is the nearest
        # target): swing on a fixed cadence against the wall, mirror
        # of EnemyInfantry's assault on the player bunker. Timer
        # starts at 0 so the first contact strike lands immediately.
        self.attack_damage = FRIENDLY_SIEGE_DAMAGE
        self.attack_cooldown = FRIENDLY_SIEGE_COOLDOWN
        self.attack_timer = 0.0

        # Standard infantry frames; None means missing assets (block fallback).
        # size=(width, height): the 1088x976 full-body sources scale to
        # the unit's world box at load, so art and hitbox match 1:1.
        self.sprite_generator = SpriteGenerator()
        self.frames = self.sprite_generator.load_unit_frames(
            prefix, size=(self.width, self.height))

        if self.frames is not None:
            self.frame_rest = self.frames["rest"]
            self.frame_rest_alt = self.frames["rest_alt"]
            self.frames_run = self.frames["run"]
            self.frame_files = self.frames["files"]
        else:
            # Block fallback; non-empty list keeps animation math safe.
            self.frame_rest = None
            self.frame_rest_alt = None
            self.frames_run = [None]
            self.frame_files = None

        # Animation state: timers mirror the other infantry classes;
        # facing 1 = right (allies charge east toward the enemy side).
        self.facing = 1
        self.run_frame = 0
        # Animation timing: the run cycle advances on a fixed frame
        # duration so animation speed is framerate independent.
        self.run_timer = 0.0
        self.run_frame_duration = INFANTRY_ANIM_FRAME_S
        self.is_moving = False
        self.shoot_animation_timer = 0.0
        self.shoot_animation_duration = INFANTRY_AIM_POSE_S

    def update(self, dt, enemies, bullets=None, enemy_bunker=None):
        """Hunt the nearest target (infantry or bunker, by proximity),
        shoot at range, finish infantry in melee, siege the bunker.

        `bullets` is the side's bullet list from the battle state; real
        shots only happen when it is passed. TARGET RULE (user): enemy
        infantry and the enemy bunker compete by PROXIMITY — the
        bunker is attacked when it is nearer than any enemy infantry
        (i.e. no infantry nearby), otherwise the nearest infantry is.
        MIXED FIGHT MODEL: bullets weaken infantry at range; contact
        with infantry resolves as the 1:1 melee exchange below; the
        bunker is fired on from one square away (no suicide trade).
        STOP-AND-SHOOT (user rule): while an enemy infantry stands in
        rifle range the soldier STANDS and fires (shoot animation);
        running resumes only once no enemy infantry is shootable.
        """
        if self.dead:
            return

        # Ranged fire cooldown ticks every frame, whichever path runs.
        self.shoot_timer = max(0.0, self.shoot_timer - dt / 1000)

        # Nearest-target selection: enemy infantry and the enemy
        # bunker in ONE pool, nearest wins (distances measured
        # center-to-center so the bunker's bigger box compares fairly
        # against the 24px soldiers). Armor is ignored: infantry can
        # never scratch armor (only artillery splash and tank shells
        # can), so they don't charge tanks either.
        target = None
        best_dist = None

        for enemy in enemies:
            if enemy.dead:
                continue
            if isinstance(enemy, ArmorUnit):
                continue
            dist = math.hypot(
                enemy.x + enemy.width / 2 - self.x,
                enemy.y + enemy.height / 2 - self.y,
            )
            if best_dist is None or dist < best_dist:
                best_dist = dist
                target = enemy

        bunker_alive = (
            enemy_bunker is not None and not enemy_bunker.is_destroyed()
        )
        if bunker_alive:
            bx = enemy_bunker.x + enemy_bunker.width / 2
            by = enemy_bunker.y + enemy_bunker.height / 2
            dist = math.hypot(bx - self.x, by - self.y)
            if best_dist is None or dist < best_dist:
                target = enemy_bunker

        # Nothing to fight at all: stop and drop the run animation
        # frame.
        if target is None:
            self.is_moving = False
            return

        # STOP-AND-SHOOT (user rule): while an enemy INFANTRY stands
        # inside rifle range, this soldier STANDS and fires on the
        # rifle cadence — both the infantry hunt and the bunker
        # charge pause; running resumes only once no enemy infantry
        # is shootable. Shootable = body not already in melee contact
        # (touching bodies stay with the clash paths below, so the
        # 1:1 trade still resolves) and the aim fits the 90-degree
        # cone once the soldier faces it. The standing aim-blip pose
        # (_fire's shoot_animation_timer) is the shoot animation.
        shoot_target = None
        shoot_dist = None
        shoot_aim = (0.0, 0.0)
        for enemy in enemies:
            if enemy.dead or isinstance(enemy, ArmorUnit):
                continue
            if self.get_hitbox().colliderect(enemy.get_hitbox()):
                continue
            sx = enemy.x + enemy.width / 2 - (self.x + self.width / 2)
            sy = enemy.y + enemy.height / 2 - (self.y + self.height / 2)
            sdist = math.hypot(sx, sy)
            if sdist >= INFANTRY_SHOOT_RANGE_PX:
                continue
            # Cone check with the facing the soldier would adopt.
            aim_facing = 1 if sx > 0 else -1
            if sdist > 0 and (sx / sdist * aim_facing) < 0.707:
                continue
            if shoot_dist is None or sdist < shoot_dist:
                shoot_target = enemy
                shoot_dist = sdist
                shoot_aim = (sx, sy)

        if shoot_target is not None:
            sx, sy = shoot_aim
            self.facing = 1 if sx > 0 else -1
            self.is_moving = False
            self.run_frame = 0
            if shoot_dist > 0:
                self._fire(sx / shoot_dist, sy / shoot_dist, bullets)
            self.shoot_animation_timer = max(
                0, self.shoot_animation_timer - dt / 1000
            )
            return

        # The bunker won the proximity race: charge it and OPEN FIRE
        # from one square away (user rule); NO suicide trade (the 1:1
        # melee is infantry-only). Rifle bullets at the wall are
        # resolved by the state's friendly-bullet loop.
        if bunker_alive and target is enemy_bunker:
            # Aim vector runs from the unit's body center to the
            # bunker's center; wall proximity uses the rect edge.
            dx = bx - (self.x + self.width / 2)
            dy = by - (self.y + self.height / 2)
            length = math.hypot(dx, dy)
            bunker_rect = enemy_bunker.get_hitbox()
            wall_dist = distance_to_rect(
                bunker_rect, self.x + self.width / 2, self.y + self.height / 2,
            )

            if wall_dist <= INFANTRY_BUNKER_SHOOT_TILES * TILE_SIZE:
                # Within one square of the wall: stop and shoot the
                # bunker on the rifle rate. The cone check is skipped —
                # the bunker IS the target and the soldier is facing it.
                self.is_moving = False
                self.run_frame = 0
                self.facing = 1 if dx > 0 else -1

                if bullets is None:
                    # Callers that did not opt into real firing keep
                    # the legacy contact swing so behavior sims still
                    # bite (round-21's siege model).
                    self.attack_timer -= dt / 1000
                    if self.attack_timer <= 0:
                        self.attack_timer = self.attack_cooldown
                        enemy_bunker.take_damage(self.attack_damage)
                        self.shoot_animation_timer = (
                            self.shoot_animation_duration
                        )
                elif length > 0:
                    self._fire(dx / length, dy / length, bullets)
            else:
                # Face and walk the direct line toward the wall.
                self.facing = 1 if dx > 0 else -1
                self.is_moving = True
                if length > 0:
                    self.x += (dx / length) * self.speed * dt / 1000
                    self.y += (dy / length) * self.speed * dt / 1000

            # Same animation cadence as the hunt path while charging.
            if self.is_moving:
                self.run_timer += dt / 1000
                while self.run_timer >= self.run_frame_duration:
                    self.run_timer -= self.run_frame_duration
                    self.run_frame = (
                        (self.run_frame + 1) % len(self.frames_run)
                    )
            else:
                self.run_frame = 0
            self.shoot_animation_timer = max(
                0, self.shoot_animation_timer - dt / 1000
            )
            return

        dx = target.x - self.x
        dy = target.y - self.y
        length = math.hypot(dx, dy)

        if length > 0:
            # Face and walk the direct line toward the target; no
            # pathfinding, no trench avoidance.
            self.facing = 1 if dx > 0 else -1
            self.is_moving = True

            # Move toward enemy
            self.x += (dx / length) * self.speed * dt / 1000
            self.y += (dy / length) * self.speed * dt / 1000

            # Shooting Logic (Range: 200px, Cone: 90 deg)
            # Ranged fire: a real bullet launches on cooldown into
            # `bullets`; the state's friendly-bullet loop resolves the
            # hit against enemies / enemy bunkers. The aim pose is
            # raised by _fire on the actual shot — per volley, never
            # pinned — mirroring EnemyInfantry and the player.
            if length < INFANTRY_SHOOT_RANGE_PX:
                # Normalize and check dot product for 90 degree cone
                nx, ny = dx / length, dy / length
                if (nx * self.facing) >= 0.707:
                    self._fire(nx, ny, bullets)
            else:
                self.shoot_animation_timer = 0

        # Animation update: the run cycle only advances while moving.
        if self.is_moving:
            self.run_timer += dt / 1000
            while self.run_timer >= self.run_frame_duration:
                self.run_timer -= self.run_frame_duration
                self.run_frame = (self.run_frame + 1) % len(self.frames_run)
        else:
            self.run_frame = 0

        self.shoot_animation_timer = max(0, self.shoot_animation_timer - dt / 1000)

        # Melee Collision
        friendly_rect = self.get_hitbox()
        enemy_rect = target.get_hitbox() if hasattr(target, "get_hitbox") else pygame.Rect(
            round(target.x), round(target.y), target.width, target.height
        )

        if friendly_rect.colliderect(enemy_rect):
            # Exactly one kill per charge: only the first frame of
            # contact deals damage (kill_count guard), then this unit
            # dies. Enemy melee mirrors this, so a clash trades 1:1.
            if self.kill_count == 0:
                target.take_damage(target.hp)
                self.kill_count = 1
            self.hp = 0
            self.dead = True

    def _fire(self, nx, ny, bullets):
        """Launch one bullet at the muzzle point, gated by the cooldown.

        nx/ny is the normalized aim vector; bullets=None means the
        caller did not opt into real firing. The weapon-raised pose
        plays exactly on the pull (cooldown cleared) and drains after
        — the shoot animation is per volley, never pinned.
        """
        if self.shoot_timer > 0:
            return

        # Trigger the aim pose on the actual shot; the shared per-frame
        # drain at the end of update() fades it back to idle.
        self.shoot_animation_timer = self.shoot_animation_duration

        if bullets is None:
            return

        # Muzzle at the unit's body center; direction continues the
        # aim. Damage carries this soldier nation's infantry handicap.
        bullet = Bullet(
            self.x + self.width / 2,
            self.y + self.height / 2,
            nx,
            ny,
        )
        bullet.damage = scaled_damage(
            self.nation, "infantry", INFANTRY_BULLET_DAMAGE,
        )
        bullets.append(bullet)
        self.shoot_timer = self.shoot_cooldown

    def current_frame_file(self):
        """CLOSE-view hires: the art file of the pose being drawn.

        Mirrors draw()'s frame selection one-to-one (run cycle wins
        over the shot blip while moving); None when the block
        fallback is active (no art files).
        """
        if self.frames is None:
            return None
        if self.is_moving:
            return self.frame_files["run"][self.run_frame]
        if self.shoot_animation_timer > 0:
            return self.frame_files["rest_alt"]
        return self.frame_files["rest"]

    def get_hitbox(self):
        """Return the unit's collision rectangle in world coordinates."""
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def draw(self, screen, camera_x):
        """Draw the animated full-body frame, or a block fallback when
        sprites are missing."""
        if self.dead:
            return

        if not render_mode.is_sprite() or self.frames is None:
            draw_unit_block(
                screen,
                self.x - camera_x,
                self.y,
                self.width,
                self.height,
                self.facing,
                BLUE,
            )
            return

        screen_x = round(self.x - camera_x)
        screen_y = round(self.y)

        # Single full-body frame (the layered legs/upper composite is
        # retired): the run cycle while moving — it wins over the shot
        # blip so a charging soldier never freezes mid-stride — the
        # second rest pose as the per-shot blip while standing, plain
        # rest otherwise.
        if self.is_moving:
            frame = self.frames_run[self.run_frame]
        elif self.shoot_animation_timer > 0:
            frame = self.frame_rest_alt
        else:
            frame = self.frame_rest

        pos = (screen_x, screen_y)
        self.sprite_generator.draw(screen, frame, pos, self.facing)
