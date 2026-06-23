"""
Project paths configuration for soccer-kpis project.

This module provides centralized path management for all data and model directories.
"""

from pathlib import Path

# Define the project root directory (soccer-kpis)
PROJECT_ROOT = Path(__file__).parents[1].resolve()

# Define data directory (soccer-kpis/data)
DATA_DIR = PROJECT_ROOT / "data"

# Papers data
PAPERS_DATA_DIR = DATA_DIR / "papers"

# Papplardo's Wyscout data (soccer-kpis/data/pappalardo)
WYSCOUT_PAPPALARDO_DIR = DATA_DIR / "pappalardo"

# StatsBomb (soccer-kpis/data/statsbomb)
STATSBOMB_DIR = DATA_DIR / "statsbomb"
STATSBOMB_MATCHES_DIR = STATSBOMB_DIR / "matches"
STATSBOMB_LINEUPS_DIR = STATSBOMB_DIR / "lineups"
STATSBOMB_EVENTS_DIR = STATSBOMB_DIR / "events"
STATSBOMB_THREE_SIXTY_DIR = STATSBOMB_DIR / "three-sixty"
STATSBOMB_COMPETITIONS_FILE = STATSBOMB_DIR / "competitions.json"

# Define models directory (soccer-kpis/models)
MODELS_DIR = PROJECT_ROOT / "models"

# Model-specific directories
EA_SPORTS_PPI_DIR = MODELS_DIR / "ea_sports_ppi"
OPTA_POINTS_DIR = MODELS_DIR / "opta_points"
PLAYERANK_DIR = MODELS_DIR / "playerank"
VAEP_DIR = MODELS_DIR / "vaep"

# Define notebooks directory (soccer-kpis/notebooks)
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Define output directory (soccer-kpis/output)
OUTPUT_DIR = PROJECT_ROOT / "output"

# Model output directories
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


def setup_project_directories():
    """Create all necessary project directories if they do not exist."""
    required_directories = [
        DATA_DIR,
        PAPERS_DATA_DIR,
        WYSCOUT_PAPPALARDO_DIR,
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

    for directory_path in required_directories:
        directory_path.mkdir(parents=True, exist_ok=True)


# Ensure all required directories exist
setup_project_directories()
