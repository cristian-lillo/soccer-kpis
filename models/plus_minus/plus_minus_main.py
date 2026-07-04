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


def convert_time_str_to_minutes(dataset: EventDataset, time_str: str) -> int:
    """Convert a time string (e.g., 'P2T34:21') to total minutes, considering the period."""
    period_durations = get_period_duration(dataset)
    previous_period_minutes = period_durations.get(str(int(time_str[1]) - 1), 0)
    minutes, seconds = map(int, time_str[3:].split(":"))
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
        }

    return segments


def get_player_start_and_end_times(dataset: EventDataset, player_name: str) -> tuple:
    """
    Retrieve the start and end times for a player in the match.

    Args:
        dataset (EventDataset): The event dataset for the match.
        player_name (str): The full name of the player.

    Returns:
        A tuple containing the start and end times in minutes.
    """
    periods_duration = get_period_duration(dataset)
    player_start_time = None
    player_end_time = None

    for team in dataset.metadata.teams:
        for player in team.players:
            if player.full_name == player_name:
                for start_time, end_time, _ in player.positions.ranges():
                    if player_start_time is None:
                        player_start_time = start_time
                    if player_end_time is None or end_time > player_end_time:
                        player_end_time = end_time

    if player_start_time is not None:
        start_minutes_in_period = convert_timedelta_to_minutes(player_start_time.timestamp)
        previous_period_minutes = periods_duration.get(str(int(player_start_time.period.id) - 1), 0)
        player_start_time = start_minutes_in_period + previous_period_minutes

    if player_end_time is not None:
        end_minutes_in_period = convert_timedelta_to_minutes(player_end_time.timestamp)
        previous_period_minutes = periods_duration.get(str(int(player_end_time.period.id) - 1), 0)
        player_end_time = end_minutes_in_period + previous_period_minutes

    return player_start_time, player_end_time


def calculate_segments_weight(dataset: EventDataset, match_segments: dict[str, dict]) -> dict[str, dict]:
    """
    Calculate the weight for each match segment based on duration and goal difference.

    Args:
        dataset (EventDataset): The event dataset for the match.
        match_segments (dict): A dictionary containing match segments.

    Returns:
        A dictionary with updated segment weights and goal counts.
    """
    home_team = dataset.metadata.teams[0].name
    goal_difference_start = 0

    for segment_key, segment_info in match_segments.items():
        segment_duration = segment_info["duration"]
        goals = segment_info["goals"]

        goal_difference_end = goal_difference_start
        home_goals = 0
        away_goals = 0

        for goal in goals:
            if goal["team"] == home_team:
                goal_difference_end += 1
                home_goals += 1
            else:
                goal_difference_end -= 1
                away_goals += 1

        weight_time = 1.0
        weight_duration = (segment_duration + RHO_2) / RHO_3
        weight_goals = RHO_4 if abs(goal_difference_start) >= 2 and abs(goal_difference_end) >= 2 else 1

        match_segments[segment_key]["weight"] = weight_time * weight_duration * weight_goals
        match_segments[segment_key]["home_goals"] = home_goals
        match_segments[segment_key]["away_goals"] = away_goals

        goal_difference_start = goal_difference_end

    return match_segments


def calculate_plus_minus_score(
    dataset: EventDataset,
    match_segments: dict[str, dict],
    player_name: str,
) -> float:
    """
    Calculate the plus-minus score for a player based on match segments.

    Args:
        dataset (EventDataset): The event dataset for the match.
        match_segments (dict): A dictionary containing match segments.
        player_name (str): The name of the player.

    Returns:
        float: The plus-minus score for the player.
    """
    player_start_time, player_end_time = get_player_start_and_end_times(dataset, player_name)

    if player_start_time is None or player_end_time is None:
        return 0.0

    plus_minus_score = 0.0

    for segment_info in match_segments.values():
        segment_start_time = convert_time_str_to_minutes(dataset, segment_info["start_time"])
        segment_end_time = convert_time_str_to_minutes(dataset, segment_info["end_time"])

        if segment_start_time < player_end_time and segment_end_time > player_start_time:
            plus_minus_score += (
                segment_info["weight"] * (segment_info["home_goals"] + segment_info["away_goals"])
            ) ** 2

    return plus_minus_score


def calculate_match_plus_minus_scores(
    dataset: EventDataset,
    match_segments: dict[str, dict],
    players_info_df: pd.DataFrame,
) -> pd.DataFrame:
    plus_minus_df = players_info_df.copy()

    for player in players_info_df["player_name"]:
        plus_minus_df.loc[plus_minus_df["player_name"] == player, "plus_minus_score"] = calculate_plus_minus_score(
            dataset, match_segments, player
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
    match_segments_data = calculate_segments_weight(dataset, match_segments)

    plus_minus_df = calculate_match_plus_minus_scores(dataset, match_segments_data, players_info_df)

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
