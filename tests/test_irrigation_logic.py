# tests/test_irrigation_logic.py

import pytest
from src.irrigation_logic import (
    clamp,
    raw_to_moisture_percent,
    is_sensor_valid,
    classify_soil,
    should_turn_pump_on,
    should_turn_pump_off,
    update_pump_state
)
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

def test_clamp():
    """Verify numeric value clamping."""
    assert clamp(50, 0, 100) == 50
    assert clamp(-10, 0, 100) == 0
    assert clamp(150, 0, 100) == 100

def test_calibration_dry_value():
    """Verify that the raw dry value maps to 0% moisture."""
    percent = raw_to_moisture_percent(DRY_RAW_VALUE)
    assert percent == 0.0

def test_calibration_wet_value():
    """Verify that the raw wet value maps to 100% moisture."""
    percent = raw_to_moisture_percent(WET_RAW_VALUE)
    assert percent == 100.0

def test_calibration_clamping():
    """Verify that out-of-calibration values are clamped correctly between 0% and 100%."""
    # Values more dry than air dry calibration limit
    dry_out_of_bounds = DRY_RAW_VALUE + 500
    assert raw_to_moisture_percent(dry_out_of_bounds) == 0.0
    
    # Values more wet than water wet calibration limit
    wet_out_of_bounds = WET_RAW_VALUE - 500
    assert raw_to_moisture_percent(wet_out_of_bounds) == 100.0

def test_dry_threshold_turns_pump_on():
    """Verify that dry soil moisture level below threshold turns the pump ON."""
    moisture = DRY_THRESHOLD_PERCENT - 5.0  # 30.0% moisture (dry)
    
    # Check simple helper function
    assert should_turn_pump_on(moisture, pump_is_on=False) is True
    
    # Check state machine transition (AUTO mode, IDLE state, pump OFF, no cooldown)
    pump_on, runtime, cooldown, state, event = update_pump_state(
        moisture_percent=moisture,
        current_state="IDLE",
        mode="AUTO",
        runtime_seconds=0,
        cooldown_seconds=0
    )
    assert pump_on is True
    assert runtime == 1
    assert state == "PUMP_ON"
    assert event == "SOIL_DRY_PUMP_ON"

def test_wet_threshold_turns_pump_off():
    """Verify that wet soil moisture level above threshold turns the pump OFF."""
    moisture = WET_THRESHOLD_PERCENT + 5.0  # 65.0% moisture (wet)
    
    # Check simple helper function
    assert should_turn_pump_off(moisture, pump_is_on=True) is True
    
    # Check state machine transition (AUTO mode, PUMP_ON state, pump ON)
    pump_on, runtime, cooldown, state, event = update_pump_state(
        moisture_percent=moisture,
        current_state="PUMP_ON",
        mode="AUTO",
        runtime_seconds=10,
        cooldown_seconds=0
    )
    assert pump_on is False
    assert runtime == 0
    assert cooldown == PUMP_COOLDOWN_SECONDS
    assert state == "SOIL_WET"
    assert event == "SOIL_WET_PUMP_OFF"

def test_hysteresis_neutral_zone():
    """Verify that the pump maintains its state in the hysteresis region (between dry and wet thresholds)."""
    # 50.0% moisture is between 35% (dry) and 60% (wet)
    moisture = (DRY_THRESHOLD_PERCENT + WET_THRESHOLD_PERCENT) / 2.0
    
    # Test case 1: Pump was already OFF. It should stay OFF.
    pump_on, runtime, cooldown, state, event = update_pump_state(
        moisture_percent=moisture,
        current_state="IDLE",
        mode="AUTO",
        runtime_seconds=0,
        cooldown_seconds=0
    )
    assert pump_on is False
    assert state == "SOIL_OK"
    assert event == "NORMAL"

    # Test case 2: Pump was already ON. It should stay ON.
    pump_on, runtime, cooldown, state, event = update_pump_state(
        moisture_percent=moisture,
        current_state="PUMP_ON",
        mode="AUTO",
        runtime_seconds=10,
        cooldown_seconds=0
    )
    assert pump_on is True
    assert runtime == 11
    assert state == "PUMP_ON"
    assert event == "NORMAL"

def test_sensor_error_turns_pump_off():
    """Verify that an invalid sensor reading turns the pump OFF immediately for safety."""
    # Test case 1: Sensor invalid flag passed in update_pump_state
    pump_on, runtime, cooldown, state, event = update_pump_state(
        moisture_percent=0.0,
        current_state="PUMP_ON",
        mode="AUTO",
        runtime_seconds=10,
        cooldown_seconds=0,
        sensor_valid=False
    )
    assert pump_on is False
    assert state == "SENSOR_ERROR"
    assert event == "SENSOR_ERROR_PUMP_OFF"
    
    # Test case 2: Checking invalid boundary inputs in is_sensor_valid helper
    assert is_sensor_valid(SENSOR_MIN_RAW - 100) is False
    assert is_sensor_valid(SENSOR_MAX_RAW + 100) is False
    assert is_sensor_valid(None) is False
    assert is_sensor_valid("invalid") is False

def test_maximum_runtime_cutoff():
    """Verify that the pump shuts off automatically if it exceeds the maximum continuous runtime."""
    moisture = DRY_THRESHOLD_PERCENT - 5.0  # 30% (soil is still dry)
    
    # Pump has run for MAX_PUMP_RUNTIME_SECONDS (30 seconds)
    pump_on, runtime, cooldown, state, event = update_pump_state(
        moisture_percent=moisture,
        current_state="PUMP_ON",
        mode="AUTO",
        runtime_seconds=MAX_PUMP_RUNTIME_SECONDS,
        cooldown_seconds=0
    )
    
    # Should force shutdown, lock cooldown, and report timeout state
    assert pump_on is False
    assert runtime == 0
    assert cooldown == PUMP_COOLDOWN_SECONDS
    assert state == "WATERING_TIMEOUT"
    assert event == "WATERING_TIMEOUT"

def test_cooldown_lockout():
    """Verify that the cooldown period prevents the pump from restarting immediately."""
    moisture = DRY_THRESHOLD_PERCENT - 5.0  # 30.0% (dry soil, normally triggers watering)
    
    # Cooldown timer is active with 10 seconds remaining, pump is OFF
    pump_on, runtime, cooldown, state, event = update_pump_state(
        moisture_percent=moisture,
        current_state="COOLDOWN_ACTIVE",
        mode="AUTO",
        runtime_seconds=0,
        cooldown_seconds=10
    )
    
    # Pump must stay OFF, and cooldown should decrement
    assert pump_on is False
    assert cooldown == 9
    assert state == "COOLDOWN_ACTIVE"
    assert event == "COOLDOWN_ACTIVE"
