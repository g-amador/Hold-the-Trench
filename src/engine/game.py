"""
Main game controller and state manager.
Handles the game loop and switching between states.
"""

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

from world.tilemap import TileMap
from states.main_menu import MainMenu


class Game:
    """
    Controls the game loop and manages states.
    """

    def __init__(self):
        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption("Hold the Trench")

        # Create window and clock
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Shared tilemap used by AssaultPhase
        self.tilemap = TileMap()

        # Game state
        self.running = True
        self.state = MainMenu(self)

    def change_state(self, new_state):
        """
        Switch to a new game state.
        """
        self.state = new_state

    def run(self):
        """
        Main game loop.
        """

        while self.running:
            dt = self.clock.tick(FPS)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.state.handle_event(event)

            # Update current state
            self.state.update(dt)

            # Render current state
            self.state.render(self.screen)
            pygame.display.flip()

        pygame.quit()
