"""Print a summary of the ten StatsBomb competition-season datasets used."""

import json

from config import paths
from config.tournaments import ALL_TOURNAMENTS


def main() -> None:
    selected_tournaments = {
        (int(tournament["competition_id"]), int(tournament["season_id"])) for tournament in ALL_TOURNAMENTS
    }
    match_files = list(paths.STATSBOMB_MATCHES_DIR.rglob("*.json"))

    match_ids: set[int] = set()
    player_ids: set[int] = set()
    event_count = 0

    for path in match_files:
        for match in json.loads(path.read_text(encoding="utf-8")):
            competition_id = int(match["competition"]["competition_id"])
            season_id = int(match["season"]["season_id"])
            if (competition_id, season_id) in selected_tournaments:
                match_ids.add(int(match["match_id"]))

    for match_id in match_ids:
        lineup_path = paths.STATSBOMB_LINEUPS_DIR / f"{match_id}.json"
        event_path = paths.STATSBOMB_EVENTS_DIR / f"{match_id}.json"

        if not lineup_path.exists() or not event_path.exists():
            raise FileNotFoundError(f"Missing StatsBomb files for match {match_id}: {lineup_path} or {event_path}")

        for team in json.loads(lineup_path.read_text(encoding="utf-8")):
            for player in team.get("lineup", []):
                if player.get("player_id") is not None:
                    player_ids.add(int(player["player_id"]))

        event_count += len(json.loads(event_path.read_text(encoding="utf-8")))

    print(f"Competencias: {len(ALL_TOURNAMENTS)}")
    print(f"Temporadas/ediciones: {len(selected_tournaments)}")
    print(f"Partidos: {len(match_ids)}")
    print(f"Jugadores: {len(player_ids)}")
    print(f"Eventos: {event_count}")


if __name__ == "__main__":
    main()
