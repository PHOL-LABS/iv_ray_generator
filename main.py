import argparse

from src.runner import GameRun


def parse_args():
    parser = argparse.ArgumentParser(description="PyPacman with optional streaming.")
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable grayscale streaming server/serial output.",
    )
    parser.add_argument(
        "--stream-port",
        type=int,
        default=None,
        help="TCP port to serve grayscale stream.",
    )
    parser.add_argument(
        "--stream-serial",
        type=str,
        default=None,
        help="Serial port path to write grayscale stream (e.g., COM3, /dev/ttyUSB0).",
    )
    parser.add_argument(
        "--stream-serial-baud",
        type=int,
        default=115200,
        help="Baudrate for serial grayscale stream (default: 115200).",
    )
    parser.add_argument(
        "--bw-stream",
        action="store_true",
        help="Send stream in black/white mode (only set-pixel runs).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    gr = GameRun(
        enable_stream=args.stream,
        stream_port=args.stream_port,
        stream_serial=args.stream_serial,
        stream_serial_baud=args.stream_serial_baud,
        bw_mode=args.bw_stream,
    )
    gr.main()
