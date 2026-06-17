# AquaSense Irrigation Control Logic and State Machine

This document details the software algorithms, mathematical calculations, and state machine transitions that govern the **AquaSense** Smart Irrigation system.

---

## 1. Soil Moisture Percentage Conversion

Capacitive soil moisture sensors return analog voltage readings which the ESP32's ADC maps into raw integer values in the range $[0, 4095]$.

To represent moisture levels in a user-friendly percentage scale ($0\%$ to $100\%$), we apply a linear interpolation based on two calibration setpoints:
* $V_{\text{dry}}$: Raw ADC reading when the sensor is suspended in dry air.
* $V_{\text{wet}}$: Raw ADC reading when the sensor is submerged in water.

### Mathematical Formula
$$M = \left( \frac{V_{\text{dry}} - V_{\text{raw}}}{V_{\text{dry}} - V_{\text{wet}}} \right) \times 100$$

Where:
* $V_{\text{raw}}$ is the current analog ADC input.
* $M$ is the calculated Moisture Percentage.

### Clamping Protection
To prevent reading fluctuations from showing values like $-5\%$ or $105\%$, the output is mathematically clamped:
$$M_{\text{clamped}} = \max(0.0, \min(M, 100.0))$$

---

## 2. Hysteresis Control Strategy

A simple single-threshold trigger is problematic. For example, if the system turned ON the pump below $40\%$ and OFF above $40\%$, tiny variations in the sensor reading (electrical noise or water ripples) would cause the relay to toggle rapidly (chatter). This can wear out mechanical relays and overheat motors.

To prevent this, AquaSense implements **hysteresis** by using two separate thresholds:
1. **Dry Threshold ($35\%$)**: The soil is dry; the pump must turn **ON**.
2. **Wet Threshold ($60\%$)**: The soil has sufficient moisture; the pump must turn **OFF**.

```text
Moisture %
  ^
100% |====================================================
     |
 60% |---------------------------+ [Pump turns OFF]
     |                           |
     |   Hysteresis Zone         |  (Pump stays ON if watering,
     |   (No State Change)       |   stays OFF if dry sensor not hit)
 35% |-------------------+-------+ [Pump turns ON]
     |                   |
  0% |===================v================================
                         Time ->
```

---

## 3. State Machine State Transitions

The system operates as a finite state machine (FSM) containing the following states:

| State | Description | Pump Status | Transition Rules |
|---|---|---|---|
| **`IDLE`** | Soil moisture is OK; pump is off. | OFF | Shifts to `SOIL_DRY` if moisture falls below $35\%$. |
| **`SOIL_DRY`** | Soil moisture is dry, but pump is off. | OFF | Shifts to `PUMP_ON` if no cooldown lockout is active. |
| **`PUMP_ON`** | Watering in progress (AUTO mode). | ON | Shifts to `SOIL_WET` if moisture exceeds $60\%$. Shifts to `WATERING_TIMEOUT` if runtime reaches 30s. |
| **`SOIL_WET`** | Soil moisture is wet; pump is off. | OFF | Shifts to `IDLE` or `SOIL_DRY` over time as soil dries. |
| **`MANUAL_ON`** | Pump is turned ON by manual toggle button. | ON | Shifts to `WATERING_TIMEOUT` if runtime exceeds 30s. |
| **`MANUAL_OFF`** | Pump is turned OFF by manual toggle button. | OFF | Reverts to user toggle commands. |
| **`SENSOR_ERROR`** | Sensor raw reading is out-of-bounds ($<0$ or $>4095$). | OFF | High priority safety override. Forces pump OFF. |
| **`WATERING_TIMEOUT`**| Pump was active for longer than 30 seconds. | OFF | Safety cutoff. Locks pump OFF and sounds alarm buzzer. |
| **`COOLDOWN_ACTIVE`**| Pump is locked out for 15 seconds after watering. | OFF | Prevents immediate restarts, allowing water to settle. |

---

## 4. Hardware Protections & Fail-Safes

### Max Runtime Protection
If the pump has been running continuously for longer than `MAX_PUMP_RUNTIME_SECONDS` (30 seconds), the system forces the pump OFF and transitions to `WATERING_TIMEOUT`. This prevents flooding if:
* The soil sensor is accidentally pulled out of the pot.
* The water supply hose is blocked or kinked, preventing water from reaching the sensor.
* The sensor fails electrically.

### Cooldown Guard
Every time the pump switches OFF, a cooldown timer (`PUMP_COOLDOWN_SECONDS` = 15 seconds) is started. During this period, the pump cannot be turned back ON by either automatic logic or manual buttons. This allows water to settle in the soil and prevents rapid cycles.
