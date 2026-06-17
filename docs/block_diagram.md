# AquaSense Block Diagram and Data Flow

This document details the functional blocks of the **AquaSense** Smart Irrigation system and how data moves between inputs, the controller, logic layers, and outputs.

---

## 1. System Block Diagram

```text
                  +--------------------------------+
                  |          Physical Soil         |
                  +---------------+--------^-------+
                                  |        |
                                  v        | (Water Delivery)
                   +--------------+--------+-------+
                   |  Capacitive Soil Moisture Sensor|
                   +--------------+----------------+
                                  |
                                  v (Analog Voltage Signal)
                   +--------------+----------------+
                   |       ESP32 / Arduino ADC     |
                   +--------------+----------------+
                                  |
                                  v (Raw ADC Value: 0 - 4095)
                   +--------------+----------------+
                   | Moisture Percentage Conversion|
                   +--------------+----------------+
                                  |
                                  v (Moisture %: 0.0 - 100.0)
                   +--------------+----------------+
                   |    Irrigation Control Logic   |
                   +-------^------+--------+-------+
                           |      |        |
    (Manual Button Control)|      |        | (Digital Trigger: HIGH/LOW)
+--------------------------+---+  |        v
| Manual Button / Mode Select  |  |  +-----+-----------------------+
+------------------------------+  |  |    Relay / MOSFET Driver    |
                                  |  +-----+-----------------------+
                                  |        |
                                  |        v (External DC Voltage)
                                  |  +-----+-----------------------+
                                  |  |      Pump / Solenoid Valve  |
                                  |  +-----------------------------+
                                  |
                                  +--------> OLED / LCD / Serial Monitor (Feedback display)
                                  |
                                  +--------> CSV Log / Python Simulation (Logging storage)
```

---

## 2. Block Component Explanations

### Soil Moisture Sensor
Reads the volumetric water content of the surrounding soil. The capacitive model is preferred over cheap resistive probes because it utilizes a protective coating to prevent copper corrosion, ensuring stable long-term operation.

### ESP32 / Arduino ADC
The Analog-to-Digital Converter (ADC) samples the analog voltage from the soil moisture sensor and maps it into a discrete digital number. The ESP32 provides a high-resolution 12-bit ADC mapping voltage to integers between `0` and `4095`.

### Moisture Percentage Conversion
Translates the raw, uncalibrated ADC readings into a human-readable percentage scale. Dry calibration represents `0%` and saturated wet represents `100%`.

### Irrigation Control Logic
The decision-making hub. It monitors the moisture percentage against dry thresholds (triggers irrigation) and wet thresholds (stops irrigation). It manages state transitions and includes safety guards (watering limits, cooldown lockouts).

### Relay / MOSFET Driver
A low-voltage microcontroller pin (`3.3V`/`5V`) cannot supply the high current needed by water pumps or solenoids. A Relay or MOSFET module acts as an electronically controlled switch, using the low-power pin signal to switch a separate high-power power source.

### Pump / Solenoid Valve
The mechanical actuator. When activated by the relay, it pumps water or opens a valve to allow water flow from a water tank or hose to the plant.

### Manual Buttons
Allow operators to switch between **AUTO** and **MANUAL** modes and trigger the pump directly, bypassing threshold rules while keeping safety timers active.

### Feedback Displays (Serial Monitor/OLED)
Provide real-time telemetry of the system. Displays the current moisture percentage, mode, system state, and active alarms.

### CSV Logs / Simulation Files
Act as the system audit trail. Saves data points and timestamps to files, allowing researchers or students to graph wetting profiles over time.
