"""
Project paths configuration for soccer-kpis project.

This module provides centralized path management for all data and model directories.
"""

from pathlib import Path

# Define the project root directory (soccer-kpis)
PROJECT_ROOT = Path(__file__).parents[1].resolve()

# Define data directory (soccer-kpis/data)
DATA_DIR = PROJECT_ROOT / "data"

# StatsBomb (soccer-kpis/data/statsbomb)
STATSBOMB_DIR = DATA_DIR / "statsbomb"
STATSBOMB_MATCHES_DIR = STATSBOMB_DIR / "matches"
STATSBOMB_LINEUPS_DIR = STATSBOMB_DIR / "lineups"
STATSBOMB_EVENTS_DIR = STATSBOMB_DIR / "events"
STATSBOMB_THREE_SIXTY_DIR = STATSBOMB_DIR / "three-sixty"
STATSBOMB_COMPETITIONS_FILE = STATSBOMB_DIR / "competitions.json"

# Define models directory (soccer-kpis/models)
MODELS_DIR = PROJECT_ROOT / "models"

# Models
EA_SPORTS_PPI_DIR = MODELS_DIR / "ea_sports_ppi"
OPTA_POINTS_DIR = MODELS_DIR / "opta_points"
PLAYERANK_DIR = MODELS_DIR / "playerank"
VAEP_DIR = MODELS_DIR / "vaep"

# Define notebooks directory (soccer-kpis/notebooks)
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Define output directory (soccer-kpis/output)
OUTPUT_DIR = PROJECT_ROOT / "output"

# Models output
EA_SPORTS_PPI_OUTPUT_DIR = OUTPUT_DIR / "ea_sports_ppi"
OPTA_POINTS_OUTPUT_DIR = OUTPUT_DIR / "opta_points"
PLAYERANK_OUTPUT_DIR = OUTPUT_DIR / "playerank"
VAEP_OUTPUT_DIR = OUTPUT_DIR / "vaep"

MODEL_OUTPUT_DIRECTORIES = [
    EA_SPORTS_PPI_OUTPUT_DIR,
    OPTA_POINTS_OUTPUT_DIR,
    PLAYERANK_OUTPUT_DIR,
    VAEP_OUTPUT_DIR,
]

# Define scripts directory (soccer-kpis/scripts)
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def create_required_directories():
    """Create all required directories if they do not exist."""
    dirs = [
        DATA_DIR,
        STATSBOMB_DIR,
        STATSBOMB_MATCHES_DIR,
        STATSBOMB_LINEUPS_DIR,
        STATSBOMB_EVENTS_DIR,
        STATSBOMB_THREE_SIXTY_DIR,
        MODELS_DIR,
        EA_SPORTS_PPI_DIR,
        OPTA_POINTS_DIR,
        PLAYERANK_DIR,
        VAEP_DIR,
        NOTEBOOKS_DIR,
        OUTPUT_DIR,
        EA_SPORTS_PPI_OUTPUT_DIR,
        OPTA_POINTS_OUTPUT_DIR,
        PLAYERANK_OUTPUT_DIR,
        VAEP_OUTPUT_DIR,
        SCRIPTS_DIR,
    ]

    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


# Create directories automatically when module is imported
create_required_directories()
