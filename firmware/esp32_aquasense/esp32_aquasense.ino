/**
 * @file esp32_aquasense.ino
 * @brief AquaSense Smart Soil Moisture Irrigation System Firmware for ESP32.
 * @details Implements automatic closed-loop threshold watering with hysteresis,
 *          non-blocking safety timers for pump protection, manual override button controls,
 *          error checking, and structured serial data reporting.
 * 
 * Hardware Connections (ESP32):
 * - Capacitive Soil Moisture Sensor (Analog Input): GPIO 34
 * - Pump Control Relay (Active HIGH / LOW supported, default active HIGH): GPIO 26
 * - Mode Select Push Button (Momentary, Pull-up): GPIO 25 (Switches AUTO <-> MANUAL)
 * - Manual Pump Trigger Button (Momentary, Pull-up): GPIO 27 (Toggles Pump in MANUAL)
 * - Status indicator LED: GPIO 2 (Blinks during events, turns ON when pump is active)
 * - Alarm Buzzer: GPIO 14 (Sounds alert on SENSOR_ERROR or WATERING_TIMEOUT)
 */

#include <Arduino.h>

// --- Pin Definitions ---
const int PIN_MOISTURE_SENSOR = 34; // ADC1 channel 6
const int PIN_PUMP_RELAY      = 26; // Digital Output to Relay
const int PIN_BTN_MODE        = 25; // Digital Input (Push Button to GND)
const int PIN_BTN_PUMP        = 27; // Digital Input (Push Button to GND)
const int PIN_STATUS_LED      = 2;  // Digital Output (Built-in LED)
const int PIN_BUZZER          = 14; // Digital Output to Buzzer

// --- Calibration and Threshold Parameters ---
// ESP32 ADC is 12-bit (0 - 4095).
// Capacitive sensor outputs high voltage (e.g. 3000) when dry and low voltage (e.g. 1200) when wet.
const int DRY_RAW_VALUE = 3000;
const int WET_RAW_VALUE = 1200;

const float DRY_THRESHOLD_PERCENT = 35.0;
const float WET_THRESHOLD_PERCENT = 60.0;

const int SENSOR_MIN_RAW = 0;
const int SENSOR_MAX_RAW = 4095;

// --- Timing Constants (in milliseconds) ---
const unsigned long SAMPLING_INTERVAL_MS   = 1000;  // Sample sensor every 1s
const unsigned long MAX_PUMP_RUNTIME_MS    = 30000; // Max continuous pump time: 30s
const unsigned long PUMP_COOLDOWN_MS       = 15000; // Cooldown limit: 15s
const unsigned long BUTTON_DEBOUNCE_MS     = 200;   // Debounce interval for buttons

// --- System State Definitions ---
enum SystemState {
  STATE_IDLE,
  STATE_SOIL_DRY,
  STATE_PUMP_ON,
  STATE_SOIL_WET,
  STATE_MANUAL_ON,
  STATE_MANUAL_OFF,
  STATE_SENSOR_ERROR,
  STATE_WATERING_TIMEOUT,
  STATE_COOLDOWN_ACTIVE
};

enum OpMode {
  MODE_AUTO,
  MODE_MANUAL
};

// --- Global State Variables ---
OpMode currentMode            = MODE_AUTO;
SystemState currentState      = STATE_IDLE;
bool pumpActive               = false;

unsigned long lastSampleTime  = 0;
unsigned long pumpStartTime   = 0;
unsigned long cooldownStartTime = 0;

// Button Debounce Timers
unsigned long lastModeBtnTime = 0;
unsigned long lastPumpBtnTime = 0;

// Buffer for serial logging event code
String currentEvent = "NORMAL";

// --- Function Prototypes ---
float rawToMoisturePercent(int rawVal);
bool isSensorValid(int rawVal);
void updateHardwareOutputs();
void handleButtons();
void logSerialOutput(int rawVal, float moisturePercent);

void setup() {
  // 1. Initialize Serial Communication
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect (Leonardo/Micro/ESP32 native USB)
  }
  
  // 2. Configure Pin Directions
  pinMode(PIN_MOISTURE_SENSOR, INPUT);
  pinMode(PIN_BTN_MODE, INPUT_PULLUP);
  pinMode(PIN_BTN_PUMP, INPUT_PULLUP);
  
  pinMode(PIN_PUMP_RELAY, OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  
  // 3. Keep Pump OFF during startup (Safety First)
  digitalWrite(PIN_PUMP_RELAY, LOW);
  digitalWrite(PIN_STATUS_LED, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  
  Serial.println("\n--- AquaSense Initialized ---");
  Serial.println("RAW_VALUE,MOISTURE_PERCENT,PUMP_STATUS,MODE,EVENT");
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Scan Input Push Buttons (Non-blocking)
  handleButtons();

  // 2. Periodic Sensor Sampling and State Updates
  if (currentMillis - lastSampleTime >= SAMPLING_INTERVAL_MS) {
    lastSampleTime = currentMillis;
    
    // Read raw ADC value
    int rawVal = analogRead(PIN_MOISTURE_SENSOR);
    bool sensorValid = isSensorValid(rawVal);
    float moisturePercent = sensorValid ? rawToMoisturePercent(rawVal) : 0.0;
    
    // Reset/Default event at each sampling cycle
    currentEvent = "NORMAL";
    
    // --- State Machine Logic ---
    
    // A. Safety Check: Check Sensor Failures
    if (!sensorValid) {
      if (pumpActive) {
        pumpActive = false;
        cooldownStartTime = currentMillis; // Trigger safety cooldown
      }
      currentState = STATE_SENSOR_ERROR;
      currentEvent = "SENSOR_ERROR_PUMP_OFF";
    }
    
    // B. Safety Check: Check Cooldown Guard
    else if (cooldownStartTime > 0 && (currentMillis - cooldownStartTime < PUMP_COOLDOWN_MS)) {
      pumpActive = false;
      currentState = STATE_COOLDOWN_ACTIVE;
      currentEvent = "COOLDOWN_ACTIVE";
    }
    
    // C. Normal Operation: Cooldown expired
    else {
      if (cooldownStartTime > 0) {
        // Cooldown has expired, reset cooldown timer
        cooldownStartTime = 0;
      }
      
      if (currentMode == MODE_AUTO) {
        if (pumpActive) {
          // Check for max runtime overrun
          unsigned long elapsedRuntime = currentMillis - pumpStartTime;
          if (elapsedRuntime >= MAX_PUMP_RUNTIME_MS) {
            pumpActive = false;
            cooldownStartTime = currentMillis; // Lock out pump
            currentState = STATE_WATERING_TIMEOUT;
            currentEvent = "WATERING_TIMEOUT";
          }
          // Check for wet soil threshold (Hysteresis OFF)
          else if (moisturePercent >= WET_THRESHOLD_PERCENT) {
            pumpActive = false;
            cooldownStartTime = currentMillis;
            currentState = STATE_SOIL_WET;
            currentEvent = "SOIL_WET_PUMP_OFF";
          }
          else {
            currentState = STATE_PUMP_ON;
          }
        }
        else { // Pump is currently OFF
          // Check for dry soil threshold (Hysteresis ON)
          if (moisturePercent < DRY_THRESHOLD_PERCENT) {
            pumpActive = true;
            pumpStartTime = currentMillis;
            currentState = STATE_PUMP_ON;
            currentEvent = "SOIL_DRY_PUMP_ON";
          }
          else {
            // Determine state classification
            if (moisturePercent >= WET_THRESHOLD_PERCENT) {
              currentState = STATE_SOIL_WET;
            } else {
              currentState = STATE_IDLE; // SOIL_OK
            }
          }
        }
      }
      
      else { // MANUAL MODE
        if (pumpActive) {
          // Max runtime safety guard must still run in manual mode!
          unsigned long elapsedRuntime = currentMillis - pumpStartTime;
          if (elapsedRuntime >= MAX_PUMP_RUNTIME_MS) {
            pumpActive = false;
            cooldownStartTime = currentMillis;
            currentState = STATE_WATERING_TIMEOUT;
            currentEvent = "WATERING_TIMEOUT";
          }
          else {
            currentState = STATE_MANUAL_ON;
          }
        }
        else {
          currentState = STATE_MANUAL_OFF;
        }
      }
    }
    
    // 3. Update Actuator Output Signals (Relay, LED, Buzzer)
    updateHardwareOutputs();
    
    // 4. Log Structured Serial Data
    logSerialOutput(rawVal, moisturePercent);
  }
}

/**
 * Converts raw ADC value from the moisture sensor to percentage [0.0 - 100.0]
 */
float rawToMoisturePercent(int rawVal) {
  if (DRY_RAW_VALUE == WET_RAW_VALUE) return 0.0;
  
  float percent = ((float)(DRY_RAW_VALUE - rawVal) / (float)(DRY_RAW_VALUE - WET_RAW_VALUE)) * 100.0;
  return constrain(percent, 0.0, 100.0);
}

/**
 * Checks if raw value lies within reasonable hardware limits
 */
bool isSensorValid(int rawVal) {
  return (rawVal >= SENSOR_MIN_RAW && rawVal <= SENSOR_MAX_RAW);
}

/**
 * Updates external relays, status indicator LEDs, and warning buzzers.
 */
void updateHardwareOutputs() {
  // Drive pump relay
  digitalWrite(PIN_PUMP_RELAY, pumpActive ? HIGH : LOW);
  
  // LED indicates pump status (Solid ON when pump runs)
  // If in an error state (SENSOR_ERROR or WATERING_TIMEOUT), double flash
  if (currentState == STATE_SENSOR_ERROR || currentState == STATE_WATERING_TIMEOUT) {
    digitalWrite(PIN_STATUS_LED, (millis() / 250) % 2 == 0 ? HIGH : LOW);
    // Beep buzzer
    digitalWrite(PIN_BUZZER, (millis() / 500) % 2 == 0 ? HIGH : LOW);
  }
  else if (currentState == STATE_COOLDOWN_ACTIVE) {
    // Single slow blink during cooldown
    digitalWrite(PIN_STATUS_LED, (millis() / 1000) % 2 == 0 ? HIGH : LOW);
    digitalWrite(PIN_BUZZER, LOW);
  }
  else {
    digitalWrite(PIN_STATUS_LED, pumpActive ? HIGH : LOW);
    digitalWrite(PIN_BUZZER, LOW);
  }
}

/**
 * Handles physical button interactions with software debouncing.
 */
void handleButtons() {
  unsigned long currentMillis = millis();

  // 1. Read Mode Button (Pin 25, active low pull-up)
  if (digitalRead(PIN_BTN_MODE) == LOW) {
    if (currentMillis - lastModeBtnTime >= BUTTON_DEBOUNCE_MS) {
      lastModeBtnTime = currentMillis;
      
      // Toggle mode
      if (currentMode == MODE_AUTO) {
        currentMode = MODE_MANUAL;
        currentState = STATE_MANUAL_OFF;
        // Turn off pump when switching modes for safety
        if (pumpActive) {
          pumpActive = false;
          cooldownStartTime = currentMillis;
        }
      } else {
        currentMode = MODE_AUTO;
        currentState = STATE_IDLE;
        if (pumpActive) {
          pumpActive = false;
          cooldownStartTime = currentMillis;
        }
      }
    }
  }

  // 2. Read Pump Toggle Button (Pin 27, active low pull-up)
  // Only valid in MANUAL mode and when not locked out by cooldown or errors
  if (digitalRead(PIN_BTN_PUMP) == LOW) {
    if (currentMode == MODE_MANUAL && currentState != STATE_COOLDOWN_ACTIVE && currentState != STATE_SENSOR_ERROR) {
      if (currentMillis - lastPumpBtnTime >= BUTTON_DEBOUNCE_MS) {
        lastPumpBtnTime = currentMillis;
        
        // Toggle pump
        pumpActive = !pumpActive;
        if (pumpActive) {
          pumpStartTime = currentMillis;
          currentState = STATE_MANUAL_ON;
          currentEvent = "MANUAL_ON";
        } else {
          cooldownStartTime = currentMillis;
          currentState = STATE_MANUAL_OFF;
          currentEvent = "MANUAL_OFF";
        }
        
        // Print change immediately
        updateHardwareOutputs();
      }
    }
  }
}

/**
 * Logs data in CSV format to the serial port.
 * RAW_VALUE,MOISTURE_PERCENT,PUMP_STATUS,MODE,EVENT
 */
void logSerialOutput(int rawVal, float moisturePercent) {
  String modeStr = (currentMode == MODE_AUTO) ? "AUTO" : "MANUAL";
  String pumpStr = pumpActive ? "ON" : "OFF";
  
  // Print serial values
  if (currentState == STATE_SENSOR_ERROR) {
    Serial.print("0,0.0,");
  } else {
    Serial.print(rawVal);
    Serial.print(",");
    Serial.print(moisturePercent, 1);
    Serial.print(",");
  }
  Serial.print(pumpStr);
  Serial.print(",");
  Serial.print(modeStr);
  Serial.print(",");
  Serial.println(currentEvent);
}
