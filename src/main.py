"""
Entry point for the game.
Creates the Game instance from engine.game and runs it.
"""

from engine.game import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
