# AquaSense: ESP32 Firmware Guide

This directory contains the firmware code for the **AquaSense** Smart Irrigation controller, developed for the **ESP32** microcontroller.

The firmware implements the core sensor read cycles, analog-to-digital (ADC) linear calibration, automatic threshold activation with hysteresis, button overrides, and safety timer lockouts.

---

## 1. Hardware Pin Configurations

| Device / Component | Pin Name | ESP32 GPIO | Connection details |
|---|---|---|---|
| **Soil Moisture Sensor** | Analog Out (A0) | **GPIO 34** | Reads analog moisture level (ADC1 Channel 6) |
| **Pump Relay** | Signal / In | **GPIO 26** | Drives 5V/12V Relay coil via transistor/optoisolator |
| **Mode Toggle Button** | Button Pin | **GPIO 25** | Connects to GND (Internal `INPUT_PULLUP` enabled) |
| **Manual Pump Button** | Button Pin | **GPIO 27** | Connects to GND (Internal `INPUT_PULLUP` enabled) |
| **Status LED** | LED Pin | **GPIO 2** | Built-in ESP32 LED; flashes on errors/cooldowns |
| **Buzzer** | VCC / IO | **GPIO 14** | Active buzzer for audible alerts |

---

## 2. Setting Up the Arduino IDE

To compile and upload the sketch:

1. **Download and Install Arduino IDE**: Ensure you are running version 1.8.x or 2.x.
2. **Install ESP32 Core**:
   - In Arduino IDE, navigate to `File` > `Preferences`.
   - Add this URL to the **Additional Board Manager URLs**:  
     `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Navigate to `Tools` > `Board` > `Boards Manager...`.
   - Search for **esp32** and install the latest version.
3. **Select Board**:
   - Go to `Tools` > `Board` > `ESP32 Arduino` and select **ESP32 Dev Module** (or your specific ESP32 board).
4. **Select Serial Port**:
   - Plug the ESP32 board into your computer's USB port.
   - Go to `Tools` > `Port` and select the active COM/TTY port.
5. **Set Serial Speed**:
   - Open the Serial Monitor (`Tools` > `Serial Monitor`).
   - Set the baud rate to **115200**.

---

## 3. Sensor Calibration Steps

Capacitive soil moisture sensors give raw analog voltage outputs. Because voltage varies with soil conditions, sensor brands, and wire length, you must calibrate the values:

1. **Air Dry Value (`DRY_RAW_VALUE`)**:
   - Hold the sensor in dry air.
   - Observe the raw values printed on the Serial Monitor.
   - Edit the constant in `esp32_aquasense.ino`:
     ```cpp
     const int DRY_RAW_VALUE = 3000; // Replace with your air reading
     ```
2. **Saturated Wet Value (`WET_RAW_VALUE`)**:
   - Submerge the sensor in water up to the max line (do not submerge the electronics at the top!).
   - Note the raw values printed.
   - Edit the constant:
     ```cpp
     const int WET_RAW_VALUE = 1200; // Replace with your water reading
     ```
3. **Recompile and Upload**: Flash the modified code back to the ESP32.

---

## 4. Serial Data Reporting Format

The firmware prints comma-separated (CSV) lines to the Serial Monitor at 1-second intervals. This output format is designed to be easily parsed by edge devices, computers, or the AquaSense Python serial logger:

`RAW_VALUE,MOISTURE_PERCENT,PUMP_STATUS,MODE,EVENT`

### Examples
* **Soil Dry (Pump triggered):** `2950,2.7,ON,AUTO,SOIL_DRY_PUMP_ON`
* **Irrigating (Normal run):** `2450,30.5,ON,AUTO,NORMAL`
* **Soil Wet (Pump shuts off):** `1180,100.0,OFF,AUTO,SOIL_WET_PUMP_OFF`
* **Cooldown Guard Active:** `2800,11.1,OFF,AUTO,COOLDOWN_ACTIVE`
* **Sensor Error Safety Alert:** `0,0.0,OFF,AUTO,SENSOR_ERROR_PUMP_OFF` (Triggered when the ADC reads an out-of-bounds voltage, indicating a short circuit or disconnected probe).
