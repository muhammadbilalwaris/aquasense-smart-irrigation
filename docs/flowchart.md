# AquaSense Firmware Control Flowchart

This document details the step-by-step firmware logical execution sequence of the **AquaSense** Smart Irrigation system.

---

## 1. System Flowchart (ASCII Representation)

```text
       [ Start ]
           |
           v
  [ Initialize Controller ]  <-- (Configure GPIOs, Serial Comm, Default Relays to OFF)
           |
           +<--------------------------------------------------------+
           |                                                         |
           v                                                         |
  [ Read Soil Moisture ]                                             |
           |                                                         |
           v                                                         |
   / Is Reading Valid? \  --[ No: Sensor Error ]--> [ Turn Pump OFF ]|
   \ (Within 0 - 4095) /                            [ Buzzer Alert  ]--+
           | Yes                                                     |
           v                                                         |
  [ Convert Raw ADC -> % ]                                           |
           |                                                         |
           v                                                         |
    / Check Mode? \                                                  |
    \ Auto vs Manual/                                                |
      /           \                                                  |
(Auto)           (Manual)                                            |
  |                 |                                                |
  v                 v                                                |
[Compare Moisture] [Check Manual Cmd]                                |
  |                 |                                                |
  |-- (Dry? < 35%)  |-- (User ON?)  --> / Cooldown Active? \         |
  |   Turn Pump ON  |   Turn Pump ON    \   (Safety check) /         |
  |                                        /        \                |
  |-- (Wet? > 60%)  |-- (User OFF?)     (Yes)       (No)             |
  |   Turn Pump OFF |   Turn Pump OFF     |          |               |
  |                 |                     v          v               |
  v                 v                [Stay OFF]  [Turn Pump ON]      |
  +--------+--------+                     |          |               |
           |                              +---->+----+               |
           v                                    |                    |
           |<-----------------------------------+                    |
           v                                                         |
   / Pump Active? \                                                  |
   \  (Check Run) /                                                  |
      /         \                                                    |
   (Yes)        (No)                                                 |
    |            |                                                   |
    v            v                                                   |
 / Max Run \  [Update Cooldown]                                      |
 \Exceeded?/     |                                                   |
  /     \        |                                                   |
(Yes)   (No)     |                                                   |
  |       |      |                                                   |
  v       v      |                                                   |
[OFF]  [Run +1]  |                                                   |
[CD]      |      |                                                   |
  |       |      |                                                   |
  v       v      v                                                   |
  +-------+------+                                                   |
          |                                                          |
          v                                                          |
   [Display Status]  <-- (Update LCD, OLED, or print Serial telemetry)
          |                                                          |
          v                                                          |
     [Log Event]     <-- (Write CSV record or serial export)         |
          |                                                          |
          v                                                          |
   [Wait 1 Second]                                                   |
          |                                                          |
          +----------------------------------------------------------+
```

---

## 2. Process Flow Description

### 1. Initialization
Runs once at boot. Sets digital output pins (relays, buzzers, LEDs) and configures inputs. The relay pin defaults to `LOW` to guarantee that the water pump is off during microcontroller startup.

### 2. Sensor Validation
The controller verifies that the ADC sensor input is within physical bounds. If a wire breaks or short circuits, the raw reading becomes extreme (e.g. `0` or `4095`). In this case, the controller overrides normal logic, turns the pump OFF immediately, flashes the LED, and reports a `SENSOR_ERROR` event to prevent overwatering.

### 3. Threshold Comparison and Hysteresis
If in **AUTO** mode, moisture is checked:
* **Below 35%**: The soil is dry. The pump turns ON.
* **Between 35% and 60%**: Hysteresis region. The pump maintains its current state. If it was already watering, it stays ON. If it was already OFF, it stays OFF. This stops rapid power toggling.
* **Above 60%**: The soil is wet. The pump turns OFF and triggers a cooldown period.

### 4. Safety Timers
* **Maximum Runtime**: If the pump has been ON for 30 consecutive seconds, it is shut down regardless of moisture levels. This prevents flooding if a sensor is dislodged or fails to detect water.
* **Cooldown Guard**: Once the pump stops, a 15-second lockout timer starts. The pump cannot be restarted during this time, allowing water to soak into the soil and protecting the pump motor from heat.

### 5. Display, Log, and Loop
Outputs status telemetry, appends data logs, and sleeps for 1 second before starting the next sampling cycle.
