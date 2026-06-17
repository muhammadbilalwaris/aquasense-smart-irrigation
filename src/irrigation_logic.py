# src/irrigation_logic.py

from src.config import (
    DRY_RAW_VALUE,
    WET_RAW_VALUE,
    DRY_THRESHOLD_PERCENT,
    WET_THRESHOLD_PERCENT,
    SENSOR_MIN_RAW,
    SENSOR_MAX_RAW,
    MAX_PUMP_RUNTIME_SECONDS,
    PUMP_COOLDOWN_SECONDS
)

def clamp(value, min_value, max_value):
    """Clamps a numeric value between a minimum and maximum range."""
    return max(min_value, min(value, max_value))

def raw_to_moisture_percent(raw_value):
    """
    Converts a raw sensor reading to soil moisture percentage (0% to 100%).
    Handles both traditional analog (voltage drops with wetness) and inverse slopes.
    """
    if raw_value is None:
        return 0.0
    try:
        raw_value = float(raw_value)
    except (ValueError, TypeError):
        return 0.0

    if DRY_RAW_VALUE == WET_RAW_VALUE:
        return 0.0

    percent = ((DRY_RAW_VALUE - raw_value) / (DRY_RAW_VALUE - WET_RAW_VALUE)) * 100.0
    return clamp(percent, 0.0, 100.0)

def is_sensor_valid(raw_value):
    """
    Validates the sensor raw reading against physical operating limits.
    An out-of-range value (e.g. unplugged wire causing 0V/5V rails or noise) is invalid.
    """
    if raw_value is None:
        return False
    try:
        val = float(raw_value)
        return SENSOR_MIN_RAW <= val <= SENSOR_MAX_RAW
    except (ValueError, TypeError):
        return False

def classify_soil(moisture_percent):
    """Classifies the soil condition based on moisture percentage."""
    if moisture_percent < DRY_THRESHOLD_PERCENT:
        return "SOIL_DRY"
    elif moisture_percent > WET_THRESHOLD_PERCENT:
        return "SOIL_WET"
    else:
        return "SOIL_OK"

def should_turn_pump_on(moisture_percent, pump_is_on):
    """Returns True if the pump should switch ON based on dry threshold."""
    if not pump_is_on and moisture_percent < DRY_THRESHOLD_PERCENT:
        return True
    return False

def should_turn_pump_off(moisture_percent, pump_is_on):
    """Returns True if the pump should switch OFF based on wet threshold (hysteresis)."""
    if pump_is_on and moisture_percent > WET_THRESHOLD_PERCENT:
        return True
    return False

def get_event(moisture_percent, pump_state, sensor_valid, water_level_ok=True, state_change=None):
    """Determines the logging event code representing current system activity."""
    if not sensor_valid or not water_level_ok:
        return "SENSOR_ERROR_PUMP_OFF"
    
    if state_change:
        return state_change
        
    if pump_state:
        return "NORMAL"
    else:
        # Pump is off, check if in cooldown
        return "NORMAL"

def update_pump_state(
    moisture_percent, 
    current_state, 
    mode, 
    runtime_seconds, 
    cooldown_seconds,
    sensor_valid=True,
    water_level_ok=True,
    manual_pump_command=None
):
    """
    Executes a single tick of the irrigation state machine.
    
    Parameters:
        moisture_percent (float): Calibrated soil moisture percentage.
        current_state (str): Current state (e.g., "IDLE", "PUMP_ON", "COOLDOWN_ACTIVE", etc.).
        mode (str): Operating mode ("AUTO" or "MANUAL").
        runtime_seconds (int): Current continuous pump runtime.
        cooldown_seconds (int): Current remaining pump cooldown timer.
        sensor_valid (bool): Whether the sensor reading is valid.
        water_level_ok (bool): Whether the supply tank has enough water.
        manual_pump_command (str): Manual toggle instruction ("ON", "OFF", or None).
        
    Returns:
        tuple: (new_pump_state (bool), new_runtime (int), new_cooldown (int), new_state (str), event (str))
    """
    pump_is_on = current_state in ["PUMP_ON", "MANUAL_ON"]

    # 1. High Priority Safety Overrides: Sensor or Water Level Failure
    if not sensor_valid or not water_level_ok:
        new_cooldown = cooldown_seconds
        # Start cooldown if pump was ON
        if pump_is_on:
            new_cooldown = PUMP_COOLDOWN_SECONDS
        return False, 0, new_cooldown, "SENSOR_ERROR", "SENSOR_ERROR_PUMP_OFF"

    # 2. Cooldown Safety Logic: Prevent pump restart during cooldown
    if cooldown_seconds > 0:
        new_cooldown = max(0, cooldown_seconds - 1)
        # Pump must remain OFF, and we are in COOLDOWN_ACTIVE state
        return False, 0, new_cooldown, "COOLDOWN_ACTIVE", "COOLDOWN_ACTIVE"

    # 3. Mode-Specific Control Logic
    if mode == "AUTO":
        if pump_is_on:
            # Safety checks while pump is running
            if runtime_seconds >= MAX_PUMP_RUNTIME_SECONDS:
                # Max runtime exceeded, trigger safety shutdown
                return False, 0, PUMP_COOLDOWN_SECONDS, "WATERING_TIMEOUT", "WATERING_TIMEOUT"
            
            # Hysteresis check
            if should_turn_pump_off(moisture_percent, True):
                return False, 0, PUMP_COOLDOWN_SECONDS, "SOIL_WET", "SOIL_WET_PUMP_OFF"
            
            # Continue running
            return True, runtime_seconds + 1, 0, "PUMP_ON", "NORMAL"
        else:
            # Pump is currently OFF
            if should_turn_pump_on(moisture_percent, False):
                return True, 1, 0, "PUMP_ON", "SOIL_DRY_PUMP_ON"
            
            # Remain OFF, state is based on soil condition
            soil_class = classify_soil(moisture_percent)
            return False, 0, 0, soil_class, "NORMAL"

    else:  # MANUAL MODE
        if pump_is_on:
            # Safety checks still apply to manual mode
            if runtime_seconds >= MAX_PUMP_RUNTIME_SECONDS:
                return False, 0, PUMP_COOLDOWN_SECONDS, "WATERING_TIMEOUT", "WATERING_TIMEOUT"
            
            if manual_pump_command == "OFF":
                return False, 0, PUMP_COOLDOWN_SECONDS, "MANUAL_OFF", "MANUAL_OFF"
            
            # Continue running in manual
            return True, runtime_seconds + 1, 0, "MANUAL_ON", "NORMAL"
        else:
            # Pump is currently OFF
            if manual_pump_command == "ON":
                return True, 1, 0, "MANUAL_ON", "MANUAL_ON"
            
            return False, 0, 0, "MANUAL_OFF", "NORMAL"
