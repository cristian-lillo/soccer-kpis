"""
Opta Points Calculator

This script calculates Opta Points for soccer players based on their match performance metrics.
"""

import warnings

import pandas as pd
from kloppy.domain import EventDataset, EventType
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

# Define points for each action
ACTION_POINTS = {
    "goals": 10,
    "shots_on_target": 4,
    "shots_off_target": 2,
    "blocked_shots": 2,
    "own_goals": -5,
    "assists": 6,
    "passes": 0.2,
    "crosses": 0.2,
    "tackles": 2,
    "interceptions": 2,
    "fouls_won": 1,
    "fouls_conceded": -1,
    "offsides": -1,
    "yellow_cards": -2,
    "red_cards": -5,
    "goals_conceded_field_player": -1,
    "goals_conceded_goalkeeper": -6,
    "penalties_won": 4,
    "saves": 5,
    "penalties_saved": 5,
}


def categorize_players_by_position(dataset: EventDataset) -> dict[str, str]:
    """
    Categorize players into 'Goalkeeper' or 'Field Player' based on their positions.

    Args:
        dataset: The event dataset.

    Returns:
        A dictionary mapping player names to their position category.
    """
    player_position_dict = {}

    for team in dataset.metadata.teams:
        for player in team.players:
            for _, _, position in player.positions.ranges():
                if position.name == "Goalkeeper":  # Check if position is Goalkeeper
                    player_position_dict[player.name] = "Goalkeeper"
                    break
            if player.name not in player_position_dict:  # If not assigned as Goalkeeper, assign as Field Player
                player_position_dict[player.name] = "Field Player"

    return player_position_dict


def count_player_offsides(dataset: EventDataset, match_events_df: pd.DataFrame) -> dict[str, int]:
    """
    Count offsides for each player.

    Args:
        dataset: The event dataset.
        match_events_df: DataFrame containing all events in the match.

    Returns:
        A dictionary mapping player names to their offsides count.
    """
    player_offsides = {}

    offside_event_ids = match_events_df.loc[
        (match_events_df["event_type"] == "PASS") & (match_events_df["result"] == "OFFSIDE"), "event_id"
    ]

    for event_id in offside_event_ids:
        event = dataset.get_event_by_id(event_id)

        # Iterate through related events to find the receiver
        for related_event_id in event.related_event_ids:  # type: ignore
            related_event = dataset.get_event_by_id(related_event_id)

            # Check if the related event is a GENERIC event (Ball Receipt)
            if related_event.event_type == EventType.GENERIC:  # type: ignore
                receiver_name = related_event.player.name  # type: ignore
                player_offsides[receiver_name] = player_offsides.get(receiver_name, 0) + 1

    return player_offsides


def get_team_conceded_goals(match_events_df: pd.DataFrame) -> dict[str, int]:
    """
    Obtain goals conceded for each team.

    Args:
        match_events_df: DataFrame containing all events in the match.

    Returns:
        A dictionary mapping team names to their goals conceded.
    """
    teams_goals_conceded = {}
    teams = match_events_df["team"].unique()

    for team in teams:
        goals_conceded = len(
            match_events_df.loc[
                (match_events_df["team"] != team)
                & (match_events_df["event_type"] == "SHOT")
                & (match_events_df["result"] == "GOAL")
            ]
        )
        teams_goals_conceded[team] = goals_conceded

    return teams_goals_conceded


def count_penalties_won(match_events_df: pd.DataFrame) -> dict[str, int]:
    """
    Count penalties won for each player.

    Args:
        match_events_df: DataFrame containing all events in the match.

    Returns:
        A dictionary mapping player names to their penalties won count.
    """
    penalties_won = {}

    # Filter penalties shot and fouls won
    penalties_shot_df = match_events_df.loc[
        (match_events_df["event_type"] == "SHOT") & (match_events_df["set_piece_type"] == "PENALTY")
    ]
    fouls_won_df = match_events_df.loc[(match_events_df["event_type"] == "GENERIC:Foul Won")]

    # Get indexes of DataFrames
    event_indexes = match_events_df.index.to_list()
    penalties_shot_indexes = penalties_shot_df.index.to_list()
    fouls_won_indexes = fouls_won_df.index.to_list()

    # Iterate through each penalty shot and look for a foul won in preceding events
    for penalty_shot_idx in penalties_shot_indexes:
        # Get all event indexes that come before the current penalty shot
        preceding_indexes = [idx for idx in event_indexes if idx < penalty_shot_idx]

        for event_idx in reversed(preceding_indexes):
            event = match_events_df.loc[event_idx]

            if event_idx in fouls_won_indexes:  # Found a foul won for this penalty shot
                player_name = event["player"]
                penalties_won[player_name] = penalties_won.get(player_name, 0) + 1
                break
            elif event["event_type"] == "FOUL_COMMITTED":  # No foul won found, stop searching
                break

    return penalties_won


def extract_player_metrics(
    dataset: EventDataset,
    match_events_df: pd.DataFrame,
    player_info_df: pd.DataFrame,
    player_positions_dict: dict[str, str],
) -> dict[str, dict[str, str | int]]:
    """
    Extract performance metrics for each player.

    Args:
        dataset: The event dataset.
        match_events_df: DataFrame containing all events in the match.
        player_info_df: DataFrame containing player information.
        player_positions_dict: A dictionary mapping player names to their position category.

    Returns:
        A dictionary mapping player names to their performance metrics.
    """
    player_metrics = {}

    # Map player names to their teams and minutes played for quick access
    nickname_mapping = dict(zip(player_info_df["player_name"], player_info_df["nickname"]))
    team_mapping = dict(zip(player_info_df["player_name"], player_info_df["team_name"]))
    minutes_mapping = dict(zip(player_info_df["player_name"], player_info_df["minutes_played"]))

    # Count assists for all players in the match
    assists_mapping = players.count_assists(match_events_df)

    # Execute helper functions
    offsides_mapping = count_player_offsides(dataset, match_events_df)
    team_goals_conceded = get_team_conceded_goals(match_events_df)
    penalties_won_mapping = count_penalties_won(match_events_df)

    for player_name in match_events_df["player"].unique():
        # Get specific player event data
        player_df = match_events_df.loc[match_events_df["player"] == player_name]

        # Use nickname, team and minutes mappings
        player_nickname = nickname_mapping[player_name] or player_name
        player_team = team_mapping[player_name]
        player_minutes = minutes_mapping[player_name]

        # Goals (G)
        goals = len(player_df.loc[(player_df["event_type"] == "SHOT") & (player_df["result"] == "GOAL")])

        # Shots on target (SonT)
        shots_on_target = len(
            player_df.loc[
                (player_df["event_type"] == "SHOT") & (player_df["result"].isin(["GOAL", "BLOCKED", "SAVED"]))
            ]
        )

        # Shots off target (SoffT)
        shots_off_target = len(
            player_df.loc[(player_df["event_type"] == "SHOT") & (player_df["result"].isin(["OFF_TARGET", "POST"]))]
        )

        # Blocked shots (BS)
        # This is a subset of Shots on Target (SonT)
        blocked_shots = len(player_df.loc[(player_df["event_type"] == "SHOT") & (player_df["result"] == "BLOCKED")])

        # Own goals (OG)
        own_goals = len(player_df.loc[(player_df["event_type"] == "SHOT") & (player_df["result"] == "OWN_GOAL")])

        # Assists (A)
        assists = assists_mapping.get(player_name, 0)

        # Passes (P)
        passes = len(
            player_df.loc[
                (player_df["event_type"] == "PASS")
                & (player_df["success"])
                & (~player_df["pass_type"].isin(["CROSS", "HAND_PASS"]))
                & (player_df["set_piece_type"] != "THROW_IN")
            ]
        )

        # Crosses (C)
        crosses = len(
            player_df.loc[
                (player_df["event_type"] == "PASS") & (player_df["pass_type"] == "CROSS") & (player_df["success"])
            ]
        )

        # Tackles (Tk)
        tackles = len(
            player_df.loc[
                (player_df["event_type"] == "DUEL") & (player_df["duel_type"].isin(["TACKLE", "SLIDING_TACKLE"]))
            ]
        )

        # Interceptions (INT)
        interceptions = len(player_df.loc[(player_df["event_type"] == "INTERCEPTION") & (player_df["success"])])

        # Fouls won (FW)
        fouls_won = len(player_df.loc[(player_df["event_type"] == "GENERIC:Foul Won")])

        # Fouls conceded (FC)
        fouls_conceded = len(player_df.loc[(player_df["event_type"] == "FOUL_COMMITED")])

        # Offsides (O)
        offsides = offsides_mapping.get(player_name, 0)

        # Yellow cards (YC)
        yellow_cards = len(
            player_df.loc[(player_df["event_type"] == "CARD") & (player_df["card_type"] == "FIRST_YELLOW")]
        )

        # Red cards (RC)
        red_cards = len(
            player_df.loc[(player_df["event_type"] == "CARD") & (player_df["card_type"].isin(["SECOND_YELLOW", "RED"]))]
        )

        # Goals conceded (GC)
        goals_conceded = team_goals_conceded[player_team]

        # Penalties won (PW)
        # This is a subset of Fouls won (FW)
        penalties_won = penalties_won_mapping.get(player_name, 0)

        # Saves (SAV)
        saves = len(player_df.loc[(player_df["event_type"] == "GOALKEEPER") & (player_df["goalkeeper_type"] == "SAVE")])

        # Penalties saved (PS)
        # This is a subset of Saves (SAV)
        penalties_saved = len(
            player_df.loc[
                (player_df["event_type"] == "GOALKEEPER")
                & (player_df["goalkeeper_type"] == "SAVE")
                & (player_df["set_piece_type"] == "PENALTY")
            ]
        )

        player_metrics[player_nickname] = {
            "team": player_team,
            "position": player_positions_dict[player_name],
            "minutes_played": player_minutes,
            "goals": goals,
            "shots_on_target": shots_on_target,
            "shots_off_target": shots_off_target,
            "blocked_shots": blocked_shots,
            "own_goals": own_goals,
            "assists": assists,
            "passes": passes,
            "crosses": crosses,
            "tackles": tackles,
            "interceptions": interceptions,
            "fouls_won": fouls_won,
            "fouls_conceded": fouls_conceded,
            "offsides": offsides,
            "yellow_cards": yellow_cards,
            "red_cards": red_cards,
            "goals_conceded": goals_conceded,
            "penalties_won": penalties_won,
            "saves": saves,
            "penalties_saved": penalties_saved,
        }

    return player_metrics


def calculate_opta_points_for_players(player_metrics: dict) -> pd.DataFrame:
    """
    Calculate Opta Points for each player.

    Args:
        player_metrics: A dictionary containing player metrics.

    Returns:
        A DataFrame containing Opta Points for each player.
    """

    # Initialize list to hold player Opta Points
    opta_points_list = []

    for player, metrics in player_metrics.items():
        player_points = 0

        # Multiply each metric by its corresponding point value
        for metric, value in metrics.items():
            if metric in ACTION_POINTS:
                if metric == "goals_conceded":
                    if metrics["position"] == "Goalkeeper":
                        player_points += ACTION_POINTS["goals_conceded_goalkeeper"] * value
                    else:
                        player_points += ACTION_POINTS["goals_conceded_field_player"] * value
                else:
                    player_points += ACTION_POINTS[metric] * value

        # Append player Opta Points data to list
        opta_points_list.append(
            {
                "player": player,
                "team": metrics["team"],
                "position": metrics["position"],
                "opta_points": player_points,
                "minutes_played": metrics["minutes_played"],
                "goals": metrics["goals"],
                "shots_on_target": metrics["shots_on_target"],
                "shots_off_target": metrics["shots_off_target"],
                "blocked_shots": metrics["blocked_shots"],
                "own_goals": metrics["own_goals"],
                "assists": metrics["assists"],
                "passes": metrics["passes"],
                "crosses": metrics["crosses"],
                "tackles": metrics["tackles"],
                "interceptions": metrics["interceptions"],
                "fouls_won": metrics["fouls_won"],
                "fouls_conceded": metrics["fouls_conceded"],
                "offsides": metrics["offsides"],
                "yellow_cards": metrics["yellow_cards"],
                "red_cards": metrics["red_cards"],
                "goals_conceded": metrics["goals_conceded"],
                "penalties_won": metrics["penalties_won"],
                "saves": metrics["saves"],
                "penalties_saved": metrics["penalties_saved"],
            }
        )

    # Create DataFrame and rank players by Opta Points
    opta_points_df = pd.DataFrame(opta_points_list)
    ranked_opta_points_df = opta_points_df.sort_values("opta_points", ascending=False).reset_index(drop=True)
    ranked_opta_points_df.insert(0, "rank", range(1, len(ranked_opta_points_df) + 1))

    return ranked_opta_points_df


def get_match_opta_points(match_id: int) -> pd.DataFrame:
    """
    Obtain Opta Points for all players in a given match.

    Args:
        match_id: StatsBomb match ID.

    Returns:
        DataFrame containing Opta Points for each player in the match.
    """
    # Load players info and match data
    players_info_df = players.get_players_info(match_id)
    dataset, player_events_df = players.load_match_data(match_id)

    # Get player positions
    player_positions_dict = categorize_players_by_position(dataset)

    # Extract player metrics
    player_metrics = extract_player_metrics(dataset, player_events_df, players_info_df, player_positions_dict)

    # Calculate Opta Points for players
    opta_points_df = calculate_opta_points_for_players(player_metrics)

    return opta_points_df


def get_tournament_opta_points(tournament: dict) -> pd.DataFrame:
    """
    Obtain Opta Points for all players in a given tournament.

    Args:
        tournament: A dictionary containing competition and season IDs.

    Returns:
        DataFrame containing Opta Points for each player in the tournament.
    """
    # Get all match IDs for the tournament
    match_ids = tournaments.get_all_match_ids(tournament)

    # Initialize empty DataFrame to store tournament Opta Points scores
    all_matches_opta_points_df = pd.DataFrame(
        columns=[
            "rank",
            "player",
            "team",
            "position",
            "opta_points",
            "minutes_played",
            "goals",
            "shots_on_target",
            "shots_off_target",
            "blocked_shots",
            "own_goals",
            "assists",
            "passes",
            "crosses",
            "tackles",
            "interceptions",
            "fouls_won",
            "fouls_conceded",
            "offsides",
            "yellow_cards",
            "red_cards",
            "goals_conceded",
            "penalties_won",
            "saves",
            "penalties_saved",
        ]
    )

    # Calculate Opta Points for each match and concatenate results
    for match_id in tqdm(match_ids, desc=f"Calculating Opta Points for matches in {tournament['label']}", ncols=150):
        match_opta_points_df = get_match_opta_points(match_id)

        # Save match Opta Points to CSV
        match_filename = paths.OPTA_POINTS_OUTPUT_DIR / tournament["label"] / f"match_{match_id}_opta_points.csv"
        match_opta_points_df.to_csv(match_filename, index=False)

        # Combine match Opta Points into all matches DataFrame
        if all_matches_opta_points_df.empty:
            all_matches_opta_points_df = match_opta_points_df
        else:
            all_matches_opta_points_df = pd.concat(
                [all_matches_opta_points_df, match_opta_points_df],
                ignore_index=True,
            )

    # Aggregate Opta Points for players across all matches in the tournament
    tournament_opta_points_df = (
        all_matches_opta_points_df.groupby(
            ["player", "team"],
            as_index=False,
        )
        .agg(
            {
                "position": lambda x: x.mode().loc[0],
                "opta_points": "sum",
                "minutes_played": "sum",
                "goals": "sum",
                "shots_on_target": "sum",
                "shots_off_target": "sum",
                "blocked_shots": "sum",
                "own_goals": "sum",
                "assists": "sum",
                "passes": "sum",
                "crosses": "sum",
                "tackles": "sum",
                "interceptions": "sum",
                "fouls_won": "sum",
                "fouls_conceded": "sum",
                "offsides": "sum",
                "yellow_cards": "sum",
                "red_cards": "sum",
                "goals_conceded": "sum",
                "penalties_won": "sum",
                "saves": "sum",
                "penalties_saved": "sum",
            }
        )
        .sort_values("opta_points", ascending=False)
        .reset_index(drop=True)
    )

    # Add rank column
    tournament_opta_points_df.insert(0, "rank", range(1, len(tournament_opta_points_df) + 1))

    # Add matches played column
    player_team_counts = all_matches_opta_points_df.value_counts(["player", "team"]).reset_index(name="matches_played")
    tournament_opta_points_df = pd.merge(
        tournament_opta_points_df, player_team_counts, how="left", on=["player", "team"]
    )

    # Save tournament Opta Points to CSV
    tournament_filename = paths.OPTA_POINTS_OUTPUT_DIR / f"{tournament['label']}_opta_points.csv"
    tournament_opta_points_df.to_csv(tournament_filename, index=False)

    return tournament_opta_points_df


def main():
    # Calculate Opta Points for National Team Tournaments
    for tournament in tqdm(
        tournaments.NATIONAL_TEAM_TOURNAMENTS,
        desc="Processing National Team Tournaments",
        ncols=150,
    ):
        get_tournament_opta_points(tournament)

    # Calculate Opta Points for European Club Leagues
    for tournament in tqdm(
        tournaments.EUROPEAN_CLUB_LEAGUES,
        desc="Processing European Club Leagues",
        ncols=150,
    ):
        get_tournament_opta_points(tournament)


if __name__ == "__main__":
    main()
