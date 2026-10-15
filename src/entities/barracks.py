"""
Barracks building.
Spawns friendly infantry every 5 seconds.
"""

from config import TILE_SIZE
from entities.enemy import EnemyInfantry
from entities.friendly_infantry import FriendlyInfantry
from utils.image_loader import load_image


class Barracks:

    def __init__(self, tile_x, tile_y, is_enemy=False):
        self.type = "enemy_barracks" if is_enemy else "barracks"
        self.is_enemy = is_enemy

        self.tile_x = tile_x
        self.tile_y = tile_y

        self.spawn_cooldown = 5.0
        self.timer = 0

        #filename = random.choice(["barraks_fr.png", "barraks_uk.png"]) if is_enemy else random.choice(["barraks_ger.png"])
        filename = "barraks_ger.png"
        self.image = load_image(
            filename,
            alpha=True, 
            size=(TILE_SIZE, TILE_SIZE),
        )

    def update(self, dt, units):
        self.timer += dt / 1000

        if self.timer < self.spawn_cooldown:
            return

        self.timer -= self.spawn_cooldown

        x = self.tile_x * TILE_SIZE
        y = self.tile_y * TILE_SIZE

        if self.is_enemy:
            units.append(EnemyInfantry(x, y))
        else:
            units.append(FriendlyInfantry(x, y))

    def draw(self, screen, camera_x):
        px = self.tile_x * TILE_SIZE - camera_x
        py = self.tile_y * TILE_SIZE
        screen.blit(self.image, (px, py))
