#!/usr/bin/env python3
"""
Binary Protocol Generator for RF Configuration

Creates a compact binary file format for efficient storage and transmission.
"""

import struct
from enum import IntEnum


class DeviceMode(IntEnum):
    """Device mode enumeration"""
    RECEIVE = 0x00
    TRANSMIT = 0x01


class StreamingProtocol(IntEnum):
    """Streaming protocol enumeration"""
    UART = 0x00
    I2C = 0x01
    SPI = 0x02
    FILE = 0x03


class Modulation(IntEnum):
    """Modulation scheme enumeration"""
    BPSK = 0x00
    QPSK = 0x01
    FSK = 0x02


# Binary protocol constants
PROTOCOL_VERSION = 0x01
MAGIC_BYTES = b'RFCF'  # RF Config File


def encode_config_binary(config):
    """
    Encode configuration into compact binary format.
    
    Binary Format (Total: 32 bytes):
    ┌─────────────────────────────────────────────────────────────┐
    │ Offset │ Size │ Type    │ Field                            │
    ├─────────────────────────────────────────────────────────────┤
    │ 0x00   │ 4    │ char[4] │ Magic bytes "RFCF"               │
    │ 0x04   │ 1    │ uint8   │ Protocol version                 │
    │ 0x05   │ 1    │ uint8   │ Device mode (0=RX, 1=TX)        │
    │ 0x06   │ 1    │ uint8   │ Streaming protocol               │
    │ 0x07   │ 1    │ uint8   │ Modulation scheme                │
    │ 0x08   │ 8    │ uint64  │ Carrier frequency (Hz)           │
    │ 0x10   │ 4    │ uint32  │ Sampling frequency (Hz)          │
    │ 0x14   │ 2    │ uint16  │ RF Gain (dB * 10)               │
    │ 0x16   │ 2    │ uint16  │ IF Gain (dB * 10)               │
    │ 0x18   │ 2    │ uint16  │ Baseband Gain (dB * 10)         │
    │ 0x1A   │ 2    │ uint16  │ Reserved                         │
    │ 0x1C   │ 4    │ uint32  │ CRC32 checksum                   │
    └─────────────────────────────────────────────────────────────┘
    
    All multi-byte values are big-endian (network byte order).
    Gains are stored as integers (dB * 10) for precision.
    """
    
    # Parse device mode
    device_mode_str = config.get('deviceMode', 'receive').lower()
    device_mode = DeviceMode.TRANSMIT if device_mode_str == 'transmit' else DeviceMode.RECEIVE
    
    # Parse streaming protocol
    protocol_str = config.get('streamingProtocol', 'uart').lower()
    protocol_map = {
        'uart': StreamingProtocol.UART,
        'i2c': StreamingProtocol.I2C,
        'spi': StreamingProtocol.SPI,
        'file': StreamingProtocol.FILE
    }
    streaming_protocol = protocol_map.get(protocol_str, StreamingProtocol.UART)
    
    # Parse modulation
    modulation_str = config.get('modulation', 'QPSK').upper()
    modulation_map = {
        'BPSK': Modulation.BPSK,
        'QPSK': Modulation.QPSK,
        'FSK': Modulation.FSK
    }
    modulation = modulation_map.get(modulation_str, Modulation.QPSK)
    
    # Parse RF parameters
    carrier_freq = int(config.get('fc', 0))
    sampling_freq = int(config.get('fs', 0))
    rf_gain = int(float(config.get('rfg', 0)) * 10)  # Convert to dB * 10
    if_gain = int(float(config.get('ifg', 0)) * 10)
    bb_gain = int(float(config.get('bbg', 0)) * 10)
    
    # Build binary data (without CRC first)
    binary_data = bytearray()
    
    # Magic bytes
    binary_data.extend(MAGIC_BYTES)
    
    # Version and configuration
    binary_data.extend(struct.pack('>B', PROTOCOL_VERSION))  # Version
    binary_data.extend(struct.pack('>B', device_mode))       # Device mode
    binary_data.extend(struct.pack('>B', streaming_protocol)) # Protocol
    binary_data.extend(struct.pack('>B', modulation))        # Modulation
    
    # Frequencies and gains
    binary_data.extend(struct.pack('>Q', carrier_freq))      # 64-bit carrier freq
    binary_data.extend(struct.pack('>I', sampling_freq))     # 32-bit sampling freq
    binary_data.extend(struct.pack('>H', rf_gain))           # 16-bit RF gain
    binary_data.extend(struct.pack('>H', if_gain))           # 16-bit IF gain
    binary_data.extend(struct.pack('>H', bb_gain))           # 16-bit BB gain
    
    # Reserved bytes
    binary_data.extend(struct.pack('>H', 0x0000))            # Reserved
    
    # Calculate CRC32
    import zlib
    crc = zlib.crc32(binary_data) & 0xFFFFFFFF
    binary_data.extend(struct.pack('>I', crc))               # CRC32
    
    return bytes(binary_data)


def decode_config_binary(binary_data):
    """
    Decode binary configuration file.
    
    Returns:
        dict: Parsed configuration
    """
    if len(binary_data) != 32:
        raise ValueError(f"Invalid binary size: {len(binary_data)} bytes (expected 32)")
    
    # Verify magic bytes
    magic = binary_data[0:4]
    if magic != MAGIC_BYTES:
        raise ValueError(f"Invalid magic bytes: {magic}")
    
    # Verify CRC
    data_without_crc = binary_data[0:28]
    stored_crc = struct.unpack('>I', binary_data[28:32])[0]
    
    import zlib
    calculated_crc = zlib.crc32(data_without_crc) & 0xFFFFFFFF
    
    if stored_crc != calculated_crc:
        raise ValueError(f"CRC mismatch: stored=0x{stored_crc:08X}, calculated=0x{calculated_crc:08X}")
    
    # Parse fields
    version = struct.unpack('>B', binary_data[4:5])[0]
    device_mode = struct.unpack('>B', binary_data[5:6])[0]
    streaming_protocol = struct.unpack('>B', binary_data[6:7])[0]
    modulation = struct.unpack('>B', binary_data[7:8])[0]
    carrier_freq = struct.unpack('>Q', binary_data[8:16])[0]
    sampling_freq = struct.unpack('>I', binary_data[16:20])[0]
    rf_gain = struct.unpack('>H', binary_data[20:22])[0] / 10.0
    if_gain = struct.unpack('>H', binary_data[22:24])[0] / 10.0
    bb_gain = struct.unpack('>H', binary_data[24:26])[0] / 10.0
    
    # Convert enums to strings
    device_mode_str = 'transmit' if device_mode == DeviceMode.TRANSMIT else 'receive'
    
    protocol_map = {
        StreamingProtocol.UART: 'uart',
        StreamingProtocol.I2C: 'i2c',
        StreamingProtocol.SPI: 'spi',
        StreamingProtocol.FILE: 'file'
    }
    protocol_str = protocol_map.get(streaming_protocol, 'uart')
    
    modulation_map = {
        Modulation.BPSK: 'BPSK',
        Modulation.QPSK: 'QPSK',
        Modulation.FSK: 'FSK'
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
        'crc': f"0x{stored_crc:08X}"
    }


def format_binary_hex(binary_data, bytes_per_line=16):
    """Format binary data as hex dump for display"""
    lines = []
    for i in range(0, len(binary_data), bytes_per_line):
        chunk = binary_data[i:i+bytes_per_line]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"{i:04X}  {hex_part:<{bytes_per_line*3}}  {ascii_part}")
    return '\n'.join(lines)


if __name__ == '__main__':
    # Test encoding/decoding
    test_config = {
        'deviceMode': 'transmit',
        'streamingProtocol': 'uart',
        'modulation': 'QPSK',
        'fc': 915000000,
        'fs': 2000000,
        'rfg': 14.5,
        'ifg': 20.0,
        'bbg': 30.5
    }
    
    print("Encoding test configuration...")
    binary = encode_config_binary(test_config)
    
    print(f"\nBinary size: {len(binary)} bytes")
    print("\nHex dump:")
    print(format_binary_hex(binary))
    
    print("\nDecoding binary...")
    decoded = decode_config_binary(binary)
    
    print("\nDecoded configuration:")
    import json
    print(json.dumps(decoded, indent=2))
