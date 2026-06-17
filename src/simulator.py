# src/simulator.py

import random
from src.config import (
    DRY_RAW_VALUE,
    WET_RAW_VALUE,
    SENSOR_MIN_RAW,
    SENSOR_MAX_RAW
)

class SoilSimulator:
    """
    Simulates a physical soil moisture ecosystem.
    Model changes dynamically based on the water pump state, simulated weather,
    noise, and hardware failures.
    """
    def __init__(self, scenario="normal_drying"):
        self.scenario = scenario.lower()
        self.step = 0
        
        # Configure initial moisture percentage based on scenario
        if self.scenario == "normal_drying":
            self.moisture = 55.0
        elif self.scenario == "very_dry_soil":
            self.moisture = 15.0
        elif self.scenario == "already_wet_soil":
            self.moisture = 85.0
        elif self.scenario == "sensor_noise":
            self.moisture = 45.0
        elif self.scenario == "sensor_failure":
            self.moisture = 40.0
        elif self.scenario == "pump_runtime_timeout":
            self.moisture = 20.0
        elif self.scenario == "random_weather":
            self.moisture = 40.0
        else:
            self.moisture = 50.0

        # Safety checks state
        self.water_level_ok = True

    def next_step(self, pump_is_on):
        """
        Transitions the simulated physical environment to the next second/step.
        
        Parameters:
            pump_is_on (bool): Current status of the simulated pump.
            
        Returns:
            tuple: (raw_value (int), water_level_ok (bool))
        """
        self.step += 1
        
        # 1. Determine rates based on scenario
        drying_rate = 2.0  # % decrease per step when pump is off
        watering_rate = 8.0  # % increase per step when pump is on
        
        if self.scenario == "random_weather":
            # Simulate sudden random events
            rand = random.random()
            if rand < 0.08:
                # Heavy rain! Sudden spike
                self.moisture += 25.0
            elif rand < 0.15:
                # Hot sunny weather: dries 3x faster
                drying_rate = 6.0
                
        elif self.scenario == "pump_runtime_timeout":
            # Simulate pump running but no water reaching the soil (e.g. empty tank or clogged pipe)
            watering_rate = 0.5  # Soil barely changes moisture, causing timeout
            
        # 2. Physics Simulation: Update moisture value based on pump state
        if pump_is_on:
            self.moisture += watering_rate
        else:
            self.moisture -= drying_rate
            
        # Clamp soil moisture to physical bounds (0% to 100%)
        self.moisture = max(0.0, min(self.moisture, 100.0))
        
        # 3. Translate moisture percentage back into a raw sensor voltage reading
        # Formula: Raw Value = DRY_VALUE - (percent/100)*(DRY_VALUE - WET_VALUE)
        raw_value = DRY_RAW_VALUE - (self.moisture / 100.0) * (DRY_RAW_VALUE - WET_RAW_VALUE)
        
        # 4. Inject Noise
        if self.scenario == "sensor_noise":
            # Test how hysteresis behaves under significant electrical/ADC noise
            noise = random.randint(-180, 180)
        else:
            # Low ambient noise typical for calibrated systems
            noise = random.randint(-15, 15)
            
        raw_value += noise
        
        # 5. Inject Safety Hazards
        # Scenario: Sensor Failure (sensor unplugged or short-circuited) after step 5
        if self.scenario == "sensor_failure" and self.step >= 5:
            # Output out-of-bounds readings to trigger safety shutdowns
            if self.step % 2 == 0:
                raw_value = -250  # Below minimum limit
            else:
                raw_value = 5200  # Above maximum limit
                
        # Scenario: Pump Timeout (Empty Water Source / Water Level Sensor fails)
        if self.scenario == "pump_runtime_timeout" and self.step >= 12:
            # Simulate float switch opening (water source depleted)
            self.water_level_ok = False
            
        # Physical clamping of the ADC value (only for non-failure states)
        if not (self.scenario == "sensor_failure" and self.step >= 5):
            raw_value = max(SENSOR_MIN_RAW, min(raw_value, SENSOR_MAX_RAW))
            
        return int(raw_value), self.water_level_ok
