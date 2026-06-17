# AquaSense Circuit Connections Guide

This document lists the wiring connections required to assemble the **AquaSense** Smart Irrigation system on a breadboard for testing.

---

## 1. Controller Pin Connections (ESP32)

### A. Capacitive Soil Moisture Sensor
| Sensor Pin | ESP32 Pin | Wire Color (Recommended) | Description |
|---|---|---|---|
| **VCC** | **3.3V** | Red | Powers the internal oscillator circuit of the sensor. |
| **GND** | **GND** | Black | Ground reference. |
| **A0 (Analog Out)** | **GPIO 34 (ADC1_6)** | Yellow / Blue | Outputs analog voltage relative to soil capacitance. |

### B. Relay Module (5V Single-Channel Relay)
| Relay Pin | Connection | Wire Color (Recommended) | Description |
|---|---|---|---|
| **VCC** | **5V / VIN** | Orange | Powers the relay electromagnet coil. |
| **GND** | **GND** | Black | Common ground connection. |
| **IN (Signal)** | **GPIO 26** | Green | Trigger signal from ESP32 to open/close relay. |

### C. UI Elements & Local Indicators
* **Mode Switch Button**: Connect one leg of a momentary push button to **GPIO 25**, and the opposite leg to **GND**. (Internal pull-up resistor configures default HIGH state).
* **Manual Pump Button**: Connect one leg of a momentary push button to **GPIO 27**, and the opposite leg to **GND**. (Internal pull-up resistor configures default HIGH state).
* **Buzzer Alarm**: Connect the buzzer positive terminal (+) to **GPIO 14**, and negative terminal (-) to **GND**.
* **Status LED**: Connect an external LED anode (longer leg) to **GPIO 2** through a $220\,\Omega$ resistor, and the cathode (shorter leg) to **GND**. (Alternatively, you can rely on the built-in LED tied to GPIO 2).

---

## 2. Actuator / Pump Output Connections

> [!IMPORTANT]
> The pump must be powered by an **external supply** (such as a 4xAA battery pack or a dedicated 5V/12V DC power brick), **NOT** directly from the ESP32 pins or the USB 5V rail.

```text
+-----------------------+      +-------------------+
| External Power Supply |      |   DC Water Pump   |
|                       |      |                   |
|     Positive (+) -----+----->+ [Relay - COM]     |
|                       |      |                   |
|                       |      +-------------------+
|                       |                | (Relay Contact CLOSED)
|                       |                v
|                       |      +-------------------+
|                       |      | [Relay - NO]      |
|                       |      +---------+---------+
|                       |                |
|                       |                v
|                       |      +-------------------+
|                       |      | Pump Positive (+) |
|                       |      +---------+---------+
|                       |                |
|     Negative (-) -----+--------------->+ Pump Negative (-) |
+-----------------------+      +-------------------+
```

### Relay Terminal Wiring
1. Connect the **Positive (+)** wire of your external power supply to the relay module's **COM (Common)** screw terminal.
2. Connect the **Positive (+)** wire of the DC pump to the relay module's **NO (Normally Open)** screw terminal.
3. Connect the **Negative (-)** wire of your external power supply directly to the **Negative (-)** wire of the DC pump.
4. *(Optional but Recommended)*: Connect a flyback diode (e.g. 1N4007) in parallel across the DC pump's positive and negative terminals. The silver band on the diode must point toward the positive terminal of the pump.

---

## 3. Circuit Safety Warnings

> [!CAUTION]
> **Avoid Common Ground Loops and Voltage Back-feed:**
> 1. Ensure the external power supply voltage matches your water pump (e.g., use a 12V supply for a 12V pump).
> 2. Do not let any wire from the high-current external battery supply come into direct contact with the ESP32 GPIO pins, as it will destroy the chips.
> 3. Keep the relay terminal block wires tightly screwed down to prevent loose wires from short-circuiting.
