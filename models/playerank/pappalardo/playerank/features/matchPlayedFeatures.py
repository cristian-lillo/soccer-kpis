import glob
import json
from collections.abc import Callable

from .abstract import Feature


class matchPlayedFeatures(Feature):
    def createFeature(
        self,
        matches_path: str,
        players_file: str,
        select: Callable | None = None,
    ) -> list[dict[str, str | int | float]]:
        """
        Computes, for each player and match:
        - Total time played (in minutes)
        - Goals scored

        Parameters:
            matches_path: Folder with JSON files corresponding to matches data.
            players_file: JSON file with players data.
            select: Function for filtering matches collection. Default: Aggregate over all matches.

        Returns:
            A collection of documents in a specific format.
            ```
            {
                'match': this.wyId,
                'player': player,
                'name': 'minutesPlayed' | 'team' | 'goalScored' | 'timestamp',
                'value': <float> | <string>,
            }
            ```
        """
        # Get IDs of goalkeepers
        players = json.load(open(players_file))
        goalkeepers_ids = [player["wyId"] for player in players if player["role"]["name"] == "Goalkeeper"]

        # Load matches data
        matches = []
        for file in glob.glob(f"{matches_path}"):
            matches += json.load(open(file))
        if select:
            matches = list(filter(select, matches))
        print(f"[matchPlayedFeatures] processing {len(matches)} matches")

        # Compute minutes played and goals scored for each player in each match
        result = []
        for match in matches:
            matchId = match["wyId"]

            duration = 90
            if match["duration"] != "Regular":
                duration = 120

            timestamp = match["dateutc"]

            for team in match["teamsData"]:
                minutes_played = {}
                goals_scored = {}

                # Process substitutions
                if (
                    match["teamsData"][team]["hasFormation"] == 1
                    and "substitutions" in match["teamsData"][team]["formation"]
                ):
                    for sub in match["teamsData"][team]["formation"]["substitutions"]:
                        if isinstance(sub, dict):
                            minute = sub["minute"]
                            minutes_played[sub["playerOut"]] = minute
                            minutes_played[sub["playerIn"]] = duration - minute

                # Process lineup players
                if match["teamsData"][team]["hasFormation"] == 1 and "lineup" in match["teamsData"][team]["formation"]:
                    for player in match["teamsData"][team]["formation"]["lineup"]:
                        goals_scored[player["playerId"]] = player["goals"]

                        if player["playerId"] not in minutes_played:  # Player not substituted out
                            minutes_played[player["playerId"]] = duration

                # Process bench players
                if match["teamsData"][team]["hasFormation"] == 1 and "bench" in match["teamsData"][team]["formation"]:
                    for player in match["teamsData"][team]["formation"]["bench"]:
                        goals_scored[player["playerId"]] = player["goals"]

                        if player["playerId"] not in minutes_played:  # Player not substituted in
                            minutes_played[player["playerId"]] = duration

                # Add minutes played by each player to result
                for player, min in minutes_played.items():
                    if player not in goalkeepers_ids:
                        document = {
                            "match": matchId,
                            "entity": player,
                            "feature": "minutesPlayed",
                            "value": min,
                        }
                        result.append(document)

                # Add goals scored by each player to result
                for player, gs in goals_scored.items():
                    if player not in goalkeepers_ids:
                        try:
                            gs = int(gs)
                        except:
                            gs = 0
                        document = {"match": matchId, "entity": player, "feature": "goalScored", "value": gs}
                        result.append(document)

                        # Add timestamp for each player
                        document = {"match": matchId, "entity": player, "feature": "timestamp", "value": timestamp}
                        result.append(document)

                        # Add team for each player
                        document = {"match": matchId, "entity": player, "feature": "team", "value": team}
                        result.append(document)

        print(f"[matchPlayedFeatures] matches features computed. {len(result)} features processed")
        return result
