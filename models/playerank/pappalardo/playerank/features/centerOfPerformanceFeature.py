import glob
import json
from collections import defaultdict
from collections.abc import Callable

import numpy as np

from .abstract import Feature


class centerOfPerformanceFeature(Feature):
    def createFeature(
        self,
        events_path: str,
        players_file: str,
        select: Callable | None = None,
    ) -> list[dict[str, str | int]]:
        """
        Compute centerOfPerformanceFeatures.

        Parameters:
            events_path: Folder path of events file.
            players_file: File path of players data file.
            select: Function for filtering matches collection. Default: Aggregate over all matches.
            entity: It could either 'team' or 'player'. It selects the aggregation for qualityFeatures among teams or players qualityfeatures.

        Note: Aggregation by team is exploited during learning phase, for features weights estimation, while aggregation by players is involved for rating phase.

        Returns:
            List of json docs dictionaries in specific format.
            ```
            {
            feature: string,
            entity: int,
            matchId : int,
            value: int
            }
            ```
        """
        # Load events data
        events = []
        for file in glob.glob(f"{events_path}"):
            data = json.load(open(file))
            if select:
                data = list(filter(select, data))
            events += data
            print(f"[centerOfPerformanceFeature] added {len(data)} events from {file}")

        # Filter out referee events
        events = filter(lambda x: x["playerId"] != 0, events)
        if select:
            events = filter(select, events)

        # Load players data and filter out goalkeepers
        players = json.load(open(players_file))
        goalkeepers_ids = {player["wyId"]: "GK" for player in players if player["role"]["name"] == "Goalkeeper"}
        events = filter(lambda x: x["playerId"] not in goalkeepers_ids, events)

        # Save player position in each event
        players_positions = defaultdict(lambda: defaultdict(list))
        for evt in events:
            if "positions" in evt:
                player = evt["playerId"]
                match = evt["matchId"]
                position = (evt["positions"][0]["x"], evt["positions"][0]["y"])
                players_positions[match][player].append(position)

        # Compute average position and number of events for each player in each match
        MIN_EVENTS = 10
        results = []

        for match, players_pos in players_positions.items():
            for p in players_pos:
                positions = players_pos[p]
                x, y, count = np.mean([x[0] for x in positions]), np.mean([x[1] for x in positions]), len(positions)
                if count > MIN_EVENTS:  # Only consider players with more than MIN_EVENTS events
                    documents = [
                        {"feature": "avg_x", "entity": p, "match": match, "value": int(x)},
                        {"feature": "avg_y", "entity": p, "match": match, "value": int(y)},
                        {"feature": "n_events", "entity": p, "match": match, "value": count},
                    ]
                    results += documents

        return results
