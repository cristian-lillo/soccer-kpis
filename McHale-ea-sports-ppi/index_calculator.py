import utils


def subindex_1(expected_goals) -> float:
    """Calculates Subindex 1 as the sum of contributions multiplied by their expected impact on team league points."""
    return 0


def subindex_2(player_minutes, team_minutes, team_result) -> float:
    """Calculates Subindex 2 as team points multiplied by the ratio of player minutes to total team minutes."""
    points_map = {
        "win": utils.POINTS_FOR_WIN,
        "draw": utils.POINTS_FOR_DRAW,
        "loss": utils.POINTS_FOR_LOSS,
    }

    if team_result in points_map:
        return points_map[team_result] * (player_minutes / team_minutes)
    else:
        raise ValueError("Invalid team result. Must be 'win', 'draw', or 'loss'.")


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
    i2 = subindex_2(stats["minutes_played"], stats["team_minutes"], stats["team_result"])
    i3 = subindex_3(stats["minutes_played"], stats["team_minutes"])
    i4 = subindex_4(stats["goals"])
    i5 = subindex_5(stats["assists"])
    i6 = subindex_6(stats["clean_sheets"], stats["position"])

    final_score = 100 * (0.25 * i1 + 0.375 * i2 + 0.125 * i3 + 0.125 * i4 + 0.0625 * i5 + 0.0625 * i6)

    return final_score
