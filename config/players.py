import warnings

import pandas as pd
from kloppy import statsbomb
from kloppy.domain import EventDataset
from socceraction.data.statsbomb import StatsBombLoader

from config import paths

# Columns to extract from the StatsBomb event data
COLUMNS_TO_EXTRACT = [
    "player_id",
    "player",
    "team_id",
    "team",
    "event_id",
    "event_type",
    "result",
    "success",
    "body_part_type",
    "pass_type",
    "duel_type",
    "set_piece_type",
    "goalkeeper_type",
    "card_type",
    "replacement_player",
    "is_counter_attack",
    "is_under_pressure",
    "coordinates_x",
    "coordinates_y",
    "time",
]

# Data types for each column
DTYPE_MAPPING = {
    "player_id": "Int64",
    "player": "string",
    "team_id": "Int64",
    "team": "string",
    "event_id": "string",
    "event_type": "category",
    "result": "category",
    "success": "boolean",
    "body_part_type": "category",
    "pass_type": "category",
    "duel_type": "category",
    "set_piece_type": "category",
    "goalkeeper_type": "category",
    "card_type": "category",
    "replacement_player": "string",
    "is_counter_attack": "boolean",
    "is_under_pressure": "boolean",
    "coordinates_x": "Float64",
    "coordinates_y": "Float64",
    "time": "string",
}

warnings.filterwarnings(
    "ignore",
    message="Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated and will change in a future version.",
    category=FutureWarning,
)


def get_players_info(match_id: int) -> pd.DataFrame:
    """
    Retrieve player information for a given match.

    Args:
        match_id (int): StatsBomb match ID.

    Returns:
        DataFrame containing player names, nicknames, team names, and minutes played.
    """
    SBL = StatsBombLoader(getter="local", root=str(paths.STATSBOMB_DIR))

    players_df = SBL.players(game_id=match_id)
    teams_df = SBL.teams(game_id=match_id)

    merged_df = players_df.merge(teams_df, on="team_id", how="left")

    return merged_df[["player_name", "nickname", "team_name", "minutes_played"]]


def load_match_data(match_id: int) -> tuple[EventDataset, pd.DataFrame]:
    """
    Load and preprocess match data for a given match ID.

    Args:
        match_id: StatsBomb match ID.

    Returns:
        A tuple containing the EventDataset and a DataFrame of player events.
    """
    dataset = statsbomb.load(
        event_data=paths.STATSBOMB_EVENTS_DIR / f"{match_id}.json",
        lineup_data=paths.STATSBOMB_LINEUPS_DIR / f"{match_id}.json",
    )

    # Filter out events from period 5 (penalty shootouts) and convert to DataFrame
    regular_and_overtime_dataset = dataset.filter(lambda event: event.period.id != 5)
    events_df = regular_and_overtime_dataset.to_df(*COLUMNS_TO_EXTRACT).astype(DTYPE_MAPPING)

    # Filter events to include only those from players who participated in the match
    players_info_df = get_players_info(match_id)
    player_events_df = events_df[events_df["player"].isin(players_info_df["player_name"])]

    return dataset, player_events_df


def get_players_position_group(dataset: EventDataset) -> dict[str, str]:
    """
    Determine the main position group of all players based on time spent in each position.

    Args:
        dataset: The event dataset containing player position data.

    Returns:
        The main position group of each player as a dictionary.
    """
    player_positions = {}

    # Iterate through dataset to find player's position history
    for team in dataset.metadata.teams:
        for player in team.players:
            player_position = ("", 0)

            for start_time, end_time, position in player.positions.ranges():
                position_duration = (end_time - start_time).total_seconds()
                position_group = position.position_group.name

                # Compare and update the variable if this position has longer duration
                prev_position, prev_duration = player_position
                if position_group != prev_position and position_duration > prev_duration:
                    player_position = (position_group, position_duration)

            player_positions[player.name] = player_position[0]

    return player_positions


def count_assists(match_events_df: pd.DataFrame) -> dict[str, int]:
    """
    Count the number of assists made by each player in a match.

    Args:
        player_events_df: DataFrame containing events by the player.
        match_events_df: DataFrame containing all events in the match.

    Returns:
        A dictionary mapping player names to their assist counts.
    """
    # Filter match goals and shot assists
    goals_df = match_events_df.loc[(match_events_df["event_type"] == "SHOT") & (match_events_df["result"] == "GOAL")]
    shot_assists_df = match_events_df.loc[match_events_df["pass_type"] == "SHOT_ASSIST"]

    # Get indexes of DataFrames
    event_indexes = match_events_df.index.to_list()
    goal_indexes = goals_df.index.to_list()
    shot_assist_indexes = shot_assists_df.index.to_list()

    # Iterate through each shot assist and look for a goal in subsequent events
    players_assists_dict = {}
    for shot_assist_idx in shot_assist_indexes:
        # Get all event indexes that come after the current shot assist
        subsequent_indexes = [idx for idx in event_indexes if idx > shot_assist_idx]

        for event_idx in subsequent_indexes:
            event = match_events_df.loc[event_idx]

            if event_idx in goal_indexes:  # Found a goal for this shot assist
                player_name = event["player"]
                players_assists_dict[player_name] = players_assists_dict.get(player_name, 0) + 1
                break
            elif event["event_type"] == "SHOT" and event["result"] != "GOAL":  # Found an unsuccessful shot
                break

    return players_assists_dict
