# PROVISIONING – Handover Document

This document provides a concise summary of the project to provision an ESP32-C3 Matter device for reliable pairing with Apple Home.

### Main Task
The primary goal is to make an ESP32-C3 Matter device advertise with a unique, stable QR code and PIN, allowing it to be reliably commissioned by Apple Home as a fresh accessory. The end-goal is a two-zone occupancy sensor, but resolving the commissioning failures is the immediate priority.

### The Path to a Stable Baseline
The most effective strategy has been to revert to a known-good firmware baseline that pairs successfully, and then apply minimal, targeted changes to alter the commissioning credentials.

**One-Page Recovery & Pairing Plan:**
```bash
# 1. Start from a known-good firmware directory.

# 2. Clean, build, and flash the application.
cd firmware
idf.py fullclean && idf.py build && idf.py -p /dev/tty.usbmodem101 flash

# 3. CRITICAL: Erase regular NVS to clear old pairings/fabrics.
python -m esptool --chip esp32c3 -p /dev/tty.usbmodem101 erase_region 0x10000 0xC000

# 4. Reset the device, monitor the output, and pair with Apple Home.
# Monitor should show "CHIPoBLE advertising started".
idf.py -p /dev/tty.usbmodem101 monitor
```

### Key Failures & Lessons Learned ("Gotchas")

1.  **Symptom**: Apple Home shows "Accessory Not Found" and serial logs show **`Fabric already commissioned. Disabling BLE advertisement`**.
    *   **Cause**: The device believes it's already paired to a fabric and won't enter BLE commissioning mode.
    *   **Solution**: You **must** erase the regular NVS partition to clear stored fabrics. The 10s button press for factory reset proved unreliable. This is the most common and critical recovery step.
    *   **Command**: `python -m esptool --chip esp32c3 -p /dev/tty.usbmodem101 erase_region 0x10000 0xC000`

2.  **Symptom**: "Accessory Not Found" and serial logs show **`E chip[SVR]: ERROR setting up transport: 2d`**.
    *   **Cause**: A custom `CommissionableDataProvider` was introduced to provide a new PIN/discriminator but failed to provide a valid **SPAKE2p verifier**. The `CommissioningWindowManager` requires this to set up the PASE session and fails before starting BLE advertising.
    *   **Solution**: The custom provider's `GetSpake2pVerifier` method must be implemented. It should generate the verifier using `PASESession::GeneratePASEVerifier()` from the passcode, salt, and iteration count.

3.  **Symptom**: A panic/reboot loop with a **`Chip stack locking error`** or `AssertChipStackLockedByCurrentThread`.
    *   **Cause**: A Matter API was called from a task other than the main CHIP thread without acquiring the stack lock. This is a race condition.
    *   **Solution**:
        1.  Wrap all custom provider methods (`GetSetupPasscode`, `GetSpake2pVerifier`, etc.) with `chip::DeviceLayer::StackLock lock;`.
        2.  Open the commissioning window by scheduling it on the CHIP thread using `chip::DeviceLayer::PlatformMgr().ScheduleWork(open_commissioning_window_deferred);` rather than calling it directly or from a timer.

4.  **Symptom**: The device advertises an old/default QR code despite flashing new factory data.
    *   **Cause**: Several issues were encountered here:
        *   Flashing the factory NVS binary to the wrong memory address (e.g., the regular `nvs` partition instead of the `fctry` partition).
        *   The `sdkconfig` file not being configured to read from the factory partition (`CONFIG_CHIP_FACTORY_NAMESPACE_PARTITION_LABEL="fctry"`).
    *   **Solution**: Verify the `fctry` partition offset in `partitions.csv` (e.g., `0x3E0000`) and use that exact address in the `esptool.py write_flash` command. Ensure `sdkconfig` points to `"fctry"`.

### Interpreting Serial Output Anomalies

-   **Benign (Ignore)**:
    -   `Warning: Checksum mismatch...`: The flashed app is just older than the last build. Re-flash if you need the latest.
    -   `E esp_matter_cluster: Config is NULL...`: An optional config pointer in the example is null. Does not affect commissioning.
    -   `W wifi: Haven't to connect...`: Correct. The device has no Wi-Fi credentials yet. BLE pairing works without it.
    -   `W comm: pin-code not found in fctry NVS...`: OK for now. The code is correctly falling back to a hardcoded default. Will be resolved by flashing a complete factory NVS.
    -   `chip[DMG]: DefaultAclStorage: 0 entries loaded`: Expected for an uncommissioned device.
    -   `chip[SVR]: WARNING: mTestEventTriggerDelegate is null`: Expected. The test delegate isn't used.
-   **Critical (Action Required)**:
    -   `E chip[SVR]: ERROR setting up transport: 2d`: **BLOCKER**. SPAKE2p verifier is missing or invalid.
    -   `Chip stack locking error` / `chipDie`: **BLOCKER**. Threading violation. See "Gotchas" section.

### Path Forward to a Unique QR Code
1.  **Start with a known-good baseline** that pairs successfully.
2.  **Add a custom `CommissionableDataProvider`** (`commission_custom.cpp`/`.h`) that correctly implements `GetSetupPasscode`, `GetSetupDiscriminator`, `GetSpake2pIterationCount`, `GetSpake2pSalt`, and `GetSpake2pVerifier` (with stack locks).
3.  **Generate a complete factory NVS binary** using `esp-matter-mfg-tool`, ensuring it contains the passcode, discriminator, and valid DAC/PAI certificates.
4.  **Perform the full flash sequence**: `idf.py flash`, `esptool.py write_flash 0x3E0000 ...`, `esptool.py erase_region 0x10000 ...`.
5.  **Reboot and pair**. The device should now advertise the new, unique credentials from the factory partition.
