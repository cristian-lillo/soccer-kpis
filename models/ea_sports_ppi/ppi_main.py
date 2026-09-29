"""
Module to calculate the EA Sports Player Performance Index (PPI) for any match and player.
"""

import warnings

import pandas as pd
from kloppy.domain import (
    CardType,
    DuelResult,
    EventDataset,
    EventType,
    InterceptionResult,
    PassResult,
    PassType,
    ShotResult,
    TakeOnResult,
)
from tqdm import tqdm

from config import paths, players, tournaments

# Ignore specific warnings for cleaner output
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

# Coefficients and points used in PPI calculation
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

POINTS = {"WIN": 3, "DRAW": 1, "LOSS": 0, "PER_GAME": 1.34, "PER_GOAL": 1.039, "PER_ASSIST": 1.039}

CLEAN_SHEET_POINTS = {"Goalkeeper": 0.585, "Defender": 0.364, "Midfielder": 0.150, "Attacker": 0.071}

INDEX_WEIGHTS = {"I1": 0.25, "I2": 0.375, "I3": 0.125, "I4": 0.125, "I5": 0.0625, "I6": 0.0625}


def calculate_tackle_win_ratio(team_dataset: EventDataset) -> float:
    """
    Calculate the tackle win ratio for a team.

    Args:
        team_dataset: The event dataset containing team data.

    Returns:
        The tackle win ratio as a float rounded to two decimal places.
    """
    total_duels = players.calculate_metric_for_player_dataset(
        team_dataset,
        EventType.DUEL,
    )
    successful_duels = players.calculate_metric_for_player_dataset(
        team_dataset,
        EventType.DUEL,
        DuelResult.WON,
    )

    if total_duels == 0:
        return 0.0
    else:
        return round(successful_duels / total_duels, 2)


def extract_player_metrics(
    dataset: EventDataset,
    players_info_df: pd.DataFrame,
) -> dict[str, dict[str, str | int]]:
    """
    Extract player metrics: minutes played, goals, assists, crosses, dribbles and passes.

    Args:
        dataset: The event dataset containing player data.
        players_info_df: DataFrame containing player information.

    Returns:
        A dictionary mapping player nicknames to their metrics.
    """
    player_metrics = {}

    # Get player position mapping
    players_position_dict = players.get_players_position_group(dataset)

    # Get unique teams to identify opponent team
    teams = players_info_df["team_name"].unique()

    for idx, player_name in enumerate(players_info_df["player_name"]):
        # Get specific player event data
        player_dataset = dataset.filter(
            lambda event, player_name=player_name: (
                False if not hasattr(event.player, "name") else event.player.name == player_name
            )
        )

        # Get nickname, team and minutes from players_info_df
        player_nickname = players_info_df.at[idx, "nickname"] or player_name
        player_team = players_info_df.at[idx, "team_name"]
        player_minutes = players_info_df.at[idx, "minutes_played"]
        opponent_team = teams[teams != player_team].item()

        # Get player metrics
        goals = players.calculate_metric_for_player_dataset(
            player_dataset,
            EventType.SHOT,
            ShotResult.GOAL,
        )
        assists = players.calculate_metric_for_player_dataset(
            player_dataset,
            EventType.PASS,
            PassResult.COMPLETE,
            PassType.ASSIST,
        )
        crosses = players.calculate_metric_for_player_dataset(
            player_dataset,
            EventType.PASS,
            PassResult.COMPLETE,
            PassType.CROSS,
        )
        dribbles = players.calculate_metric_for_player_dataset(
            player_dataset,
            EventType.TAKE_ON,
            TakeOnResult.COMPLETE,
        )
        passes = players.calculate_metric_for_player_dataset(
            player_dataset,
            EventType.PASS,
            PassResult.COMPLETE,
        )

        player_metrics[player_nickname] = {
            "team": player_team,
            "opponent_team": opponent_team,
            "position": players_position_dict[player_name],
            "minutes_played": player_minutes,
            "goals": goals,
            "assists": assists,
            "crosses": crosses,
            "dribbles": dribbles,
            "passes": passes,
        }

    return player_metrics


def extract_team_metrics(
    dataset: EventDataset,
    team_minutes_dict: dict[str, int],
) -> dict[str, dict[str, str | int | float]]:
    """
    Extract team metrics: total minutes, goals, yellow cards, red cards, interceptions, clearances, tackle win ratio.

    Args:
        dataset: EventDataset containing the match data.
        team_minutes_dict: Dictionary mapping team names to total minutes played.

    Returns:
        A dictionary mapping team names to their metrics.
    """
    team_metrics = {}

    for team in dataset.metadata.teams:
        # Get specific team event data
        team_name = team.name
        team_dataset = dataset.filter(
            lambda event, team_name=team_name: (
                False if not hasattr(event.player, "name") else event.player.team.name == team_name
            )
        )

        # Get team metrics
        goals = players.calculate_metric_for_player_dataset(
            team_dataset,
            EventType.SHOT,
            ShotResult.GOAL,
        )
        yellow_cards = players.calculate_metric_for_player_dataset(
            team_dataset,
            EventType.CARD,
            card_filter=CardType.FIRST_YELLOW,
        )
        red_cards = players.calculate_metric_for_player_dataset(
            team_dataset,
            EventType.CARD,
            card_filter=[CardType.SECOND_YELLOW, CardType.RED],
        )
        interceptions = players.calculate_metric_for_player_dataset(
            team_dataset,
            EventType.INTERCEPTION,
            InterceptionResult.SUCCESS,
        )
        clearances = players.calculate_metric_for_player_dataset(
            team_dataset,
            EventType.CLEARANCE,
        )

        team_metrics[team_name] = {
            "total_minutes": team_minutes_dict[team_name],
            "goals": goals,
            "yellow_cards": yellow_cards,
            "red_cards": red_cards,
            "interceptions": interceptions,
            "clearances": clearances,
            "tackle_win_ratio": calculate_tackle_win_ratio(team_dataset),
        }

    return team_metrics


def calculate_players_performance_index(player_metrics: dict[str, dict], team_metrics: dict[str, dict]) -> pd.DataFrame:
    """
    Calculate the Player Performance Index (PPI) for each player based on their metrics and team metrics.

    Args:
        player_metrics: A dictionary mapping player nicknames to their metrics.
        team_metrics: A dictionary mapping team names to their metrics.

    Returns:
        DataFrame containing PPI scores for each player.
    """
    ppi_list = []

    for player, metrics in player_metrics.items():
        # Extract metrics
        player_team, opponent_team = metrics["team"], metrics["opponent_team"]
        opp_metrics = team_metrics[opponent_team]
        team_goals, opponent_goals = team_metrics[player_team]["goals"], team_metrics[opponent_team]["goals"]

        # Calculate minutes ratio once
        minutes_ratio = round(metrics["minutes_played"] / team_metrics[player_team]["total_minutes"], 2)

        # Subindex 1: Modelling Match Outcome
        index_1 = (
            MODEL_COEFFICIENTS["constant"]
            + metrics["crosses"] * MODEL_COEFFICIENTS["crosses"]
            + metrics["dribbles"] * MODEL_COEFFICIENTS["dribbles"]
            + metrics["passes"] * MODEL_COEFFICIENTS["passes"]
            + opp_metrics["interceptions"] * MODEL_COEFFICIENTS["opp_interceptions"]
            + opp_metrics["yellow_cards"] * MODEL_COEFFICIENTS["opp_yellows"]
            + opp_metrics["red_cards"] * MODEL_COEFFICIENTS["opp_reds"]
            + opp_metrics["tackle_win_ratio"] * MODEL_COEFFICIENTS["opp_tackle_win_ratio"]
            + opp_metrics["clearances"] * MODEL_COEFFICIENTS["opp_clearances"]
        )

        # Subindex 2: Points-Sharing Index
        if team_goals > opponent_goals:
            index_2 = minutes_ratio * POINTS["WIN"]
        elif team_goals == opponent_goals:
            index_2 = minutes_ratio * POINTS["DRAW"]
        else:
            index_2 = minutes_ratio * POINTS["LOSS"]

        # Subindex 3: Appearance Index
        index_3 = minutes_ratio * POINTS["PER_GAME"]

        # Subindex 4: Goal-Scoring Index
        index_4 = metrics["goals"] * POINTS["PER_GOAL"]

        # Subindex 5: Assists Index
        index_5 = metrics["assists"] * POINTS["PER_ASSIST"]

        # Subindex 6: Clean-Sheets Index
        index_6 = CLEAN_SHEET_POINTS.get(metrics["position"], 0) if opponent_goals == 0 else 0

        # Final PPI calculation
        player_index = round(
            100
            * (
                INDEX_WEIGHTS["I1"] * index_1
                + INDEX_WEIGHTS["I2"] * index_2
                + INDEX_WEIGHTS["I3"] * index_3
                + INDEX_WEIGHTS["I4"] * index_4
                + INDEX_WEIGHTS["I5"] * index_5
                + INDEX_WEIGHTS["I6"] * index_6
            )
        )

        ppi_list.append(
            {
                "player": player,
                "team": metrics["team"],
                "position": metrics["position"],
                "index_score": player_index,
                "minutes_played": metrics["minutes_played"],
                "goals": metrics["goals"],
                "assists": metrics["assists"],
                "crosses": metrics["crosses"],
                "dribbles": metrics["dribbles"],
                "passes": metrics["passes"],
                "opposition_interceptions": opp_metrics["interceptions"],
                "opposition_yellow_cards": opp_metrics["yellow_cards"],
                "opposition_red_cards": opp_metrics["red_cards"],
                "opposition_tackle_win_ratio": opp_metrics["tackle_win_ratio"],
                "opposition_clearances": opp_metrics["clearances"],
            }
        )

    # Create DataFrame and rank players by index score
    ppi_df = pd.DataFrame(ppi_list)
    ranked_ppi_df = ppi_df.sort_values("index_score", ascending=False).reset_index(drop=True)
    ranked_ppi_df.insert(0, "rank", range(1, len(ranked_ppi_df) + 1))

    return ranked_ppi_df


def get_match_ppi_scores(match_id: int) -> pd.DataFrame:
    """
    Obtain PPI scores for all players in a given match.

    Args:
        match_id: StatsBomb match ID.

    Returns:
        DataFrame containing PPI scores for each player in the match.
    """
    # Load players info and team minutes
    players_info_df = players.get_players_info(match_id)
    team_minutes_dict = players_info_df.groupby("team_name")["minutes_played"].sum().to_dict()  # type: ignore

    # Load match data
    dataset, _ = players.load_match_data(match_id)

    # Extract metrics
    player_metrics = extract_player_metrics(dataset, players_info_df)
    team_metrics = extract_team_metrics(dataset, team_minutes_dict)  # type: ignore

    # Calculate PPI for players
    ppi_df = calculate_players_performance_index(player_metrics, team_metrics)

    return ppi_df


def get_tournament_ppi_scores(tournament: dict) -> pd.DataFrame:
    """
    Obtain PPI scores for all players in a given tournament.

    Args:
        tournament: A dictionary containing competition and season IDs.

    Returns:
        DataFrame containing PPI scores for each player in the tournament.
    """
    # Get all match IDs for the tournament
    match_ids = tournaments.get_all_match_ids(tournament)

    # Initialize empty DataFrame to store tournament PPI scores
    all_matches_ppi_df = pd.DataFrame(
        columns=[
            "rank",
            "player",
            "team",
            "position",
            "index_score",
            "minutes_played",
            "goals",
            "assists",
            "crosses",
            "dribbles",
            "passes",
            "opposition_interceptions",
            "opposition_yellow_cards",
            "opposition_red_cards",
            "opposition_tackle_win_ratio",
            "opposition_clearances",
        ]
    )

    # Calculate PPI for each match and concatenate results
    for match_id in tqdm(match_ids, desc=f"Calculating PPI for matches in {tournament['label']}", ncols=150):
        match_ppi_df = get_match_ppi_scores(match_id)

        # Save match PPI scores to CSV
        match_filename = paths.EA_SPORTS_PPI_OUTPUT_DIR / tournament["label"] / f"match_{match_id}_ppi_scores.csv"
        match_ppi_df.to_csv(match_filename, index=False)

        # Combine match PPI scores into all matches DataFrame
        if all_matches_ppi_df.empty:
            all_matches_ppi_df = match_ppi_df
        else:
            all_matches_ppi_df = pd.concat([all_matches_ppi_df, match_ppi_df], ignore_index=True)

    # Aggregate PPI scores for players across all matches in the tournament
    tournament_ppi_df = (
        all_matches_ppi_df.groupby(
            ["player", "team"],
            as_index=False,
        )
        .agg(
            {
                "position": lambda x: x.mode().loc[0],
                "index_score": "sum",
                "minutes_played": "sum",
                "goals": "sum",
                "assists": "sum",
                "crosses": "sum",
                "dribbles": "sum",
                "passes": "sum",
            }
        )
        .sort_values("index_score", ascending=False)
        .reset_index(drop=True)
    )

    # Add rank column
    tournament_ppi_df.insert(0, "rank", range(1, len(tournament_ppi_df) + 1))

    # Add matches played column
    player_team_counts = all_matches_ppi_df.value_counts(["player", "team"]).reset_index(name="matches_played")
    tournament_ppi_df = pd.merge(tournament_ppi_df, player_team_counts, how="left", on=["player", "team"])

    # Save tournament PPI scores to CSV
    tournament_filename = paths.EA_SPORTS_PPI_OUTPUT_DIR / f"{tournament['label']}_ppi_scores.csv"
    tournament_ppi_df.to_csv(tournament_filename, index=False)

    return tournament_ppi_df


def main():
    # Calculate PPI for National Team Tournaments
    for tournament in tqdm(
        tournaments.NATIONAL_TEAM_TOURNAMENTS,
        desc="Processing National Team Tournaments",
        ncols=150,
    ):
        get_tournament_ppi_scores(tournament)

    # Calculate PPI for European Club Leagues
    for tournament in tqdm(
        tournaments.EUROPEAN_CLUB_LEAGUES,
        desc="Processing European Club Leagues",
        ncols=150,
    ):
        get_tournament_ppi_scores(tournament)


if __name__ == "__main__":
    main()
