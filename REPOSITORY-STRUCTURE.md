# Repository Structure

This document explains what is committed to the repository vs. what is generated locally.

## 📦 What's in the Repository (Committed)

```
esp32-matter-guide/
├── .gitignore                  # Excludes build artifacts and credentials
├── SETUP-GUIDE.md             # ⭐ Main setup guide
├── PROVISIONING.md            # Provisioning documentation
├── esp32-matter-guide.md      # Additional guide content
├── PATCH-SUMMARY.md           # Patch documentation
└── patches/                   # Bug fixes for ESP-Matter
    ├── README.md
    └── esp32-factory-data-provider-getsetuppasscode.patch
```

**Total: 7 files** (all documentation and patches)

## 🚫 What's NOT in the Repository (Local Only)

### Firmware Builds
- `my_occupancy_sensor/` or `firmware/` - Created by following SETUP-GUIDE.md
- `build/` - ESP-IDF build artifacts
- `*.bin`, `*.elf`, `*.map` - Compiled binaries

### Credentials & Certificates (Security Sensitive!)
- `*.pem`, `*.der`, `*.key` - PKI certificates and keys
- `131b_1234/` - Factory partition data with device credentials
- `*-partition.bin` - Factory partitions with unique device IDs
- `*_PAA_*`, `*_PAI_*`, `*_DAC_*` - Certificate chain files

### Logs & Temporary Files
- `*.txt` - Serial output captures, logs
- `deep-research/` - AI research notes
- `temp-matter-occupancy-sensor/` - Old/temporary work
- `*.csv` - Credentials and manufacturing data (except partitions.csv in firmware)

## 🔄 How to Use This Repository

1. **Clone the repository**:
   ```bash
   git clone https://github.com/copperdogma/esp32-matter-guide.git
   cd esp32-matter-guide
   ```

2. **Follow SETUP-GUIDE.md**:
   - Sets up ESP-IDF and ESP-Matter
   - Applies necessary patches
   - Creates firmware directory with your device code
   - Generates unique credentials
   - Builds and flashes firmware

3. **Result**: You'll have a working Matter device with:
   - Firmware in `firmware/` (not committed)
   - Unique credentials in `131b_1234/` (not committed)
   - Build artifacts in `build/` (not committed)

## 🔒 Security Note

**NEVER commit credentials or certificates!** The `.gitignore` is configured to prevent this, but always verify before pushing:

```bash
# Check what will be committed
git status

# Verify no sensitive files
git diff --cached --name-only | grep -E '\.(pem|der|key|bin)$' && echo "⚠️ STOP! Credentials detected!"
```

## 📝 Contributing

When contributing to this repository:
- ✅ DO commit: Documentation improvements, patch updates
- ❌ DON'T commit: Build artifacts, credentials, local configurations
- ⚠️ VERIFY: Run `git status` before committing

## 🎯 Repository Purpose

This repository provides:
1. **Complete setup guide** for ESP32-C3 Matter devices
2. **Patches** for known ESP-Matter bugs  
3. **Documentation** for troubleshooting and best practices

It does NOT provide:
- Pre-built firmware (you build it)
- Credentials (you generate unique ones)
- Device-specific configurations (you create them)

This ensures every device has unique credentials and the guide remains device-agnostic.

