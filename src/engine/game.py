"""
Game engine: manages states and main loop.
"""

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from states.main_menu import MainMenu


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        from world.tilemap import TileMap
        self.tilemap = TileMap()

        self.state = MainMenu(self)

    def change_state(self, new_state):
        self.state = new_state

    def run(self):
        while self.running:
            dt = self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.state.handle_event(event)

            self.state.update(dt)
            self.state.render(self.screen)

            pygame.display.flip()

        pygame.quit()
