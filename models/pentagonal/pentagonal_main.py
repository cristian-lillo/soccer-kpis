"""
Opta Points Calculator

This script calculates Opta Points for soccer players based on their match performance metrics.
"""

import warnings

import pandas as pd
from kloppy.domain import EventDataset
from tqdm import tqdm

from config import paths, players, tournaments

# Filter warnings
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

# Define coefficients
VARIABLES_COEFFICIENTS: dict[str, list[float]] = {
    "goals": [0.299, 0.004, 0.098, -0.115, -0.028],
    "assists": [0.044, 0.041, -0.026, 0.208, -0.019],
    "shots": [0.277, 0.008, 0.060, -0.065, -0.016],
    "shots_on_target": [0.295, 0.019, 0.067, -0.087, -0.034],
    "dribbles": [0.107, -0.056, 0.029, 0.124, 0.010],
    "key_passes": [0.011, 0.058, -0.073, 0.299, -0.016],
    "crosses": [-0.161, -0.109, 0.017, 0.438, -0.049],
    "passes": [0.039, 0.119, 0.174, 0.096, -0.024],
    "passing_accuracy": [-0.021, 0.397, -0.149, -0.055, -0.011],
    "short_passes": [0.043, 0.141, 0.141, 0.095, -0.009],
    "short_passing_accuracy": [-0.043, 0.320, -0.059, -0.044, -0.045],
    "long_passes": [0.000, -0.068, 0.345, 0.076, -0.116],
    "long_passing_accuracy": [0.100, 0.331, -0.204, -0.060, 0.050],
    "balls_recovered": [-0.103, -0.010, -0.19, 0.106, 0.308],
    "tackles": [-0.032, -0.040, 0.154, -0.005, 0.164],
    "clearances": [0.112, -0.106, 0.417, -0.207, -0.132],
    "fouls_committed": [0.116, -0.081, -0.043, -0.125, 0.471],
    "yellow_cards": [-0.042, 0.039, -0.194, -0.032, 0.505],
    "red_cards": [0.090, -0.164, 0.336, -0.071, -0.098],
}

FACTOR_COEFFICIENTS: dict[str, float] = {
    "F1": 0.2688,
    "F2": 0.2042,
    "F3": 0.2040,
    "F4": 0.1854,
    "F5": 0.1374,
}

FACTOR_VARIABLES_DF = pd.DataFrame.from_dict(
    VARIABLES_COEFFICIENTS,
    orient="index",
    columns=list(FACTOR_COEFFICIENTS.keys()),
)


def extract_player_metrics(
    dataset: EventDataset,
    match_events_df: pd.DataFrame,
    player_info_df: pd.DataFrame,
) -> dict[str, dict[str, str | int]]:
    """
    Extract player metrics needed for Pentagonal Evaluation Model calculation.

    Args:
        dataset: The dataset containing match events and player information.
        match_events_df: DataFrame containing match events.
        player_info_df: DataFrame containing player information.

    Returns:
        A dictionary mapping player nicknames to their metrics.
    """
    player_metrics = {}

    # Map player names to their teams and minutes played for quick access
    nickname_mapping = dict(zip(player_info_df["player_name"], player_info_df["nickname"]))
    team_mapping = dict(zip(player_info_df["player_name"], player_info_df["team_name"]))
    minutes_mapping = dict(zip(player_info_df["player_name"], player_info_df["minutes_played"]))

    # Get player position mapping and assists count
    position_mapping = players.get_players_position_group(dataset)
    assists_mapping = players.count_assists(match_events_df)

    for player_name in match_events_df["player"].unique():
        # Get specific player event data
        player_df = match_events_df.loc[match_events_df["player"] == player_name]

        # Use nickname, team and minutes mappings
        player_nickname = nickname_mapping[player_name] or player_name
        player_team = team_mapping[player_name]
        player_minutes = minutes_mapping[player_name]

        # Attacking metrics
        goals = len(player_df.loc[(player_df["event_type"] == "SHOT") & (player_df["result"] == "GOAL")])
        assists = assists_mapping.get(player_name, 0)
        shots = len(player_df.loc[player_df["event_type"] == "SHOT"])
        shots_on_target = len(
            player_df.loc[
                (player_df["event_type"] == "SHOT") & (player_df["result"].isin(["GOAL", "BLOCKED", "SAVED"]))
            ]
        )
        dribbles = len(
            player_df.loc[
                (player_df["event_type"] == "DUEL") & (player_df["duel_type"] == "TAKE_ON") & (player_df["success"])
            ]
        )
        key_passes = len(
            player_df.loc[
                (player_df["event_type"] == "PASS") & (player_df["pass_type"] == "SMART_PASS") & (player_df["success"])
            ]
        )
        crosses = len(
            player_df.loc[
                (player_df["event_type"] == "PASS") & (player_df["pass_type"] == "CROSS") & (player_df["success"])
            ]
        )

        # Distribution metrics
        passes = len(player_df.loc[(player_df["event_type"] == "PASS") & (player_df["success"])])
        passing_accuracy = (
            (passes / len(player_df.loc[player_df["event_type"] == "PASS"]))
            if len(player_df.loc[player_df["event_type"] == "PASS"]) > 0
            else 0.0
        )
        short_passes = len(
            player_df.loc[
                (player_df["event_type"] == "PASS") & (player_df["pass_type"] == "SIMPLE_PASS") & (player_df["success"])
            ]
        )
        short_passing_accuracy = (
            (
                short_passes
                / len(player_df.loc[(player_df["event_type"] == "PASS") & (player_df["pass_type"] == "SIMPLE_PASS")])
            )
            if len(player_df.loc[(player_df["event_type"] == "PASS") & (player_df["pass_type"] == "SIMPLE_PASS")]) > 0
            else 0.0
        )
        long_passes = len(
            player_df.loc[
                (player_df["event_type"] == "PASS") & (player_df["pass_type"] == "LONG_BALL") & (player_df["success"])
            ]
        )
        long_passing_accuracy = (
            (
                long_passes
                / len(player_df.loc[(player_df["event_type"] == "PASS") & (player_df["pass_type"] == "LONG_BALL")])
            )
            if len(player_df.loc[(player_df["event_type"] == "PASS") & (player_df["pass_type"] == "LONG_BALL")]) > 0
            else 0.0
        )

        # Defensive metrics
        balls_recovered = len(player_df.loc[(player_df["event_type"] == "RECOVERY")])
        tackles = len(
            player_df.loc[
                (player_df["event_type"] == "DUEL")
                & (player_df["duel_type"] == "SLIDING_TACKLE")
                & (player_df["success"])
            ]
        )
        clearances = len(player_df.loc[(player_df["event_type"] == "CLEARANCE")])
        fouls_committed = len(player_df.loc[(player_df["event_type"] == "FOUL_COMMITED")])
        yellow_cards = len(
            player_df.loc[(player_df["event_type"] == "CARD") & (player_df["card_type"] == "FIRST_YELLOW")]
        )
        red_cards = len(
            player_df.loc[(player_df["event_type"] == "CARD") & (player_df["card_type"].isin(["SECOND_YELLOW", "RED"]))]
        )

        player_metrics[player_nickname] = {
            "team": player_team,
            "position": position_mapping[player_name],
            "minutes_played": player_minutes,
            "goals": goals,
            "assists": assists,
            "shots": shots,
            "shots_on_target": shots_on_target,
            "dribbles": dribbles,
            "key_passes": key_passes,
            "crosses": crosses,
            "passes": passes,
            "passing_accuracy": passing_accuracy,
            "short_passes": short_passes,
            "short_passing_accuracy": short_passing_accuracy,
            "long_passes": long_passes,
            "long_passing_accuracy": long_passing_accuracy,
            "balls_recovered": balls_recovered,
            "tackles": tackles,
            "clearances": clearances,
            "fouls_committed": fouls_committed,
            "yellow_cards": yellow_cards,
            "red_cards": red_cards,
        }

    return player_metrics


def calculate_players_pentagonal_score(player_metrics: dict, FACTOR_VARIABLES_DF: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Pentagonal Score for each player.

    Args:
        player_metrics: A dictionary containing player metrics.
        FACTOR_VARIABLES_DF: A DataFrame containing the factor variables for the Pentagonal Score calculation.

    Returns:
        A DataFrame containing Pentagonal Scores for each player.
    """

    # Initialize list to hold players Pentagonal Scores
    pentagonal_scores_list = []

    for player, metrics in player_metrics.items():
        player_points = 0

        for factor in FACTOR_VARIABLES_DF.columns:
            factor_score = sum(
                metrics[metric] * FACTOR_VARIABLES_DF.loc[metric, factor] for metric in FACTOR_VARIABLES_DF.index
            )
            player_points += factor_score * FACTOR_COEFFICIENTS[factor]

        # Append player Pentagonal Scores to list
        pentagonal_scores_list.append(
            {
                "player": player,
                "team": metrics["team"],
                "position": metrics["position"],
                "pentagonal_score": player_points,
                "minutes_played": metrics["minutes_played"],
                "goals": metrics["goals"],
                "assists": metrics["assists"],
                "shots": metrics["shots"],
                "shots_on_target": metrics["shots_on_target"],
                "dribbles": metrics["dribbles"],
                "key_passes": metrics["key_passes"],
                "crosses": metrics["crosses"],
                "passes": metrics["passes"],
                "passing_accuracy": metrics["passing_accuracy"],
                "short_passes": metrics["short_passes"],
                "short_passing_accuracy": metrics["short_passing_accuracy"],
                "long_passes": metrics["long_passes"],
                "long_passing_accuracy": metrics["long_passing_accuracy"],
                "balls_recovered": metrics["balls_recovered"],
                "tackles": metrics["tackles"],
                "clearances": metrics["clearances"],
                "fouls_committed": metrics["fouls_committed"],
                "yellow_cards": metrics["yellow_cards"],
                "red_cards": metrics["red_cards"],
            }
        )

    # Convert list to DataFrame
    pentagonal_scores_df = pd.DataFrame(pentagonal_scores_list)
    return pentagonal_scores_df


def get_match_pentagonal_scores(match_id: int) -> pd.DataFrame:
    """
    Obtain Pentagonal Scores for all players in a given match.

    Args:
        match_id: StatsBomb match ID.

    Returns:
        DataFrame containing Pentagonal Scores for each player in the match.
    """
    # Load players info and match data
    players_info_df = players.get_players_info(match_id)
    dataset, player_events_df = players.load_match_data(match_id)

    # Extract player metrics
    player_metrics = extract_player_metrics(dataset, player_events_df, players_info_df)

    # Calculate Pentagonal Scores for players
    pentagonal_scores_df = calculate_players_pentagonal_score(player_metrics, FACTOR_VARIABLES_DF)

    return pentagonal_scores_df


def get_tournament_pentagonal_scores(tournament: dict) -> pd.DataFrame:
    """
    Obtain Pentagonal Scores for all players in a given tournament.

    Args:
        tournament: A dictionary containing competition and season IDs.

    Returns:
        DataFrame containing Pentagonal Scores for each player in the tournament.
    """
    # Get all match IDs for the tournament
    match_ids = tournaments.get_all_match_ids(tournament)

    # Initialize empty DataFrame to store tournament Pentagonal Scores
    all_matches_pentagonal_scores_df = pd.DataFrame(
        columns=[
            "rank",
            "player",
            "team",
            "position",
            "pentagonal_score",
            "minutes_played",
            "goals",
            "assists",
            "shots",
            "shots_on_target",
            "dribbles",
            "key_passes",
            "crosses",
            "passes",
            "passing_accuracy",
            "short_passes",
            "short_passing_accuracy",
            "long_passes",
            "long_passing_accuracy",
            "balls_recovered",
            "tackles",
            "clearances",
            "fouls_committed",
            "yellow_cards",
            "red_cards",
        ]
    )

    # Calculate Pentagonal Scores for each match and concatenate results
    for match_id in tqdm(
        match_ids, desc=f"Calculating Pentagonal Scores for matches in {tournament['label']}", ncols=150
    ):
        match_pentagonal_scores_df = get_match_pentagonal_scores(match_id)

        # Save match Pentagonal Scores to CSV
        match_filename = (
            paths.PENTAGONAL_SCORE_OUTPUT_DIR / tournament["label"] / f"match_{match_id}_pentagonal_scores.csv"
        )
        match_pentagonal_scores_df.to_csv(match_filename, index=False)

        # Combine match Pentagonal Scores into all matches DataFrame
        if all_matches_pentagonal_scores_df.empty:
            all_matches_pentagonal_scores_df = match_pentagonal_scores_df
        else:
            all_matches_pentagonal_scores_df = pd.concat(
                [all_matches_pentagonal_scores_df, match_pentagonal_scores_df],
                ignore_index=True,
            )

    # Aggregate Pentagonal Scores for players across all matches in the tournament
    tournament_pentagonal_scores_df = (
        all_matches_pentagonal_scores_df.groupby(
            ["player", "team"],
            as_index=False,
        )
        .agg(
            {
                "position": lambda x: x.mode().loc[0],
                "pentagonal_score": "sum",
                "minutes_played": "sum",
                "goals": "sum",
                "assists": "sum",
                "shots": "sum",
                "shots_on_target": "sum",
                "dribbles": "sum",
                "key_passes": "sum",
                "crosses": "sum",
                "passes": "sum",
                "passing_accuracy": "mean",
                "short_passes": "sum",
                "short_passing_accuracy": "mean",
                "long_passes": "sum",
                "long_passing_accuracy": "mean",
                "balls_recovered": "sum",
                "tackles": "sum",
                "clearances": "sum",
                "fouls_committed": "sum",
                "yellow_cards": "sum",
                "red_cards": "sum",
            }
        )
        .sort_values("pentagonal_score", ascending=False)
        .reset_index(drop=True)
    )

    # Add rank column
    tournament_pentagonal_scores_df.insert(0, "rank", range(1, len(tournament_pentagonal_scores_df) + 1))

    # Add matches played column
    player_team_counts = all_matches_pentagonal_scores_df.value_counts(["player", "team"]).reset_index(
        name="matches_played"
    )
    tournament_pentagonal_scores_df = pd.merge(
        tournament_pentagonal_scores_df, player_team_counts, how="left", on=["player", "team"]
    )

    # Save tournament Pentagonal Scores to CSV
    tournament_filename = paths.PENTAGONAL_SCORE_OUTPUT_DIR / f"{tournament['label']}_pentagonal_scores.csv"
    tournament_pentagonal_scores_df.to_csv(tournament_filename, index=False)

    return tournament_pentagonal_scores_df


def main():
    # Calculate Pentagonal Scores for National Team Tournaments
    for tournament in tqdm(
        tournaments.NATIONAL_TEAM_TOURNAMENTS,
        desc="Processing National Team Tournaments",
        ncols=150,
    ):
        get_tournament_pentagonal_scores(tournament)

    # Calculate Pentagonal Scores for European Club Leagues
    for tournament in tqdm(
        tournaments.EUROPEAN_CLUB_LEAGUES,
        desc="Processing European Club Leagues",
        ncols=150,
    ):
        get_tournament_pentagonal_scores(tournament)


if __name__ == "__main__":
    main()
