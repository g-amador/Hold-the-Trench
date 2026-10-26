"""
Bunker building: the win/lose anchor of a battle.

The player's bunker must survive; destroying every enemy bunker wins
the battle. Bunkers do not shoot: they are pure objectives with hp
that other buildings and the player protect or attack.
"""

import pygame

from config import TILE_SIZE, GREY
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from systems.factions import building_variant_filenames
from utils.image_loader import load_first_image


class Bunker:
    def __init__(self, tile_x, tile_y, is_enemy=False, faction="allies"):
        self.is_enemy = is_enemy
        self.faction = faction
        # type strings match the map spot_types keys.
        self.type = "enemy_bunker" if is_enemy else "bunker"

        self.tile_x = tile_x
        self.tile_y = tile_y

        # Bunkers are the tankiest entity; hp only ever decreases here.
        self.hp = 200
        self.dead = False

        # Footprint is bigger than one tile so the bunker is a real
        # obstacle behind the trench line.
        self.width = TILE_SIZE * 2
        self.height = TILE_SIZE * 3

        # World coordinates used for targeting and collision: the
        # bunker sticks UP from its anchor tile (y offset), which keeps
        # the hitbox aligned with the drawn fortification.
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE - (self.height - TILE_SIZE)

        # Art side: random per-building from the faction's pool, same
        # rule as the other buildings (axis = ger, allies = brit/fr) —
        # scene-variant chain loader (a/b/c/d with summer-day fallback)
        # per the user's letter mapping: a summer day, b summer night,
        # c winter day, d winter night.
        self.image = load_first_image(
            building_variant_filenames(faction, "bunker"),
            alpha=True,
            size=(TILE_SIZE, TILE_SIZE),
        )

        # Mirror enemy art so it faces the battlefield like its units.
        # Flipping copies the cached surface: the cache is never mutated.
        # A None image (no art at all) is left flipped-free: draw()
        # falls back to the block mode instead.
        if is_enemy and self.image is not None:
            self.image = pygame.transform.flip(self.image, True, False)

    def get_hitbox(self):
        """Return the bunker's collision rectangle in world coordinates."""
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )

    def update(self):
        # Passive objective: nothing to simulate.
        pass

    def take_damage(self, dmg):
        """Apply damage; hp floors at 0 so `is_destroyed` reads true once."""
        self.hp = max(0, self.hp - dmg)
        self.dead = self.hp <= 0

    def is_destroyed(self):
        """Win/lose checks test hp directly (hp == 0 = collapsed)."""
        return self.hp <= 0

    def draw(self, screen, camera_x):
        """Sprite in SPRITES mode; flat grey block in BLOCK mode.

        Block mode must show no textures at all: the block covers the
        bunker's full (2x3 tile) footprint so the objective still reads
        as a large structure while every texture is hidden.
        """
        if not render_mode.is_sprite() or self.image is None:
            # Anchor on the hitbox so the block lines up with the
            # bunker's real collision area.
            rect = self.get_hitbox()
            rect.x -= round(camera_x)
            draw_unit_block(
                screen,
                rect.x,
                rect.y,
                rect.width,
                rect.height,
                -1 if self.is_enemy else 1,
                GREY,
            )
            return

        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        screen.blit(self.image, (px, py))
