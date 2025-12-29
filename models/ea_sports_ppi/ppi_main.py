"""
Module to calculate the EA Sports Player Performance Index (PPI) for any match and player.
"""

import warnings

import pandas as pd
from kloppy.domain import EventDataset
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


def get_player_position_group(dataset: EventDataset, player_name: str) -> str:
    """
    Determine the main position group of a player based on time spent in each position.

    Args:
        dataset: The event dataset containing player position data.
        player_name: The name of the player.

    Returns:
        The main position group of the player as a string.
    """
    player_position = ("", 0)

    # Iterate through dataset to find player's position history
    for team in dataset.metadata.teams:
        for player in team.players:
            # Only get position for the specified player
            if player.name == player_name:
                for start_time, end_time, position in player.positions.ranges():
                    position_duration = (end_time - start_time).total_seconds()
                    position_group = position.position_group.name

                    # Compare and update the variable if this position has longer duration
                    prev_position, prev_duration = player_position
                    if position_group != prev_position and position_duration > prev_duration:
                        player_position = (position_group, position_duration)

    # Return only the position name
    return player_position[0]


def calculate_tackle_win_ratio(team_events_df: pd.DataFrame) -> float:
    """
    Calculate the tackle win ratio for a team.

    Args:
        team_events_df: DataFrame containing events for the team.

    Returns:
        The tackle win ratio as a float rounded to two decimal places.
    """
    total_duels = len(team_events_df.loc[team_events_df["event_type"] == "DUEL"])
    successful_duels = len(team_events_df.loc[(team_events_df["event_type"] == "DUEL") & (team_events_df["success"])])

    if total_duels == 0:
        return 0.0
    else:
        return round(successful_duels / total_duels, 2)


def extract_player_metrics(
    dataset: EventDataset,
    match_events_df: pd.DataFrame,
    player_info_df: pd.DataFrame,
) -> dict[str, dict[str, str | int]]:
    """
    Extract player metrics: minutes played, goals, assists, crosses, dribbles and passes.

    Args:
        dataset: The event dataset containing player data.
        match_events_df: DataFrame containing all events in the match.
        player_info_df: DataFrame containing player information.

    Returns:
        A dictionary mapping player nicknames to their metrics.
    """
    player_metrics = {}

    # Map player names to their teams and minutes played for quick access
    nickname_mapping = dict(zip(player_info_df["player_name"], player_info_df["nickname"]))
    team_mapping = dict(zip(player_info_df["player_name"], player_info_df["team_name"]))
    minutes_mapping = dict(zip(player_info_df["player_name"], player_info_df["minutes_played"]))

    # Get assists count for all players in the match
    assists_mapping = players.count_assists(match_events_df)

    # Get unique teams to identify opponent team
    teams = player_info_df["team_name"].unique()

    for player_name in match_events_df["player"].unique():
        match_events_df = match_events_df.loc[match_events_df["player"] == player_name]

        # Use nickname, team and minutes mappings
        player_nickname = nickname_mapping[player_name] or player_name
        player_team = team_mapping[player_name]
        opponent_team = teams[teams != player_team].item()
        player_minutes = minutes_mapping[player_name]

        # Get player metrics
        goals = len(
            match_events_df.loc[(match_events_df["event_type"] == "SHOT") & (match_events_df["result"] == "GOAL")]
        )
        crosses = len(match_events_df.loc[(match_events_df["pass_type"] == "CROSS") & (match_events_df["success"])])
        dribbles = len(match_events_df.loc[(match_events_df["event_type"] == "TAKE_ON") & (match_events_df["success"])])
        passes = len(match_events_df.loc[(match_events_df["event_type"] == "PASS") & (match_events_df["success"])])

        player_metrics[player_nickname] = {
            "team": player_team,
            "opponent_team": opponent_team,
            "position": get_player_position_group(dataset, player_name),
            "minutes_played": player_minutes,
            "goals": goals,
            "assists": assists_mapping.get(player_name, 0),
            "crosses": crosses,
            "dribbles": dribbles,
            "passes": passes,
        }

    return player_metrics


def extract_team_metrics(
    match_events_df: pd.DataFrame,
    team_minutes_dict: dict[str, int],
) -> dict[str, dict[str, str | int | float]]:
    """
    Extract team metrics: total minutes, goals, yellow cards, red cards, interceptions, clearances, tackle win ratio.

    Args:
        match_events_df: DataFrame containing all events in the match.
        team_minutes_dict: Dictionary mapping team names to total minutes played.

    Returns:
        A dictionary mapping team names to their metrics.
    """
    team_metrics = {}

    for team in match_events_df["team"].unique():
        team_events_df = match_events_df[match_events_df["team"] == team]

        # Get team metrics
        goals = len(team_events_df.loc[(team_events_df["event_type"] == "SHOT") & (team_events_df["result"] == "GOAL")])
        yellow_cards = len(
            team_events_df.loc[
                (team_events_df["event_type"] == "CARD") & (team_events_df["card_type"] == "FIRST_YELLOW")
            ]
        )
        red_cards = len(
            team_events_df.loc[
                (team_events_df["event_type"] == "CARD") & (team_events_df["card_type"].isin(["RED", "SECOND_YELLOW"]))
            ]
        )
        interceptions = len(
            team_events_df.loc[(team_events_df["event_type"] == "INTERCEPTION") & (team_events_df["success"])]
        )
        clearances = len(team_events_df.loc[team_events_df["event_type"] == "CLEARANCE"])

        team_metrics[team] = {
            "total_minutes": team_minutes_dict[team],
            "goals": goals,
            "yellow_cards": yellow_cards,
            "red_cards": red_cards,
            "interceptions": interceptions,
            "clearances": clearances,
            "tackle_win_ratio": calculate_tackle_win_ratio(team_events_df),
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
    team_minutes_dict = players.get_minutes_played_by_team(match_id)

    # Load match data
    dataset, match_events_df = players.load_match_data(match_id)

    # Extract metrics
    player_metrics = extract_player_metrics(dataset, match_events_df, players_info_df)
    team_metrics = extract_team_metrics(match_events_df, team_minutes_dict)

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
