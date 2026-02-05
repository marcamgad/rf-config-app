#!/usr/bin/env python3
"""
UART Configuration Sender for Host PC
Sends encapsulated configuration packets to Single Board Computer via UART
"""

import serial
import struct
import time
import json
import argparse
import sys
from pathlib import Path

# Packet structure constants
START_BYTE = 0xAA
END_BYTE = 0x55
PACKET_VERSION = 0x01


def calculate_checksum(data):
    """Calculate simple checksum (sum of all bytes mod 256)"""
    return sum(data) & 0xFF


def encapsulate_config(binary_data):
    """
    Encapsulate binary configuration data into a packet format:
    
    Packet Format:
    [START_BYTE][VERSION][LENGTH_HIGH][LENGTH_LOW][BINARY_DATA][CHECKSUM][END_BYTE]
    
    - START_BYTE: 0xAA (1 byte)
    - VERSION: 0x01 (1 byte)
    - LENGTH: Data length (2 bytes, big-endian)
    - BINARY_DATA: Binary configuration (32 bytes)
    - CHECKSUM: Sum of all data bytes mod 256 (1 byte)
    - END_BYTE: 0x55 (1 byte)
    """
    data_length = len(binary_data)
    
    # Calculate checksum
    checksum = calculate_checksum(binary_data)
    
    # Build packet
    packet = bytearray()
    packet.append(START_BYTE)
    packet.append(PACKET_VERSION)
    packet.extend(struct.pack('>H', data_length))  # Big-endian 16-bit length
    packet.extend(binary_data)
    packet.append(checksum)
    packet.append(END_BYTE)
    
    return bytes(packet)



def check_connection(port, baudrate):
    """
    Verify that the serial port exists and can be opened.
    Does not attempt to send data.
    """
    print(f"[*] Checking connection to {port}...")
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=1
        )
        ser.close()
        print(f"[*] SUCCESS: Successfully opened {port}")
        return True
    except serial.SerialException as e:
        print(f"[X] FAILURE: Could not open {port}")
        print(f"    Reason: {e}")
        return False
    except Exception as e:
        print(f"[X] FAILURE: Unexpected error: {e}")
        return False


def send_config_uart(port, baudrate, config_file):

    # Import binary_protocol helpers - handle both relative and packaged imports
    try:
        from binary_protocol import decode_config_binary, encode_config_binary, format_binary_hex
    except ImportError:
        # Fallback for packaged executable if modules are bundled differently or missing
        print("[!] Warning: Could not import binary_protocol. Ensure it is bundled correctly.")
        return False
    
    # Read configuration file
    config_path = Path(config_file)
    
    if not config_path.exists():
        print(f"[*] Error: Configuration file not found: {config_file}")
        return False
    
    binary_data = None
    
    if config_path.suffix == '.bin':
        # Read binary file directly
        with open(config_path, 'rb') as f:
            binary_data = f.read()
        
        # Decode and display
        try:
            decoded = decode_config_binary(binary_data)
            print(f"[*] Binary configuration ({len(binary_data)} bytes):")
            print(f"   Device: {decoded['device_mode']}")
            print(f"   Protocol: {decoded['streaming_protocol']}")
            print(f"   Modulation: {decoded['modulation']}")
            print(f"   Carrier Freq: {decoded['carrier_frequency_hz']:,} Hz ({decoded['carrier_frequency_hz']/1e6:.3f} MHz)")
            print(f"   Sampling Freq: {decoded['sampling_frequency_hz']:,} Hz ({decoded['sampling_frequency_hz']/1e6:.3f} MHz)")
            print(f"   Gains: RF={decoded['rf_gain_db']} dB, IF={decoded['if_gain_db']} dB, BB={decoded['baseband_gain_db']} dB")
            print(f"   CRC: {decoded['crc']}")
        except Exception as e:
            print(f"[*] Error decoding binary file: {e}")
            return False
            
    elif config_path.suffix == '.json':
        # Parse JSON and create binary
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Convert to binary format
        config_dict = {
            'deviceMode': config_data['device_mode'],
            'streamingProtocol': config_data['streaming_protocol'],
            'modulation': config_data['rf_parameters']['modulation'],
            'fc': config_data['rf_parameters']['carrier_frequency_hz'],
            'fs': config_data['rf_parameters']['sampling_frequency_hz'],
            'rfg': config_data['rf_parameters']['rf_gain_db'],
            'ifg': config_data['rf_parameters']['if_gain_db'],
            'bbg': config_data['rf_parameters']['baseband_gain_db']
        }
        binary_data = encode_config_binary(config_dict)
        print(f"[*] Converted JSON to binary ({len(binary_data)} bytes)")
        
    else:
        # Read compact string and convert to binary
        with open(config_path, 'r') as f:
            config_string = f.read().strip()
        
        print(f"[*] Compact string: {config_string}")
        
        # Parse compact string: MODE|PROTOCOL|MOD|FC|FS|RFG|IFG|BBG
        parts = config_string.split('|')
        if len(parts) != 8:
            print(f"[*] Error: Invalid compact string format")
            return False
        
        try:
            config_dict = {
                'deviceMode': parts[0].lower(),
                'streamingProtocol': parts[1].lower(),
                'modulation': parts[2],
                'fc': int(parts[3]),
                'fs': int(parts[4]),
                'rfg': float(parts[5]),
                'ifg': float(parts[6]),
                'bbg': float(parts[7])
            }
            binary_data = encode_config_binary(config_dict)
            print(f"[*] Converted to binary ({len(binary_data)} bytes)")
        except ValueError as e:
             print(f"[*] Error parsing compact string values: {e}")
             return False
    
    if binary_data is None:
        print(f"[*] Error: Failed to generate binary data")
        return False
    
    print(f"\n[*] Binary data (hex):")
    print(format_binary_hex(binary_data))
    
    # Encapsulate into packet
    packet = encapsulate_config(binary_data)
    
    print(f"\n[*] Packet size: {len(packet)} bytes (header: 6, data: {len(binary_data)}, footer: 2)")
    print(f"[*] Packet (hex): {packet.hex()}")
    
    try:
        # Open serial port
        print(f"[*] Opening serial port: {port} @ {baudrate} baud")
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        
        # Wait for port to stabilize
        time.sleep(0.5)
        
        # Send packet
        print(f"[*] Sending packet...")
        bytes_sent = ser.write(packet)
        ser.flush()
        
        print(f"[*] Sent {bytes_sent} bytes successfully!")
        
        # Wait for acknowledgment (optional)
        print("[*] Waiting for acknowledgment...")
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"[*] Received response: {response.decode('utf-8', errors='ignore')}")
        else:
            print("[*] No response received (Timeout)")
        
        ser.close()
        print("[*] Serial port closed")
        return True
        
    except serial.SerialException as e:
        print(f"\n[X] CONNECTION ERROR: Could not access serial port {port}")
        print(f"    Details: {e}")
        print("\nPossible solutions:")
        print(f"  1. Ensure USB cable is connected.")
        print(f"  2. Check if {port} is the correct port name.")
        if "Permission denied" in str(e):
             print("  3. Check permissions (try running as sudo/admin)")
        print("  4. Ensure no other application is using this port.")
        return False
    except Exception as e:
        print(f"[*] Unexpected Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Send RF configuration to Single Board Computer via UART'
    )
    parser.add_argument(
        '-p', '--port',
        required=True,
        help='Serial port (e.g., /dev/ttyUSB0, COM3)'
    )
    parser.add_argument(
        '-b', '--baudrate',
        type=int,
        default=115200,
        help='Baud rate (default: 115200)'
    )
    # File is optional if just checking connection
    parser.add_argument(
        '-f', '--file',
        help='Configuration file (.txt, .json, or .bin)'
    )
    parser.add_argument(
        '--check-connection',
        action='store_true',
        help='Verify serial port connection without sending data'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("RF Configuration UART Sender")
    print("=" * 60)
    
    # Mode 1: Check Connection
    if args.check_connection:
        success = check_connection(args.port, args.baudrate)
        if success:
            print("[*] Connection check passed.")
            sys.exit(0)
        else:
            print("[X] Connection check failed.")
            sys.exit(1)
            
    # Mode 2: Send Config
    if not args.file:
        print("[!] Error: --file argument is required ensuring configuration data is sent.")
        print("    Use --check-connection if you only want to test the port.")
        parser.print_help()
        sys.exit(1)
        
    success = send_config_uart(args.port, args.baudrate, args.file)
    
    if success:
        print("\n[*] Configuration sent successfully!")
        sys.exit(0)
    else:
        print("\n[*] Failed to send configuration")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled by user.")
        sys.exit(1)
