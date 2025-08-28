from pathlib import Path

# Define routes for data directories
DATA_DIR = Path("data")
MATCHES_DIR = DATA_DIR / "matches"
LINEUPS_DIR = DATA_DIR / "lineups"
EVENTS_DIR = DATA_DIR / "events"
THREE_SIXTY_DIR = DATA_DIR / "three_sixty"

# Subindex 1: Model coefficients
MODEL_COEFFICIENTS = {
    "crosses": 0.519,
    "dribbles": 0.118,
    "passes": 0.034,
    "opp_interceptions": -0.024,
    "opp_yellows": 0.253,
    "opp_reds": 1.023,
    "opp_tackle_win_ratio": -0.170,
    "opp_clearances": -0.017,
    "constant": 6.463,
}

# Subindex 2: Points for match outcomes
POINTS_FOR_WIN = 3
POINTS_FOR_DRAW = 1
POINTS_FOR_LOSS = 0

# Subindex 3: Average points per game
POINTS_PER_GAME = 1.34

# Subindex 4: Points per goal
POINTS_PER_GOAL = 1.039

# Subindex 5: Points per assist
POINTS_PER_ASSIST = 1.039

# Subindex 6: Points for clean sheets based on position
POINTS_PER_CLEAN_SHEET = {"GK": 0.585, "DF": 0.364, "MF": 0.150, "ST": 0.071}
