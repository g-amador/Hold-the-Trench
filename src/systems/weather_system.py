"""
systems/weather_system.py

Weather effects for Hold the Trench.
"""

import random
import pygame


class WeatherSystem:
    """
    Controls battlefield weather.
    """

    WEATHER_TYPES = [

        "clear",

        "fog",

        "rain"

    ]

    def __init__(
        self,
        weather=None
    ):

        #
        # Current weather
        #
        self.weather = (
            weather
            if weather is not None
            else random.choice(
                self.WEATHER_TYPES
            )
        )

        #
        # Gameplay modifiers
        #
        self.visibility_multiplier = 1.0

        self.accuracy_multiplier = 1.0

        #
        # Configure weather
        #
        self.configure()

    def configure(
        self
    ):
        """
        Configure weather effects.
        """

        if self.weather == "clear":

            self.visibility_multiplier = 1.0

            self.accuracy_multiplier = 1.0

        elif self.weather == "fog":

            self.visibility_multiplier = 0.60

            self.accuracy_multiplier = 0.80

        elif self.weather == "rain":

            self.visibility_multiplier = 0.75

            self.accuracy_multiplier = 0.85

    def affects_range(
        self,
        base_range
    ):
        """
        Return modified range.
        """

        return int(
            base_range *
            self.visibility_multiplier
        )

    def affects_accuracy(
        self,
        base_accuracy
    ):
        """
        Return modified accuracy.
        """

        return (
            base_accuracy *
            self.accuracy_multiplier
        )

    def update(
        self,
        delta_time
    ):
        """
        Future weather animation hook.
        """

        pass

    def draw_overlay(
        self,
        screen
    ):
        """
        Draw weather effects.
        """

        if self.weather == "clear":
            return

        overlay = pygame.Surface(
            screen.get_size()
        )

        #
        # Fog
        #
        if self.weather == "fog":

            overlay.set_alpha(
                90
            )

            overlay.fill(
                (
                    180,
                    180,
                    180
                )
            )

        #
        # Rain
        #
        elif self.weather == "rain":

            overlay.set_alpha(
                50
            )

            overlay.fill(
                (
                    60,
                    60,
                    80
                )
            )

        screen.blit(
            overlay,
            (0, 0)
        )

    def get_description(
        self
    ):
        """
        Weather text.
        """

        descriptions = {

            "clear":
                "Clear skies",

            "fog":
                "Heavy fog",

            "rain":
                "Rainstorm"

        }

        return descriptions.get(
            self.weather,
            "Unknown"
        )