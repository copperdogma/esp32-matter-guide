# ESP-Matter Patch Summary

## ✅ Patch Setup Complete (October 16, 2025)

### What Was Created

1. **Patch File**: `patches/esp32-factory-data-provider-getsetuppasscode.patch`
   - Implements `ESP32FactoryDataProvider::GetSetupPasscode()` 
   - Fixes upstream bug where function returns `NOT_IMPLEMENTED`
   - Enables QR code and manual pairing code generation

2. **Patch README**: `patches/README.md`
   - Documents the patch purpose and usage
   - Includes check script to verify if patch is still needed
   - Instructions for reporting when bug is fixed upstream

3. **Updated SETUP-GUIDE.md**:
   - Added patch check as Step 0 (required first step)
   - Updated QR Code Resolution section with patch instructions
   - Includes warnings to check upstream status before applying
   - References patch file instead of manual edits

### Current System Status

- ✅ Your ESP32-Matter installation is **already patched** (manually applied earlier)
- ✅ Patch file created for **future fresh installations**
- ✅ Documentation updated with **check-first workflow**

### For Future Users / AI Agents

**CRITICAL**: Always run the patch check first:

```bash
if grep "GetSetupPasscode.*override" ~/esp/esp-matter/connectedhomeip/connectedhomeip/src/platform/ESP32/ESP32FactoryDataProvider.h | grep -q "CHIP_ERROR_NOT_IMPLEMENTED"; then
    echo "⚠️ Bug exists - apply patch"
    cd ~/esp/esp-matter
    patch -p1 < /path/to/patches/esp32-factory-data-provider-getsetuppasscode.patch
else
    echo "✅ Bug fixed upstream - skip patch!"
    echo "📝 Update SETUP-GUIDE.md to remove patch instructions"
fi
```

### If Bug Gets Fixed Upstream

When ESP-Matter fixes this bug, the AI should:

1. **Detect the fix** using the check script
2. **Alert the user** with the good news message
3. **Suggest updates**:
   - Remove patch instructions from SETUP-GUIDE.md
   - Delete the patch file
   - Update this summary

### Additional Requirements

After applying the patch (if needed), you must also:

1. **Add `pin-code` to factory CSV** (esp-matter-mfg-tool omits this):
   ```csv
   pin-code,data,u32,20202021
   ```

2. **Regenerate factory partition**:
   ```bash
   python $IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py generate \
     partition.csv partition.bin 0x6000
   ```

3. **Rebuild firmware** (to include patched provider)

4. **Flash both** firmware and factory partition

### Success Criteria

When everything works correctly, you should see:

```
I (1390) chip[SVR]: SetupQRCode: [MT:Y.K90GSY00KA0648G00]
I (1400) chip[SVR]: Copy/paste the below URL in a browser to see the QR Code:
I (1410) chip[SVR]: https://project-chip.github.io/connectedhomeip/qrcode.html?data=MT%3AY.K90GSY00KA0648G00
I (1420) chip[SVR]: Manual pairing code: [34970112332]
```

### Reporting Upstream

If the bug still exists when you read this, please report to:
- https://github.com/espressif/esp-matter/issues
- Title: "ESP32FactoryDataProvider::GetSetupPasscode() returns NOT_IMPLEMENTED"
- Impact: Breaks QR code generation for factory data providers
- Fix: Implement function to read from NVS (see patch for details)

