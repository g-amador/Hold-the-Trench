"""
Wave director.
Spawns enemies in waves and configures build spots based on wave composition.
"""

from entities.enemy import Infantry, Cavalry, Tank


class WaveDirector:
    def __init__(self, tilemap, waves, enemies_per_wave):
        self.tilemap = tilemap
        self.total_waves = waves
        self.enemies_per_wave = enemies_per_wave

        self.wave_number = 1
        self.enemies = []

        self.spawn_wave()

    def spawn_wave(self):
        self.enemies = []

        spawn_x = self.tilemap.width * 32 + 200
        spawn_y_base = (self.tilemap.height // 2) * 32

        for i in range(self.enemies_per_wave):
            y = spawn_y_base + (i % 5) * 10

            if self.wave_number == 1:
                self.enemies.append(Infantry(spawn_x, y))
            elif self.wave_number == 2:
                if i % 2 == 0:
                    self.enemies.append(Cavalry(spawn_x, y))
                else:
                    self.enemies.append(Infantry(spawn_x, y))
            else:
                if i % 3 == 0:
                    self.enemies.append(Tank(spawn_x, y))
                else:
                    self.enemies.append(Infantry(spawn_x, y))

        strength = sum(e.hp for e in self.enemies)
        has_tanks = any(isinstance(e, Tank) for e in self.enemies)
        has_cavalry = any(isinstance(e, Cavalry) for e in self.enemies)

        self.tilemap.configure_build_spots(strength, has_tanks, has_cavalry)

    def update(self):
        self.enemies = [e for e in self.enemies if not e.dead]

        if not self.enemies and self.wave_number < self.total_waves:
            self.wave_number += 1
            self.enemies_per_wave += 2
            self.spawn_wave()

    def get_enemies(self):
        return self.enemies
