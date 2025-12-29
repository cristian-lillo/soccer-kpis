"""
Module to calculate the EA Sports Player Performance Index (PPI) for any match and player.
"""

import warnings

import pandas as pd
from kloppy.domain import EventDataset

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












def calculate_tackle_win_ratio(team_df: pd.DataFrame) -> float:
    """Calculate tackle win ratio for a team"""
    total_duels = len(team_df[team_df["event_type"] == "DUEL"])
    successful_duels = len(team_df[team_df["event_type"] == "DUEL"][team_df["success"]])

    if total_duels == 0:
        return 0.0
    else:
        return round(successful_duels / total_duels, 2)


def extract_player_metrics(dataset: EventDataset, minutes_dataset: list, df: pd.DataFrame) -> dict:
    """Extract player metrics: team, position, minutes played, goals, assists, crosses, dribbles and passes"""
    # Initialize dictionary to hold player metrics
    player_metrics = {}

    for player_name in df["player"].unique():
        # Filter events data for the specific player
        player_df = df[df["player"] == player_name]

        # Obtain individual metrics
        player_team, opponent_team = get_player_and_opponent_teams(dataset, player_df)
        player_position = get_player_position(dataset, player_name)
        player_minutes = get_player_minutes(minutes_dataset, player_name)
        player_goals = len(player_df[player_df["event_type"] == "SHOT"][player_df["result"] == "GOAL"])
        player_assists = calculate_assists_for_player(player_df, df)
        player_crosses = len(player_df[player_df["pass_type"] == "CROSS"][player_df["success"]])
        player_dribbles = len(player_df[player_df["event_type"] == "TAKE_ON"][player_df["success"]])
        player_passes = len(player_df[player_df["event_type"] == "PASS"][player_df["success"]])

        # Store metrics in dictionary
        player_metrics[player_name] = {
            "team": player_team,
            "opponent_team": opponent_team,
            "position": player_position,
            "minutes_played": player_minutes,
            "goals": player_goals,
            "assists": player_assists,
            "crosses": player_crosses,
            "dribbles": player_dribbles,
            "passes": player_passes,
        }

    return player_metrics


def extract_team_metrics(minutes_played_dataset: list, df: pd.DataFrame) -> dict:
    """Extract team metrics: minutes played, goals, yellow and red cards, interceptions, clearances and tackle wins"""
    # Initialize dictionary to hold team metrics
    team_metrics = {}

    for team in df["team"].unique():
        team_df = df[df["team"] == team]

        # Obtain team metrics
        team_minutes = get_team_minutes(minutes_played_dataset, team)
        team_goals = len(team_df[team_df["event_type"] == "SHOT"][team_df["result"] == "GOAL"])
        team_yellow_cards = len(team_df[team_df["event_type"] == "CARD"][team_df["card_type"] == "FIRST_YELLOW"])
        team_red_cards = len(
            team_df[team_df["event_type"] == "CARD"][team_df["card_type"].isin(["RED", "SECOND_YELLOW"])]
        )
        team_interceptions = len(team_df[team_df["event_type"] == "INTERCEPTION"][team_df["success"]])
        team_clearances = len(team_df[team_df["event_type"] == "CLEARANCE"])
        team_tackle_win_ratio = calculate_tackle_win_ratio(team_df)

        # Store metrics in dictionary
        team_metrics[team] = {
            "total_minutes": team_minutes,
            "goals": team_goals,
            "yellow_cards": team_yellow_cards,
            "red_cards": team_red_cards,
            "interceptions": team_interceptions,
            "clearances": team_clearances,
            "tackle_win_ratio": team_tackle_win_ratio,
        }

    return team_metrics


def calculate_ppi_for_players(player_metrics: dict, team_metrics: dict) -> pd.DataFrame:
    """Calculate EA Sports PPI for each player"""
    # Initialize list to hold player PPI scores
    ppi_list = []

    for player, metrics in player_metrics.items():
        # Get metrics needed for calculations
        player_team = metrics["team"]
        player_position = metrics["position"]
        player_goals = metrics["goals"]
        player_assists = metrics["assists"]
        player_crosses = metrics["crosses"]
        player_dribbles = metrics["dribbles"]
        player_passes = metrics["passes"]

        opponent_team = metrics["opponent_team"]
        opponent_metrics = team_metrics[opponent_team]
        opp_yellows = opponent_metrics["yellow_cards"]
        opp_reds = opponent_metrics["red_cards"]
        opp_interceptions = opponent_metrics["interceptions"]
        opp_clearances = opponent_metrics["clearances"]
        opp_tackle_win_ratio = opponent_metrics["tackle_win_ratio"]

        team_goals = team_metrics[player_team]["goals"]
        opponent_goals = team_metrics[opponent_team]["goals"]

        player_minutes = metrics["minutes_played"]
        team_minutes = team_metrics[player_team]["total_minutes"]
        minutes_ratio = round(player_minutes / team_minutes, 2) if team_minutes > 0 else 0

        # Subindex 1: Modelling Match Outcome
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

        index_1 = MODEL_COEFFICIENTS["constant"]
        index_1 += player_crosses * MODEL_COEFFICIENTS["crosses"]
        index_1 += player_dribbles * MODEL_COEFFICIENTS["dribbles"]
        index_1 += player_passes * MODEL_COEFFICIENTS["passes"]
        index_1 += opp_interceptions * MODEL_COEFFICIENTS["opp_interceptions"]
        index_1 += opp_yellows * MODEL_COEFFICIENTS["opp_yellows"]
        index_1 += opp_reds * MODEL_COEFFICIENTS["opp_reds"]
        index_1 += opp_tackle_win_ratio * MODEL_COEFFICIENTS["opp_tackle_win_ratio"]
        index_1 += opp_clearances * MODEL_COEFFICIENTS["opp_clearances"]

        # Subindex 2: Points-Sharing Index
        POINTS_FOR_WIN = 3
        POINTS_FOR_DRAW = 1
        POINTS_FOR_LOSS = 0

        if team_goals > opponent_goals:
            index_2 = minutes_ratio * POINTS_FOR_WIN
        elif team_goals == opponent_goals:
            index_2 = minutes_ratio * POINTS_FOR_DRAW
        else:
            index_2 = minutes_ratio * POINTS_FOR_LOSS

        # Subindex 3: Appearance Index
        POINTS_PER_GAME = 1.34
        index_3 = minutes_ratio * POINTS_PER_GAME

        # Subindex 4: Goal-Scoring Index
        POINTS_PER_GOAL = 1.039
        index_4 = player_goals * POINTS_PER_GOAL

        # Subindex 5: Assists Index
        POINTS_PER_ASSIST = 1.039
        index_5 = player_assists * POINTS_PER_ASSIST

        # Subindex 6: Clean-Sheets Index
        POINTS_PER_CLEAN_SHEET_GOALKEEPER = 0.585
        POINTS_PER_CLEAN_SHEET_DEFENDER = 0.364
        POINTS_PER_CLEAN_SHEET_MIDFIELDER = 0.150
        POINTS_PER_CLEAN_SHEET_STRIKER = 0.071

        if opponent_goals == 0:
            match player_position:
                case "Goalkeeper":
                    index_6 = POINTS_PER_CLEAN_SHEET_GOALKEEPER
                case "Defender":
                    index_6 = POINTS_PER_CLEAN_SHEET_DEFENDER
                case "Midfielder":
                    index_6 = POINTS_PER_CLEAN_SHEET_MIDFIELDER
                case "Attacker":
                    index_6 = POINTS_PER_CLEAN_SHEET_STRIKER
                case _:
                    index_6 = 0
        else:
            index_6 = 0

        # Final PPI calculation
        I1_WEIGHT = 0.25
        I2_WEIGHT = 0.375
        I3_WEIGHT = 0.125
        I4_WEIGHT = 0.125
        I5_WEIGHT = 0.0625
        I6_WEIGHT = 0.0625

        player_index = round(
            100
            * (
                I1_WEIGHT * index_1
                + I2_WEIGHT * index_2
                + I3_WEIGHT * index_3
                + I4_WEIGHT * index_4
                + I5_WEIGHT * index_5
                + I6_WEIGHT * index_6
            )
        )

        # Append player PPI data to list
        ppi_list.append(
            {
                "player": player,
                "team": player_team,
                "position": player_position,
                "index_score": player_index,
                "minutes_played": player_minutes,
                "goals": player_goals,
                "assists": player_assists,
                "crosses": player_crosses,
                "dribbles": player_dribbles,
                "passes": player_passes,
            }
        )

    # Convert list to DataFrame
    ppi_df = pd.DataFrame(ppi_list)
    return ppi_df

    # Load players info and team minutes
    players_info_df = players.get_players_info(match_id)
    team_minutes_dict = players.get_minutes_played_by_team(match_id)

def calculate_ppi_for_match(match_id: int) -> pd.DataFrame:
    """Calculate PPI for all players in a match"""
    # Load match data
    dataset, match_events_df = players.load_match_data(match_id)

    # Extract metrics

    # Calculate index scores
    ppi_df = calculate_ppi_for_players(player_metrics, team_metrics)
    player_metrics = extract_player_metrics(dataset, match_events_df, players_info_df)
    team_metrics = extract_team_metrics(match_events_df, team_minutes_dict)

    # Convert to DataFrame and rank players
    ppi_df = ppi_df.sort_values("index_score", ascending=False).reset_index(drop=True)
    ppi_df.insert(0, "rank", range(1, len(ppi_df) + 1))

    return ppi_df


def calculate_ppi_for_tournament(tournament: dict) -> pd.DataFrame:
    """Calculate PPI for all players in a tournament given a list of match IDs"""
    match_ids = tournaments.get_all_match_ids(tournament)

    all_players_ppi_df = pd.DataFrame(
        columns=[
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
        ]
    )

    for i, match_id in enumerate(match_ids):
        print(f"Calculating PPI for match {match_id}... ({i + 1}/{len(match_ids)})")

        ppi_df = calculate_ppi_for_match(match_id)
        all_players_ppi_df = pd.concat([all_players_ppi_df, ppi_df], ignore_index=True)

    # Merge PPI scores for players appearing in multiple matches by averaging their scores
    all_players_ppi_df = (
        all_players_ppi_df.groupby(
            ["player", "team"],
            as_index=False,
        )
        .agg(
            {
                "index_score": "avg",
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
    all_players_ppi_df.insert(0, "rank", range(1, len(all_players_ppi_df) + 1))

    # Save index scores to CSV
    output_filename = paths.EA_SPORTS_PPI_OUTPUT_DIR / f"{tournament['label']}_ppi_scores.csv"
    all_players_ppi_df.to_csv(output_filename, index=False)

    return all_players_ppi_df


def main():
    """Main function to demonstrate PPI calculation"""
    # Example: Calculate PPI for UEFA Euro 2024 tournament
    tournament = tournaments.EURO_2024
    ppi_df = calculate_ppi_for_tournament(tournament)

    print(f"\nTop 10 Players in {tournament['label']} by EA Sports PPI:")
    print(ppi_df.head(10))


if __name__ == "__main__":
    main()
