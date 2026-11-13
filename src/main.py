"""
Entry point for the game.

Creates the Game instance from engine.game and runs it. Run with
`python src/main.py` from the src/ directory (or repo root with the
venv): the script's folder becomes the import root for this
package-less module layout.
"""

from engine.game import Game


def main():
    # One Game object owns the window, clock, world, and state machine.
    game = Game()

    # run() loops until QUIT, or until a state sets game.running = False.
    game.run()


if __name__ == "__main__":
    # Guard so importing main.py never starts the game loop.
    main()
