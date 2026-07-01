"""
systems/wave_director.py

Controls enemy wave generation and victory conditions.
"""

import random

from src.config import (
    MIN_WAVES,
    MAX_WAVES,
    MAP_WIDTH
)

from src.entities.enemy import Enemy


class WaveDirector:
    """
    Handles all enemy assaults.
    """

    def __init__(self):

        #
        # Total waves required
        #
        self.total_waves = random.randint(
            MIN_WAVES,
            MAX_WAVES
        )

        #
        # Current wave number
        #
        self.current_wave = 0

        #
        # Active enemies
        #
        self.enemies = []

        #
        # Has the scenario ended?
        #
        self.victory = False

        #
        # Delay between waves
        #
        self.wave_cooldown = 3.0

        self.cooldown_timer = 0.0

        self.waiting_for_next_wave = True

    def update(self, delta_time):
        """
        Update wave progression.
        """

        #
        # Update enemies
        #
        for enemy in self.enemies:
            enemy.update(delta_time)

        #
        # Remove dead enemies
        #
        self.enemies = [
            enemy
            for enemy in self.enemies
            if not enemy.is_dead()
        ]

        #
        # Wave finished?
        #
        if (
            len(self.enemies) == 0
            and not self.waiting_for_next_wave
        ):

            self.waiting_for_next_wave = True
            self.cooldown_timer = self.wave_cooldown

        #
        # Spawn next wave
        #
        if self.waiting_for_next_wave:

            self.cooldown_timer -= delta_time

            if self.cooldown_timer <= 0:

                self.start_next_wave()

    def start_next_wave(self):
        """
        Spawn a new assault wave.
        """

        #
        # Victory check
        #
        if self.current_wave >= self.total_waves:

            self.victory = True

            print("Scenario completed!")

            return

        self.current_wave += 1

        self.waiting_for_next_wave = False

        enemy_count = (
            3 +
            self.current_wave * 2
        )

        print(
            f"Wave "
            f"{self.current_wave}/"
            f"{self.total_waves}"
        )

        #
        # Spawn enemies
        #
        for _ in range(enemy_count):

            spawn_x = random.randint(
                0,
                MAP_WIDTH - 1
            )

            spawn_y = 0

            enemy = Enemy(
                spawn_x,
                spawn_y
            )

            self.enemies.append(enemy)

    def draw(self, screen):
        """
        Draw all active enemies.
        """

        for enemy in self.enemies:
            enemy.draw(screen)

    def is_victory(self):
        """
        Scenario completed?
        """

        return self.victory