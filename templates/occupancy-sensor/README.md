# Occupancy Sensor Template

This template demonstrates how to implement a Matter-compatible occupancy sensor using an ESP32-C3 with a PIR (Passive Infrared) motion sensor.

## What's Occupancy-Sensor Specific

### Matter Configuration
- **Endpoint Type**: `occupancy_sensor` (not `temperature_sensor`, `light`, etc.)
- **Cluster**: OccupancySensing (0x0406)
- **Sensor Type**: PIR (`OccupancySensorTypeEnum::kPir`)
- **Occupancy Attribute**: Binary (occupied = true/false)

### Hardware Integration
- **GPIO Pin**: GPIO 3 (`CONFIG_PIR_DATA_PIN`) - configurable via `idf.py menuconfig` under "Example Configuration"
- **Interrupt Type**: `GPIO_INTR_ANYEDGE` - triggers on both rising and falling edges
- **Pull Mode**: `GPIO_PULLDOWN_ONLY` - ensures clean signal when motion is not detected
- **Note**: Default PIR GPIO in ESP-Matter examples is GPIO 7, but can be changed to match your hardware

### Key Code Sections

#### In `app_main.cpp`:
- **Lines 38-52**: `occupancy_sensor_notification()` - Schedules attribute updates when motion is detected
- **Lines 140-148**: Occupancy sensor endpoint creation with PIR type configuration
- **Lines 150-156**: PIR driver initialization with callback to `occupancy_sensor_notification()`

#### In `drivers/pir.cpp`:
- **Lines 25-37**: `pir_gpio_handler()` - ISR that detects occupancy state changes
- **Lines 39-49**: GPIO initialization with interrupt configuration
- **Line 16**: `PIR_SENSOR_PIN` - the specific GPIO pin used

## Adapting for Other Sensor Types

To adapt this template for a different sensor type (e.g., temperature, humidity, light, contact):

1. **Change the endpoint type** in `app_main.cpp`:
   - Replace `occupancy_sensor::create()` with appropriate type (e.g., `temperature_sensor::create()`)
   - Update the cluster configuration (e.g., `TemperatureMeasurement::Id`)

2. **Modify the driver**:
   - Replace PIR driver with your sensor's driver
   - Update GPIO configuration or I2C/SPI initialization as needed
   - Change the data type (bool → int16_t for temperature, uint16_t for humidity, etc.)

3. **Update the callback**:
   - Modify `occupancy_sensor_notification()` to match your sensor's data format
   - Use appropriate attribute IDs for your cluster type

## What Stays the Same

The following parts are generic to all Matter devices and should rarely need changes:
- Commissioning setup and window management
- Factory reset button handling
- Network configuration (WiFi/Thread)
- Matter stack initialization (`esp_matter::start()`)
- Event callbacks for fabric management
- Onboarding code printing

## Hardware Requirements

- ESP32-C3 development board
- PIR motion sensor (e.g., HC-SR501, AM312)
- Connection: PIR OUT → GPIO 3 (configurable), VCC → 3.3V, GND → GND

An AI working with this template would understand that the GPIO pin, sensor type, and attribute updates are the primary things to modify for different sensor implementations.

