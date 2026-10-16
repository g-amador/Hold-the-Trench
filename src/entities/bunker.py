"""
Bunker building.
The player's bunker must survive; the enemy bunker is the assault objective.
"""

import pygame
import random

from config import TILE_SIZE, GREY
from utils.image_loader import load_image


class Bunker:
    def __init__(self, tile_x, tile_y, is_enemy=False):
        self.is_enemy = is_enemy
        self.type = "enemy_bunker" if is_enemy else "bunker"

        self.tile_x = tile_x
        self.tile_y = tile_y

        self.hp = 200
        self.dead = False
        self.width = TILE_SIZE * 2
        self.height = TILE_SIZE * 3

        # World coordinates used for targeting and collision.
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE - (self.height - TILE_SIZE)

        filename = random.choice(["bunker_fr.png", "bunker_brit.png"]) if is_enemy else random.choice(["bunker_ger.png"])        
        self.image = load_image(
            filename,
            alpha=True, 
            size=(TILE_SIZE, TILE_SIZE),
        )

        if is_enemy:
            self.image = pygame.transform.flip(self.image, True, False)

    def get_hitbox(self):
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )

    def update(self):
        pass

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)
        self.dead = self.hp <= 0

    def is_destroyed(self):
        return self.hp <= 0

    def draw(self, screen, camera_x):
        rect = self.get_hitbox()
        rect.x -= round(camera_x)

        #color = (150, 65, 65) if self.is_enemy else GREY
        #pygame.draw.rect(screen, color, rect)

        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        screen.blit(self.image, (px, py))
