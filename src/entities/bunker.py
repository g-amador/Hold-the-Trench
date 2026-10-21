"""
Bunker building: the win/lose anchor of a battle.

The player's bunker must survive; destroying every enemy bunker wins
the battle. Bunkers do not shoot: they are pure objectives with hp
that other buildings and the player protect or attack.
"""

import pygame
import random

from config import TILE_SIZE, GREY
from graphics import render_mode
from graphics.block_drawer import draw_unit_block
from utils.image_loader import load_image


class Bunker:
    def __init__(self, tile_x, tile_y, is_enemy=False):
        self.is_enemy = is_enemy
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

        # Art side (placeholder faction logic until the faction table
        # lands), same convention as Barracks.
        prefix = f"building_bunker"

        filename = random.choice([f"{prefix}_fr.png", f"{prefix}_brit.png"]) if is_enemy else random.choice([f"{prefix}_ger.png"])
        self.image = load_image(
            filename,
            alpha=True,
            size=(TILE_SIZE, TILE_SIZE),
        )

        # Mirror enemy art so it faces the battlefield like its units.
        # Flipping copies the cached surface: the cache is never mutated.
        if is_enemy:
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
        if not render_mode.is_sprite():
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
