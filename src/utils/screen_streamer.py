import os
import socket
import struct
import threading
import queue
import time
from typing import List, Tuple, Optional

import pygame

try:
    import serial  # type: ignore
except ImportError:  # pragma: no cover - handled at runtime
    serial = None


class ScreenStreamer:
    """
    Encode pygame surfaces to grayscale and stream them over TCP and/or a raw
    serial file, plus decode incoming frames back into pygame surfaces.
    The protocol is documented in STREAMING_PROTOCOL.md.
    """

    START_BYTE = 0xA5
    MAGIC = b"IVG"
    VERSION = 1
    HEADER_STRUCT = struct.Struct("<B3sB I H H I")
    RUN_STRUCT = struct.Struct("<I B H")
    HEADER_SIZE = HEADER_STRUCT.size
    RUN_SIZE = RUN_STRUCT.size
    START_SEQ = bytes([START_BYTE]) + MAGIC

    def __init__(
        self,
        width: int,
        height: int,
        tcp_port: Optional[int] = None,
        serial_path: Optional[str] = None,
        serial_baud: int = 115200,
    ):
        self.width = width
        self.height = height
        self.tcp_port = tcp_port
        self.serial_path = serial_path
        self.serial_baud = serial_baud
        self.frame_id = 0
        self._stop_event = threading.Event()
        self._accept_thread = None
        self._listener = None
        self._clients: List[socket.socket] = []
        self._clients_lock = threading.Lock()
        self._serial = None

    def start(self):
        if self.tcp_port:
            self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._listener.bind(("0.0.0.0", self.tcp_port))
            self._listener.listen(5)
            self._accept_thread = threading.Thread(
                target=self._accept_loop, daemon=True
            )
            self._accept_thread.start()
        if self.serial_path:
            if serial is None:
                raise RuntimeError("pyserial is required for serial streaming")
            # Non-blocking serial writer.
            self._serial = serial.Serial(
                self.serial_path, baudrate=self.serial_baud, timeout=0
            )

    def stop(self):
        self._stop_event.set()
        if self._listener:
            try:
                self._listener.close()
            except OSError:
                pass
        if self._accept_thread:
            self._accept_thread.join(timeout=1)
        with self._clients_lock:
            for client in self._clients:
                try:
                    client.close()
                except OSError:
                    pass
            self._clients.clear()
        if self._serial:
            try:
                self._serial.close()
            except OSError:
                pass

    def _accept_loop(self):
        while not self._stop_event.is_set():
            try:
                self._listener.settimeout(1.0)
                conn, _addr = self._listener.accept()
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                with self._clients_lock:
                    self._clients.append(conn)
            except socket.timeout:
                continue
            except OSError:
                break

    def _broadcast(self, data: bytes):
        stale: List[socket.socket] = []
        with self._clients_lock:
            for client in self._clients:
                try:
                    client.sendall(data)
                except OSError:
                    stale.append(client)
            for dead in stale:
                try:
                    dead.close()
                except OSError:
                    pass
                if dead in self._clients:
                    self._clients.remove(dead)
        if self._serial:
            try:
                self._serial.write(data)
            except OSError:
                pass

    def send_surface(self, surface: pygame.Surface):
        packet = self.encode_surface(surface)
        self._broadcast(packet)

    def encode_surface(self, surface: pygame.Surface) -> bytes:
        rgb_bytes = pygame.image.tostring(surface, "RGB")
        gray_values = self._rgb_to_gray(rgb_bytes)
        payload = self._encode_runs(gray_values)
        header = self.HEADER_STRUCT.pack(
            self.START_BYTE,
            self.MAGIC,
            self.VERSION,
            self.frame_id,
            self.width,
            self.height,
            len(payload),
        )
        self.frame_id = (self.frame_id + 1) & 0xFFFFFFFF
        return header + payload

    def _encode_runs(self, gray_values: bytes) -> bytes:
        payload = bytearray()
        total = len(gray_values)
        idx = 0
        while idx < total:
            current = gray_values[idx]
            run_len = 1
            limit = min(total - idx, 65535)
            while run_len < limit and gray_values[idx + run_len] == current:
                run_len += 1
            payload += self.RUN_STRUCT.pack(idx, current, run_len)
            idx += run_len
        return bytes(payload)

    @staticmethod
    def _rgb_to_gray(rgb_bytes: bytes) -> bytes:
        gray = bytearray(len(rgb_bytes) // 3)
        gi = 0
        for i in range(0, len(rgb_bytes), 3):
            r = rgb_bytes[i]
            g = rgb_bytes[i + 1]
            b = rgb_bytes[i + 2]
            gray[gi] = int(0.299 * r + 0.587 * g + 0.114 * b)
            gi += 1
        return bytes(gray)

    @classmethod
    def extract_frames(cls, buffer: bytes) -> Tuple[List[Tuple[int, int, int, bytes]], bytes]:
        """
        Extract complete frames from a byte buffer. Returns (frames, remainder).
        Each frame tuple: (frame_id, width, height, grayscale_bytes).
        """
        frames: List[Tuple[int, int, int, bytes]] = []
        search_from = 0
        while True:
            start_idx = buffer.find(cls.START_SEQ, search_from)
            if start_idx == -1:
                # Keep a small tail to handle split markers.
                tail = buffer[-3:] if len(buffer) > 3 else buffer
                return frames, tail
            if len(buffer) < start_idx + cls.HEADER_SIZE:
                return frames, buffer[start_idx:]
            header_chunk = buffer[start_idx:start_idx + cls.HEADER_SIZE]
            try:
                (
                    start_byte,
                    magic,
                    version,
                    frame_id,
                    width,
                    height,
                    payload_len,
                ) = cls.HEADER_STRUCT.unpack(header_chunk)
            except struct.error:
                search_from = start_idx + 1
                continue
            if start_byte != cls.START_BYTE or magic != cls.MAGIC:
                search_from = start_idx + 1
                continue
            total_len = cls.HEADER_SIZE + payload_len
            if len(buffer) < start_idx + total_len:
                return frames, buffer[start_idx:]
            payload = buffer[start_idx + cls.HEADER_SIZE:start_idx + total_len]
            gray = cls._decode_payload(payload, width * height)
            frames.append((frame_id, width, height, gray))
            buffer = buffer[start_idx + total_len :]
            search_from = 0

    @classmethod
    def _decode_payload(cls, payload: bytes, pixel_count: int) -> bytes:
        gray = bytearray(pixel_count)
        for i in range(0, len(payload), cls.RUN_SIZE):
            chunk = payload[i : i + cls.RUN_SIZE]
            if len(chunk) < cls.RUN_SIZE:
                break
            offset, gval, run_len = cls.RUN_STRUCT.unpack(chunk)
            end = min(offset + run_len, pixel_count)
            if offset >= pixel_count or offset >= end:
                continue
            gray[offset:end] = bytes([gval]) * (end - offset)
        return bytes(gray)

    @staticmethod
    def gray_to_surface(gray: bytes, width: int, height: int) -> pygame.Surface:
        rgb = bytearray()
        for g in gray:
            rgb.extend((g, g, g))
        return pygame.image.frombuffer(bytes(rgb), (width, height), "RGB")


class StreamClient:
    """
    Simple client that reads frames from a TCP socket or serial file and yields
    decoded surfaces.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        serial_path: Optional[str] = None,
        serial_baud: int = 115200,
    ):
        if not port and not serial_path:
            raise ValueError("Either port or serial_path is required")
        self.host = host or "127.0.0.1"
        self.port = port
        self.serial_path = serial_path
        self.serial_baud = serial_baud
        self._conn = None
        self._buffer = b""
        self._queue: "queue.Queue[bytes]" = queue.Queue()
        self._reader_thread = None
        self._stop_event = threading.Event()

    def start(self):
        if self.port:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._conn = sock
        else:
            if serial is None:
                raise RuntimeError("pyserial is required for serial streaming")
            self._conn = serial.Serial(
                self.serial_path, baudrate=self.serial_baud, timeout=0
            )
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def stop(self):
        self._stop_event.set()
        if self._reader_thread:
            self._reader_thread.join(timeout=1)
        if self._conn:
            try:
                self._conn.close()
            except OSError:
                pass

    def _reader_loop(self):
        while not self._stop_event.is_set():
            try:
                if isinstance(self._conn, socket.socket):
                    chunk = self._conn.recv(4096)
                else:
                    chunk = self._conn.read(4096)
                if not chunk:
                    time.sleep(0.01)
                    continue
                self._queue.put(chunk)
            except (BlockingIOError, InterruptedError):
                time.sleep(0.01)
            except OSError:
                break

    def poll_frames(self) -> List[Tuple[int, int, int, pygame.Surface]]:
        frames: List[Tuple[int, int, int, pygame.Surface]] = []
        while not self._queue.empty():
            chunk = self._queue.get()
            self._buffer += chunk
        if not self._buffer:
            return frames
        decoded, self._buffer = ScreenStreamer.extract_frames(self._buffer)
        for frame_id, width, height, gray in decoded:
            surface = ScreenStreamer.gray_to_surface(gray, width, height)
            frames.append((frame_id, width, height, surface))
        return frames
