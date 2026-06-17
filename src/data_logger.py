# src/data_logger.py

import os
import csv
from datetime import datetime

class DataLogger:
    """
    Handles CSV data logging for the smart irrigation system.
    Logs system statuses, sensor values, runtime details, and events for audits.
    """
    def __init__(self, filepath):
        self.filepath = filepath
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensures that the directory path for the log file exists."""
        dir_name = os.path.dirname(self.filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)

    def log_event(
        self, 
        raw_value, 
        moisture_percent, 
        soil_status, 
        pump_status, 
        mode, 
        event, 
        runtime_seconds, 
        cooldown_seconds
    ):
        """
        Appends a timestamped log entry to the CSV log.
        
        Parameters:
            raw_value (int): Raw analog reading from the sensor (or None).
            moisture_percent (float): Calculated moisture percentage.
            soil_status (str): Soil state classification (e.g. SOIL_DRY, SOIL_OK, etc.).
            pump_status (bool): Whether the pump is ON (True) or OFF (False).
            mode (str): Operating mode (AUTO/MANUAL).
            event (str): Specific log event code (e.g. WATERING_TIMEOUT).
            runtime_seconds (int): Pump continuous runtime in seconds.
            cooldown_seconds (int): Pump remaining cooldown in seconds.
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        file_exists = os.path.exists(self.filepath)
        headers = [
            "Date", "Time", "Raw Value", "Moisture Percent", "Soil Status",
            "Pump Status", "Mode", "Event", "Runtime Seconds", "Cooldown Seconds"
        ]

        # Convert pump_status to string representation
        pump_status_str = "ON" if pump_status else "OFF"
        
        # Format values for readability
        raw_value_val = raw_value if raw_value is not None else "N/A"
        moisture_val = round(moisture_percent, 1)

        try:
            with open(self.filepath, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(headers)
                
                writer.writerow([
                    date_str, 
                    time_str, 
                    raw_value_val, 
                    moisture_val, 
                    soil_status,
                    pump_status_str, 
                    mode, 
                    event, 
                    runtime_seconds, 
                    cooldown_seconds
                ])
        except IOError as e:
            print(f"[Error] Failed to write to log file: {e}")
