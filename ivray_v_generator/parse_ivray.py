#!/usr/bin/env python3
"""Utility to convert ivray vector tables to XML."""

import argparse
import struct
import sys
import xml.etree.ElementTree as ET


HEADER_STRUCT = struct.Struct("<4sIff")
VECTOR_COUNT_STRUCT = struct.Struct("<I")
VECTOR_STRUCT = struct.Struct("<hh")


def read_header(handle):
    data = handle.read(HEADER_STRUCT.size)
    if len(data) != HEADER_STRUCT.size:
        raise ValueError("File is too small to contain a valid header.")

    magic, frame_count, brightness, speed = HEADER_STRUCT.unpack(data)

    if magic != b"IVRY":
        raise ValueError("Invalid magic bytes. Not an IVRay file.")

    return frame_count, brightness, speed


def read_frames(handle, frame_count):
    frames = []

    for index in range(frame_count):
        count_data = handle.read(VECTOR_COUNT_STRUCT.size)
        if len(count_data) != VECTOR_COUNT_STRUCT.size:
            raise ValueError(f"Unexpected end of file while reading frame {index}.")

        (vector_count,) = VECTOR_COUNT_STRUCT.unpack(count_data)

        vectors_data = handle.read(VECTOR_STRUCT.size * vector_count)
        if len(vectors_data) != VECTOR_STRUCT.size * vector_count:
            raise ValueError(f"Unexpected end of file while reading vectors for frame {index}.")

        vectors = [VECTOR_STRUCT.unpack_from(vectors_data, offset)
                   for offset in range(0, len(vectors_data), VECTOR_STRUCT.size)]
        frames.append(vectors)

    return frames


def build_xml(frames, brightness, speed, start_frame, end_frame):
    root = ET.Element(
        "ivray",
        brightness=f"{brightness:.6f}",
        speed=f"{speed:.6f}",
        frame_count=str(len(frames)),
    )

    current_x = 0
    current_y = 0

    for index, vectors in enumerate(frames):
        in_range = start_frame <= index <= end_frame

        frame_element = None
        if in_range:
            frame_element = ET.SubElement(root, "frame", index=str(index), vectors=str(len(vectors)))

        for dx, dy in vectors:
            current_x += dx
            current_y += dy

            if frame_element is not None:
                ET.SubElement(
                    frame_element,
                    "vector",
                    dx=str(dx),
                    dy=str(dy),
                    x=str(current_x),
                    y=str(current_y),
                )

    if hasattr(ET, "indent"):
        ET.indent(root)

    return ET.ElementTree(root)


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path to the ivray file.")
    parser.add_argument("output", help="Path to the XML file to create.")
    parser.add_argument("--start", type=int, default=0, help="First frame index to include (default: 0).")
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="Last frame index to include (default: last frame in the file).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])

    with open(args.input, "rb") as handle:
        frame_count, brightness, speed = read_header(handle)
        frames = read_frames(handle, frame_count)

    end_frame = frame_count - 1 if args.end is None else args.end

    if args.start < 0 or args.start >= frame_count:
        raise SystemExit(f"Start frame {args.start} is out of range (0-{frame_count - 1}).")

    if end_frame < args.start:
        raise SystemExit("End frame must be greater than or equal to start frame.")

    if end_frame >= frame_count:
        raise SystemExit(f"End frame {end_frame} is out of range (0-{frame_count - 1}).")

    tree = build_xml(frames, brightness, speed, args.start, end_frame)
    tree.write(args.output, xml_declaration=True, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
