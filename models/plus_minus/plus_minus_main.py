"""
Module to calculate offensive and defensive plus-minus scores for a match.
"""

import warnings
from datetime import timedelta

import pandas as pd
from kloppy.domain import EventDataset
from tqdm import tqdm

from config import paths, players, tournaments

warnings.filterwarnings(
    "ignore",
    message="The default of observed=False is deprecated and will be changed to True in a future version of pandas. Pass observed=False to retain current behavior or observed=True to adopt the future default and silence this warning.",
    category=FutureWarning,
)

warnings.filterwarnings(
    "ignore",
    message="Boolean Series key will be reindexed to match DataFrame index.",
    category=UserWarning,
)

# Constants for Plus-Minus calculations
RHO_2 = 300.0
RHO_3 = 300.0
RHO_4 = 2.5

# Factor are not defined. Won't be used in the current implementation, but kept for future reference.
NUMBER_OF_RED_CARDS = [1, 2, 3, 4]
RED_FACTOR_OFFENSIVE_HOME = {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4}
RED_FACTOR_DEFENSIVE_HOME = {1: 0.05, 2: 0.1, 3: 0.15, 4: 0.2}
RED_FACTOR_OFFENSIVE_AWAY = {1: 0.08, 2: 0.16, 3: 0.24, 4: 0.32}
RED_FACTOR_DEFENSIVE_AWAY = {1: 0.04, 2: 0.08, 3: 0.12, 4: 0.16}


def get_match_start_and_end_times(dataset: EventDataset) -> tuple[str, str]:
    """Retrieve the start and end times of a match from the dataset."""
    periods = dataset.metadata.periods
    return str(periods[0].start_time), str(periods[-1].end_time)


def convert_timedelta_to_minutes(duration: timedelta) -> int:
    """Convert a timedelta object to total minutes, rounding up if seconds are 30 or more."""
    minutes, seconds = divmod(duration.seconds, 60)
    return minutes + 1 if seconds >= 30 else minutes


def get_period_duration(dataset: EventDataset) -> dict[str, int]:
    """ "Retrieve the duration of each period in a match, converting to total minutes."""
    periods = dataset.metadata.periods
    durations = {f"{period.id}": period.duration for period in periods}
    return {f"{key}": convert_timedelta_to_minutes(duration) for key, duration in durations.items()}


def convert_time_str_to_minutes(dataset, time_str: str) -> int:
    """
    Convert a time string in the format "P#T##:##" to minutes.

    Parameters:
    - dataset: The event dataset for the match.
    - time_str: The time string to convert.

    Returns:
        The total number of minutes represented by the time string.
    """
    period_durations = get_period_duration(dataset)

    current_period = int(time_str[1])
    minutes, seconds = map(int, time_str[3:].split(":"))

    previous_period_minutes = sum(period_durations.get(str(period_id), 0) for period_id in range(1, current_period))

    if current_period == 5:
        return previous_period_minutes  # Don't add extra minutes for penalty shootouts
    else:
        return previous_period_minutes + minutes + (1 if seconds >= 30 else 0)


def calculate_segment_duration(dataset: EventDataset, start_time: str, end_time: str) -> int:
    """Calculate the duration of a match segment in minutes, given start and end times."""
    start_minutes = convert_time_str_to_minutes(dataset, start_time)
    end_minutes = convert_time_str_to_minutes(dataset, end_time)
    duration = end_minutes - start_minutes
    return duration if duration > 0 else 1


def divide_match_in_segments(dataset: EventDataset, match_events_df: pd.DataFrame) -> dict[str, dict]:
    """
    Divide a match into segments based on events like substitutions and red cards.

    Args:
        dataset (EventDataset): The event dataset for the match.
        match_events_df (pd.DataFrame): DataFrame containing match events.

    Returns:
        A dictionary where keys are segment identifiers and values are dictionaries containing segment details.
    """
    home_team: str = dataset.metadata.teams[0].name
    away_team: str = dataset.metadata.teams[1].name

    match_start, match_end = get_match_start_and_end_times(dataset)
    event_times = {match_start, match_end}
    segments = {}

    substitutions = match_events_df.loc[match_events_df["event_type"] == "SUBSTITUTION", "time"]
    red_cards = match_events_df.loc[
        (match_events_df["event_type"] == "CARD") & (match_events_df["card_type"] == "RED"), "time"
    ]
    player_off = match_events_df.loc[match_events_df["event_type"] == "PLAYER_OFF", "time"]
    player_on = match_events_df.loc[match_events_df["event_type"] == "PLAYER_ON", "time"]

    event_times.update(substitutions)
    event_times.update(red_cards)
    event_times.update(player_off)
    event_times.update(player_on)

    sorted_event_times = sorted(event_times)
    for i in range(len(sorted_event_times) - 1):
        start_time = sorted_event_times[i]
        end_time = sorted_event_times[i + 1]
        segment_key = f"{start_time} - {end_time}"
        segments[segment_key] = {
            "start_time": start_time,
            "end_time": end_time,
            "duration": calculate_segment_duration(dataset, start_time, end_time),
            "goals": match_events_df.loc[
                (match_events_df["time"] >= start_time)
                & (match_events_df["time"] < end_time)
                & (match_events_df["event_type"] == "SHOT")
                & (match_events_df["success"]),
                ["team", "time"],
            ].to_dict(orient="records"),
            "home_goals": len(
                match_events_df.loc[
                    (match_events_df["time"] >= start_time)
                    & (match_events_df["time"] < end_time)
                    & (match_events_df["event_type"] == "SHOT")
                    & (match_events_df["success"])
                    & (match_events_df["team"] == home_team)
                ]
            ),
            "away_goals": len(
                match_events_df.loc[
                    (match_events_df["time"] >= start_time)
                    & (match_events_df["time"] < end_time)
                    & (match_events_df["event_type"] == "SHOT")
                    & (match_events_df["success"])
                    & (match_events_df["team"] == away_team)
                ]
            ),
        }

    return segments


def get_player_start_and_end_times(dataset: EventDataset, player_name: str) -> tuple:
    """
    Determine the start and end times of a player's participation in the match.

    Args:
        dataset: The event dataset containing player position data.
        player_name: The name of the player.

    Returns:
        A tuple containing the start and end times of the player's participation.
    """
    periods_duration = get_period_duration(dataset)

    player_start_time = None
    player_end_time = None

    # Iterate through dataset to find player's position history
    for team in dataset.metadata.teams:
        for player in team.players:
            # Only get position for the specified player
            if player.full_name == player_name:
                for start_time, end_time, _ in player.positions.ranges():
                    if player_start_time is None:
                        player_start_time = start_time
                    if player_end_time is None or end_time > player_end_time:
                        player_end_time = end_time

    # Convert start and end times to minutes, considering previous period durations
    if player_start_time is not None:
        current_period = int(player_start_time.period.id)
        previous_periods_minutes = sum(periods_duration.get(str(i), 0) for i in range(1, current_period))
        start_minutes_in_period = convert_timedelta_to_minutes(player_start_time.timestamp)
        player_start_time = previous_periods_minutes + start_minutes_in_period
    if player_end_time is not None:
        current_period = int(player_end_time.period.id)
        previous_periods_minutes = sum(periods_duration.get(str(i), 0) for i in range(1, current_period))
        end_minutes_in_period = convert_timedelta_to_minutes(player_end_time.timestamp)
        player_end_time = previous_periods_minutes + (end_minutes_in_period if current_period != 5 else 0)

    return player_start_time, player_end_time


def calculate_plus_minus_score(
    dataset: EventDataset,
    match_segments: dict[str, dict],
    player_name: str,
    team: str,
) -> float:
    """
    Calculate the plus-minus score for a player based on match segments.

    Args:
        dataset (EventDataset): The event dataset for the match.
        match_segments (dict): A dictionary containing match segments.
        player_name (str): The name of the player.
        team (str): The name of the player's team.

    Returns:
        float: The plus-minus score for the player.
    """
    home_team: str = dataset.metadata.teams[0].name

    player_start_time, player_end_time = get_player_start_and_end_times(dataset, player_name)

    plus_minus_score = 0.0

    if player_start_time is None or player_end_time is None:
        return plus_minus_score

    for segment_info in match_segments.values():
        segment_start_time = convert_time_str_to_minutes(dataset, segment_info["start_time"])
        segment_end_time = convert_time_str_to_minutes(dataset, segment_info["end_time"])

        if segment_start_time < player_end_time and segment_end_time > player_start_time:
            if team == home_team:
                plus_minus_score += segment_info["home_goals"] - segment_info["away_goals"]
            else:
                plus_minus_score += segment_info["away_goals"] - segment_info["home_goals"]

    return plus_minus_score


def calculate_match_plus_minus_scores(
    dataset: EventDataset,
    match_segments: dict[str, dict],
    players_info_df: pd.DataFrame,
) -> pd.DataFrame:
    plus_minus_df = players_info_df.copy()

    for player in players_info_df["player_name"]:
        team: str = players_info_df.loc[players_info_df["player_name"] == player, "team_name"].values[0]  # type: ignore
        plus_minus_df.loc[plus_minus_df["player_name"] == player, "plus_minus_score"] = calculate_plus_minus_score(
            dataset,
            match_segments,
            player,
            team,
        )

    plus_minus_df = plus_minus_df.sort_values(by="plus_minus_score", ascending=False).reset_index(drop=True)
    plus_minus_df.insert(0, "rank", range(1, len(plus_minus_df) + 1))

    for index, row in plus_minus_df.iterrows():
        player_name = row["player_name"]
        player_start_time, player_end_time = get_player_start_and_end_times(dataset, player_name)
        plus_minus_df.at[index, "start_time"] = int(player_start_time)
        plus_minus_df.at[index, "end_time"] = int(player_end_time)

        player_nickname = row["nickname"]
        if pd.notnull(player_nickname):
            plus_minus_df.at[index, "player_name"] = player_nickname

    plus_minus_df.drop(columns=["nickname"], inplace=True)
    plus_minus_df.rename(columns={"player_name": "player", "team_name": "team"}, inplace=True)

    return plus_minus_df


def get_match_plus_minus_scores(match_id: int) -> pd.DataFrame:
    """
    Obtain Plus-Minus scores for all players in a given match.

    Args:
        match_id: StatsBomb match ID.

    Returns:
        DataFrame containing Plus-Minus scores for each player in the match.
    """
    players_info_df = players.get_players_info(match_id)
    dataset, match_events_df = players.load_match_data(match_id)

    match_segments = divide_match_in_segments(dataset, match_events_df)

    plus_minus_df = calculate_match_plus_minus_scores(dataset, match_segments, players_info_df)

    return plus_minus_df


def get_tournament_plus_minus_scores(tournament: dict) -> pd.DataFrame:
    """
    Obtain Plus-Minus scores for all players in a given tournament.

    Args:
        tournament: A dictionary containing competition and season IDs.

    Returns:
        DataFrame containing Plus-Minus scores for each player in the tournament.
    """
    # Get all match IDs for the tournament
    match_ids = tournaments.get_all_match_ids(tournament)

    # Initialize empty DataFrame to store tournament Plus-Minus scores
    all_matches_plus_minus_df = pd.DataFrame(
        columns=[
            "rank",
            "player",
            "team",
            "plus_minus_score",
            "minutes_played",
        ]
    )

    # Calculate Plus-Minus scores for each match and concatenate results
    for match_id in tqdm(
        match_ids,
        desc=f"Calculating Plus-Minus scores for matches in {tournament['label']}",
        ncols=150,
    ):
        match_plus_minus_df = get_match_plus_minus_scores(match_id)

        # Save match Plus-Minus scores to CSV
        match_filename = paths.PLUS_MINUS_OUTPUT_DIR / tournament["label"] / f"match_{match_id}_plus_minus_scores.csv"
        match_plus_minus_df.to_csv(match_filename, index=False)

        # Combine match Plus-Minus scores into all matches DataFrame
        if all_matches_plus_minus_df.empty:
            all_matches_plus_minus_df = match_plus_minus_df
        else:
            all_matches_plus_minus_df = pd.concat([all_matches_plus_minus_df, match_plus_minus_df], ignore_index=True)

    # Aggregate Plus-Minus scores for players across all matches in the tournament
    tournament_plus_minus_df = (
        all_matches_plus_minus_df.groupby(
            ["player", "team"],
            as_index=False,
        )
        .agg(
            {
                "plus_minus_score": "sum",
                "minutes_played": "sum",
            }
        )
        .sort_values("plus_minus_score", ascending=False)
        .reset_index(drop=True)
    )

    # Add rank column
    tournament_plus_minus_df.insert(0, "rank", range(1, len(tournament_plus_minus_df) + 1))

    # Add matches played column
    player_team_counts = all_matches_plus_minus_df.value_counts(["player", "team"]).reset_index(name="matches_played")
    tournament_plus_minus_df = pd.merge(tournament_plus_minus_df, player_team_counts, how="left", on=["player", "team"])

    # Save tournament Plus-Minus scores to CSV
    tournament_filename = paths.PLUS_MINUS_OUTPUT_DIR / f"{tournament['label']}_plus_minus_scores.csv"
    tournament_plus_minus_df.to_csv(tournament_filename, index=False)

    return tournament_plus_minus_df


def main():
    # Calculate Plus-Minus for National Team Tournaments
    for tournament in tqdm(
        tournaments.NATIONAL_TEAM_TOURNAMENTS,
        desc="Processing National Team Tournaments",
        ncols=150,
    ):
        get_tournament_plus_minus_scores(tournament)

    # Calculate Plus-Minus for European Club Leagues
    for tournament in tqdm(
        tournaments.EUROPEAN_CLUB_LEAGUES,
        desc="Processing European Club Leagues",
        ncols=150,
    ):
        get_tournament_plus_minus_scores(tournament)


if __name__ == "__main__":
    main()
