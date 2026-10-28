"""
Friendly infantry spawned from barracks.

Homes onto the nearest enemy, engages in melee, kills exactly one
enemy and dies. The one-kill design keeps fights perfectly
symmetrical with enemy melee (both sides lose one unit per clash).
"""

import math
import pygame

from config import BLUE
from entities.armor import ArmorUnit
from entities.bullet import Bullet
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from graphics.sprite_generator import SpriteGenerator
from systems.factions import unit_prefix

class FriendlyInfantry:
    """Ally rifle infantry: one charge, one kill, one death."""

    def __init__(self, x, y, faction="allies"):
        # Spawn at the barracks' tile origin in pixel coordinates.
        self.x = x
        self.y = y

        # Baseline stats mirror EnemyInfantry so melee is a fair trade.
        self.speed = 120
        self.hp = 40
        self.width = 24
        self.height = 24
        self.dead = False
        # One-kill guard: a charging friendly may kill exactly one
        # enemy, then dies. Without it, both sides could farm kills
        # off a single clash.
        self.kill_count = 0

        # Ranged fire: cooldown gates shots; the aim-pose timer plays
        # on every pull (see update).
        self.shoot_cooldown = 1.2
        self.shoot_timer = 0.0

        # Side-picked soldier art: random nation from the faction pool
        # (brit/fr for allies, ger/aust for axis — systems/factions.py).
        prefix, self.nation = unit_prefix(faction)

        # Standard infantry frames; None means missing assets (block fallback).
        self.sprite_generator = SpriteGenerator()
        self.frames = self.sprite_generator.load_unit_frames(prefix)

        if self.frames is not None:
            self.legs_idle = self.frames["legs_idle"]
            self.legs_run = self.frames["legs_run"]
            self.upper_idle = self.frames["upper_idle"]
            self.upper_aim = self.frames["upper_aim"]
        else:
            # Block fallback; non-empty list keeps animation math safe.
            self.legs_idle = None
            self.legs_run = [None]
            self.upper_idle = None
            self.upper_aim = None

        # Animation state: timers mirror the other infantry classes;
        # facing 1 = right (allies charge east toward the enemy side).
        self.facing = 1
        self.run_frame = 0
        self.run_timer = 0.0
        self.run_frame_duration = 0.12
        self.is_moving = False
        self.shoot_animation_timer = 0.0
        self.shoot_animation_duration = 0.18

    def update(self, dt, enemies, bullets=None):
        """Hunt the nearest enemy: shoot at range, finish in melee.

        `bullets` is the side's bullet list from the battle state; real
        shots only happen when it is passed. MIXED FIGHT MODEL: bullets
        weaken targets at range; contact still resolves as the 1:1
        melee exchange below.
        """
        if self.dead:
            return

        # Ranged fire cooldown ticks every frame, whichever path runs.
        self.shoot_timer = max(0.0, self.shoot_timer - dt / 1000)

        # Nearest-target selection: single-priority homing, no formation.
        target = None
        best_dist = None

        for enemy in enemies:
            if enemy.dead:
                continue
            # Armored targets are ignored: infantry can never scratch
            # armor (only artillery splash and tank shells can), so
            # they don't charge tanks either.
            if isinstance(enemy, ArmorUnit):
                continue
            dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                target = enemy

        # No enemies left: stop and drop the run animation frame.
        if target is None:
            self.is_moving = False
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
            if length < 200:
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
                self.run_frame = (self.run_frame + 1) % len(self.legs_run)
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

        # Muzzle at the unit's body center; direction continues the aim.
        bullets.append(
            Bullet(
                self.x + self.width / 2,
                self.y + self.height / 2,
                nx,
                ny,
            )
        )
        self.shoot_timer = self.shoot_cooldown

    def take_damage(self, damage):
        """Apply damage and mark the unit dead when its health reaches zero."""
        if self.dead:
            return

        self.hp = max(0, self.hp - damage)
        if self.hp == 0:
            self.dead = True

    def get_hitbox(self):
        """Return the unit's collision rectangle in world coordinates."""
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def draw(self, screen, camera_x):
        """Draw the animated sprite, or a block fallback when sprites missing."""
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

        legs = self.legs_run[self.run_frame] if self.is_moving else self.legs_idle
        upper = self.upper_aim if self.shoot_animation_timer > 0 else self.upper_idle

        pos = (screen_x, screen_y)
        self.sprite_generator.draw(screen, legs, pos, self.facing)
        self.sprite_generator.draw(screen, upper, pos, self.facing)
