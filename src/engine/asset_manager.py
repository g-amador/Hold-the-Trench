"""
engine/asset_manager.py

Centralized asset loading and caching
for Hold the Trench.
"""

import os
import pygame


class AssetManager:
    """
    Handles loading and caching
    of images, sounds, music,
    and fonts.
    """

    def __init__(self):

        #
        # Asset caches
        #
        self.images = {}

        self.sounds = {}

        self.fonts = {}

    #
    # Images
    #

    def load_image(
        self,
        path,
        convert_alpha=True
    ):
        """
        Load image and cache it.
        """

        if path in self.images:

            return self.images[path]

        try:

            image = pygame.image.load(
                path
            )

            if convert_alpha:

                image = (
                    image.convert_alpha()
                )

            else:

                image = (
                    image.convert()
                )

            self.images[path] = image

            return image

        except Exception as e:

            print(
                f"Image load failed: "
                f"{path}"
            )

            print(e)

            return None

    #
    # Sounds
    #

    def load_sound(
        self,
        path
    ):
        """
        Load sound and cache it.
        """

        if path in self.sounds:

            return self.sounds[path]

        try:

            sound = pygame.mixer.Sound(
                path
            )

            self.sounds[path] = sound

            return sound

        except Exception as e:

            print(
                f"Sound load failed: "
                f"{path}"
            )

            print(e)

            return None

    #
    # Music
    #

    def play_music(
        self,
        path,
        loops=-1
    ):
        """
        Play music.
        """

        try:

            pygame.mixer.music.load(
                path
            )

            pygame.mixer.music.play(
                loops
            )

        except Exception as e:

            print(
                f"Music load failed: "
                f"{path}"
            )

            print(e)

    def stop_music(
        self
    ):
        """
        Stop music.
        """

        pygame.mixer.music.stop()

    #
    # Fonts
    #

    def get_font(
        self,
        name,
        size
    ):
        """
        Get cached font.
        """

        key = (
            name,
            size
        )

        if key in self.fonts:

            return self.fonts[key]

        try:

            if name is None:

                font = (
                    pygame.font.SysFont(
                        "Arial",
                        size
                    )
                )

            else:

                font = pygame.font.Font(
                    name,
                    size
                )

            self.fonts[key] = font

            return font

        except Exception:

            font = pygame.font.SysFont(
                "Arial",
                size
            )

            self.fonts[key] = font

            return font

    #
    # Utility
    #

    def unload_all(
        self
    ):
        """
        Clear caches.
        """

        self.images.clear()

        self.sounds.clear()

        self.fonts.clear()

    def asset_exists(
        self,
        path
    ):
        """
        Check asset existence.
        """

        return os.path.exists(
            path
        )