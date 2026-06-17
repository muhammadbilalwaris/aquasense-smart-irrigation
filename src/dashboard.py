# src/dashboard.py

import os

def clear_terminal():
    """Clears the console terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_dashboard(
    raw_value, 
    moisture_percent, 
    soil_status, 
    pump_status, 
    mode, 
    event, 
    runtime_seconds, 
    cooldown_seconds,
    current_step,
    total_steps
):
    """
    Renders a formatted text dashboard of the AquaSense irrigation system in the console.
    """
    pump_indicator = "ON (Watering)" if pump_status else "OFF (Idle)"
    cooldown_indicator = f"ACTIVE ({cooldown_seconds}s remaining)" if cooldown_seconds > 0 else "READY (0s)"
    sensor_display = f"{raw_value}" if raw_value is not None else "OUT OF BOUNDS"
    
    # Formatting styles
    print("\n" + "=" * 55)
    print("      AquaSense: Smart Irrigation Control Dashboard      ")
    print("=" * 55)
    print(f" Simulation Progress : Step {current_step}/{total_steps}")
    print(f" System Mode         : {mode}")
    print(f" Control Event       : {event}")
    print("-" * 55)
    print(f" Soil Moisture Raw   : {sensor_display}")
    print(f" Moisture Percentage : {moisture_percent:.1f}%")
    print(f" Soil Health Status  : {soil_status}")
    print("-" * 55)
    print(f" Pump Valve Relay    : {pump_indicator}")
    print(f" Active Run Timer    : {runtime_seconds}s (Max Limit: 30s)")
    print(f" Cooldown Guard      : {cooldown_indicator}")
    print("=" * 55)
