"""
Module to calculate the EA Sports Player Performance Index (PPI) and group match events by player.
"""

import sys
from pathlib import Path

import pandas as pd
from kloppy import statsbomb, wyscout

from .index_calculator import index_score

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parents[2]))
from config import project_paths


def get_player_data(match_id: int, player_id: int, provider="statsbomb") -> pd.DataFrame:
    """Fetches player data from the specified provider for a given match and player ID."""
    # Load dataset based on provider
    if provider == "statsbomb":
        dataset = statsbomb.load(
            event_data=project_paths.STATSBOMB_EVENTS_DIR / f"{match_id}.json",
            lineup_data=project_paths.STATSBOMB_LINEUPS_DIR / f"{match_id}.json",
        )
    elif provider == "wyscout":
        dataset = wyscout.load(
            event_data=project_paths.WYSCOUT_PROCESSED_V2_DIR / f"{match_id}.json",
        )
    else:
        raise ValueError("Unsupported provider. Use 'statsbomb' or 'wyscout'.")

    # Filter columns from the dataset
    filtered_dataset = dataset.to_df(
        "player_id",
        "player",
        "team_id",
        "team",
        "event_type",
        "event_name",
        "result",
        "success",
    )

    print(f"### DataFrame:\n{filtered_dataset.head(10)}\n")
    print(f"### Description:\n{filtered_dataset.describe()}\n")
    print(f"### Info:\n{filtered_dataset.info()}\n")

    return filtered_dataset


def main():
    # StatsBomb match and player IDs for testing (UEFA Euro 2024 Final - Lamine Yamal)
    match_id = 3943043
    player_id = 316046

    get_player_data(match_id, player_id)

    # Example player data
    player_example = {
        "position": "ST",
        "minutes_played": 90,
        "goals": 2,
        "assists": 1,
        "home_goals": 4,
        "away_goals": 2,
        "team_minutes": 990,
        "clean_sheets": 0,
        "crosses": 3,
        "dribbles": 1,
        "passes": 20,
        "opp_interceptions": 3,
        "opp_yellows": 1,
        "opp_reds": 0,
        "opp_tackle_win_ratio": 0.2,
        "opp_clearances": 1,
    }

    # Calculate and print the player index
    player_index = index_score(player_example)
    print(f"Player Index: {player_index:.2f}")


if __name__ == "__main__":
    main()
