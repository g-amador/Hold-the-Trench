"""
Game engine: owns the window, clock, world, and current state, and runs
the main loop.

States (main menu, battle, win, game over) are plain objects that each
implement handle_event(event) / update(dt) / render(screen). Switching
states is simple object replacement via change_state(); there is no
state stack and no cleanup contract.
"""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from states.main_menu import MainMenu
from world.tilemap import TileMap


class Game:
    def __init__(self):
        # Initialize pygame once; display, fonts, sprites depend on it.
        pygame.init()

        # Software window; sizes come from config so tuning lives there.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Loop flag. Menu/end states set it False to quit without errors.
        self.running = True

        # Shared world. The menu rebuilds a fresh TileMap right before
        # starting a battle, so each fight starts from the same map.
        self.tilemap = TileMap()

        # First state; every state keeps a reference to this Game so it
        # can switch screens and read the shared tilemap.
        self.state = MainMenu(self)

    def change_state(self, new_state):
        """Replace the current state.

        Accepts any object with handle_event / update / render; no
        lifecycle hooks, transitions are instant.
        """
        self.state = new_state

    def run(self):
        while self.running:
            # tick() caps the frame rate by delaying, and returns how
            # many milliseconds the last frame took: project-wide `dt`
            # is milliseconds, so movement code divides by 1000.
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    # Every other event is delegated wholesale; the
                    # state decides what keys it cares about.
                    self.state.handle_event(event)

            # Frame pipeline: simulate, draw the state's screen, flip.
            self.state.update(dt)
            self.state.render(self.screen)

            pygame.display.flip()

        pygame.quit()
