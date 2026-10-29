"""
WW1 infantry player: WASD movement, tile collision with wall sliding,
wire slow-down, sprite animation, and cone-limited auto-shooting.

Collision uses tiny stepped moves tested against the tilemap, so walls
slide instead of sticking. Long-range shots only fire inside a 90
degree cone in front of the facing direction.
"""

import math
import pygame

from config import TILE_SIZE, BLUE, INFANTRY_SPEED
from entities.bullet import Bullet
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from graphics.sprite_generator import SpriteGenerator
from systems.factions import unit_prefix


# Tile characters that can never be walked through (trench wall, hill).
BLOCKING_TILES = {"#", "H"}
# Building type strings that are solid obstacles once constructed
# (the free-placed statics are solid 4x4s too). ENEMY buildings block
# the player as well (user: "my controlled unit should collide with
# enemy buildings and artillery"): the check below matches the bare
# player-side kind OR any "enemy_"-prefixed kind.
BLOCKING_BUILDINGS = {"mg", "bunker", "barracks", "artillery",
                      "air_field", "tank_factory"}
# Build spot types the player collides with while still unbuilt:
# empty spots are solid so buildings can't be walked into existence.
BUILDABLE_SPOTS = {"mg", "barracks", "artillery"}
# Wire characters slow movement to a fraction of base speed.
SLOW_TILES = {"W"}


class Player:
    """The player-controlled ally infantry; free float position, tile collision."""

    def __init__(self, x, y, faction="allies"):
        # World position as float: sub-pixel movement stays smooth.
        self.x = float(x)
        self.y = float(y)

        # Speed in px/s (config single source, same soldier pace as
        # the barracks infantry); footprint matches the sprite frames.
        self.speed = INFANTRY_SPEED
        self.width = 24
        self.height = 24

        # Side-picked soldier art: random nation from the faction pool
        # (brit/fr for allies, ger/aust for axis). The faction table
        # owns the pools (systems/factions.py).
        prefix, self.nation = unit_prefix(faction)

        # Shooting: a cooldown gates auto-fire, and a short timer keeps
        # the aim pose on screen after each shot.
        self.shoot_cooldown = 0.25
        self.shoot_timer = 0

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

        # Animation timing: the run cycle advances on a fixed frame
        # duration so animation speed is framerate independent.
        self.run_frame = 0
        self.run_timer = 0.0
        self.run_frame_duration = 0.12

        # The aim pose stays visible for a fixed beat after each shot.
        self.shoot_animation_timer = 0.0
        self.shoot_animation_duration = 0.18

        self.is_moving = False
        self.facing = 1  # 1 = right, -1 = left

    def get_hitbox(self):
        """Return the player's hitbox in world coordinates."""
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )

    def _is_blocked_at(self, x, y, tilemap, enemies=None):
        """Check terrain, build spots, buildings, and enemy collisions.

        The single source of truth for "can the player stand here":
        movement code probes candidate positions with this before or
        after every move step.
        """
        # Candidate hitbox at the hypothetical position.
        rect = pygame.Rect(
            round(x),
            round(y),
            self.width,
            self.height,
        )

        # Tile range covered by the hitbox: dividing by TILE_SIZE maps
        # pixel rect edges to tile indices (-1 keeps right/bottom edges
        # inclusive).
        min_tile_x = rect.left // TILE_SIZE
        max_tile_x = (rect.right - 1) // TILE_SIZE
        min_tile_y = rect.top // TILE_SIZE
        max_tile_y = (rect.bottom - 1) // TILE_SIZE

        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                tile = tilemap.get_tile(tile_x, tile_y)

                # Off-world is always blocking (map edge).
                if tile is None:
                    return True

                # Solid terrain: trench wall, hill face.
                if tile.type_char in BLOCKING_TILES:
                    return True

                spot_type = tilemap.spot_types.get((tile_x, tile_y))

                # An EMPTY build spot is solid across its whole
                # footprint until construction (buildings can't be
                # walked into existence; the extra tiles around an MG
                # spot count even when its marker itself isn't under
                # the player).
                spot = tilemap.empty_spot_covering(tile_x, tile_y)
                if spot is not None and spot[0] in BUILDABLE_SPOTS:
                    return True

                # Solid terrain: trench wall, hill face — checked AFTER
                # spots so multi-tile spot logic stays together.
                if tile.type_char in BLOCKING_TILES:
                    return True

                # Constructed buildings block every tile their
                # footprint covers (an MG occupies 4x4, not just its
                # marker tile). Enemy-pre-fixed kinds are solid too:
                # the player cannot walk into an enemy MG nest,
                # artillery, bunker, barracks, or static.
                building = tilemap.building_covering(tile_x, tile_y)

                covered_type = getattr(building, "type", None) if (
                    building is not None
                ) else None

                if (
                    covered_type in BLOCKING_BUILDINGS
                    or (
                        covered_type is not None
                        and covered_type.startswith("enemy_")
                    )
                ):
                    return True

        # Enemies are solid too: the player cannot walk through units.
        if enemies:
            for enemy in enemies:
                if enemy.dead:
                    continue

                # Duck-typed target: prefer get_hitbox(), fall back to a
                # plain rect for anything with raw x/y/size attributes.
                if hasattr(enemy, "get_hitbox"):
                    enemy_rect = enemy.get_hitbox()
                else:
                    enemy_rect = pygame.Rect(
                        round(enemy.x),
                        round(enemy.y),
                        enemy.width,
                        enemy.height,
                    )

                if rect.colliderect(enemy_rect):
                    return True

        return False

    def _move_axis(self, amount, axis, tilemap, enemies=None):
        """Move along one axis without crossing blocking geometry.

        Steps in 1px increments instead of one jump: an unobstructed
        move lands exactly on the requested distance, while any blocked
        step stops the axis there — which is what preserves wall
        sliding (the other axis can still move freely).
        """
        if amount == 0:
            return

        direction = 1 if amount > 0 else -1
        remaining = abs(amount)
        max_step = 1.0

        while remaining > 0:
            step_size = min(remaining, max_step)
            step = direction * step_size

            # Probe the next position on this axis only; the other axis
            # keeps its current value so sliding along walls works.
            test_x = self.x + step if axis == "x" else self.x
            test_y = self.y + step if axis == "y" else self.y

            # First blocked step ends movement on this axis; whatever
            # was already committed earlier in the loop stays.
            if self._is_blocked_at(test_x, test_y, tilemap, enemies):
                break

            if axis == "x":
                self.x = test_x
            else:
                self.y = test_y

            remaining -= step_size

    def handle_input(self, dt, tilemap, enemies=None):
        """Read held keys and resolve movement through per-axis sliding."""
        # Global key state (not events): holding a key means continuous
        # movement for the whole frame.
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        # Face the direction of horizontal movement.
        if dx > 0:
            self.facing = 1
        elif dx < 0:
            self.facing = -1

        # Normalize diagonal movement so diagonals are not sqrt(2)x
        # faster than cardinal movement.
        if dx and dy:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length

        # Terrain on the current tile modifies speed; wire halves it.
        tile_x = int(self.x // TILE_SIZE)
        tile_y = int(self.y // TILE_SIZE)
        tile = tilemap.get_tile(tile_x, tile_y)

        move_speed = self.speed

        if tile and tile.type_char in SLOW_TILES:
            move_speed *= 0.45

        # dt is milliseconds: convert to seconds for px/s speeds.
        move_x = dx * move_speed * dt / 1000
        move_y = dy * move_speed * dt / 1000

        # Resolve axes separately to preserve wall sliding.
        self._move_axis(move_x, "x", tilemap, enemies)
        self._move_axis(move_y, "y", tilemap, enemies)

    def _clamp_to_bounds(self, tilemap):
        """Keep the player inside the static map's boundaries.

        The map IS the playfield: both axes clamp to the tilemap's real
        pixel extents (never the window size or any hardcoded margin).
        The map edge therefore reads exactly like a wall the player can
        press against, including the very top row.
        """
        world_width = tilemap.width * TILE_SIZE
        world_height = tilemap.height * TILE_SIZE

        self.x = max(0.0, min(self.x, world_width - self.width))
        self.y = max(0.0, min(self.y, world_height - self.height))

    def update(self, dt, tilemap, enemies=None):
        """Move input -> collisions -> run animation -> shot timers."""
        # Previous position for movement detection: the input step is
        # the truth, this just measures whether it changed anything.
        old_x = self.x
        old_y = self.y

        self.handle_input(dt, tilemap, enemies)
        self._clamp_to_bounds(tilemap)

        # is_moving drives both the walk animation and idle reset below;
        # small epsilon avoids flicker from float jitter.
        self.is_moving = (
            abs(self.x - old_x) > 0.01
            or abs(self.y - old_y) > 0.01
        )

        if self.is_moving:
            # Advance the run cycle only while actually moving.
            self.run_timer += dt / 1000

            while self.run_timer >= self.run_frame_duration:
                self.run_timer -= self.run_frame_duration
                self.run_frame = (self.run_frame + 1) % len(self.legs_run)
        else:
            # Idle pose: reset to the first frame and drain the timer.
            self.run_frame = 0
            self.run_timer = 0.0

        # Timers count down in ms regardless of movement.
        self.shoot_timer = max(0.0, self.shoot_timer - dt / 1000)
        self.shoot_animation_timer = max(
            0.0,
            self.shoot_animation_timer - dt / 1000,
        )

    def shoot_toward(self, target, bullets):
        """Fire at a target within a 90-grade cone in front of the player.

        Cone check via dot product: the normalized direction to the
        target dotted with the facing vector equals cos(angle), so
        requiring >= cos(45 degrees) allows targets within 45 degrees
        up or down from exactly-ahead (the full cone spans 90 degrees).
        """
        # Cooldown gate: shots only when the last one has expired.
        if self.shoot_timer > 0:
            return

        # Muzzle at the player's center; aim at the target's center.
        start_x = self.x + self.width / 2
        start_y = self.y + self.height / 2

        target_x = target.x + target.width / 2
        target_y = target.y + target.height / 2

        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.hypot(dx, dy)

        if distance == 0:
            return

        # Normalize target vector so the bullet flies at constant speed
        # regardless of distance.
        nx, ny = dx / distance, dy / distance

        # Facing vector: (1, 0) if right, (-1, 0) if left; firing is
        # horizontal-only by design (a trench shooting mechanic).
        fx, fy = (self.facing, 0)

        # Dot product of normalized vectors = cos(theta)
        # cos(45 degrees) is approx 0.707
        dot_product = nx * fx + ny * fy

        # Outside the cone: refuse (this keeps "shooting backwards"
        # impossible even to nearby targets).
        if dot_product < 0.707:
            return

        bullets.append(Bullet(start_x, start_y, nx, ny))

        # Both timers restart: one gates the next shot, one plays the
        # aim pose art.
        self.shoot_timer = self.shoot_cooldown
        self.shoot_animation_timer = self.shoot_animation_duration

    def auto_fire(self, dt, enemies, bullets):
        """Shoot the nearest enemy within a 90-degree cone in front, within 300 pixels.

        Selection is distance-first (nearest in range AND cone wins);
        the actual shot is delegated to shoot_toward, which re-checks
        the cone and cooldown. dt is unused: firing is not timed by the
        update loop, only by target presence; kept for call-signature
        compatibility.
        """
        if self.shoot_timer > 0:
            return

        player_x = self.x + self.width / 2
        player_y = self.y + self.height / 2

        nearest_enemy = None
        nearest_distance = float("inf")

        for enemy in enemies:
            # Dead units are excluded early: no shots at corpses.
            if getattr(enemy, "dead", False):
                continue

            enemy_x = enemy.x + enemy.width / 2
            enemy_y = enemy.y + enemy.height / 2
            dx = enemy_x - player_x
            dy = enemy_y - player_y
            distance = math.hypot(dx, dy)

            # Range gate: 300px is the player's engagement envelope.
            if distance == 0 or distance > 300:
                continue

            # Normalize target vector
            nx, ny = dx / distance, dy / distance

            # Dot product with facing vector (self.facing, 0)
            dot_product = nx * self.facing

            # Only consider enemies within 45 degrees up/down (total 90 deg cone)
            if dot_product < 0.707:
                continue

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_enemy = enemy

        if nearest_enemy:
            self.shoot_toward(nearest_enemy, bullets)

    def draw(self, screen, camera_x):
        """Draw animated legs and upper body, or blocks when sprites are missing."""
        if not render_mode.is_sprite() or self.frames is None:
            self._draw_block(screen, camera_x)
            return

        screen_x = round(self.x - camera_x)
        screen_y = round(self.y)

        if self.is_moving:
            legs = self.legs_run[self.run_frame]
        else:
            legs = self.legs_idle

        if self.shoot_animation_timer > 0:
            upper = self.upper_aim
        else:
            upper = self.upper_idle

        position = (screen_x, screen_y)
        self.sprite_generator.draw(
            screen, legs, position, self.facing
        )
        self.sprite_generator.draw(
            screen, upper, position, self.facing
        )

    def _draw_block(self, screen, camera_x):
        """Fallback rendering: flat block with a marker on the facing edge."""
        draw_unit_block(
            screen,
            self.x - camera_x,
            self.y,
            self.width,
            self.height,
            self.facing,
            BLUE,
        )
