# tests/test_data_logger.py

import os
import csv
from src.data_logger import DataLogger

def test_csv_logger_creation_and_headers(tmp_path):
    """
    Verifies that the CSV log file is created and contains the correct column headers.
    Uses pytest's tmp_path fixture to avoid polluting the actual project log directory.
    """
    test_filepath = tmp_path / "test_irrigation_log.csv"
    filepath_str = str(test_filepath)
    
    # Instantiate logger (file should not exist yet)
    assert not os.path.exists(filepath_str)
    logger = DataLogger(filepath_str)
    
    # Log a single event
    logger.log_event(
        raw_value=2500,
        moisture_percent=32.54,
        soil_status="SOIL_DRY",
        pump_status=True,
        mode="AUTO",
        event="SOIL_DRY_PUMP_ON",
        runtime_seconds=1,
        cooldown_seconds=0
    )
    
    # Assert that file was created
    assert os.path.exists(filepath_str)
    
    # Verify the structure of the CSV file
    with open(filepath_str, "r", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        
        # Assert headers match the expected schema
        expected_headers = [
            "Date", "Time", "Raw Value", "Moisture Percent", "Soil Status",
            "Pump Status", "Mode", "Event", "Runtime Seconds", "Cooldown Seconds"
        ]
        assert reader[0] == expected_headers
        
        # Assert data row contents
        data_row = reader[1]
        assert len(data_row) == 10
        
        # Verify specific fields (ignoring Date/Time dynamic values)
        assert data_row[2] == "2500"
        assert data_row[3] == "32.5"      # Rounded to 1 decimal
        assert data_row[4] == "SOIL_DRY"
        assert data_row[5] == "ON"
        assert data_row[6] == "AUTO"
        assert data_row[7] == "SOIL_DRY_PUMP_ON"
        assert data_row[8] == "1"
        assert data_row[9] == "0"
