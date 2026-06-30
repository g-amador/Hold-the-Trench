"""
systems/save_system.py

Save/load functionality for Hold the Trench.
"""

import json
import os
from datetime import datetime


class SaveSystem:
    """
    Handles saving and loading
    campaign progress.
    """

    SAVE_DIRECTORY = "saves"

    SAVE_FILE = "campaign.json"

    def __init__(self):

        #
        # Ensure save directory exists
        #
        os.makedirs(
            self.SAVE_DIRECTORY,
            exist_ok=True
        )

    def get_save_path(
        self
    ):
        """
        Return full save path.
        """

        return os.path.join(
            self.SAVE_DIRECTORY,
            self.SAVE_FILE
        )

    def save_campaign(
        self,
        progression
    ):
        """
        Save campaign progress.
        """

        data = {

            "scenario_number":
                progression.scenario_number,

            "difficulty_multiplier":
                progression.difficulty_multiplier,

            "victories":
                progression.victories,

            "total_kills":
                progression.total_kills,

            "total_supplies":
                progression.total_supplies,

            "saved_at":
                datetime.now().isoformat()

        }

        try:

            with open(
                self.get_save_path(),
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=4
                )

            print(
                "Campaign saved."
            )

            return True

        except Exception as e:

            print(
                "Save failed:"
            )

            print(e)

            return False

    def load_campaign(
        self,
        progression
    ):
        """
        Load campaign progress.
        """

        path = self.get_save_path()

        if not os.path.exists(
            path
        ):

            return False

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

            progression.scenario_number = (
                data.get(
                    "scenario_number",
                    1
                )
            )

            progression.difficulty_multiplier = (
                data.get(
                    "difficulty_multiplier",
                    1.0
                )
            )

            progression.victories = (
                data.get(
                    "victories",
                    0
                )
            )

            progression.total_kills = (
                data.get(
                    "total_kills",
                    0
                )
            )

            progression.total_supplies = (
                data.get(
                    "total_supplies",
                    0
                )
            )

            print(
                "Campaign loaded."
            )

            return True

        except Exception as e:

            print(
                "Load failed:"
            )

            print(e)

            return False

    def delete_save(
        self
    ):
        """
        Delete save file.
        """

        path = self.get_save_path()

        try:

            if os.path.exists(
                path
            ):

                os.remove(
                    path
                )

                print(
                    "Save deleted."
                )

            return True

        except Exception as e:

            print(
                "Delete failed:"
            )

            print(e)

            return False

    def save_exists(
        self
    ):
        """
        Check if save exists.
        """

        return os.path.exists(
            self.get_save_path()
        )

    def get_save_info(
        self
    ):
        """
        Read save metadata.
        """

        if not self.save_exists():

            return None

        try:

            with open(
                self.get_save_path(),
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

            return {

                "scenario":
                    data.get(
                        "scenario_number",
                        1
                    ),

                "victories":
                    data.get(
                        "victories",
                        0
                    ),

                "saved_at":
                    data.get(
                        "saved_at",
                        "Unknown"
                    )

            }

        except Exception:

            return None