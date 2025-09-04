"""
Module to calculate the EA Sports Player Performance Index (PPI).
"""

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


def _subindex_1(stats: dict) -> float:
    """Calculates Subindex 1 as the sum of contributions multiplied by their expected impact on team league points."""
    score = MODEL_COEFFICIENTS["constant"]
    for action, coeff in MODEL_COEFFICIENTS.items():
        if action != "constant":
            count = stats.get(action, 0)
            score += coeff * count
    return score


def _subindex_2(player_minutes: int, team_minutes: int, home_goals: int, away_goals: int) -> float:
    """Calculates Subindex 2 as team points multiplied by the ratio of player minutes to total team minutes."""
    if home_goals > away_goals:
        return POINTS_FOR_WIN * (player_minutes / team_minutes)
    elif home_goals == away_goals:
        return POINTS_FOR_DRAW * (player_minutes / team_minutes)
    else:  # home_goals < away_goals
        return POINTS_FOR_LOSS * (player_minutes / team_minutes)


def _subindex_3(player_minutes: int, team_minutes: int) -> float:
    """Calculates Subindex 3 as avg. points per game multiplied by the ratio of player minutes to total team minutes."""
    return POINTS_PER_GAME * (player_minutes / team_minutes)


def _subindex_4(goals: int) -> float:
    """Calculates Subindex 4 as the points per goal multiplied by the number of goals scored by the player."""
    return POINTS_PER_GOAL * goals


def _subindex_5(assists: int) -> float:
    """Calculates Subindex 5 as the points per assist multiplied by the number of assists provided by the player."""
    return POINTS_PER_ASSIST * assists


def _subindex_6(clean_sheets: int, position: str) -> float:
    """Calculates Subindex 6 as clean sheet points awarded based on the player's position (GK, DEF, MID, or ST)."""
    return POINTS_PER_CLEAN_SHEET[position] * clean_sheets


def index_score(stats: dict) -> float:
    """Computes the final player index score by weighting all subindices."""
    i1 = _subindex_1(stats)
    i2 = _subindex_2(stats["minutes_played"], stats["team_minutes"], stats["home_goals"], stats["away_goals"])
    i3 = _subindex_3(stats["minutes_played"], stats["team_minutes"])
    i4 = _subindex_4(stats["goals"])
    i5 = _subindex_5(stats["assists"])
    i6 = _subindex_6(stats["clean_sheets"], stats["position"])

    final_score = 100 * (0.25 * i1 + 0.375 * i2 + 0.125 * i3 + 0.125 * i4 + 0.0625 * i5 + 0.0625 * i6)

    return final_score
