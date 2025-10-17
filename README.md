# ESP32-C3 Matter Device Guide

A comprehensive, AI-verified guide for building Matter-compatible devices with ESP32-C3 that commission successfully with Apple Home.

## 🎯 Purpose

This repository provides complete documentation for developing ESP32-C3 Matter devices from environment setup through successful commissioning. It includes patches for upstream bugs, troubleshooting procedures, and device templates—all verified by successfully commissioning an occupancy sensor to Apple Home.

## ✨ Key Features

- **Complete Setup Guide** - Step-by-step instructions from zero to working device
- **Upstream Bug Fixes** - Patches with instructions to check if still needed
- **Device Templates** - Working occupancy sensor example with PIR driver
- **Troubleshooting** - Solutions to common commissioning failures
- **Security-First** - Credentials never committed, generated uniquely per device

## 🚀 Quick Start

```bash
# 1. Clone this repository
git clone https://github.com/copperdogma/esp32-matter-guide.git
cd esp32-matter-guide

# 2. Follow the setup guide
open SETUP-GUIDE.md

# 3. Result: Working Matter device commissioned to Apple Home! 🎉
```

## 📚 Documentation

### Essential Reading
- **[SETUP-GUIDE.md](SETUP-GUIDE.md)** - ⭐ **START HERE** - Complete walkthrough from environment setup to commissioning
- **[patches/README.md](patches/README.md)** - Upstream bug fixes and how to check if still needed
- **[templates/occupancy-sensor/README.md](templates/occupancy-sensor/README.md)** - Working PIR sensor example

### Additional Resources
- **[docs/MATTER-TECHNICAL-GUIDE.md](docs/MATTER-TECHNICAL-GUIDE.md)** - Deep dive into Matter protocol, PASE/CASE sessions, and Apple Home integration
- **[LICENSE](LICENSE)** - MIT License

## 📦 Repository Structure

### What's Committed (Documentation Focus)

```
esp32-matter-guide/
├── README.md                  # This file
├── LICENSE                    # MIT License
├── SETUP-GUIDE.md            # ⭐ Main setup guide
├── .gitignore                # Excludes build artifacts and credentials
│
├── patches/                  # Upstream bug fixes
│   ├── README.md
│   └── esp32-factory-data-provider-getsetuppasscode.patch
│
├── templates/                # Device implementation examples
│   └── occupancy-sensor/
│       ├── README.md         # Occupancy sensor guide
│       ├── app_main.cpp      # Main application code
│       └── drivers/          # PIR sensor driver
│           ├── pir.h
│           └── pir.cpp
│
└── docs/                     # Technical deep-dives
    └── MATTER-TECHNICAL-GUIDE.md
```

### What's NOT Committed (Generated Locally)

**Firmware & Builds**
- `firmware/` - Created by following SETUP-GUIDE.md
- `build/` - ESP-IDF build artifacts
- `*.bin`, `*.elf`, `*.map` - Compiled binaries

**Credentials & Certificates** (Security Sensitive!)
- `*.pem`, `*.der`, `*.key` - PKI certificates and keys
- `131b_1234/` - Factory partition data with device credentials
- `*-partition.bin` - Factory partitions with unique device IDs
- `*_PAA_*`, `*_PAI_*`, `*_DAC_*` - Certificate chain files

**Logs & Temporary Files**
- `*.txt` - Serial output captures, logs
- `deep-research/` - AI research notes
- `*.csv` - Credentials and manufacturing data (except `partitions.csv` in firmware)

## 🔧 What You'll Build

Following this guide, you'll:

1. **Set up development environment** - ESP-IDF 5.4.1 + ESP-Matter
2. **Apply necessary patches** - Fix upstream `GetSetupPasscode` bug if needed
3. **Create firmware** - Using occupancy sensor template or custom implementation
4. **Generate unique credentials** - PAA, PAI, DAC certificates and SPAKE2+ verifiers
5. **Build and flash** - Complete device programming
6. **Commission successfully** - Pair with Apple Home via QR code

**Success Criteria**: Device shows QR code at boot, pairs with Apple Home, and responds to occupancy events.

## 🐛 Known Issues & Solutions

### ESP32FactoryDataProvider GetSetupPasscode Bug

**Issue**: `ESP32FactoryDataProvider::GetSetupPasscode()` returns `CHIP_ERROR_NOT_IMPLEMENTED`, preventing QR code generation.

**Status**: Upstream bug (as of Oct 2025). Patch provided.

**Solution**: See [patches/README.md](patches/README.md) for detection script and patch application.

## 🔒 Security

**⚠️ NEVER commit credentials or certificates!**

The `.gitignore` is configured to prevent this, but always verify:

```bash
# Check what will be committed
git status

# Verify no sensitive files
git diff --cached --name-only | grep -E '\.(pem|der|key|bin)$' && echo "⚠️ STOP! Credentials detected!"
```

Every device should have **unique** credentials. This guide shows you how to generate them.

## 🎓 Learning Path

1. **New to Matter?** Start with [docs/MATTER-TECHNICAL-GUIDE.md](docs/MATTER-TECHNICAL-GUIDE.md) for protocol fundamentals
2. **Ready to build?** Follow [SETUP-GUIDE.md](SETUP-GUIDE.md) step-by-step
3. **Hit an issue?** Check the Troubleshooting section in [SETUP-GUIDE.md](SETUP-GUIDE.md)
4. **Creating different sensor?** Use [templates/occupancy-sensor/](templates/occupancy-sensor/) as reference

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [ESP-IDF](https://github.com/espressif/esp-idf) and [ESP-Matter](https://github.com/espressif/esp-matter)
- Commissioned successfully with Apple Home on iOS 18
- Guide refined through extensive AI-assisted debugging and verification

---

**Ready to build Matter devices?** Start with [SETUP-GUIDE.md](SETUP-GUIDE.md)! 🚀

