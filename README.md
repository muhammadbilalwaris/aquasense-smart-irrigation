# AquaSense: Smart Irrigation System Using Soil Moisture Sensors

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](requirements.txt)
[![Build Status](https://img.shields.io/badge/Tests-Passing-green.svg)](tests/)

**AquaSense** is a complete, GitHub-ready automated smart irrigation control system. It is designed to measure soil moisture level using a capacitive sensor, decide whether plants require water, and automatically control a water pump or solenoid valve. The system minimizes water wastage, protects plants from overwatering, supports manual/automatic operational overrides, logs historical events to CSV, and includes a high-fidelity Python simulation layer to run without physical hardware.

Academic Title: **Design and Implementation of a Smart Irrigation System Using Soil Moisture Sensors**

---

## 📖 Table of Contents
1. [Features](#-features)
2. [System Architecture](#-system-architecture)
3. [How It Works](#-how-it-works)
4. [Safety Warnings](#-safety-warnings)
5. [Hardware Requirements](#-hardware-requirements)
6. [Software Requirements & Installation](#-software-requirements--installation)
7. [Python Simulation Mode](#-python-simulation-mode)
8. [Running Automated Tests](#-running-automated-tests)
9. [ESP32 Firmware & Calibration](#-esp32-firmware--calibration)
10. [Repository Structure](#-repository-structure)
11. [Future Improvements](#-future-improvements)
12. [License](#-license)

---

## 🌟 Features

* **Soil Moisture Monitoring**: Reads volumetric water content and converts it to a clean 0% - 100% scale.
* **Hysteresis Control**: Prevents rapid ON/OFF switching (chattering) near thresholds by using separate dry trigger (35%) and wet stop (60%) limits.
* **Automatic & Manual Modes**: Support for automatic threshold-based control or manual button-driven overrides.
* **Max Runtime Safety Cutoff**: Prevents garden flooding by automatically shutting down the pump if it runs continuously for more than 30 seconds.
* **Cooldown Protection**: Enforces a mandatory 15-second pump lockout period after each watering cycle to protect the pump and let water absorb.
* **Sensor & Water Level Diagnostics**: Shuts down the pump immediately and triggers a buzzer alarm if the sensor reads out-of-bounds values or if the supply tank runs empty.
* **Telemetry Data Logger**: Appends detailed data records (ADC value, moisture, pump state, events, timers) to a CSV file.
* **Offline Python Simulator**: Generates physical soil depletion scenarios, noise, and safety hazards, allowing you to run and verify the control loop without any hardware.

---

## 🗺️ System Architecture

```text
+---------------------+       +-----------------------+       +----------------------+
| Capacitive Moisture |       |    ESP32 / Arduino    |       |   Push Buttons (x2)  |
| Sensor (GPIO 34)    +------>+      Controller       +<------+ - Mode (GPIO 25)     |
+---------------------+       |                       |       | - Pump Toggle (GP27) |
                              +-------+-------+-------+       +----------------------+
                                      |       |
                                      |       +---------------+
                                      v                       v
                          +-----------+-----------+       +---+---+-----+
                          | Relay Module (GPIO 26)|       | Status LED  |
                          +-----------+-----------+       | (GPIO 2)    |
                                      |                   +-------------+
                                      v
                          +-----------+-----------+
                          |   DC Water Pump / Valve|
                          +-----------------------+
```

---

## ⚙️ How It Works

1. **Sense**: The capacitive soil moisture sensor probes the soil. It outputs an analog voltage inverse to the water content (high voltage when dry, low voltage when wet).
2. **Convert**: The ESP32's 12-bit ADC converts the voltage into a raw digital value between `0` and `4095`. The firmware scales this raw value to a moisture percentage:
   $$\text{Moisture Percentage} = \left(\frac{\text{DRY\_RAW\_VALUE} - \text{Raw Value}}{\text{DRY\_RAW\_VALUE} - \text{WET\_RAW\_VALUE}}\right) \times 100$$
3. **Decide**: The controller checks the selected mode (Auto vs Manual) and applies the safety timers. In Auto mode:
   - If Moisture $< 35\%$ and Cooldown is inactive $\rightarrow$ Turn Pump ON.
   - If Moisture $> 60\%$ or continuous watering duration exceeds 30 seconds $\rightarrow$ Turn Pump OFF and start Cooldown.
4. **Actuate**: The controller drives the Relay Signal pin (GPIO 26). The relay closes, routing power from the external supply to the water pump.
5. **Log**: Telemetry and events are written to the Serial port and logged into `data/sample_irrigation_log.csv`.

---

## ⚠️ Safety Warnings

> [!IMPORTANT]
> * **DO NOT power the water pump directly from microcontroller pins.** Microcontrollers cannot supply the current required to run motors. Always route pump power through an isolating relay or MOSFET module.
> * **Always use a separate power source for the pump.** Powering inductive motors from the board's USB line can cause voltage drops that reset the board.
> * **Install a Flyback Diode (e.g., 1N4007) across DC pump terminals** to clamp voltage spikes caused by motor de-activation.
> * Keep water away from all exposed microcontroller connections. If deploying outdoors, utilize an IP65 waterproof housing.
> * **AC Mains (110V/220V AC) pumps should only be wired by qualified persons.** For student projects and safe demos, we strongly advise using low-voltage DC water pumps (5V - 12V).

---

## 🛠️ Hardware Requirements

* **Development Board**: ESP32 (NodeMCU or DevKit) or Arduino Uno.
* **Sensor**: Capacitive Soil Moisture Sensor (e.g., v1.2 or v2.0).
* **Actuator**: 5V Single-Channel Relay Module.
* **Water Pump**: 3V-6V Mini Submersible Water Pump or a 12V Solenoid Valve.
* **Indicators**: Active 5V Buzzer and standard $220\,\Omega$ resistor with a LED.
* **Power Source**: 5V USB (for ESP32) + 4xAA battery pack or 12V DC Adapter (for Pump).
* **Cables**: Breadboard and male-to-female/male-to-male jumper wires.

---

## 💻 Software Requirements & Installation

To run the Python simulation or run tests locally, you need Python 3.10 or newer.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/muhammadbilalwaris/aquasense-smart-irrigation.git
   cd aquasense-smart-irrigation
   ```

2. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🧪 Python Simulation Mode

You can run the full system simulation directly in your terminal without any hardware.

To start the simulator:
```bash
python src/main.py
```

### Simulation Scenarios
The simulator allows you to test how the system reacts to different physical events:
1. **`normal_drying`**: Runs standard evaporation cycles where soil dries down, triggers the pump, and turns off when wet.
2. **`very_dry_soil`**: Tests immediate pump triggering in drought conditions.
3. **`already_wet_soil`**: Verifies that the pump remains OFF when soil moisture is already sufficient.
4. **`sensor_noise`**: Introduces reading spikes to test the stabilizing effect of the hysteresis gap.
5. **`sensor_failure`**: Simulates out-of-range sensor readings (e.g., unplugged wire) and verifies the immediate safety shutdown.
6. **`pump_runtime_timeout`**: Simulates a dry tank or clogged pipe where soil moisture does not increase, testing the 30-second pump cutoff and alarm.
7. **`random_weather`**: Simulates environmental challenges like sudden rainstorms and rapid hot days.

---

## ⚙️ Running Automated Tests

AquaSense includes unit tests for the core state machine, calculations, and logging functions.

Run the test suite using `pytest`:
```bash
pytest
```

---

## 🔌 ESP32 Firmware & Calibration

The firmware code is located in [`firmware/esp32_aquasense/esp32_aquasense.ino`](firmware/esp32_aquasense/esp32_aquasense.ino).

### Uploading Firmware
1. Open the Arduino IDE.
2. Open [`firmware/esp32_aquasense/esp32_aquasense.ino`](firmware/esp32_aquasense/esp32_aquasense.ino).
3. Connect your ESP32 board to your computer.
4. Select board **ESP32 Dev Module** and choose your active COM port.
5. Click **Upload**.

### Calibration Steps
Every capacitive sensor has slightly different analog voltage output ranges.
1. **Dry Calibration**: Hold the sensor in the air. Note the raw ADC value printed on the Serial Monitor. Update `DRY_RAW_VALUE` in the code.
2. **Wet Calibration**: Submerge the sensor in water up to the safety line. Note the raw ADC value. Update `WET_RAW_VALUE` in the code.
3. Re-upload the sketch to the ESP32.

---

## 📁 Repository Structure

```text
aquasense-smart-irrigation/
│
├── README.md                           # Main documentation guide
├── LICENSE                             # MIT License terms
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Standard git ignore definitions
│
├── firmware/
│   ├── esp32_aquasense/
│   │   └── esp32_aquasense.ino        # ESP32 firmware sketch
│   └── README.md                       # Firmware-specific connections & instructions
│
├── src/
│   ├── config.py                       # Configuration & threshold constants
│   ├── irrigation_logic.py             # Core state machine logic
│   ├── simulator.py                    # Environment soil moisture simulator
│   ├── data_logger.py                  # CSV event and telemetry logger
│   └── dashboard.py                    # Terminal output formatter
│
├── data/
│   └── sample_irrigation_log.csv       # Sample logs for audit tests
│
├── docs/
│   ├── block_diagram.md                # System block connections and data flow
│   ├── flowchart.md                    # Logic flow flowchart
│   ├── methodology.md                  # Development methodology
│   ├── safety_notes.md                 # Detailed safety guidelines
│   ├── circuit_connections.md          # ESP32 breadboard wiring schematics
│   └── irrigation_logic.md             # Logic formulas and FSM transitions
│
├── diagrams/
│   └── system_architecture.txt         # ASCII art architecture diagram
│
└── tests/
    ├── test_irrigation_logic.py        # Control logic test suite
    └── test_data_logger.py             # Logging test suite
```

---

## 🚀 Future Improvements

* **Web Dashboard**: Implement a local web page on the ESP32 using WebSockets to graph moisture levels in real-time.
* **Wi-Fi Alerts & Cloud Logging**: Log data points directly to platforms like ThingSpeak or Adafruit IO, and send SMS/email alerts via IFTTT.
* **Rain Bypass**: Integrate an outdoor rain sensor to bypass watering schedules if rain is detected.
* **Flow Sensor Integration**: Measure volumetric water consumption and detect leakage.
* **Solar Powering**: Implement deep sleep code optimizations to run the system off small solar panels.
* **Multi-Zone Control**: Expand the logic to support multiple soil sensors and independent solenoid valves.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
