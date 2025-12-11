"""
Configuration for soccer competitions and seasons.
"""

from socceraction.data.statsbomb import StatsBombLoader

from config import paths

# StatsBomb competition and season IDs
PREMIER_LEAGUE = {
    "label": "premier_league",
    "country_name": "England",
    "competition_name": "Premier League",
    "season_name": "2015/2016",
    "competition_id": 2,
    "season_id": 27,
}

LA_LIGA = {
    "label": "la_liga",
    "country_name": "Spain",
    "competition_name": "La Liga",
    "season_name": "2015/2016",
    "competition_id": 11,
    "season_id": 27,
}

SERIE_A = {
    "label": "serie_a",
    "country_name": "Italy",
    "competition_name": "Serie A",
    "season_name": "2015/2016",
    "competition_id": 12,
    "season_id": 27,
}

BUNDESLIGA = {
    "label": "bundesliga",
    "country_name": "Germany",
    "competition_name": "1. Bundesliga",
    "season_name": "2015/2016",
    "competition_id": 9,
    "season_id": 27,
}

LIGUE_1 = {
    "label": "ligue_1",
    "country_name": "France",
    "competition_name": "Ligue 1",
    "season_name": "2015/2016",
    "competition_id": 7,
    "season_id": 27,
}

WORLD_CUP_2018 = {
    "label": "world_cup_2018",
    "country_name": "International",
    "competition_name": "FIFA World Cup",
    "season_name": "2018",
    "competition_id": 43,
    "season_id": 3,
}

WORLD_CUP_2022 = {
    "label": "world_cup_2022",
    "country_name": "International",
    "competition_name": "FIFA World Cup",
    "season_name": "2022",
    "competition_id": 43,
    "season_id": 106,
}

EURO_2020 = {
    "label": "euro_2020",
    "country_name": "Europe",
    "competition_name": "UEFA Euro",
    "season_name": "2020",
    "competition_id": 55,
    "season_id": 43,
}

EURO_2024 = {
    "label": "euro_2024",
    "country_name": "Europe",
    "competition_name": "UEFA Euro",
    "season_name": "2024",
    "competition_id": 55,
    "season_id": 282,
}

COPA_AMERICA_2024 = {
    "label": "copa_america_2024",
    "country_name": "South America",
    "competition_name": "Copa America",
    "season_name": "2024",
    "competition_id": 223,
    "season_id": 282,
}

EUROPEAN_CLUB_LEAGUES = [
    PREMIER_LEAGUE,
    LA_LIGA,
    SERIE_A,
    BUNDESLIGA,
    LIGUE_1,
]

NATIONAL_TEAM_TOURNAMENTS = [
    WORLD_CUP_2018,
    WORLD_CUP_2022,
    EURO_2020,
    EURO_2024,
    COPA_AMERICA_2024,
]


def get_all_match_ids(tournament: dict) -> list[int]:
    """Retrieve all StatsBomb match IDs for a given tournament."""
    SBL = StatsBombLoader(
        getter="local",
        root=str(paths.STATSBOMB_DIR),
    )

    games_df = SBL.games(
        competition_id=tournament["competition_id"],
        season_id=tournament["season_id"],
    )
    games_df.sort_values(by=["game_day", "game_date"], ascending=False, inplace=True)

    match_ids = games_df["game_id"].tolist()

    return match_ids
