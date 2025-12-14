import argparse
import pygame

from src.utils.screen_streamer import StreamClient


def main():
    parser = argparse.ArgumentParser(
        description="Viewer for grayscale stream over TCP or serial."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--serial", help="Serial port path (e.g., COM3 or /dev/ttyUSB0)")
    args = parser.parse_args()

    client = StreamClient(host=args.host, port=args.port, serial_path=args.serial)
    client.start()

    pygame.init()
    screen = None
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        frames = client.poll_frames()
        for _frame_id, width, height, surface in frames:
            if screen is None:
                screen = pygame.display.set_mode((width, height))
            screen.blit(surface, (0, 0))
            pygame.display.flip()
        clock.tick(60)

    client.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
