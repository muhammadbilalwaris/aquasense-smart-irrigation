# src/main.py

import time
import sys
from src.config import (
    LOG_FILE,
    SAMPLING_INTERVAL_SECONDS,
    DEFAULT_MODE
)
from src.simulator import SoilSimulator
from src.irrigation_logic import (
    raw_to_moisture_percent,
    is_sensor_valid,
    update_pump_state
)
from src.data_logger import DataLogger
from src.dashboard import display_dashboard, clear_terminal

def print_banner():
    print("""
=========================================================
      AquaSense: Smart Soil Moisture Irrigation
                 Simulation Console
=========================================================
Welcome! This simulator models physical soil moisture
depletion and watering cycles while demonstrating the
underlying safety systems, calibration, and hysteresis.
---------------------------------------------------------
""")

def select_scenario():
    scenarios = {
        "1": ("normal_drying", "Normal Drying (Cycle through dry-watering-wet states)"),
        "2": ("very_dry_soil", "Very Dry Soil (Test immediate pump activation in drought)"),
        "3": ("already_wet_soil", "Already Wet Soil (Test that pump stays OFF)"),
        "4": ("sensor_noise", "Sensor Noise (Test hysteresis immunity against fluctuations)"),
        "5": ("sensor_failure", "Sensor Failure (Test safety pump shutoff on invalid sensor)"),
        "6": ("pump_runtime_timeout", "Pump Timeout / Tank Empty (Test dry tank and max run overrides)"),
        "7": ("random_weather", "Random Weather (Test system stability during rain and dry spells)"),
    }
    
    print("Choose a Simulation Scenario:")
    for key, (_, desc) in scenarios.items():
        print(f" [{key}] {desc}")
    
    choice = input("\nSelect scenario [1-7] (default 1): ").strip()
    selected = scenarios.get(choice, scenarios["1"])
    print(f"-> Selected Scenario: {selected[1]}\n")
    return selected[0]

def select_mode():
    print("Choose Control Mode:")
    print(" [1] AUTO (Automatic threshold-based watering with hysteresis)")
    print(" [2] MANUAL (User triggers pump ON/OFF; safety timers still run)")
    
    choice = input("\nSelect mode [1-2] (default 1): ").strip()
    if choice == "2":
        print("-> Selected Mode: MANUAL\n")
        return "MANUAL"
    else:
        print("-> Selected Mode: AUTO\n")
        return "AUTO"

def select_run_style():
    print("Choose Execution Style:")
    print(" [1] Auto-Run (Step automatically every 0.5 seconds)")
    print(" [2] Step-by-Step (Press Enter to execute the next step)")
    
    choice = input("\nSelect style [1-2] (default 1): ").strip()
    return "STEP" if choice == "2" else "AUTO_PLAY"

def main():
    clear_terminal()
    print_banner()
    
    # Setup configuration
    scenario = select_scenario()
    mode = select_mode()
    run_style = select_run_style()
    
    # Ask for steps
    try:
        steps_input = input("Enter number of simulation steps (default 30): ").strip()
        steps = int(steps_input) if steps_input else 30
    except ValueError:
        steps = 30
    print(f"-> Simulation will run for {steps} steps.\n")
    time.sleep(1)
    
    # Initialize components
    simulator = SoilSimulator(scenario=scenario)
    logger = DataLogger(LOG_FILE)
    
    # Control variables (start at default safe states)
    pump_status = False
    runtime_seconds = 0
    cooldown_seconds = 0
    current_state = "IDLE"
    
    print("Starting simulation... Press Ctrl+C to terminate early.")
    time.sleep(1.5)
    
    # Main simulation loop
    for step in range(1, steps + 1):
        # 1. Fetch sensor values and environment flags from simulator
        raw_val, water_level_ok = simulator.next_step(pump_status)
        
        # 2. Convert and validate sensor readings
        sensor_valid = is_sensor_valid(raw_val)
        moisture_percent = raw_to_moisture_percent(raw_val) if sensor_valid else 0.0
        
        # 3. Handle manual input if in manual mode
        manual_pump_command = None
        if mode == "MANUAL" and sensor_valid and cooldown_seconds == 0 and not (current_state == "WATERING_TIMEOUT"):
            clear_terminal()
            print(f"--- MANUAL INPUT REQUEST (Step {step}/{steps}) ---")
            print(f"Current Soil Moisture: {moisture_percent:.1f}%")
            print(f"Pump Status: {'ON' if pump_status else 'OFF'}")
            print(f"Runtime: {runtime_seconds}s | Cooldown: {cooldown_seconds}s")
            print("-------------------------------------------------")
            print("Select Manual Action:")
            print(" [1] Turn Pump ON")
            print(" [2] Turn Pump OFF")
            print(" [3] Do Nothing (maintain state)")
            print(" [4] Stop Simulation")
            action = input("Enter command [1-4] (default 3): ").strip()
            
            if action == "1":
                manual_pump_command = "ON"
            elif action == "2":
                manual_pump_command = "OFF"
            elif action == "4":
                print("Simulation aborted by user.")
                sys.exit(0)
        
        # 4. Process State Machine Tick
        pump_status, runtime_seconds, cooldown_seconds, current_state, event = update_pump_state(
            moisture_percent=moisture_percent,
            current_state=current_state,
            mode=mode,
            runtime_seconds=runtime_seconds,
            cooldown_seconds=cooldown_seconds,
            sensor_valid=sensor_valid,
            water_level_ok=water_level_ok,
            manual_pump_command=manual_pump_command
        )
        
        # 5. Render dashboard update
        clear_terminal()
        display_dashboard(
            raw_value=raw_val,
            moisture_percent=moisture_percent,
            soil_status=current_state,
            pump_status=pump_status,
            mode=mode,
            event=event,
            runtime_seconds=runtime_seconds,
            cooldown_seconds=cooldown_seconds,
            current_step=step,
            total_steps=steps
        )
        
        # 6. Save event to CSV log file
        logger.log_event(
            raw_value=raw_val if sensor_valid else None,
            moisture_percent=moisture_percent,
            soil_status=current_state,
            pump_status=pump_status,
            mode=mode,
            event=event,
            runtime_seconds=runtime_seconds,
            cooldown_seconds=cooldown_seconds
        )
        
        # 7. Wait and advance step
        if step < steps:
            if run_style == "STEP":
                input("\nPress [Enter] to run next step...")
            else:
                time.sleep(0.5)
                
    print("\nSimulation complete. Data saved successfully to:", LOG_FILE)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user. Exiting.")
        sys.exit(0)
