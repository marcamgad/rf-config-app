#!/usr/bin/env python3
"""
NanoPi UART Driver - RF Configuration Receiver

Receives encapsulated configuration packets over UART and decodes
the embedded HackRF configuration binary payload.

Packet format (from uart_sender.py):
[START][VERSION][LEN_H][LEN_L][PAYLOAD][CHECKSUM][END]
  START   = 0xAA
  END     = 0x55
  VERSION = 0x01
  LENGTH  = big-endian uint16
  CHECKSUM = sum(payload) & 0xFF

Payload format (from binary_protocol.py):
32 bytes with magic "RFCF" and CRC32.
"""

import argparse
import json
import struct
import sys
import time
from enum import IntEnum

import serial


START_BYTE = 0xAA
END_BYTE = 0x55
PACKET_VERSION = 0x01
PROTOCOL_VERSION = 0x01
MAGIC_BYTES = b'RFCF'


class DeviceMode(IntEnum):
    RECEIVE = 0x00
    TRANSMIT = 0x01


class StreamingProtocol(IntEnum):
    UART = 0x00
    I2C = 0x01
    SPI = 0x02
    FILE = 0x03


class Modulation(IntEnum):
    BPSK = 0x00
    QPSK = 0x01
    FSK = 0x02


def calculate_checksum(data: bytes) -> int:
    return sum(data) & 0xFF


class PacketParseError(Exception):
    pass


def read_exact(ser: serial.Serial, size: int, timeout_s: float = 2.0) -> bytes:
    """Read exactly size bytes or raise PacketParseError on timeout."""
    deadline = time.time() + timeout_s
    buf = bytearray()
    while len(buf) < size:
        if time.time() > deadline:
            raise PacketParseError(f"Timeout while reading {size} bytes")
        chunk = ser.read(size - len(buf))
        if chunk:
            buf.extend(chunk)
    return bytes(buf)


def find_start_byte(ser: serial.Serial, timeout_s: float = 2.0) -> None:
    """Consume bytes until START_BYTE is found or timeout."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        b = ser.read(1)
        if not b:
            continue
        if b[0] == START_BYTE:
            return
    raise PacketParseError("Timeout waiting for START_BYTE")


def read_packet(ser: serial.Serial, timeout_s: float = 2.0) -> bytes:
    """Read a single encapsulated packet and return payload bytes."""
    find_start_byte(ser, timeout_s=timeout_s)

    header = read_exact(ser, 3, timeout_s=timeout_s)
    version = header[0]
    if version != PACKET_VERSION:
        raise PacketParseError(f"Unsupported packet version: {version}")

    length = struct.unpack('>H', header[1:3])[0]
    payload = read_exact(ser, length, timeout_s=timeout_s)
    checksum = read_exact(ser, 1, timeout_s=timeout_s)[0]
    end = read_exact(ser, 1, timeout_s=timeout_s)[0]

    if end != END_BYTE:
        raise PacketParseError(f"Invalid END_BYTE: 0x{end:02X}")

    calculated = calculate_checksum(payload)
    if checksum != calculated:
        raise PacketParseError(
            f"Checksum mismatch: stored=0x{checksum:02X}, calculated=0x{calculated:02X}"
        )

    return payload


def decode_payload(payload: bytes) -> dict:
    """Decode payload using binary_protocol and return parsed config dict."""
    return decode_config_binary(payload)


def decode_config_binary(binary_data: bytes) -> dict:
    if len(binary_data) != 32:
        raise ValueError(f"Invalid binary size: {len(binary_data)} bytes (expected 32)")

    magic = binary_data[0:4]
    if magic != MAGIC_BYTES:
        raise ValueError(f"Invalid magic bytes: {magic}")

    data_without_crc = binary_data[0:28]
    stored_crc = struct.unpack('>I', binary_data[28:32])[0]

    import zlib

    calculated_crc = zlib.crc32(data_without_crc) & 0xFFFFFFFF
    if stored_crc != calculated_crc:
        raise ValueError(
            f"CRC mismatch: stored=0x{stored_crc:08X}, calculated=0x{calculated_crc:08X}"
        )

    version = struct.unpack('>B', binary_data[4:5])[0]
    device_mode = struct.unpack('>B', binary_data[5:6])[0]
    streaming_protocol = struct.unpack('>B', binary_data[6:7])[0]
    modulation = struct.unpack('>B', binary_data[7:8])[0]
    carrier_freq = struct.unpack('>Q', binary_data[8:16])[0]
    sampling_freq = struct.unpack('>I', binary_data[16:20])[0]
    rf_gain = struct.unpack('>H', binary_data[20:22])[0] / 10.0
    if_gain = struct.unpack('>H', binary_data[22:24])[0] / 10.0
    bb_gain = struct.unpack('>H', binary_data[24:26])[0] / 10.0

    device_mode_str = 'transmit' if device_mode == DeviceMode.TRANSMIT else 'receive'
    protocol_map = {
        StreamingProtocol.UART: 'uart',
        StreamingProtocol.I2C: 'i2c',
        StreamingProtocol.SPI: 'spi',
        StreamingProtocol.FILE: 'file',
    }
    protocol_str = protocol_map.get(streaming_protocol, 'uart')

    modulation_map = {
        Modulation.BPSK: 'BPSK',
        Modulation.QPSK: 'QPSK',
        Modulation.FSK: 'FSK',
    }
    modulation_str = modulation_map.get(modulation, 'QPSK')

    return {
        'version': version,
        'device_mode': device_mode_str,
        'streaming_protocol': protocol_str,
        'modulation': modulation_str,
        'carrier_frequency_hz': carrier_freq,
        'sampling_frequency_hz': sampling_freq,
        'rf_gain_db': rf_gain,
        'if_gain_db': if_gain,
        'baseband_gain_db': bb_gain,
        'crc': f"0x{stored_crc:08X}",
    }


def run_receiver(port: str, baudrate: int, once: bool, timeout_s: float) -> None:
    print("=" * 60)
    print("NanoPi UART RF Configuration Receiver")
    print("=" * 60)
    print(f"Port: {port} @ {baudrate} baud")
    print("Waiting for packets...")

    with serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.2,
    ) as ser:
        while True:
            try:
                payload = read_packet(ser, timeout_s=timeout_s)
                decoded = decode_payload(payload)
                print("\n[*] Packet received and decoded:")
                print(json.dumps(decoded, indent=2))

                if once:
                    return
            except PacketParseError as e:
                # Non-fatal: keep listening
                print(f"[!] Packet parse error: {e}")
                if once:
                    return
            except Exception as e:
                print(f"[X] Unexpected error: {e}")
                if once:
                    return


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NanoPi UART driver to receive and decode RF configuration packets"
    )
    parser.add_argument(
        "-p",
        "--port",
        required=True,
        help="Serial port (e.g., /dev/ttyS1, /dev/ttyUSB0)",
    )
    parser.add_argument(
        "-b",
        "--baudrate",
        type=int,
        default=115200,
        help="Baud rate (default: 115200)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Receive only one packet then exit",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Packet read timeout in seconds (default: 2.0)",
    )

    args = parser.parse_args()

    try:
        run_receiver(args.port, args.baudrate, args.once, args.timeout)
    except KeyboardInterrupt:
        print("\n[!] Receiver stopped by user")
        sys.exit(1)


if __name__ == "__main__":
    main()