# ESP32-Matter Utility Scripts

This directory contains helper scripts for working with ESP32-Matter projects.

## capture_boot.py

Captures serial output from an ESP32 device during boot, with automatic device reset via DTR/RTS toggle.

**Essential for:**
- Verifying QR code generation
- Debugging boot issues
- Checking commissioning setup
- AI-driven development workflows (non-interactive)

### Basic Usage

```bash
# Default: capture from /dev/cu.usbmodem101 for 12 seconds
./scripts/capture_boot.py

# View the captured log
cat boot_capture.txt
```

### Advanced Usage

```bash
# Custom port
./scripts/capture_boot.py -p /dev/cu.usbmodem2101

# Custom output file
./scripts/capture_boot.py -o my_boot_log.txt

# Longer capture duration (useful for slow boots)
./scripts/capture_boot.py -d 20

# Skip device reset (capture without DTR/RTS toggle)
./scripts/capture_boot.py --no-reset

# Combine options
./scripts/capture_boot.py -p /dev/cu.usbmodem101 -o logs/boot.txt -d 15
```

### What It Checks

The script automatically analyzes the captured output and reports:

- ✓ QR code found (`SetupQRCode`)
- ⚠ QR code generation failed (`GetSetupPasscode() failed`)
- ✓ BLE commissioning active (`CHIPoBLE advertising started`)
- ⚠ Transport errors (`ERROR setting up transport`)
- ⚠ Device crashes (`CONFLICT`, `abort()`)

### Requirements

```bash
pip install pyserial
```

### Exit Codes

- `0` - Success, data captured
- `1` - Error (pyserial not installed, port unavailable, etc.)

### Troubleshooting

**"Could not open /dev/cu.usbmodem101"**
- Device not connected or wrong port
- Another program (like `idf.py monitor`) is using the port
- Try listing ports: `ls /dev/cu.*`

**"No data captured"**
- Wrong baud rate (default: 115200)
- Device not booting
- Check physical connection

**"pyserial not installed"**
- Run: `pip install pyserial`

