"""
main.py

Entry point for Hold the Trench.
"""

import sys

from src.engine.game import Game


def main():
    """
    Start the game.
    """

    try:

        game = Game()

        game.run()

    except KeyboardInterrupt:

        print(
            "\nHold the Trench terminated."
        )

    except Exception as e:

        print(
            "\nFatal error:"
        )

        print(e)

        raise

    finally:

        sys.exit()


if __name__ == "__main__":

    main()