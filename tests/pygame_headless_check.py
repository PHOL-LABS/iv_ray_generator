"""Headless pygame smoke test.

This script ensures pygame can initialize and create a window using
the dummy SDL video driver so CI runners without a real display can
still execute the project.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame


def main():
    pygame.init()
    try:
        display = pygame.display.set_mode((64, 64))
        if display is None:
            raise RuntimeError("Pygame display surface was not created.")

        pygame.display.set_caption("CI Smoke Test")
        display.fill((0, 0, 0))
        pygame.display.flip()
        pygame.event.pump()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
