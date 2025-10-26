# ESP32-C3 Matter Occupancy Sensor Setup Guide

**Last Updated**: October 17, 2025  
**Status**: Complete and Verified using Claude 4.5 Sonnet to execute the commands.
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

**📝 macOS Serial Port Note**: On macOS, use `/dev/cu.usbmodem101` for flashing/writing (esptool) and `/dev/tty.usbmodem101` for monitoring (idf.py monitor). The `cu` (call-up) device allows non-blocking writes, while `tty` is for terminal interaction.

---

## 🚀 ESSENTIAL QUICK-REFERENCE COMMANDS

### Environment Setup (Required First)
```bash
# Initialize ESP-IDF and ESP-Matter environments
cd ~/esp/esp-idf && source ./export.sh && cd ~/esp/esp-matter && source ./export.sh && export IDF_CCACHE_ENABLE=1
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
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 write_flash 0x3E0000 131b_1234/<UUID>/partition_fixed.bin
```

### Using the Template Firmware
**Location**: `templates/occupancy-sensor/` - Minimal working PIR occupancy sensor firmware (can adapt to any device type)

```bash
# From project root directory
cp -r ~/esp/esp-matter/examples/sensors ./firmware
cd firmware
cp $PROJECT_ROOT/templates/occupancy-sensor/app_main.cpp main/
cp $PROJECT_ROOT/templates/occupancy-sensor/drivers/pir.* main/drivers/

# Build and flash
idf.py set-target esp32c3 && idf.py build
idf.py -p /dev/cu.usbmodem101 flash
idf.py -p /dev/tty.usbmodem101 monitor
```

**To change device type**: Replace `endpoint::create()` in `main/app_main.cpp` with your target device (see `~/esp/esp-matter/examples/` for reference). Keep sdkconfig credentials unchanged.

### 3. Monitor Serial Output
```bash
# Human (interactive) monitoring only
# First setup environment, then navigate to project, then monitor
source ~/esp/esp-idf/export.sh && source ~/esp/esp-matter/export.sh
idf.py -p /dev/tty.usbmodem101 monitor
```

### 3.1 Capture Full Boot Log (Non-Interactive, AI-Friendly)
```bash
# Use the provided boot capture script (requires pyserial: pip install pyserial)
# This automatically resets the device and captures ~12 seconds of serial output
$PROJECT_ROOT/scripts/capture_boot.py

# Or with custom options:
$PROJECT_ROOT/scripts/capture_boot.py -p /dev/cu.usbmodem101 -o boot_capture.txt -d 15

# Inspect captured log
head -200 boot_capture.txt

# Get help on all options
$PROJECT_ROOT/scripts/capture_boot.py --help
```

**🤖 AI Note**: When providing setup summaries, always include the QR code HTTP link:
```bash
# Extract QR code and generate HTTP link for AI summary
QR_CODE=$(grep "SetupQRCode:" boot_capture.txt | sed 's/.*\[\(.*\)\].*/\1/')
if [ ! -z "$QR_CODE" ]; then
    echo "QR Code: $QR_CODE"
    echo "QR Code URL: https://project-chip.github.io/connectedhomeip/qrcode.html?data=$(echo $QR_CODE | sed 's/:/%3A/g')"
fi
```

**Features:**
- Automatically resets device via DTR/RTS toggle
- Captures full boot sequence including QR codes
- Analyzes output for common issues (QR code present, crashes, errors)
- Configurable port, duration, and output file

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

### Known Issue: QR Code Not Printing (GetSetupPasscode Bug)

**Symptom**: QR code fails to generate with error `2d` (PERSISTED_STORAGE_VALUE_NOT_FOUND)

**Root Cause**: As of October 2025, ESP-Matter's `ESP32FactoryDataProvider::GetSetupPasscode()` returns `CHIP_ERROR_NOT_IMPLEMENTED`, and `esp-matter-mfg-tool` omits the `pin-code` NVS entry.

**Check if bug is fixed** (run this first - covered in Step 2):
```bash
if grep "GetSetupPasscode.*override" ~/esp/esp-matter/connectedhomeip/connectedhomeip/src/platform/ESP32/ESP32FactoryDataProvider.h | grep -q "CHIP_ERROR_NOT_IMPLEMENTED"; then
    echo "⚠️  Bug exists - follow fix below"
else
    echo "✅ Bug fixed upstream - skip this section!"
fi
```

**Fix** (if bug exists):
1. Apply patch (from project root): `cd ~/esp/esp-matter && patch -p1 < $PROJECT_ROOT/patches/esp32-factory-data-provider-getsetuppasscode.patch`
2. After running `esp-matter-mfg-tool`, edit `131b_1234/<UUID>/internal/partition.csv` and add:
   ```
   pin-code,data,u32,<your-passcode>
   ```
   (right after the `discriminator` line, using your actual passcode)
3. Regenerate partition: `python $IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py generate partition.csv partition_fixed.bin 0x6000`
4. Rebuild, flash firmware, and flash factory partition

**Expected Result**: QR code and manual pairing code now print in serial output

### 4. Generate Credentials (Complete Workflow)
```bash
# Generate random unique values for this device
PASSCODE=$(shuf -i 10000000-99999999 -n 1)
DISCRIMINATOR=0x$(printf "%03X" $((RANDOM % 4096)))
CERT_ID="ZIG20142ZB330$(printf "%03d" $((RANDOM % 1000)))-24"
echo "Generated unique credentials:"
echo "  Passcode: $PASSCODE"
echo "  Discriminator: $DISCRIMINATOR"
echo "  Certificate ID: $CERT_ID"

# Generate PAA certificate
chip-cert gen-att-cert --type a --subject-cn "ESP32-C3 Matter PAA" --valid-from "2024-01-01 00:00:00" --lifetime 3650 --out-key ESP32_C3_Matter_PAA_key.pem --out ESP32_C3_Matter_PAA_cert.pem

# Generate PAI certificate  
chip-cert gen-att-cert --type i --subject-cn "ESP32-C3 Matter PAI" --subject-vid 0x131B --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key ESP32_C3_Matter_PAA_key.pem --ca-cert ESP32_C3_Matter_PAA_cert.pem --out-key ESP32_C3_Matter_PAI_key.pem --out ESP32_C3_Matter_PAI_cert.pem

# Generate DAC certificate
chip-cert gen-att-cert --type d --subject-cn "ESP32-C3 Matter DAC" --subject-vid 0x131B --subject-pid 0x1234 --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key ESP32_C3_Matter_PAI_key.pem --ca-cert ESP32_C3_Matter_PAI_cert.pem --out-key ESP32_C3_Matter_DAC_key.pem --out ESP32_C3_Matter_DAC_cert.pem

# Generate Certification Declaration
chip-cert gen-cd --key ESP32_C3_Matter_PAA_key.pem --cert ESP32_C3_Matter_PAA_cert.pem --out ESP32_C3_Matter_CD.der --format-version 1 --vendor-id 0x131B --product-id 0x1234 --device-type-id 0x0107 --certificate-id "$CERT_ID" --security-level 0 --security-info 0 --version-number 1 --certification-type 0

# Generate factory partition with unique credentials
esp-matter-mfg-tool -v 0x131B -p 0x1234 --passcode $PASSCODE --discriminator $DISCRIMINATOR --dac-cert ESP32_C3_Matter_DAC_cert.pem --dac-key ESP32_C3_Matter_DAC_key.pem --pai --cert ESP32_C3_Matter_PAI_cert.pem --key ESP32_C3_Matter_PAI_key.pem --cert-dclrn ESP32_C3_Matter_CD.der --lifetime 2000 --outdir .
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

### Step 0: Set Up Project Directory

**Option A - New Setup**: Clone this repository first to access patches and templates:

```bash
cd ~/Documents  # or wherever you keep projects
git clone https://github.com/copperdogma/esp32-matter-guide.git
cd esp32-matter-guide
PROJECT_ROOT=$(pwd)
```

**Option B - Existing Project**: If you already have a project with templates and patches:

```bash
cd ~/path/to/your/project  # e.g., ~/Documents/Projects/death-matter-controller
PROJECT_ROOT=$(pwd)
```

**📁 Directory Structure**: All commands in this guide assume you're working from the project root (`$PROJECT_ROOT`). Your firmware project will be created in `firmware/` subdirectory, which keeps all project files, credentials, and build artifacts organized in one place.

### Step 1: Install ESP-IDF and ESP-Matter

```bash
# Install dependencies
xcode-select --install
brew install cmake ninja ccache python@3.10

# For Apple Silicon Macs (M1/M2/M3): Install Rosetta 2 (optional but recommended)
# ESP-IDF 5.x has native ARM64 support, but some dependencies may still need x86_64
# You can skip this and only install if you encounter "Bad CPU type" errors
/usr/sbin/softwareupdate --install-rosetta --agree-to-license

# Clone ESP-IDF 5.4.1
mkdir -p ~/esp
cd ~/esp
git clone -b v5.4.1 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32c3

# IMPORTANT: Ensure all submodules are initialized (--recursive flag sometimes misses some)
git submodule update --init --recursive

# Clone ESP-Matter
cd ~/esp
git clone --depth 1 https://github.com/espressif/esp-matter.git
cd esp-matter
git submodule update --init --depth 1
cd connectedhomeip/connectedhomeip
./scripts/checkout_submodules.py --platform esp32 darwin --shallow
cd ../..
./install.sh

# macOS-specific workaround: If install.sh fails with "externally-managed-environment" error
# This is due to macOS/Python PEP 668 restrictions on newer macOS versions
# Run this if you see that error:
pip3 install --break-system-packages -r connectedhomeip/connectedhomeip/scripts/setup/requirements.build.txt
```

### Step 2: Check and Apply Upstream Patches

```bash
# From the project root directory
# Check if the GetSetupPasscode bug exists
if grep "GetSetupPasscode.*override" ~/esp/esp-matter/connectedhomeip/connectedhomeip/src/platform/ESP32/ESP32FactoryDataProvider.h | grep -q "CHIP_ERROR_NOT_IMPLEMENTED"; then
    echo "⚠️  Bug exists - applying patch..."
    cd ~/esp/esp-matter
    patch -p1 < $PROJECT_ROOT/patches/esp32-factory-data-provider-getsetuppasscode.patch
    cd -  # Return to previous directory
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

# Navigate to project root
cd $PROJECT_ROOT

# Copy the sensors example from ESP-Matter (includes build infrastructure)
# This creates the firmware folder INSIDE your project
cp -r ~/esp/esp-matter/examples/sensors ./firmware
cd firmware

# Replace with template files (occupancy-only, no I2C conflicts)
cp $PROJECT_ROOT/templates/occupancy-sensor/app_main.cpp main/
cp $PROJECT_ROOT/templates/occupancy-sensor/drivers/pir.* main/drivers/

# Configure for ESP32-C3
idf.py set-target esp32c3

# Configure sdkconfig for production credentials
# Method 1: Direct edit (recommended for AI agents and automation)
cat >> sdkconfig << 'EOF'
CONFIG_ENABLE_ESP32_FACTORY_DATA_PROVIDER=y
CONFIG_ENABLE_ESP32_DEVICE_INSTANCE_INFO_PROVIDER=y
CONFIG_USE_FACTORY_DATA_FOR_COMMISSIONING_VALUES=y
# CONFIG_ENABLE_TEST_COMMISSIONING_CREDENTIALS is not set
CONFIG_CHIP_FACTORY_NAMESPACE_PARTITION_LABEL="fctry"
CONFIG_PIR_DATA_PIN=3
EOF

# Apply configuration changes
idf.py reconfigure

# Method 2: Interactive menuconfig (HUMANS ONLY - requires TTY)
# AI agents cannot use interactive tools, so skip this if you're an AI
# If you're a human, you can instead run:
#   idf.py menuconfig
# Then navigate to:
#   - "Component config" → "CHIP Device Layer" → "Matter Device Config"
#     ✓ Enable "ESP32 Factory Data Provider"
#     ✓ Enable "ESP32 Device Instance Info Provider"  
#   - "Component config" → "CHIP Device Layer" → "Commissioning options"
#     ✓ Enable "Use Commissioning Data from Factory Partition"
#     ✗ DISABLE "Enable Test Commissioning Credentials"
#   - "Component config" → "CHIP Device Layer" → "Factory Partition Label"
#     Set to: "fctry"
#   - "Example Configuration"
#     Set "PIR Data Pin" to: 3
#   Save and exit
```

### Step 4: Generate Unique Device Credentials

```bash
# Generate random unique values for this device
PASSCODE=$(shuf -i 10000000-99999999 -n 1)
DISCRIMINATOR=0x$(printf "%03X" $((RANDOM % 4096)))
CERT_ID="ZIG20142ZB330$(printf "%03d" $((RANDOM % 1000)))-24"
echo "Generated unique credentials:"
echo "  Passcode: $PASSCODE"
echo "  Discriminator: $DISCRIMINATOR"
echo "  Certificate ID: $CERT_ID"

# Generate certificate chain
chip-cert gen-att-cert --type a --subject-cn "Matter PAA" --valid-from "2024-01-01 00:00:00" --lifetime 3650 --out-key PAA_key.pem --out PAA_cert.pem

chip-cert gen-att-cert --type i --subject-cn "Matter PAI" --subject-vid 0x131B --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key PAA_key.pem --ca-cert PAA_cert.pem --out-key PAI_key.pem --out PAI_cert.pem

chip-cert gen-att-cert --type d --subject-cn "Matter DAC" --subject-vid 0x131B --subject-pid 0x1234 --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key PAI_key.pem --ca-cert PAI_cert.pem --out-key DAC_key.pem --out DAC_cert.pem

chip-cert gen-cd --key PAA_key.pem --cert PAA_cert.pem --out CD.der --format-version 1 --vendor-id 0x131B --product-id 0x1234 --device-type-id 0x0107 --certificate-id "$CERT_ID" --security-level 0 --security-info 0 --version-number 1 --certification-type 0

# Generate factory partition with unique credentials
esp-matter-mfg-tool -v 0x131B -p 0x1234 --passcode $PASSCODE --discriminator $DISCRIMINATOR --dac-cert DAC_cert.pem --dac-key DAC_key.pem --pai --cert PAI_cert.pem --key PAI_key.pem --cert-dclrn CD.der --lifetime 2000 --outdir .
```

### Step 5: Add pin-code to Factory Partition

```bash
# Find the generated UUID directory and set UUID variable
ls -la 131b_1234/
UUID="<your-uuid-from-above>"  # Replace with actual UUID from ls output

# Add pin-code to factory partition CSV using sed
# ⚠️ IMPORTANT: Use the SAME passcode value you chose in Step 4
# This MUST match the PASSCODE variable from Step 4
sed -i.bak '/discriminator,data,u32,/a\
pin-code,data,u32,'"$PASSCODE" 131b_1234/$UUID/internal/partition.csv

# Verify the pin-code was added (should show the pin-code line)
grep "pin-code" 131b_1234/$UUID/internal/partition.csv

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

### Step 7: Verify Device Commissioning

```bash
# Capture boot log to verify QR code generation
$PROJECT_ROOT/scripts/capture_boot.py -p /dev/cu.usbmodem101 -o boot_capture.txt -d 15

# Check for QR code and commissioning info
grep -A 3 "SetupQRCode\|Manual pairing code\|CHIPoBLE advertising" boot_capture.txt

# Expected output shows your unique QR code and manual pairing code
# Example:
# I (xxxx) chip[SVR]: SetupQRCode: [MT:Y.XXXXXXXXXXXXXXX]
# I (xxxx) chip[SVR]: Copy/paste the below URL in a browser to see the QR Code:
# I (xxxx) chip[SVR]: https://project-chip.github.io/connectedhomeip/qrcode.html?data=MT%3AY.XXXXXXXXXXXXXXX
# I (xxxx) chip[SVR]: Manual pairing code: [XXXXXXXXXXX]
# I (xxxx) chip[DL]: CHIPoBLE advertising started

# Extract QR code for HTTP link generation
QR_CODE=$(grep "SetupQRCode:" boot_capture.txt | sed 's/.*\[\(.*\)\].*/\1/')
if [ ! -z "$QR_CODE" ]; then
    echo "QR Code: $QR_CODE"
    echo "QR Code URL: https://project-chip.github.io/connectedhomeip/qrcode.html?data=$(echo $QR_CODE | sed 's/:/%3A/g')"
fi
```

### Step 8: Commission to Apple Home

1. Open Apple Home app on iPhone/iPad
2. Tap "+" → "Add Accessory"
3. Scan the QR code from boot log, or enter manual pairing code
4. Follow prompts to complete setup
5. Test the occupancy sensor by waving your hand in front of the PIR sensor

**Success!** Your device should now appear in Apple Home and respond to motion detection.

---

## AI Testing/Fixing Loop

**🤖 For AI Agents**: After completing the setup, always perform this testing loop to verify the device is working correctly and fix any issues.

### Quick Test Command
```bash
# Capture device output with 30-second timeout
python3 scripts/capture_boot.py -p /dev/cu.usbmodem101 -o boot_test.txt -d 30

# Check for success indicators
grep -E "SetupQRCode|Manual pairing code|CHIPoBLE|Created.*endpoint.*ID:" boot_test.txt

# Check for errors
grep -E "ERROR|Error|error|abort|crash|failed|Failed" boot_test.txt
```

### Common Issues and Fixes

**Issue**: `Dynamic endpoint count cannot be greater than CONFIG_ESP_MATTER_MAX_DYNAMIC_ENDPOINT_COUNT`
- **Fix**: Increase `CONFIG_ESP_MATTER_MAX_DYNAMIC_ENDPOINT_COUNT` in `sdkconfig` to accommodate all endpoints
- **Rule**: Need `N+1` where N = number of dynamic endpoints (endpoint 0 is reserved for root)

**Issue**: Device crashes during endpoint creation
- **Fix**: Check endpoint count configuration and rebuild with `idf.py reconfigure && idf.py build`

**Issue**: No QR code generated
- **Fix**: Ensure factory partition is flashed and device has proper credentials

### Testing Loop Process
1. **Capture**: Run boot capture script
2. **Analyze**: Check for errors and success indicators
3. **Fix**: Address any issues found
4. **Rebuild**: `idf.py reconfigure && idf.py build`
5. **Flash**: `idf.py -p /dev/cu.usbmodem101 flash`
6. **Verify**: Re-run capture to confirm fix
7. **Repeat**: Until device boots cleanly with QR code

**Expected Success Output**:
- All endpoints created successfully (IDs 1-N)
- QR code generated: `SetupQRCode: [MT:...]`
- Manual pairing code: `Manual pairing code: [XXXXXXXXXXX]`
- No crash/abort errors

### Memory Allocation Errors (esp-aes)

**Issue**: Device crashes with `esp-aes: Failed to allocate memory` during boot
- **Cause**: Hardware AES acceleration requires memory allocation that can fail with limited heap
- **Fix**: Disable hardware AES in `sdkconfig` to use software AES:
  ```bash
  cd firmware
  # Edit sdkconfig to set:
  # CONFIG_MBEDTLS_HARDWARE_AES is not set
  idf.py reconfigure && idf.py build
  idf.py -p /dev/cu.usbmodem101 flash
  ```
- **Note**: Software AES uses more CPU but avoids heap allocation issues

### Factory Reset After Failed Commissioning

**Issue**: Device crashes with `esp-aes: Failed to allocate memory` after attempting Home app pairing
- **Cause**: Corrupted Matter commissioning data in NVS
- **Fix**: Erase flash completely and re-flash firmware:
  ```bash
  cd firmware
  idf.py -p /dev/cu.usbmodem101 erase-flash
  idf.py -p /dev/cu.usbmodem101 flash
  ```
- **Note**: This regenerates fresh credentials and QR code

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

**"error: externally-managed-environment" (macOS)**
- Cause: macOS Python PEP 668 restrictions on newer systems
- Symptom: ESP-Matter `./install.sh` fails during Python dependency installation
- Solution: Install dependencies with override flag:
  ```bash
  cd ~/esp/esp-matter
  pip3 install --break-system-packages -r connectedhomeip/connectedhomeip/scripts/setup/requirements.build.txt
  ```

**"fatal error: esp_app_desc.h: No such file or directory"**
- Cause: ESP-IDF submodules not fully initialized
- Solution: Initialize all submodules explicitly:
  ```bash
  cd ~/esp/esp-idf
  git submodule update --init --recursive
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

**"At least one of the feature(s) must be supported" - Occupancy Sensor Crash**
- Cause: Missing feature flag configuration for occupancy sensor cluster
- Error: `assert failed: ABORT_CLUSTER_CREATE`
- Symptom: Device crashes during endpoint creation, before QR code prints
- Solution: The template includes the required feature flag (as of Oct 2025), but if you're creating custom sensors, add:
  ```cpp
  occupancy_sensor_config.occupancy_sensing.feature_flags =
      cluster::occupancy_sensing::feature::passive_infrared::get_id();
  ```
  This must be set BEFORE calling `occupancy_sensor::create()`

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
cd $PROJECT_ROOT/firmware
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

**Step 2: Generate new unique credentials**
```bash
# Navigate to your firmware directory
cd $PROJECT_ROOT/firmware

# Generate new random values
PASSCODE=$(shuf -i 10000000-99999999 -n 1)
DISCRIMINATOR=0x$(printf "%03X" $((RANDOM % 4096)))
CERT_ID="ZIG20142ZB330$(printf "%03d" $((RANDOM % 1000)))-24"
echo "New credentials: Passcode=$PASSCODE, Discriminator=$DISCRIMINATOR, CertID=$CERT_ID"

# Generate certificate chain with new values
chip-cert gen-att-cert --type a --subject-cn "ESP32-C3 Matter PAA v3" --valid-from "2024-01-01 00:00:00" --lifetime 3650 --out-key ESP32_C3_Matter_PAA_v3_key.pem --out ESP32_C3_Matter_PAA_v3_cert.pem

# Generate PAI (Product Attestation Intermediate)
chip-cert gen-att-cert --type i --subject-cn "ESP32-C3 Matter PAI v3" --subject-vid 0x131B --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key ESP32_C3_Matter_PAA_v3_key.pem --ca-cert ESP32_C3_Matter_PAA_v3_cert.pem --out-key ESP32_C3_Matter_PAI_v3_key.pem --out ESP32_C3_Matter_PAI_v3_cert.pem

# Generate DAC (Device Attestation Certificate)
chip-cert gen-att-cert --type d --subject-cn "ESP32-C3 Matter DAC v3" --subject-vid 0x131B --subject-pid 0x1234 --valid-from "2024-01-01 00:00:00" --lifetime 3650 --ca-key ESP32_C3_Matter_PAI_v3_key.pem --ca-cert ESP32_C3_Matter_PAI_v3_cert.pem --out-key ESP32_C3_Matter_DAC_v3_key.pem --out ESP32_C3_Matter_DAC_v3_cert.pem

chip-cert gen-cd --key ESP32_C3_Matter_PAA_v3_key.pem --cert ESP32_C3_Matter_PAA_v3_cert.pem --out ESP32_C3_Matter_CD_v3.der --format-version 1 --vendor-id 0x131B --product-id 0x1234 --device-type-id 0x0107 --certificate-id "$CERT_ID" --security-level 0 --security-info 0 --version-number 1 --certification-type 0

# Generate factory partition with new credentials
esp-matter-mfg-tool -v 0x131B -p 0x1234 --passcode $PASSCODE --discriminator $DISCRIMINATOR --dac-cert ESP32_C3_Matter_DAC_v3_cert.pem --dac-key ESP32_C3_Matter_DAC_v3_key.pem --pai --cert ESP32_C3_Matter_PAI_v3_cert.pem --key ESP32_C3_Matter_PAI_v3_key.pem --cert-dclrn ESP32_C3_Matter_CD_v3.der --lifetime 2000 --outdir .
```

**Step 3: Add pin-code to factory CSV**
```bash
# Locate the generated UUID directory
ls -la 131b_1234/

# Add pin-code using the same passcode from Step 2
UUID="<your-uuid-here>"
sed -i.bak '/discriminator,data,u32,/a\
pin-code,data,u32,'"$PASSCODE" 131b_1234/$UUID/internal/partition.csv
```

**Step 4: Regenerate factory partition binary**
```bash
python $IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py generate 131b_1234/$UUID/internal/partition.csv 131b_1234/$UUID/partition_fixed.bin 0x6000
```

**Step 5: Erase NVS, flash new partition, and reboot**
```bash
# Erase operational NVS (clears old pairings)
python -m esptool --chip esp32c3 -p /dev/cu.usbmodem101 erase_region 0x10000 0xC000

# Flash new factory partition
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 write_flash 0x3E0000 131b_1234/$UUID/partition_fixed.bin

# Reboot device to load new credentials
esptool.py --chip esp32c3 -p /dev/cu.usbmodem101 run
```

**Step 6: Verify new credentials**
```bash
# Capture boot log to verify new QR code
$PROJECT_ROOT/scripts/capture_boot.py -p /dev/cu.usbmodem101 -o boot_capture_new.txt -d 15
grep -A 3 "SetupQRCode" boot_capture_new.txt

# Extract and display QR code with HTTP link
QR_CODE=$(grep "SetupQRCode:" boot_capture_new.txt | sed 's/.*\[\(.*\)\].*/\1/')
if [ ! -z "$QR_CODE" ]; then
    echo "New QR Code: $QR_CODE"
    echo "QR Code URL: https://project-chip.github.io/connectedhomeip/qrcode.html?data=$(echo $QR_CODE | sed 's/:/%3A/g')"
fi
```

**Step 7: Re-commission to Apple Home**
- Open Apple Home app → Add Accessory
- Scan new QR code or enter manual pairing code
- Verify device pairs successfully and responds to occupancy events

### Process Summary

This workflow generates completely unique credentials each time:
- **Passcode**: Random 8-digit number (10,000,000 - 99,999,999)
- **Discriminator**: Random hex value (0x000 - 0xFFF)
- **Certificate ID**: Random 3-digit suffix (000-999)
- **QR Code**: Automatically generated from unique values

**Result**: Each device gets a unique QR code and manual pairing code, preventing conflicts when commissioning multiple devices.

---

## Additional Resources

For deeper technical understanding of Matter protocol, commissioning flows, and Apple Home integration, see:
- **[docs/MATTER-TECHNICAL-GUIDE.md](docs/MATTER-TECHNICAL-GUIDE.md)** - Comprehensive Matter fundamentals, PASE/CASE protocols, and advanced debugging

---

**End of Setup Guide** - For deeper technical understanding, see [docs/MATTER-TECHNICAL-GUIDE.md](docs/MATTER-TECHNICAL-GUIDE.md)