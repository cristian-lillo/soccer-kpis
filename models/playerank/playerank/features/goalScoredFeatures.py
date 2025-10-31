import glob
import json
from collections.abc import Callable

from .abstract import Feature


class goalScoredFeatures(Feature):
    """
    Goals scored by each team in each match.
    """

    def createFeature(self, matches_path: str, select: Callable | None = None):
        """
        Stores goalScoredFeatures on database.

        Args:
            matches_path: File path of matches file.
            select: Function for filtering matches collection. Default: Aggregate over all matches.

        Returns:
            List of documents in the format `{match: matchId, entity: team, feature: feature, value: value}`.
        """
        matches = []

        # Load matches from all files
        for file in glob.glob(f"{matches_path}"):
            data = json.load(open(file))
            matches += data
            print(f"[GoalScored features] added {len(data)} matches")

        # Apply filtering if provided
        if select:
            matches = filter(select, matches)

        result = []
        for match in matches:
            if "teamsData" in match:
                for team in match["teamsData"]:
                    document = {
                        "match": match["wyId"],
                        "entity": team,
                        "feature": "goal-scored",
                        "value": match["teamsData"][team]["score"],
                    }
                    result.append(document)

        return result
