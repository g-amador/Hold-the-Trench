"""
engine/renderer.py

Central rendering system.
"""

import pygame


class Renderer:
    """
    Handles game rendering.
    """

    def draw_tilemap(
        self,
        screen,
        tilemap
    ):
        tilemap.draw(screen)

    def draw_enemies(
        self,
        screen,
        enemies
    ):
        for enemy in enemies:

            enemy.draw(
                screen
            )

    def draw_buildings(
        self,
        screen,
        buildings
    ):
        for building in buildings:

            building.draw(
                screen
            )

    def draw_text(
        self,
        screen,
        font,
        text,
        x,
        y,
        color
    ):

        surface = font.render(
            text,
            True,
            color
        )

        screen.blit(
            surface,
            (x, y)
        )

    def draw_pause_overlay(
        self,
        screen,
        width,
        height
    ):

        overlay = pygame.Surface(
            (
                width,
                height
            )
        )

        overlay.set_alpha(
            180
        )

        overlay.fill(
            (30, 30, 30)
        )

        screen.blit(
            overlay,
            (0, 0)
        )

    def draw_centered_text(
        self,
        screen,
        font,
        text,
        y,
        color
    ):

        surface = font.render(
            text,
            True,
            color
        )

        screen.blit(
            surface,
            (
                screen.get_width() // 2
                - surface.get_width() // 2,
                y
            )
        )