# AquaSense Development Methodology

This document outlines the systematic engineering process followed to research, design, prototype, calibrate, test, and document the **AquaSense Smart Irrigation System**.

---

## Engineering Phase Walkthrough

### 1. Problem Analysis & Research
* **The Problem**: Traditional agricultural and residential watering works on crude timers, leading to massive water wastage, high utility bills, and plant damage due to overwatering or under-watering.
* **The Solution**: Construct an automated closed-loop feedback control system that monitors the actual moisture level of the root soil and delivers water dynamically only when needed.

### 2. Hardware Component Selection
* **Microcontroller**: The **ESP32** was selected due to its integrated ADC channels, rapid processing speed (240MHz), dual cores, low power modes, and potential for future IoT Wi-Fi integrations.
* **Sensor**: A **capacitive soil moisture sensor** was chosen over resistive probes. Resistive probes pass electric current directly through wet soil, leading to rapid anode/cathode corrosion (often failing within weeks). Capacitive sensors measure dielectric changes without exposing electrodes, increasing lifespan.
* **Actuators**: A **5V Electromagnetic Relay module** is selected to isolate the low-power ESP32 logic circuit from the high-power water pump circuit.

### 3. Sensor Calibration
Soil density, composition, and salinity vary. Thus, physical calibration is mandatory:
* **Air Dry Reading**: The sensor is suspended in dry air to record the upper voltage boundary (`DRY_RAW_VALUE`).
* **Saturated Wet Reading**: The sensor is placed in water to record the lowest voltage output (`WET_RAW_VALUE`).
* **Normalization**: The linear scaling formula maps voltage values to moisture percentage ($0\%$ to $100\%$).

### 4. Defining Control Thresholds
* **Dry Threshold (35%)**: Set as the point where typical garden plants begin to experience moderate water stress, triggering irrigation.
* **Wet Threshold (60%)**: Set as the target saturation level for healthy soil aeration, stopping water delivery.

### 5. Interfacing and Prototyping
* Connect the capacitive sensor to an analog-capable input channel (ESP32 GPIO 34).
* Wire the relay control pin to a digital output (ESP32 GPIO 26).
* Configure two push buttons with internal pull-up resistors to toggle modes (GPIO 25) and manually control the pump (GPIO 27).

### 6. Control Algorithm Design
* Implement a state machine in C++ and Python.
* Integrate **Hysteresis**: Prevents rapid pump toggling (chattering) when moisture is right at the threshold.
* Integrate **Safety Protections**: Implemented a maximum pump run limit (30s) to prevent flood disasters if a sensor falls out of the pot, and a cooldown limit (15s) to protect the relay contact points and allow water absorption.

### 7. Simulation and Testing
* Developed a Python simulator (`src/simulator.py`) to model physical soil moisture absorption and drying rates.
* Conducted test cases: Normal drying cycles, Sensor failures (short circuits), Pump timeouts (empty tank), and random weather events.

### 8. Physical Verification & Deployment
* **Phase 1 (Safe LED Demo)**: Program the ESP32 and use the built-in LED (GPIO 2) to simulate the pump. Verify that the LED lights up when the sensor is dry and turns off when wet.
* **Phase 2 (DC Pump Assembly)**: Interface the relay, connect an external battery/supply, and wire a low-voltage DC water pump.
* **Phase 3 (Logging Audit)**: Output metrics to CSV files and monitor soil moisture patterns to verify water savings.
