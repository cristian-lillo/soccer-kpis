"""
Configuration file for soccer KPIs analysis project.
Contains data paths and project settings.
"""

from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).parent

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EVENTS_DATA_DIR = DATA_DIR / "events"
STATSBOMB_DATA_DIR = DATA_DIR / "statsbomb"

# Output directories
OUTPUT_DIR = BASE_DIR / "output"
ANALYSIS_OUTPUT_DIR = OUTPUT_DIR / "analysis"
PLOTS_DIR = OUTPUT_DIR / "plots"
REPORTS_DIR = OUTPUT_DIR / "reports"

# File patterns
EVENTS_FILE_PATTERN = "*.json"
MATCH_DATA_PATTERN = "match_*.json"


# Create directories if they don't exist
def create_directories():
    """Create all necessary directories if they don't exist."""
    directories = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        EVENTS_DATA_DIR,
        STATSBOMB_DATA_DIR,
        OUTPUT_DIR,
        ANALYSIS_OUTPUT_DIR,
        PLOTS_DIR,
        REPORTS_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Directory ensured: {directory}")


# Usage example
if __name__ == "__main__":
    create_directories()
    print(f"Base directory: {BASE_DIR}")
    print(f"Data directory: {DATA_DIR}")
