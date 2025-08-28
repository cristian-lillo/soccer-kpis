import utils


def subindex_1(stats) -> float:
    """Calculates Subindex 1 as the sum of contributions multiplied by their expected impact on team league points."""
    score = utils.MODEL_COEFFICIENTS["constant"]
    for action, coeff in utils.MODEL_COEFFICIENTS.items():
        if action != "constant":
            count = stats.get(action, 0)
            score += coeff * count
    return score


def subindex_2(player_minutes, team_minutes, home_goals, away_goals) -> float:
    """Calculates Subindex 2 as team points multiplied by the ratio of player minutes to total team minutes."""
    if home_goals > away_goals:
        return utils.POINTS_FOR_WIN * (player_minutes / team_minutes)
    elif home_goals == away_goals:
        return utils.POINTS_FOR_DRAW * (player_minutes / team_minutes)
    else:  # home_goals < away_goals
        return utils.POINTS_FOR_LOSS * (player_minutes / team_minutes)


def subindex_3(player_minutes, team_minutes) -> float:
    """Calculates Subindex 3 as avg. points per game multiplied by the ratio of player minutes to total team minutes."""
    return utils.POINTS_PER_GAME * (player_minutes / team_minutes)


def subindex_4(goals) -> float:
    """Calculates Subindex 4 as the points per goal multiplied by the number of goals scored by the player."""
    return utils.POINTS_PER_GOAL * goals


def subindex_5(assists) -> float:
    """Calculates Subindex 5 as the points per assist multiplied by the number of assists provided by the player."""
    return utils.POINTS_PER_ASSIST * assists


def subindex_6(clean_sheets, position) -> float:
    """Calculates Subindex 6 as clean sheet points awarded based on the player's position (GK, DEF, MID, or ST)."""
    return utils.POINTS_PER_CLEAN_SHEET[position] * clean_sheets


def index_score(stats):
    """Computes the final player index score by weighting all subindices."""
    i1 = subindex_1(stats)
    i2 = subindex_2(stats["minutes_played"], stats["team_minutes"], stats["home_goals"], stats["away_goals"])
    i3 = subindex_3(stats["minutes_played"], stats["team_minutes"])
    i4 = subindex_4(stats["goals"])
    i5 = subindex_5(stats["assists"])
    i6 = subindex_6(stats["clean_sheets"], stats["position"])

    final_score = 100 * (0.25 * i1 + 0.375 * i2 + 0.125 * i3 + 0.125 * i4 + 0.0625 * i5 + 0.0625 * i6)

    return final_score
