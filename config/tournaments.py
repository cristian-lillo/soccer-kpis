"""
Configuration for soccer competitions and seasons.
"""

from socceraction.data.statsbomb import StatsBombLoader

from config import paths

# StatsBomb competition and season IDs
PREMIER_LEAGUE: dict[str, str | int] = {
    "label": "premier_league",
    "country_name": "England",
    "competition_name": "Premier League",
    "season_name": "2015/2016",
    "display_name": "Premier League 2015/2016",
    "competition_id": 2,
    "season_id": 27,
}


LA_LIGA: dict[str, str | int] = {
    "label": "la_liga",
    "country_name": "Spain",
    "competition_name": "La Liga",
    "season_name": "2015/2016",
    "display_name": "La Liga 2015/2016",
    "competition_id": 11,
    "season_id": 27,
}

SERIE_A: dict[str, str | int] = {
    "label": "serie_a",
    "country_name": "Italy",
    "competition_name": "Serie A",
    "season_name": "2015/2016",
    "display_name": "Serie A 2015/2016",
    "competition_id": 12,
    "season_id": 27,
}

BUNDESLIGA: dict[str, str | int] = {
    "label": "bundesliga",
    "country_name": "Germany",
    "competition_name": "1. Bundesliga",
    "season_name": "2015/2016",
    "display_name": "Bundesliga 2015/2016",
    "competition_id": 9,
    "season_id": 27,
}

LIGUE_1: dict[str, str | int] = {
    "label": "ligue_1",
    "country_name": "France",
    "competition_name": "Ligue 1",
    "season_name": "2015/2016",
    "display_name": "Ligue 1 2015/2016",
    "competition_id": 7,
    "season_id": 27,
}

WORLD_CUP_2018: dict[str, str | int] = {
    "label": "world_cup_2018",
    "country_name": "International",
    "competition_name": "FIFA World Cup",
    "season_name": "2018",
    "display_name": "FIFA World Cup 2018",
    "competition_id": 43,
    "season_id": 3,
}

WORLD_CUP_2022: dict[str, str | int] = {
    "label": "world_cup_2022",
    "country_name": "International",
    "competition_name": "FIFA World Cup",
    "season_name": "2022",
    "display_name": "FIFA World Cup 2022",
    "competition_id": 43,
    "season_id": 106,
}

EURO_2020: dict[str, str | int] = {
    "label": "euro_2020",
    "country_name": "Europe",
    "competition_name": "UEFA Euro",
    "season_name": "2020",
    "display_name": "UEFA Euro 2020",
    "competition_id": 55,
    "season_id": 43,
}

EURO_2024: dict[str, str | int] = {
    "label": "euro_2024",
    "country_name": "Europe",
    "competition_name": "UEFA Euro",
    "season_name": "2024",
    "display_name": "UEFA Euro 2024",
    "competition_id": 55,
    "season_id": 282,
}

COPA_AMERICA_2024: dict[str, str | int] = {
    "label": "copa_america_2024",
    "country_name": "South America",
    "competition_name": "Copa America",
    "season_name": "2024",
    "display_name": "Copa America 2024",
    "competition_id": 223,
    "season_id": 282,
}

EUROPEAN_CLUB_LEAGUES: list[dict[str, str | int]] = [
    PREMIER_LEAGUE,
    LA_LIGA,
    SERIE_A,
    BUNDESLIGA,
    LIGUE_1,
]

NATIONAL_TEAM_TOURNAMENTS: list[dict[str, str | int]] = [
    WORLD_CUP_2018,
    WORLD_CUP_2022,
    EURO_2020,
    EURO_2024,
    COPA_AMERICA_2024,
]

ALL_TOURNAMENTS: list[dict[str, str | int]] = EUROPEAN_CLUB_LEAGUES + NATIONAL_TEAM_TOURNAMENTS


def setup_tournament_directories() -> None:
    """Create necessary directories for each tournament in model output directories."""
    for model_output_dir in paths.MODEL_OUTPUT_DIRECTORIES:
        for tournament in ALL_TOURNAMENTS:
            tournament_dir = model_output_dir / str(tournament["label"])
            tournament_dir.mkdir(parents=True, exist_ok=True)


def get_all_match_ids(tournament: dict[str, str | int]) -> list[int]:
    """
    Retrieve all StatsBomb match IDs for a given tournament.

    Args:
        tournament (dict): A dictionary containing competition and season IDs.

    Returns:
        list[int]: A list of match IDs.
    """
    SBL = StatsBombLoader(getter="local", root=str(paths.STATSBOMB_DIR))

    games_df = SBL.games(competition_id=int(tournament["competition_id"]), season_id=int(tournament["season_id"]))
    games_df.sort_values(by=["game_day", "game_date"], ascending=False, inplace=True)

    match_ids = games_df["game_id"].tolist()

    return match_ids


# Ensure all required directories exist
setup_tournament_directories()

# StatsBomb match ID for UEFA Euro 2024 Final
match_ids = get_all_match_ids(EURO_2024)
EURO_2024_FINAL_MATCH_ID = match_ids[0]
