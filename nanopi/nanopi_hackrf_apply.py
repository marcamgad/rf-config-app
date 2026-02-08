#!/usr/bin/env python3
"""
NanoPi: Apply RF configuration to HackRF One over USB.

This script accepts a configuration payload (from UART or .bin file)
and applies it to HackRF via hackrf_transfer.

Notes:
- HackRF settings are applied while streaming (RX/TX).
- For RX, the script can stream to /dev/null for a short duration.
- For TX, an IQ file is required.
"""

import argparse
import os
import subprocess
import sys

from nanopi_uart_driver import read_packet, decode_payload


def read_config_from_uart(port: str, baudrate: int, timeout_s: float) -> dict:
    import serial

    with serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.2,
    ) as ser:
        payload = read_packet(ser, timeout_s=timeout_s)
        return decode_payload(payload)


def read_config_from_bin(bin_path: str) -> dict:
    with open(bin_path, "rb") as f:
        payload = f.read()
    return decode_payload(payload)


def build_hackrf_command(
    cfg: dict,
    mode: str,
    duration_s: float,
    iq_file: str | None,
    samples_override: int | None,
) -> list[str]:
    freq = int(cfg["carrier_frequency_hz"])
    samp = int(cfg["sampling_frequency_hz"])

    # Map gains to HackRF fields (common mapping)
    lna_gain = int(cfg["rf_gain_db"])    # LNA gain (0-40 dB)
    vga_gain = int(cfg["if_gain_db"])    # VGA gain (0-62 dB)
    txvga = int(cfg["baseband_gain_db"]) # TX VGA gain (0-47 dB)

    cmd = ["hackrf_transfer", "-f", str(freq), "-s", str(samp)]

    if mode == "rx":
        # RX gains
        cmd += ["-l", str(lna_gain), "-g", str(vga_gain)]
        # Stream to /dev/null for duration
        samples = samples_override if samples_override is not None else int(samp * duration_s)
        if samples <= 0:
            samples = 1
        cmd += ["-r", "/dev/null", "-n", str(samples)]
    else:
        if not iq_file:
            raise ValueError("TX mode requires --iq-file")
        if not os.path.exists(iq_file):
            raise FileNotFoundError(iq_file)
        # TX gains
        cmd += ["-x", str(txvga)]
        # Stream IQ file
        cmd += ["-t", iq_file]

    return cmd


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply RF config to HackRF One over USB")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--uart", action="store_true", help="Read config from UART")
    source.add_argument("--bin", metavar="PATH", help="Read config from .bin file")

    parser.add_argument("-p", "--port", help="UART port (e.g., /dev/ttyS1)")
    parser.add_argument("-b", "--baudrate", type=int, default=115200, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=2.0, help="UART packet timeout")

    parser.add_argument("--mode", choices=["rx", "tx"], default="rx", help="HackRF mode")
    parser.add_argument("--duration", type=float, default=0.1, help="RX duration (seconds)")
    parser.add_argument("--samples", type=int, help="Override RX sample count")
    parser.add_argument("--iq-file", help="TX IQ file path")

    parser.add_argument("--dry-run", action="store_true", help="Print command only")

    args = parser.parse_args()

    if args.uart:
        if not args.port:
            print("[X] --port is required when using --uart")
            sys.exit(1)
        cfg = read_config_from_uart(args.port, args.baudrate, args.timeout)
    else:
        cfg = read_config_from_bin(args.bin)

    cmd = build_hackrf_command(cfg, args.mode, args.duration, args.iq_file, args.samples)

    print("[*] HackRF command:")
    print(" ".join(cmd))

    if args.dry_run:
        return

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()