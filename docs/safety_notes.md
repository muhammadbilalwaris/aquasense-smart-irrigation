# AquaSense Electrical & Physical Safety Guidelines

Working on projects that combine liquid water with electric currents requires strict adherence to safety protocols. This guide outlines mandatory precautions to protect both the user and the electrical hardware.

---

## 1. Electrical Isolation and Actuation

> [!WARNING]
> **NEVER connect a water pump directly to microcontroller GPIO pins (ESP32/Arduino).**
> GPIO pins are rated for very low currents (typically 12mA to 20mA maximum). Driving an inductive load like a motor directly will draw excessive current, immediately destroying the microcontroller's internal transistor structures.

### Action Plan
* **Use a Relay or MOSFET**: Control the pump circuit using a 5V/12V mechanical relay or power MOSFET module. This completely isolates the low-voltage logic side from the high-voltage load side.
* **Flyback Diode Protection**: Inductive loads (pumps, solenoid coils) produce high-voltage spikes (inductive kickback) when powered off. Install a flyback diode (e.g., 1N4007) in parallel across the DC pump terminals (pointing towards the positive supply line) to redirect these spikes away from the driver electronics.
* **Dual Power Sources**: Always power the water pump from a separate power supply (e.g., an external battery pack or DC adapter) rather than the ESP32's `3.3V` or `5V (VIN)` pins. This prevents voltage drops, logic resets, and overheating.

---

## 2. Liquid and Environment Safety

> [!CAUTION]
> **Keep water completely isolated from exposed electronics.**

### Rules for Outdoor Setup
* **Waterproof Enclosure**: If installing the system in a greenhouse, nursery, or garden, place the ESP32, relay board, and breadboards inside a waterproof junction box (IP65 rated or higher).
* **Drip Loops**: Always shape electrical cables with a "drip loop" (letting cables curve downward below the entry point of the enclosure). This ensures that running condensation or water drops drip off the wire instead of running directly into the enclosure.
* **Sensor Sealing**: The capacitive sensor head (where the cable connects) must be protected. Coat the exposed solder pads and connector in silicone sealant or marine-grade hot glue to prevent soil water from shorting the sensor's power pins.

---

## 3. High Voltage Hazards (AC Power)

> [!DANGER]
> **Mains Voltage (110V/220V AC) can be lethal.**

* **Low-Voltage DC Default**: For safety, educational demos, and student projects, **only use low-voltage DC water pumps (5V, 6V, or 12V DC)**. These voltages do not pose a shock hazard.
* **AC Pump Wiring**: If your project requires a large AC pump (e.g. 120V pump for large garden irrigation):
  - All AC wiring must be enclosed in electrical boxes.
  - Integrate a Ground Fault Circuit Interrupter (GFCI) outlet.
  - Mains AC wiring should only be assembled and verified by qualified persons.

---

## 4. Operational Protocols

1. **Verify with an LED First**: Before hookup of a water pump or solenoid, replace the actuator with a simple LED and resistor. Verify that the control logic, threshold rules, and button functions toggle the LED correctly.
2. **Dry Hands Only**: Never touch live wiring, connectors, or USB plugs with wet hands. Disconnect the USB cable or main power supply before rearranging any circuit connections on the breadboard.
