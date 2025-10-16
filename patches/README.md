# ESP-Matter Patches

This directory contains patches for known bugs in the ESP-Matter repository.

## ⚠️ IMPORTANT: Check Before Applying

**Always check if patches are still needed** before applying them. Upstream bugs may be fixed in newer versions.

## Available Patches

### esp32-factory-data-provider-getsetuppasscode.patch

**Bug**: ESP32FactoryDataProvider::GetSetupPasscode() returns `CHIP_ERROR_NOT_IMPLEMENTED`  
**Impact**: QR code and manual pairing code generation fails with error 2d  
**Affects**: ESP-Matter as of October 2025  
**Upstream Issue**: https://github.com/espressif/esp-matter/issues (report if still exists)

**Check if still needed**:
```bash
if grep "GetSetupPasscode.*override" ~/esp/esp-matter/connectedhomeip/connectedhomeip/src/platform/ESP32/ESP32FactoryDataProvider.h | grep -q "CHIP_ERROR_NOT_IMPLEMENTED"; then
    echo "Patch NEEDED - bug still exists"
else
    echo "Patch NOT needed - bug fixed upstream!"
fi
```

**Apply patch**:
```bash
cd ~/esp/esp-matter
patch -p1 < /path/to/this/patch/esp32-factory-data-provider-getsetuppasscode.patch
```

**What it does**:
- Implements `GetSetupPasscode()` to read `pin-code` from NVS
- Allows QR code generator to access the setup passcode
- Matches implementation pattern used by all other platforms (STM32, Nordic, NXP, etc.)

**Additional steps required**:
1. Add `pin-code` entry to factory partition CSV (esp-matter-mfg-tool omits this)
2. Regenerate factory partition binary
3. Rebuild firmware to include patched provider

See SETUP-GUIDE.md for complete instructions.

## Reporting Fixed Bugs

If you find that a patch is no longer needed:

1. **Alert the user** that the bug is fixed
2. **Update SETUP-GUIDE.md** to remove patch instructions
3. **Delete the obsolete patch** from this directory
4. **Update this README** to reflect the fix

Example message:
```
🎉 GOOD NEWS: ESP-Matter has fixed the GetSetupPasscode bug upstream!
The patch esp32-factory-data-provider-getsetuppasscode.patch is NO LONGER NEEDED.

Please:
1. Skip patch application
2. Update SETUP-GUIDE.md
3. Delete the patch file
```

