"""
systems/building_system.py

Handles player structure placement.
"""

import pygame

from src.config import (
    TRENCH_COST,
    MG_NEST_COST,
    BUNKER_COST,
    ARTILLERY_COST
)

from src.entities.trench import Trench
from src.entities.mg_nest import MGNest
from src.entities.bunker import Bunker
from src.entities.artillery import Artillery


class BuildingSystem:
    """
    Construction system.
    """

    def __init__(self):
        """
        Initialize construction system.
        """

        #
        # Currently selected structure
        #
        self.selected_building = "trench"

    def handle_event(
        self,
        event,
        tilemap,
        economy
    ):
        """
        Handle construction input.
        """

        #
        # Building selection
        #
        if event.type == pygame.KEYDOWN:

            #
            # Trench
            #
            if event.key == pygame.K_1:

                self.selected_building = "trench"

                print(
                    "Selected: Trench"
                )

            #
            # MG Nest
            #
            elif event.key == pygame.K_2:

                self.selected_building = "mg_nest"

                print(
                    "Selected: MG Nest"
                )

            #
            # Bunker
            #
            elif event.key == pygame.K_3:

                self.selected_building = "bunker"

                print(
                    "Selected: Bunker"
                )

            #
            # Artillery
            #
            elif event.key == pygame.K_4:

                self.selected_building = "artillery"

                print(
                    "Selected: Artillery"
                )

            return

        #
        # Mouse placement
        #
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        #
        # Left mouse only
        #
        if event.button != 1:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        tile_x, tile_y = tilemap.world_to_tile(
            mouse_x,
            mouse_y
        )

        tile = tilemap.get_tile(
            tile_x,
            tile_y
        )

        #
        # Invalid tile
        #
        if tile is None:
            return

        #
        # Blocked terrain
        #
        if not tile.walkable:

            print(
                "Cannot build here."
            )

            return

        #
        # Tile unavailable
        #
        if tile.building is not None:

            print(
                "Tile already occupied."
            )

            return

        #
        # Build selected structure
        #
        if self.selected_building == "trench":

            self.place_trench(
                tile,
                economy
            )

        elif self.selected_building == "mg_nest":

            self.place_mg_nest(
                tile,
                economy
            )

        elif self.selected_building == "bunker":

            self.place_bunker(
                tile,
                economy
            )

        elif self.selected_building == "artillery":

            self.place_artillery(
                tile,
                economy
            )

    def place_trench(
        self,
        tile,
        economy
    ):
        """
        Build trench.
        """

        if not economy.spend(
            TRENCH_COST
        ):

            print(
                "Not enough supplies."
            )

            return

        tile.building = Trench(
            tile
        )

        print(
            f"Trench built at "
            f"({tile.x}, {tile.y})"
        )

    def place_mg_nest(
        self,
        tile,
        economy
    ):
        """
        Build MG nest.
        """

        if not economy.spend(
            MG_NEST_COST
        ):

            print(
                "Not enough supplies."
            )

            return

        tile.building = MGNest(
            tile
        )

        print(
            f"MG Nest built at "
            f"({tile.x}, {tile.y})"
        )

    def place_bunker(
        self,
        tile,
        economy
    ):
        """
        Build bunker.
        """

        if not economy.spend(
            BUNKER_COST
        ):

            print(
                "Not enough supplies."
            )

            return

        tile.building = Bunker(
            tile
        )

        print(
            f"Bunker built at "
            f"({tile.x}, {tile.y})"
        )

    def place_artillery(
        self,
        tile,
        economy
    ):
        """
        Build artillery.
        """

        if not economy.spend(
            ARTILLERY_COST
        ):

            print(
                "Not enough supplies."
            )

            return

        tile.building = Artillery(
            tile
        )

        print(
            f"Artillery built at "
            f"({tile.x}, {tile.y})"
        )