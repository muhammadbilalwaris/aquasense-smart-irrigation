# src/config.py

# Calibration raw values for the soil moisture sensor
# For capacitive sensors, dry soil typically yields a higher voltage (higher raw ADC value)
# and wet soil yields a lower voltage (lower raw ADC value).
DRY_RAW_VALUE = 3000
WET_RAW_VALUE = 1200

# Soil moisture threshold percentages for irrigation control
DRY_THRESHOLD_PERCENT = 35.0
WET_THRESHOLD_PERCENT = 60.0

# Physical limits of the ADC (ESP32 is 12-bit ADC, mapping 0 to 4095)
SENSOR_MIN_RAW = 0
SENSOR_MAX_RAW = 4095

# Safety settings
MAX_PUMP_RUNTIME_SECONDS = 30
PUMP_COOLDOWN_SECONDS = 15
SAMPLING_INTERVAL_SECONDS = 1

# Default operational settings
DEFAULT_MODE = "AUTO"  # Options: "AUTO", "MANUAL"

# CSV logging configuration
LOG_FILE = "data/sample_irrigation_log.csv"
