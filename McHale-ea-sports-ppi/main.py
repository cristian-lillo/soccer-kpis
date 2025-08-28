import pandas as pd

import index_calculator
import utils

data_dir = utils.DATA_DIR
matches_dir = utils.MATCHES_DIR
lineups_dir = utils.LINEUPS_DIR
events_dir = utils.EVENTS_DIR
three_sixty_dir = utils.THREE_SIXTY_DIR


def get_competitions_with_360_data() -> list:
    """
    Extract competitions with available 360 data and return a list of (competition_id, season_id) tuples.
    """
    # Create Competitions DataFrame from JSON file
    competitions_file_path = data_dir / "competitions.json"
    competitions_df = pd.read_json(competitions_file_path)

    # Filter out competitions without 360 data
    competitions_df.dropna(subset=["match_available_360"], inplace=True)

    # Get the competition and season IDs
    competition_season_pairs = list(competitions_df[["competition_id", "season_id"]].itertuples(index=False, name=None))

    return competition_season_pairs


def get_competition_matches(competition_id: int, season_id: int) -> list[int]:
    """
    Extract matches for a given competition and season.
    """
    # Create Matches DataFrame from JSON file
    competition_dir = matches_dir / f"{competition_id}"
    matches_file_path = competition_dir / f"{season_id}.json"
    matches_df = pd.read_json(matches_file_path)

    # Get match IDs
    match_ids = matches_df["match_id"].to_list()

    return match_ids


def group_match_events_by_player(match_id: int):
    """
    Group match events by player for a given match ID.
    """
    # Create Events DataFrame from JSON file
    events_file_path = events_dir / f"{match_id}.json"
    events_df = pd.read_json(events_file_path)

    # Group events by player
    player_events_df = events_df.groupby("player")
    print(player_events_df)

    return player_events_df


def main():
    competition_season_pairs = get_competitions_with_360_data()

    for competition_id, season_id in competition_season_pairs:
        match_ids = get_competition_matches(competition_id, season_id)

        for match_id in match_ids:
            # Group events by player for each match
            player_events_df = group_match_events_by_player(match_id)

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
    }

    # Calculate and print the player index
    player_index = index_calculator.index_score(player_example)
    print(f"Player Index: {player_index:.2f}")


if __name__ == "__main__":
    main()
