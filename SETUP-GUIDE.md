# ESP32-C3 Matter Occupancy Sensor Setup Guide

**Last Updated**: October 17, 2025  
**Status**: Complete and Verified  
**Goal**: Set up ESP32-C3 as a Matter-compatible device that can be reliably commissioned to Apple Home with unique, changeable credentials.

**Tested Hardware**:
- ESP32-C3 Supermini (any ESP32-C3 board should work)
- PIR motion sensor on GPIO 3 (HC-SR501 or similar)
- USB-C connection for programming and serial monitoring

**What This Guide Provides**:
- Complete environment setup (ESP-IDF 5.4.1 + ESP-Matter)
- Step-by-step firmware building and flashing
- Factory credential generation with unique QR codes
- Tested solutions for upstream ESP-Matter bugs
- Commissioning to Apple Home
- Verified process for changing device QR codes
- Comprehensive troubleshooting for common issues

---

## ✅ SUCCESS SUMMARY (October 16, 2025)

The ESP32-C3 Matter occupancy sensor is now **fully functional** with unique credentials:

- **Status**: ✅ Firmware builds, flashes, and boots successfully
- **QR Code**: `MT:Y.K90GSY00KA0648G00` ✅ PRINTING
- **Manual Code**: `34970112332` ✅ PRINTING
- **BLE Commissioning**: ✅ Active
- **PIR Sensor**: ✅ Working on GPIO 3
- **Commissioned**: ✅ Successfully added to Apple Home
- **Tested**: ✅ PIR sensor detects occupancy in Home app

**Key Fix Applied**: Patched ESP32FactoryDataProvider to implement `GetSetupPasscode()` and added `pin-code` to factory NVS partition. See [QR Code Issue Resolution](#-qr-code-issue-resolved-october-16-2025) for details.

---

## 🚀 ESSENTIAL QUICK-REFERENCE COMMANDS

### Environment Setup (Required First)
```bash
# Initialize ESP-IDF and ESP-Matter environments
cd ~/esp/esp-idf && source ./export.sh && cd ~/esp/esp-matter && source ./export.sh && export IDF_CCACHE_ENABLE=1
```

### 0. Check for Upstream Patches (REQUIRED FIRST STEP)
```bash
# CRITICAL: Check if ESP-Matter bugs have been fixed upstream
# This prevents applying unnecessary patches to already-fixed code

echo "Checking ESP32FactoryDataProvider for GetSetupPasscode bug..."
if grep "GetSetupPasscode.*override" ~/esp/esp-matter/connectedhomeip/connectedhomeip/src/platform/ESP32/ESP32FactoryDataProvider.h | grep -q "CHIP_ERROR_NOT_IMPLEMENTED"; then
    echo "⚠️  BUG CONFIRMED: GetSetupPasscode returns NOT_IMPLEMENTED"
    echo "📋 Patch REQUIRED: Apply patches/esp32-factory-data-provider-getsetuppasscode.patch"
else
    echo "✅ BUG FIXED: GetSetupPasscode is properly implemented!"
    echo "🎉 NO PATCH NEEDED - Skip patch application step"
    echo "📝 UPDATE REQUIRED: SETUP-GUIDE.md should be updated to remove patch"
fi
```

### 1. Complete Chip Erase
```bash
# WARNING: This erases ALL data from the ESP32-C3
esptool.py --chip esp32c3 -p /dev/tty.usbmodem101 erase_flash
```

### 2. Build and Flash Firmware
```bash
# Navigate to your firmware directory
cd ~/path/to/your/firmware

# Build firmware
idf.py build

# Flash complete firmware (bootloader, partition table, app, OTA data)
idf.py -p /dev/cu.usbmodem101 flash

# Flash factory partition with credentials (after generating)
# Replace <UUID> with your actual UUID from 131b_1234/ directory
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 write_flash 0x3E0000 131b_1234/<UUID>/<UUID>-partition.bin
```

### Using the Template Firmware
- **What it is**: A minimal, working ESP-Matter firmware configured as a PIR occupancy sensor, verified to build/flash/boot. Use it as a starting point for any device type.
- **Location**: `templates/occupancy-sensor/` in this repository
- **How to use**:
  1) Copy the template to start a new project:
     ```bash
     cp -r templates/occupancy-sensor ~/esp/projects/my_new_matter_device
     cd ~/esp/projects/my_new_matter_device
     ```
  2) Set target and build:
     ```bash
     idf.py set-target esp32c3 && idf.py build
     ```
  3) Flash and monitor (replace port if needed):
     ```bash
     idf.py -p /dev/cu.usbmodem101 flash
     idf.py -p /dev/tty.usbmodem101 monitor
     ```
- **Switching to another Matter device type**:
  - Replace the endpoint creation in `main/app_main.cpp` from the provided occupancy sensor to another device type using ESP-Matter APIs (e.g., on/off light, contact sensor). See ESP-Matter examples in `~/esp/esp-matter/examples/` for the target device, then mirror its `endpoint::create(...)` usage and cluster attributes.
  - Keep `sdkconfig` production credentials and partition layout unchanged.
  - Rebuild and flash.

### 3. Monitor Serial Output
```bash
# Human (interactive) monitoring only
# First setup environment, then navigate to project, then monitor
cd ~/esp/esp-idf && source ./export.sh && cd ~/esp/esp-matter && source ./export.sh && cd ~/path/to/your/firmware
idf.py -p /dev/tty.usbmodem101 monitor
```

### 3.1 Capture Full Boot Log via PySerial (Most Reliable in Non-TTY/CI)
```bash
# Requires: pyserial (pip install pyserial)
# Captures full boot header by toggling DTR/RTS and reading for ~12s
python3 - << 'PY'
import sys, time
try:
    import serial
except Exception as e:
    print('pyserial not installed:', e); sys.exit(1)
port = '/dev/cu.usbmodem101'
baud = 115200
out_path = 'boot_capture.txt'
ser = serial.Serial(port=port, baudrate=baud, timeout=0.1)
ser.reset_input_buffer(); ser.reset_output_buffer()
# Toggle DTR/RTS to reset
ser.dtr = False; ser.rts = False; time.sleep(0.05)
ser.dtr = True; ser.rts = True
end = time.time() + 12.0
with open(out_path, 'wb') as f:
    while time.time() < end:
        data = ser.read(4096)
        if data:
            f.write(data); f.flush()
        else:
            time.sleep(0.02)
ser.close()
print('Wrote to', out_path)
PY

# Inspect captured log
head -200 boot_capture.txt
```

### 3.2 Print QR and Manual Code at Boot (Firmware)
To print the Base38 QR and manual pairing code on startup, use the official helper:

```cpp
// In main/app_main.cpp
#include <app/server/OnboardingCodesUtil.h>

// After Matter start (esp_matter::start)
PrintOnboardingCodes(
    chip::RendezvousInformationFlags(
        chip::RendezvousInformationFlag::kBLE)
        .Set(chip::RendezvousInformationFlag::kOnNetwork));
```

Notes:
- Ensure CHIP includes are available so `app/server/OnboardingCodesUtil.h` resolves (matches the temp template project).
- Rebuild and flash; the serial log will show the QR string (`MT:...`) and manual code.

### ✅ QR Code Issue RESOLVED (October 16, 2025)

**⚠️ UPSTREAM BUG CONFIRMED**: As of October 2025, the ESP-Matter repository has an incomplete implementation in `ESP32FactoryDataProvider`. The `GetSetupPasscode()` function returns `CHIP_ERROR_NOT_IMPLEMENTED`, and `esp-matter-mfg-tool` omits the `pin-code` NVS entry. This causes QR code generation to fail with error `2d` (PERSISTED_STORAGE_VALUE_NOT_FOUND).

**🔍 CHECK BEFORE APPLYING PATCH**:
Before applying the patch below, verify if the issue still exists:

```bash
# Check if GetSetupPasscode returns NOT_IMPLEMENTED
if grep "GetSetupPasscode.*override" ~/esp/esp-matter/connectedhomeip/connectedhomeip/src/platform/ESP32/ESP32FactoryDataProvider.h | grep -q "CHIP_ERROR_NOT_IMPLEMENTED"; then
    echo "BUG EXISTS - Apply patch"
else
    echo "BUG FIXED - Skip patch!"
fi
```

**⚠️ IF BUG IS FIXED UPSTREAM**: The patch is no longer needed! Alert the user:
```
🎉 GOOD NEWS: ESP-Matter has fixed the GetSetupPasscode bug upstream!
The patch in patches/esp32-factory-data-provider-getsetuppasscode.patch is NO LONGER NEEDED.

ACTION REQUIRED:
1. Do NOT apply the patch
2. Update SETUP-GUIDE.md to remove patch instructions
3. Delete patches/esp32-factory-data-provider-getsetuppasscode.patch
4. You can now use factory data providers without modifications!
```

---

**IF BUG STILL EXISTS** (apply patch):

**Root Cause**: ESP32FactoryDataProvider's `GetSetupPasscode()` returns `CHIP_ERROR_NOT_IMPLEMENTED`. The QR code generator requires the actual setup passcode, causing generation to fail.

**Solution - Apply Patch**:

1. **Apply the patch** (from esp-matter root):
   ```bash
   cd ~/esp/esp-matter
   patch -p1 < /path/to/esp32-matter-guide/patches/esp32-factory-data-provider-getsetuppasscode.patch
   ```

2. **Verify patch applied successfully**:
   ```bash
   # Should show the implementation, NOT "CHIP_ERROR_NOT_IMPLEMENTED"
   grep -A 3 "GetSetupPasscode.*setupPasscode)" ~/esp/esp-matter/connectedhomeip/connectedhomeip/src/platform/ESP32/ESP32FactoryDataProvider.cpp
   ```

3. **Add pin-code to factory partition CSV** (after esp-matter-mfg-tool generation):
   ```csv
   chip-factory,namespace,,
   discriminator,data,u32,3840
   pin-code,data,u32,20202021          # ← ADD THIS (use your actual passcode)
   iteration-count,data,u32,10000
   salt,data,string,qmqmzOZyEwdzYdVGQ6Uu9CLK/EqONB9OD3ILHX2uiSQ=
   verifier,data,string,kjCQe/05BKFiHeqWhUyHPKMenVKnqb+JYNmEfVCavnsERxIgSP/6vgOGGLt4qs8A+SVHgenXdnc48thnNcvgVxfQMuVVHFpVJuo1Pr/ujn58ilEwdGuTpDzPJbT7k6nQvg==
   ```

4. **Regenerate factory partition**:
   ```bash
   python $IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py generate \
     partition.csv partition_fixed.bin 0x6000
   ```

5. **Rebuild and flash**:
   ```bash
   idf.py build
   idf.py -p /dev/cu.usbmodem101 flash
   esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 write_flash 0x3E0000 partition_fixed.bin
   ```

**Expected Output** (QR code now prints):
```
I (1390) chip[SVR]: SetupQRCode: [MT:Y.K90GSY00KA0648G00]
I (1400) chip[SVR]: Copy/paste the below URL in a browser to see the QR Code:
I (1410) chip[SVR]: https://project-chip.github.io/connectedhomeip/qrcode.html?data=MT%3AY.K90GSY00KA0648G00
I (1420) chip[SVR]: Manual pairing code: [34970112332]
```

**NVS Key Names for ESP32** (confirmed from ESP32Config.cpp):
- `discriminator` → Setup discriminator (u32)
- `pin-code` → Setup passcode (u32) ← **REQUIRED for QR code**
- `iteration-count` → SPAKE2+ iteration count (u32)
- `salt` → SPAKE2+ salt (string, base64)
- `verifier` → SPAKE2+ verifier (string, base64)
- All in `chip-factory` namespace

**To Report Upstream**: If this bug still exists when you're reading this, please report to:
- https://github.com/espressif/esp-matter/issues
- Reference: ESP32FactoryDataProvider::GetSetupPasscode() returns NOT_IMPLEMENTED, breaking QR code generation

### 4. Generate Credentials (Complete Workflow)
```bash
# Generate PAA certificate
chip-cert gen-att-cert --type a --subject-cn "ESP32-C3 Matter PAA" --valid-from "2024-01-01 00:00:00" --lifetime 3650 --out-key ESP32_C3_Matter_PAA_key.pem --out ESP32_C3_Matter_PAA_cert.pem

# Generate PAI certificate  
chip-cert gen-att-cert --type i --subject-cn "ESP32-C3 Matter PAI" --subject-vid 0x131B --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key ESP32_C3_Matter_PAA_key.pem --ca-cert ESP32_C3_Matter_PAA_cert.pem --out-key ESP32_C3_Matter_PAI_key.pem --out ESP32_C3_Matter_PAI_cert.pem

# Generate DAC certificate
chip-cert gen-att-cert --type d --subject-cn "ESP32-C3 Matter DAC" --subject-vid 0x131B --subject-pid 0x1234 --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key ESP32_C3_Matter_PAI_key.pem --ca-cert ESP32_C3_Matter_PAI_cert.pem --out-key ESP32_C3_Matter_DAC_key.pem --out ESP32_C3_Matter_DAC_cert.pem

# Generate Certification Declaration (NOTE: Use proper certificate ID format)
chip-cert gen-cd --key ESP32_C3_Matter_PAA_key.pem --cert ESP32_C3_Matter_PAA_cert.pem --out ESP32_C3_Matter_CD.der --format-version 1 --vendor-id 0x131B --product-id 0x1234 --device-type-id 0x0107 --certificate-id "ZIG20142ZB330001-24" --security-level 0 --security-info 0 --version-number 1 --certification-type 0

# Generate factory partition (NOTE: Use correct parameter names)
esp-matter-mfg-tool -v 0x131B -p 0x1234 --passcode 20202021 --discriminator 0xF00 --dac-cert ESP32_C3_Matter_DAC_cert.pem --dac-key ESP32_C3_Matter_DAC_key.pem --pai --cert ESP32_C3_Matter_PAI_cert.pem --key ESP32_C3_Matter_PAI_key.pem --cert-dclrn ESP32_C3_Matter_CD.der --outdir .
```

### 5. Change Device QR Code (Quick Reference)
**See full tested workflow in**: [How to Change Device QR Code](#how-to-change-device-qr-code-tested--verified)

```bash
# Quick summary - refer to full section for details
# 1. Remove device from Apple Home
# 2. Generate new certs (PAA → PAI → DAC → CD)
# 3. Run esp-matter-mfg-tool with NEW passcode/discriminator
# 4. Add pin-code to factory CSV
# 5. Regenerate partition binary
# 6. Erase NVS, flash partition, REBOOT device
# 7. Verify new QR code in boot log
# 8. Re-commission to Apple Home
```

---

## Step-by-Step Setup Guide

This section provides a clean, linear path from zero to a working Matter device. Follow these steps in order.

### Prerequisites

- macOS with Xcode Command Line Tools installed
- ESP32-C3 development board connected via USB
- Basic familiarity with terminal/command line

### Step 1: Install ESP-IDF and ESP-Matter

```bash
# Install dependencies
xcode-select --install
brew install cmake ninja ccache python@3.10

# For Apple Silicon Macs, install Rosetta 2
/usr/sbin/softwareupdate --install-rosetta --agree-to-license

# Clone ESP-IDF 5.4.1
mkdir -p ~/esp
cd ~/esp
git clone -b v5.4.1 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32c3

# Clone ESP-Matter
cd ~/esp
git clone --depth 1 https://github.com/espressif/esp-matter.git
cd esp-matter
git submodule update --init --depth 1
cd connectedhomeip/connectedhomeip
./scripts/checkout_submodules.py --platform esp32 darwin --shallow
cd ../..
./install.sh
```

### Step 2: Check and Apply Upstream Patches

```bash
# Check if the GetSetupPasscode bug exists
if grep "GetSetupPasscode.*override" ~/esp/esp-matter/connectedhomeip/connectedhomeip/src/platform/ESP32/ESP32FactoryDataProvider.h | grep -q "CHIP_ERROR_NOT_IMPLEMENTED"; then
    echo "⚠️  Bug exists - applying patch..."
    cd ~/esp/esp-matter
    patch -p1 < /path/to/esp32-matter-guide/patches/esp32-factory-data-provider-getsetuppasscode.patch
    echo "✅ Patch applied successfully"
else
    echo "✅ Bug already fixed upstream - no patch needed!"
fi
```

### Step 3: Create Your Firmware Project

```bash
# Set up environment (do this in every new terminal)
cd ~/esp/esp-idf && source ./export.sh
cd ~/esp/esp-matter && source ./export.sh
export IDF_CCACHE_ENABLE=1

# Copy the sensors example from ESP-Matter (includes build infrastructure)
cp -r ~/esp/esp-matter/examples/sensors ~/esp/my_matter_device
cd ~/esp/my_matter_device

# Replace with template files (occupancy-only, no I2C conflicts)
cp /path/to/esp32-matter-guide/templates/occupancy-sensor/app_main.cpp main/
cp /path/to/esp32-matter-guide/templates/occupancy-sensor/drivers/pir.* main/drivers/

# Configure for ESP32-C3
idf.py set-target esp32c3

# Configure sdkconfig for production credentials (use menuconfig)
idf.py menuconfig
# Navigate to:
# - "Component config" → "CHIP Device Layer" → "Matter Device Config"
#   ✓ Enable "ESP32 Factory Data Provider"
#   ✓ Enable "ESP32 Device Instance Info Provider"  
# - "Component config" → "CHIP Device Layer" → "Commissioning options"
#   ✓ Enable "Use Commissioning Data from Factory Partition"
#   ✗ DISABLE "Enable Test Commissioning Credentials"
# - "Component config" → "CHIP Device Layer" → "Factory Partition Label"
#   Set to: "fctry"
# - "Example Configuration"
#   Set "PIR Data Pin" to: 3
# Save and exit menuconfig
```

### Step 4: Generate Unique Device Credentials

```bash
# Generate certificate chain
chip-cert gen-att-cert --type a --subject-cn "Matter PAA" --valid-from "2024-01-01 00:00:00" --lifetime 3650 --out-key PAA_key.pem --out PAA_cert.pem

chip-cert gen-att-cert --type i --subject-cn "Matter PAI" --subject-vid 0x131B --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key PAA_key.pem --ca-cert PAA_cert.pem --out-key PAI_key.pem --out PAI_cert.pem

chip-cert gen-att-cert --type d --subject-cn "Matter DAC" --subject-vid 0x131B --subject-pid 0x1234 --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key PAI_key.pem --ca-cert PAI_cert.pem --out-key DAC_key.pem --out DAC_cert.pem

chip-cert gen-cd --key PAA_key.pem --cert PAA_cert.pem --out CD.der --format-version 1 --vendor-id 0x131B --product-id 0x1234 --device-type-id 0x0107 --certificate-id "ZIG20142ZB330001-24" --security-level 0 --security-info 0 --version-number 1 --certification-type 0

# Generate factory partition
esp-matter-mfg-tool -v 0x131B -p 0x1234 --passcode 20202021 --discriminator 0xF00 --dac-cert DAC_cert.pem --dac-key DAC_key.pem --pai --cert PAI_cert.pem --key PAI_key.pem --cert-dclrn CD.der --outdir .
```

### Step 5: Add pin-code to Factory Partition

```bash
# Find the generated UUID
ls -la 131b_1234/

# Add pin-code to the CSV (replace <UUID> with actual UUID)
UUID="<your-uuid-from-above>"
echo "Adding pin-code to partition CSV..."

# Edit the file to add pin-code line after discriminator
# Manually edit 131b_1234/$UUID/internal/partition.csv and add:
# pin-code,data,u32,20202021
# (right after the discriminator line)

# Regenerate factory partition binary
python $IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py generate 131b_1234/$UUID/internal/partition.csv 131b_1234/$UUID/partition_fixed.bin 0x6000
```

### Step 6: Build and Flash Firmware

```bash
# Build firmware
idf.py build

# Erase chip (first time only)
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 erase_flash

# Flash firmware
idf.py -p /dev/cu.usbmodem101 flash

# Flash factory partition (replace UUID)
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 write_flash 0x3E0000 131b_1234/$UUID/partition_fixed.bin

# Reboot device
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 run
```

### Step 7: Verify QR Code

```bash
# Monitor serial output
idf.py -p /dev/tty.usbmodem101 monitor

# Look for these lines in the output:
# I (xxxx) chip[SVR]: SetupQRCode: [MT:Y.K90GSY00KA0648G00]
# I (xxxx) chip[SVR]: Manual pairing code: [34970112332]
# I (xxxx) chip[DL]: CHIPoBLE advertising started
```

### Step 8: Commission to Apple Home

1. Open Apple Home app on iPhone/iPad
2. Tap "+" → "Add Accessory"
3. Scan the QR code from serial output, or enter manual pairing code
4. Follow prompts to complete setup
5. Test the occupancy sensor by waving your hand in front of the PIR sensor

**Success!** Your device should now appear in Apple Home and respond to motion detection.

---

## Troubleshooting

### Environment Issues

**"esptool.py: command not found"**
- Cause: ESP-IDF environment not initialized
- Solution: Run the environment setup commands:
  ```bash
  cd ~/esp/esp-idf && source ./export.sh
  cd ~/esp/esp-matter && source ./export.sh
  export IDF_CCACHE_ENABLE=1
  ```

### Certificate Generation Issues

**"Invalid value specified for Certificate Id"**
- Cause: Certificate ID format not recognized by CSA standards
- Solution: Use proper format like "ZIG20142ZB330001-24" (not "ESP32-001" or simple numbers)

**"esp-matter-mfg-tool: error: unrecognized arguments: --cd"**
- Cause: Wrong parameter name for certification declaration
- Solution: Use `--cert-dclrn` instead of `--cd`

### Flashing and Boot Issues

**"Accessory Not Found" Immediately After Flashing**
- Cause: Device didn't automatically reboot after flashing factory partition
- Solution: Explicitly reboot with `esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 run`

**Device in Boot Loop or No Serial Output**
- Cause: Could be firmware issue, I2C driver conflict, or hardware problem
- Solution: 
  1. Check serial connection (use `/dev/cu.usbmodem101` not `/dev/tty.usbmodem101`)
  2. Erase chip completely and reflash
  3. Verify GPIO pin configurations match your hardware

**"CONFLICT! driver_ng is not allowed to be used with this old driver" I2C Error**
- Cause: Mixing old I2C driver API with new driver API (common with SHTC3 sensor)
- Symptom: Device boots then immediately crashes in abort() loop
- Solution: 
  1. Remove conflicting I2C-based endpoints from `app_main.cpp`
  2. The provided template already has SHTC3 removed for this reason
  3. If adding new I2C sensors, ensure all drivers use the same I2C API version

### Commissioning Issues

**"Fabric already commissioned. Disabling BLE advertisement"**
- Cause: Device has existing pairing data in NVS
- Solution: Erase operational NVS:
  ```bash
  python -m esptool --chip esp32c3 -p /dev/cu.usbmodem101 erase_region 0x10000 0xC000
  # Then reboot device
  esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 run
  ```

**"ERROR setting up transport: 2d" or QR Code Not Printing**
- Cause: Missing `pin-code` in factory NVS or GetSetupPasscode not implemented
- Solution: 
  1. Verify patch was applied (see Step 2)
  2. Ensure `pin-code` was added to factory CSV
  3. Regenerate factory partition and reflash

**"Chip stack locking error" / AssertChipStackLockedByCurrentThread**
- Cause: Matter API called from wrong thread (ISR, GPIO callback, etc.)
- Solution: Use `chip::DeviceLayer::PlatformMgr().ScheduleWork()` to defer to Matter thread

**"Device Advertises Old/Wrong QR Code"**
- Cause: Factory partition flashed to wrong address or wrong partition label in sdkconfig
- Solution:
  1. Verify partition offset in `partitions.csv` (should be 0x3E0000 for `fctry`)
  2. Check `sdkconfig` has `CONFIG_CHIP_FACTORY_NAMESPACE_PARTITION_LABEL="fctry"`
  3. Reflash factory partition to correct address

### Post-Removal Issues

**CASE Errors After Removing Device from Apple Home**
- Symptom: Repeated `E chip[SC]: CASE failed to match destination ID with local fabrics`
- This is **NORMAL and EXPECTED!**
- iOS continues trying to reconnect to cached devices
- Device correctly rejects unauthorized attempts
- Errors will stop on their own as cache expires
- **No action required** - proves security is working correctly

### Serial Output Interpretation

**Benign Messages (Safe to Ignore)**:
- `Warning: Checksum mismatch`: App is older than build, reflash if needed
- `E esp_matter_cluster: Config is NULL`: Optional config pointer, doesn't affect commissioning
- `W wifi: Haven't to connect`: Expected, no WiFi credentials yet
- `W comm: pin-code not found in fctry NVS`: Falls back to hardcoded default
- `chip[DMG]: DefaultAclStorage: 0 entries loaded`: Expected for uncommissioned device
- `chip[SVR]: WARNING: mTestEventTriggerDelegate is null`: Expected, not used

**Critical Messages (Action Required)**:
- `E chip[SVR]: ERROR setting up transport: 2d`: SPAKE2p verifier missing/invalid
- `Chip stack locking error` / `chipDie`: Threading violation
- `Fabric already commissioned`: Device in operational mode, erase NVS

### Recovery Procedure

If commissioning completely fails:

```bash
# 1. Full chip erase
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 erase_flash

# 2. Rebuild and flash everything
cd ~/esp/my_matter_device
idf.py fullclean
idf.py build
idf.py -p /dev/cu.usbmodem101 flash

# 3. Reflash factory partition (replace UUID)
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 write_flash 0x3E0000 131b_1234/<UUID>/partition_fixed.bin

# 4. Reboot and verify
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 run
idf.py -p /dev/tty.usbmodem101 monitor
```

---

## How to Change Device QR Code (Tested & Verified)

This section documents the complete, tested process for changing a device's QR code and commissioning credentials. This is useful when you need to:
- Generate unique credentials for multiple devices
- Replace compromised credentials
- Test different passcode/discriminator combinations

### Complete Workflow

**Step 1: Remove device from Apple Home** (if currently paired)
- Open Apple Home app → Select device → Remove Accessory

**Step 2: Generate new certificate chain**
```bash
cd /path/to/your/firmware/directory

# Generate PAA (Product Attestation Authority)
chip-cert gen-att-cert --type a --subject-cn "ESP32-C3 Matter PAA v3" --valid-from "2024-01-01 00:00:00" --lifetime 3650 --out-key ESP32_C3_Matter_PAA_v3_key.pem --out ESP32_C3_Matter_PAA_v3_cert.pem

# Generate PAI (Product Attestation Intermediate)
chip-cert gen-att-cert --type i --subject-cn "ESP32-C3 Matter PAI v3" --subject-vid 0x131B --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key ESP32_C3_Matter_PAA_v3_key.pem --ca-cert ESP32_C3_Matter_PAA_v3_cert.pem --out-key ESP32_C3_Matter_PAI_v3_key.pem --out ESP32_C3_Matter_PAI_v3_cert.pem

# Generate DAC (Device Attestation Certificate)
chip-cert gen-att-cert --type d --subject-cn "ESP32-C3 Matter DAC v3" --subject-vid 0x131B --subject-pid 0x1234 --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key ESP32_C3_Matter_PAI_v3_key.pem --ca-cert ESP32_C3_Matter_PAI_v3_cert.pem --out-key ESP32_C3_Matter_DAC_v3_key.pem --out ESP32_C3_Matter_DAC_v3_cert.pem

# Generate CD (Certification Declaration)
chip-cert gen-cd --key ESP32_C3_Matter_PAA_v3_key.pem --cert ESP32_C3_Matter_PAA_v3_cert.pem --out ESP32_C3_Matter_CD_v3.der --format-version 1 --vendor-id 0x131B --product-id 0x1234 --device-type-id 0x0107 --certificate-id "ZIG20142ZB330003-24" --security-level 0 --security-info 0 --version-number 1 --certification-type 0
```

**Step 3: Generate factory partition with NEW credentials**
```bash
# Use different passcode and discriminator to ensure QR code is unique
# Valid passcode range: avoid sequential/repetitive patterns
# Discriminator range: 0x000 to 0xFFF (0-4095)

esp-matter-mfg-tool -v 0x131B -p 0x1234 --passcode 34567890 --discriminator 0x800 --dac-cert ESP32_C3_Matter_DAC_v3_cert.pem --dac-key ESP32_C3_Matter_DAC_v3_key.pem --pai --cert ESP32_C3_Matter_PAI_v3_cert.pem --key ESP32_C3_Matter_PAI_v3_key.pem --cert-dclrn ESP32_C3_Matter_CD_v3.der --outdir .
```

**Step 4: Add pin-code to factory CSV**
```bash
# Locate the generated UUID directory
ls -la 131b_1234/

# Edit the partition CSV (replace UUID with your actual UUID)
# Add this line after discriminator:
# pin-code,data,u32,34567890

# Example using sed:
UUID="<your-uuid-here>"
sed -i.bak '/discriminator,data,u32,/a\
pin-code,data,u32,34567890' 131b_1234/$UUID/internal/partition.csv
```

**Step 5: Regenerate factory partition binary**
```bash
python $IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py generate 131b_1234/$UUID/internal/partition.csv 131b_1234/$UUID/partition_fixed.bin 0x6000
```

**Step 6: Erase NVS, flash new partition, and reboot**
```bash
# Erase operational NVS (clears old pairings)
python -m esptool --chip esp32c3 -p /dev/cu.usbmodem101 erase_region 0x10000 0xC000

# Flash new factory partition
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 write_flash 0x3E0000 131b_1234/$UUID/partition_fixed.bin

# CRITICAL: Reboot device to load new credentials
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 run
```

**Step 7: Verify new QR code**
```bash
# Capture boot log
python3 - << 'PY'
import sys, time, serial
port = '/dev/cu.usbmodem101'
baud = 115200
out_path = 'boot_capture_new.txt'
ser = serial.Serial(port=port, baudrate=baud, timeout=0.1)
ser.reset_input_buffer(); ser.reset_output_buffer()
ser.dtr = False; ser.rts = False; time.sleep(0.05)
ser.dtr = True; ser.rts = True
end = time.time() + 12.0
with open(out_path, 'wb') as f:
    while time.time() < end:
        data = ser.read(4096)
        if data:
            f.write(data); f.flush()
        else:
            time.sleep(0.02)
ser.close()
print('Wrote to', out_path)
PY

# Check QR code
grep -A 3 "SetupQRCode" boot_capture_new.txt
```

**Step 8: Re-commission to Apple Home**
- Open Apple Home app → Add Accessory
- Scan new QR code or enter manual pairing code
- Verify device pairs successfully and responds to occupancy events

### Verified Results (October 16, 2025)

**Original Credentials:**
- QR Code: `MT:Y.K90GSY00KA0648G00`
- Manual Code: `34970112332`
- Passcode: 20202021
- Discriminator: 3840 (0xF00)

**New Credentials (v3):**
- QR Code: `MT:Y.K90GSY00AJVH7SR00` ✅
- Manual Code: `21403421094` ✅
- Passcode: 34567890
- Discriminator: 2048 (0x800)

**Status**: ✅ COMPLETED & VERIFIED
- Device successfully changed QR code
- Device re-commissioned to Apple Home
- PIR occupancy sensor functioning correctly
- Process fully documented and tested

---

## Additional Resources

For deeper technical understanding of Matter protocol, commissioning flows, and Apple Home integration, see:
- **[docs/MATTER-TECHNICAL-GUIDE.md](docs/MATTER-TECHNICAL-GUIDE.md)** - Comprehensive Matter fundamentals, PASE/CASE protocols, and advanced debugging

---

**End of Setup Guide** - For deeper technical understanding, see [docs/MATTER-TECHNICAL-GUIDE.md](docs/MATTER-TECHNICAL-GUIDE.md)