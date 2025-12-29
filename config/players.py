import warnings

import pandas as pd
from socceraction.data.statsbomb import StatsBombLoader

from config import paths

warnings.filterwarnings(
    "ignore",
    message="Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated and will change in a future version.",
    category=FutureWarning,
)


def _merge_players_and_team_data(match_id: int) -> pd.DataFrame:
    """
    Merge player and team data for a given match.

    Args:
        match_id (int): StatsBomb match ID.

    Returns:
        DataFrame containing merged player and team information.
    """
    SBL = StatsBombLoader(getter="local", root=str(paths.STATSBOMB_DIR))

    players_df = SBL.players(game_id=match_id)
    teams_df = SBL.teams(game_id=match_id)

    # Merge players and teams dataframes on team_id
    merged_df = players_df.merge(teams_df, on="team_id", how="left")

    return merged_df


def get_players_info(match_id: int) -> pd.DataFrame:
    """
    Retrieve player information for a given match.

    Args:
        match_id (int): StatsBomb match ID.

    Returns:
        DataFrame containing player names, nicknames, team names, and minutes played.
    """
    merged_df = _merge_players_and_team_data(match_id)

    return merged_df[["player_name", "nickname", "team_name", "minutes_played"]]


def get_minutes_played_by_team(match_id: int) -> dict[str, int]:
    """
    Calculate total minutes played by each team in a given match.

    Args:
        match_id (int): StatsBomb match ID.

    Returns:
        dict[str, float]: Dictionary mapping team names to total minutes played.
    """
    merged_df = _merge_players_and_team_data(match_id)

    team_minutes = merged_df.groupby("team_name")["minutes_played"].sum().to_dict()

    return team_minutes

