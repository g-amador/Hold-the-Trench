"""
systems/pathfinding.py

Basic pathfinding.

Will later be replaced with A*.
"""


class Pathfinder:
    """
    Basic pathfinder.
    """

    def get_next_step(
        self,
        start_x,
        start_y,
        goal_x,
        goal_y
    ):
        """
        Return next movement tile.
        """

        next_x = start_x
        next_y = start_y

        #
        # Horizontal movement
        #
        if goal_x > start_x:
            next_x += 1

        elif goal_x < start_x:
            next_x -= 1

        #
        # Vertical movement
        #
        if goal_y > start_y:
            next_y += 1

        elif goal_y < start_y:
            next_y -= 1

        return (
            next_x,
            next_y
        )

    def build_path(
        self,
        start_x,
        start_y,
        goal_x,
        goal_y
    ):
        """
        Build a simple direct path.
        """

        path = []

        current_x = start_x
        current_y = start_y

        while (
            current_x != goal_x or
            current_y != goal_y
        ):

            current_x, current_y = (
                self.get_next_step(
                    current_x,
                    current_y,
                    goal_x,
                    goal_y
                )
            )

            path.append(
                (
                    current_x,
                    current_y
                )
            )

        return path