"""
Project paths configuration for soccer-kpis project.

This module provides centralized path management for all data and model directories.
"""

from pathlib import Path

# Define the project root directory (soccer-kpis)
PROJECT_ROOT = Path(__file__).parents[1].resolve()

# Define data directory (soccer-kpis/data)
DATA_DIR = PROJECT_ROOT / "data"

# StatsBomb
STATSBOMB_DIR = DATA_DIR / "statsbomb"
STATSBOMB_MATCHES_DIR = STATSBOMB_DIR / "matches"
STATSBOMB_LINEUPS_DIR = STATSBOMB_DIR / "lineups"
STATSBOMB_EVENTS_DIR = STATSBOMB_DIR / "events"
STATSBOMB_THREE_SIXTY_DIR = STATSBOMB_DIR / "three-sixty"
STATSBOMB_COMPETITIONS_FILE = STATSBOMB_DIR / "competitions.json"

# WyScout
WYSCOUT_DIR = DATA_DIR / "wyscout"
WYSCOUT_PROCESSED_DIR = WYSCOUT_DIR / "processed" / "files"
WYSCOUT_PROCESSED_V2_DIR = WYSCOUT_DIR / "processed-v2" / "files"

# Chile
CHILE_DIR = DATA_DIR / "chile"

# Other data providers
METRICA_SPORTS_DIR = DATA_DIR / "metrica-sports"
SKILLCORNER_DIR = DATA_DIR / "skillcorner"
SPORTEC_SOLUTIONS_DIR = DATA_DIR / "sportec-solutions"
WYSCOUT_PAPPALARDO_DIR = DATA_DIR / "wyscout-pappalardo"

# Define models directory (soccer-kpis/models)
MODELS_DIR = PROJECT_ROOT / "models"

# Models
EA_SPORTS_PPI_DIR = MODELS_DIR / "ea-sports-ppi"
PLAYERANK_DIR = MODELS_DIR / "playerank"
VAEP_DIR = MODELS_DIR / "vaep"

# Define notebooks directory (soccer-kpis/notebooks)
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Define scripts directory (soccer-kpis/scripts)
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
