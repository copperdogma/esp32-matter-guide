<!-- 9af845c7-e192-472c-abb5-011a9b4636d7 e9924765-311d-47ec-aca3-746bff4d89fc -->
# ESP32-C3 Matter Occupancy Sensor Setup Plan

## Phase 0: Initialize Documentation & Clean Baseline

- Create `SETUP-GUIDE.md` as the primary living document
- Document will track every attempt, success, and failure in real-time
- Each subsequent step will be written to the doc BEFORE execution, then updated with results
- **CRITICAL FIRST STEP**: Perform complete chip erase to clear all NVS, fabrics, and credentials
- Document the erase command in SETUP-GUIDE.md
- Execute `esptool.py --chip esp32c3 -p /dev/tty.usbmodem101 erase_flash`
- Update doc with result

## Phase 1: Environment Verification & Setup

- Document environment verification steps in SETUP-GUIDE.md
- Verify ESP-IDF v5.4.1 and ESP-Matter installations are functional
- Test serial connection to ESP32-C3 at `/dev/tty.usbmodem101`
- Create shell alias `get_idf_matter` for environment initialization
- Verify `chip-cert` and `esp-matter-mfg-tool` are available
- Update SETUP-GUIDE.md with results (success/failure/issues)

## Phase 2: Build Occupancy Sensor Firmware

- Start from ESP-Matter occupancy sensor example (`examples/occupancy_sensor`)
- Configure for ESP32-C3 target with GPIO3 for PIR sensor input
- Set up proper partition table with dedicated factory partition (`fctry`)
- Configure sdkconfig for production credentials:
- Disable `CONFIG_ENABLE_TEST_SETUP_PARAMS`
- Enable factory data providers
- Point to `fctry` partition
- Build and verify compilation succeeds

## Phase 3: Generate Unique Credentials

- Generate test PAA certificate using `chip-cert`
- Generate Certification Declaration (CD)
- Use `esp-matter-mfg-tool` to create factory partition binary with:
- Unique passcode and discriminator
- SPAKE2+ verifier
- DAC/PAI certificates
- Device info (VID: 0x131B, PID: 0x1234, device type: 0x0107 for occupancy sensor)
- Save QR code and commissioning credentials

## Phase 4: Flash & Commission Device

- Full flash sequence:
- Flash bootloader, partition table, firmware
- Flash factory data to `fctry` partition address
- Erase operational NVS to ensure clean commissioning state
- Monitor serial output for healthy boot indicators:
- "CHIPoBLE advertising started"
- "cm=1" (commissioning mode)
- Correct QR code display
- Commission to Apple Home via QR code scan
- Verify occupancy sensor appears and responds to PIR input on GPIO3

## Phase 5: Test Credential Regeneration

- Generate a second set of unique credentials
- Erase operational NVS only (preserve firmware)
- Flash new factory partition
- Verify device advertises with new QR code
- Commission as "new" device to Apple Home
- Confirm both devices can coexist (different credentials)

## Phase 6: Document Streamlined Process

- Create final setup guide with:
- One-time environment setup steps
- Firmware build commands
- Credential generation workflow
- Complete flash sequence with exact addresses
- NVS erasure for re-commissioning
- Troubleshooting section based on PROVISIONING.md gotchas
- How to change QR code on demand
- Include validation steps and expected serial output
- Add notes on pitfalls/corrections for esp32-matter-guide.md

## Key Technical Details

- **Serial Port**: `/dev/tty.usbmodem101`
- **PIR Sensor**: GPIO3
- **Device Type**: 0x0107 (Occupancy Sensor)
- **Partition Strategy**: Separate `fctry` partition for factory data, regular `nvs` for operational data
- **Critical NVS Addresses**: Verify from partition table (likely nvs at 0x9000 or 0x10000, fctry at higher address)
- **Credential Generation**: Use `esp-matter-mfg-tool` as primary method for repeatability

### To-dos

- [ ] Verify ESP-IDF and ESP-Matter installations are functional, test tools availability
- [ ] Build occupancy sensor firmware from ESP-Matter example with GPIO3 PIR configuration
- [ ] Generate PAA, CD, and factory partition binary with unique credentials using mfg-tool
- [ ] Flash complete device and commission to Apple Home, verify PIR functionality
- [ ] Test credential regeneration workflow - generate new credentials and re-flash
- [ ] Create streamlined setup guide document with all steps and troubleshooting
- [ ] Test guide by following it from scratch to ensure completeness and accuracy