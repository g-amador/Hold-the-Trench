"""
WW1 enemies: Infantry, Cavalry, Tank.

EnemyBase provides the shared machinery (advance, hp, death, gold
drops); subclasses override update() to add behavior. Because gold
drops live on the base class, the battle state can treat every enemy
uniformly: update -> spawn_gold on death -> filter the list.
"""

import math
import pygame
import random

from config import (
    RED,
    INFANTRY_SPEED,
    INFANTRY_HP,
    INFANTRY_GOLD_DROP,
    INFANTRY_SHOOT_COOLDOWN,
    INFANTRY_SHOOT_RANGE_PX,
    INFANTRY_BULLET_DAMAGE,
    ENEMY_SIEGE_DAMAGE,
    ENEMY_SIEGE_COOLDOWN,
    LEGACY_TANK_SPEED,
    LEGACY_TANK_HP,
    LEGACY_TANK_GOLD_DROP,
)
from entities.armor import ArmorUnit
from entities.bullet import Bullet
from entities.gold_pickup import GoldPickup
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from graphics.sprite_generator import SpriteGenerator
from systems.factions import unit_prefix, side_coin, scaled_damage, scaled_hp


class EnemyBase:
    """Shared enemy behavior: horizontal advance, hp, death, gold drop."""

    def __init__(self, x, y, speed, hp, gold_drop):
        # World position; movement details come from the subclass call.
        self.x = x
        self.y = y

        self.speed = speed
        self.hp = hp
        self.gold_drop = gold_drop

        # Footprint defaults; subclasses resize per unit type to fit art.
        self.width = 24
        self.height = 32

        # Both flags drive state-side filtering: dead removes the unit,
        # gold_spawned guarantees a single drop per death.
        self.dead = False
        self.gold_spawned = False

        # Coin art dropped at death. EnemyInfantry sets this from the
        # player's chosen side (factions.side_coin — axis coins when
        # the player is allies, french coins when they are axis);
        # subclasses without a side keep the german default so every
        # enemy drop has sensible art.
        self.coin = "coin_ger.png"

    def update(self, dt):
        """Generic advance: walk left at constant speed.

        Baseline movement; AI-driven subclasses (EnemyInfantry) override
        this and do not call super().
        """
        # Guard first: callers already skip dead units, this is the
        # double safety for any other caller.
        if self.dead:
            return

        # dt is milliseconds: move left (toward the player's side) at a
        # fixed speed, no acceleration or friction.
        self.x -= self.speed * dt / 1000

        # Death check here so hp changes from anywhere (melee, future
        # effects) register without every caller remembering to check.
        if self.hp <= 0:
            self.dead = True

    def get_hitbox(self):
        """Return the enemy's collision rectangle in world coordinates."""
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )

    def draw(self, screen, camera_x):
        """Placeholder for units without sprites (Cavalry, Tank): red block."""
        if self.dead:
            return

        pygame.draw.rect(
            screen,
            (200, 50, 50),
            (self.x - camera_x, self.y, self.width, self.height)
        )

    def take_damage(self, dmg):
        """Subtract hp; hp <= 0 flips the dead flag used by all filters."""
        self.hp -= dmg
        if self.hp <= 0:
            self.dead = True

    def spawn_gold(self):
        """Drop gold exactly once after death.

        gold_spawned guards against multiple drops when the state polls
        this every frame; returns None while alive, then the pickup once.
        """
        if self.dead and not self.gold_spawned and self.gold_drop > 0:
            self.gold_spawned = True
            return GoldPickup(
                self.x,
                self.y,
                self.gold_drop,
                texture=self.coin,
            )
        return None
    
class EnemyInfantry(EnemyBase):
    """Rifle infantry: homes onto the nearest friendly; the clash is mutually lethal."""

    def __init__(self, x, y, faction="axis"):
        # Side-picked soldier art: random nation from the faction pool
        # (ger/aust for axis, brit/fr for allies — systems/factions.py).
        # Rolled FIRST so the WWI balance handicaps can scale this
        # unit's stats at spawn (resistance -> hp).
        prefix, self.nation = unit_prefix(faction)

        # Baseline stats: soldier speed, moderate hp, small gold bounty
        # (all from config; hp carries the nation's resistance handicap).
        super().__init__(
            x,
            y,
            speed=INFANTRY_SPEED,
            hp=scaled_hp(self.nation, "infantry", INFANTRY_HP),
            gold_drop=INFANTRY_GOLD_DROP,
        )
        # Coin drops follow the PLAYER's chosen side (user rule). Set
        # AFTER the base ctor — the base writes its own default coin,
        # which previously OVERWROTE whatever subclass coin had been
        # set before the call (germ coins everywhere for every nation).
        # Axis soldiers always drop the german coin; allied soldiers
        # (brit AND fr alike) always drop the french coin
        # (factions.side_coin).
        self.coin = side_coin(faction)
        # Match the sprite footprint; the base 24x32 would not fit the art.
        self.width = 24
        self.height = 24
        # Marks barracks-spawned units for future wave/cost bookkeeping.
        self.is_barracks_unit = True

        # Siege stats (used when no friendly units remain): swing on a
        # fixed cadence against the assault objective. Timer starts at
        # 0 so the first contact strike lands immediately.
        self.attack_damage = ENEMY_SIEGE_DAMAGE
        self.attack_cooldown = ENEMY_SIEGE_COOLDOWN
        self.attack_timer = 0.0

        # Ranged fire against friendlies in range, on cooldown; mirrors
        # FriendlyInfantry so ranged fights resolve the same both ways.
        self.shoot_cooldown = INFANTRY_SHOOT_COOLDOWN
        self.shoot_timer = 0.0

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

        # Face the player side initially; retargeting flips it to the
        # target's direction every frame.
        self.facing = -1
        self.run_frame = 0
        self.run_timer = 0.0
        self.run_frame_duration = 0.12
        self.is_moving = False
        # Aim-pose animation mirrors the player's: a short timer keeps
        # the weapon-raised art on screen after each shot triangle.
        self.shoot_animation_timer = 0.0
        self.shoot_animation_duration = 0.18

    def update(self, dt, friendlies, bullets=None, player_bunker=None):
        """Hunt a friendly, shoot at range, fight on contact; siege the
        bunker when none remain.

        `bullets` is the side's bullet list from the battle state; real
        shots only happen when it is passed. Priority order: nearest
        living friendly first; when there are no friendlies left,
        charge and attack the player bunker.
        """
        if self.dead: return

        # Ranged fire cooldown ticks every frame, whichever path runs.
        self.shoot_timer = max(0.0, self.shoot_timer - dt / 1000)

        # dt is milliseconds; enemies use straight-line moves, no tiles.
        move_amount = self.speed * dt / 1000
        self.is_moving = True

        # Compare only living targets so dying units stop dragging fire.
        # Armored units are excluded entirely: infantry can neither
        # shoot nor melee armor through, so they ignore it (the hull
        # MGs and artillery do the anti-tank work).
        living_friendlies = [
            f for f in friendlies
            if not f.dead and not isinstance(f, ArmorUnit)
        ]

        if living_friendlies:
            # Nearest living friendly is the single target priority
            # (no formation behavior).
            target = min(living_friendlies, key=lambda f: math.hypot(f.x - self.x, f.y - self.y))
            dx, dy = target.x - self.x, target.y - self.y
            dist = math.hypot(dx, dy)

            if dist > 0:
                # Homing movement: walk the direct line to the target.
                # Facing flips toward the movement direction so the art
                # always looks at whoever it is hunting.
                self.facing = 1 if dx > 0 else -1
                self.x += (dx / dist) * move_amount
                self.y += (dy / dist) * move_amount

                # Ranged fire (Range 200px, Cone 90 deg): a real
                # bullet on cooldown into `bullets` (the state's
                # enemy-bullet loop hits friendlies). The aim pose is
                # raised by _fire on the actual shot and drains after
                # it, so shooting reads as a blip per volley.
                if dist < 200:
                    if (dx / dist * self.facing) >= 0.707:
                        self._fire(dx / dist, dy / dist, bullets)

            # Animation update (mirrors FriendlyInfantry): the run
            # cycle advances while moving, and the aim pose drains
            # after each shot — without this the hunt path returned
            # with legs frozen on frame 0 and the pose pinned on.
            if self.is_moving:
                self.run_timer += dt / 1000
                while self.run_timer >= self.run_frame_duration:
                    self.run_timer -= self.run_frame_duration
                    self.run_frame = (self.run_frame + 1) % len(self.legs_run)
            else:
                self.run_frame = 0

            self.shoot_animation_timer = max(
                0,
                self.shoot_animation_timer - dt / 1000,
            )

            # Melee contact: mutual destruction. The hit is applied in
            # both HP pools at once (no per-hit rolls), so exactly one
            # engagement kills exactly one enemy and exactly one friendly.
            if self.get_hitbox().colliderect(target.get_hitbox()):
                target.hp -= self.hp
                target.dead = target.hp <= 0
                self.take_damage(self.hp)
            return

        # No friendly unit left to fight: siege the player bunker.
        if player_bunker is not None and not player_bunker.is_destroyed():
            # Aim at the bunker's center: its hitbox sticks up from the
            # anchor tile, so walking to the center reaches the wall.
            bx = player_bunker.x + player_bunker.width / 2
            by = player_bunker.y + player_bunker.height / 2
            dx, dy = bx - self.x, by - self.y
            dist = math.hypot(dx, dy)

            # In contact: stop advancing (the siege reads as attackers
            # pressed against the wall, not marching through it) and
            # swing on a fixed cadence; the rifle pose marks the hits.
            if self.get_hitbox().colliderect(player_bunker.get_hitbox()):
                self.is_moving = False
                self.run_frame = 0

                self.attack_timer -= dt / 1000
                if self.attack_timer <= 0:
                    self.attack_timer = self.attack_cooldown
                    player_bunker.take_damage(self.attack_damage)
                    self.shoot_animation_timer = self.shoot_animation_duration
                return

            # Charge movement: walk the direct line to the bunker,
            # facing it so the art reads correctly on approach.
            self.facing = 1 if dx > 0 else -1
            if dist > 0:
                self.x += (dx / dist) * move_amount
                self.y += (dy / dist) * move_amount

            # Same run-cycle cadence as the hunt path while charging.
            self.run_timer += dt / 1000
            while self.run_timer >= self.run_frame_duration:
                self.run_timer -= self.run_frame_duration
                self.run_frame = (self.run_frame + 1) % len(self.legs_run)
            self.shoot_animation_timer = max(
                0,
                self.shoot_animation_timer - dt / 1000,
            )
            return

        # Nothing alive to fight and no bunker to siege (bunker already
        # destroyed = battle over, or a map with no player bunker):
        # drain the march animation and idle.
        self.run_timer += dt / 1000
        while self.run_timer >= self.run_frame_duration:
            self.run_timer -= self.run_frame_duration
            self.run_frame = (self.run_frame + 1) % len(self.legs_run)
        self.shoot_animation_timer = max(0, self.shoot_animation_timer - dt / 1000)

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
        # aim. Damage carries this soldier nation's infantry handicap
        # (ger stormtroopers 1.05x etc.).
        bullet = Bullet(self.x + self.width / 2, self.y + self.height / 2, nx, ny)
        bullet.damage = scaled_damage(
            self.nation, "infantry", INFANTRY_BULLET_DAMAGE,
        )
        bullets.append(bullet)
        self.shoot_timer = self.shoot_cooldown

    def draw(self, screen, camera_x):
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
                RED,
            )
            return

        screen_x = round(self.x - camera_x)
        screen_y = round(self.y)

        legs = self.legs_run[self.run_frame] if self.is_moving else self.legs_idle
        upper = self.upper_aim if self.shoot_animation_timer > 0 else self.upper_idle

        pos = (screen_x, screen_y)
        self.sprite_generator.draw(screen, legs, pos, self.facing)
        self.sprite_generator.draw(screen, upper, pos, self.facing)

class Tank(EnemyBase):
    """Slow assault placeholder: heavy hp, biggest bounty."""

    def __init__(self, x, y):
        # Armor removes the usual speed advantage: deliberate contrast
        # with cavalry, same gold-driven economy pressure. Stats from
        # the config table (user rule: every stat centralized).
        super().__init__(
            x,
            y,
            speed=LEGACY_TANK_SPEED,
            hp=LEGACY_TANK_HP,
            gold_drop=LEGACY_TANK_GOLD_DROP,
        )
        self.width = 48
        self.height = 32