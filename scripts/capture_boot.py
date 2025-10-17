#!/usr/bin/env python3
"""
ESP32 Boot Log Capture Utility

Captures serial output from an ESP32 device during boot by toggling DTR/RTS
to trigger a reset. This is essential for debugging Matter device commissioning
and verifying QR code generation.

Usage:
    ./scripts/capture_boot.py                           # Use defaults
    ./scripts/capture_boot.py -p /dev/cu.usbmodem101    # Specify port
    ./scripts/capture_boot.py -o my_boot.txt            # Custom output file
    ./scripts/capture_boot.py -d 15                     # Capture for 15 seconds
"""

import sys
import time
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description='Capture ESP32 boot log via serial port',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '-p', '--port',
        default='/dev/cu.usbmodem101',
        help='Serial port (default: /dev/cu.usbmodem101)'
    )
    parser.add_argument(
        '-b', '--baud',
        type=int,
        default=115200,
        help='Baud rate (default: 115200)'
    )
    parser.add_argument(
        '-o', '--output',
        default='boot_capture.txt',
        help='Output file path (default: boot_capture.txt)'
    )
    parser.add_argument(
        '-d', '--duration',
        type=float,
        default=12.0,
        help='Capture duration in seconds (default: 12.0)'
    )
    parser.add_argument(
        '--no-reset',
        action='store_true',
        help='Skip DTR/RTS toggle (no device reset)'
    )
    
    args = parser.parse_args()
    
    # Try to import pyserial
    try:
        import serial
    except ImportError:
        print("ERROR: pyserial not installed", file=sys.stderr)
        print("Install with: pip install pyserial", file=sys.stderr)
        print(f"Fallback: waiting {args.duration} seconds without capture...", file=sys.stderr)
        time.sleep(args.duration)
        sys.exit(1)
    
    # Open serial port
    try:
        ser = serial.Serial(
            port=args.port,
            baudrate=args.baud,
            timeout=0.1
        )
    except serial.SerialException as e:
        print(f"ERROR: Could not open {args.port}: {e}", file=sys.stderr)
        print("Make sure the device is connected and no other program is using the port.", file=sys.stderr)
        sys.exit(1)
    
    # Clear buffers
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    
    # Reset device by toggling DTR/RTS (unless disabled)
    if not args.no_reset:
        print(f"Resetting device on {args.port}...")
        ser.dtr = False
        ser.rts = False
        time.sleep(0.05)
        ser.dtr = True
        ser.rts = True
        time.sleep(0.05)
    
    # Capture serial output
    print(f"Capturing for {args.duration} seconds to {args.output}...")
    end_time = time.time() + args.duration
    
    try:
        with open(args.output, 'wb') as f:
            bytes_captured = 0
            while time.time() < end_time:
                data = ser.read(4096)
                if data:
                    f.write(data)
                    f.flush()
                    bytes_captured += len(data)
                else:
                    time.sleep(0.02)
    except KeyboardInterrupt:
        print("\nCapture interrupted by user")
    finally:
        ser.close()
    
    # Summary
    print(f"✓ Captured {bytes_captured:,} bytes to {args.output}")
    
    # Check for common issues
    if bytes_captured == 0:
        print("WARNING: No data captured. Check that:")
        print("  - Device is connected to the correct port")
        print("  - No other program (idf.py monitor) is using the port")
        print("  - Baud rate matches device configuration")
    
    # Look for key indicators
    try:
        with open(args.output, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        if 'SetupQRCode' in content:
            print("✓ Found QR code in output")
        elif 'GetSetupPasscode() failed' in content:
            print("⚠ QR code generation failed (GetSetupPasscode error)")
        
        if 'CHIPoBLE advertising started' in content:
            print("✓ BLE commissioning active")
        
        if 'ERROR setting up transport' in content:
            print("⚠ Transport setup error detected")
        
        if 'CONFLICT' in content or 'abort()' in content:
            print("⚠ Device crash detected in boot log")
            
    except Exception as e:
        print(f"Note: Could not analyze output: {e}")

if __name__ == '__main__':
    main()

