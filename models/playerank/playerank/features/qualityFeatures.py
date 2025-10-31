import glob
import json
from collections import defaultdict
from collections.abc import Callable

from .abstract import Feature
from .wyscoutEventsDefinition import tag2name


class qualityFeatures(Feature):
    """
    Quality features are the count of events with outcomes.

    For example:
    - Number of accurate passes
    - Number of wrong passes
    - ...
    """

    def createFeature(
        self,
        events_path: str,
        players_file: str,
        entity: str = "team",
        select: Callable[[dict], bool] | None = None,
    ):
        """
        Compute qualityFeatures.

        Parameters:
            events_path: File path of events file.
            entity: It could be either 'team' or 'player'. It selects the aggregation for qualityFeatures among teams or players.
            select: Function for filtering events collection. Default: Aggregate over all events.

        Returns:
            A list of dictionaries in the format `matchId -> entity -> feature -> value`.
        """
        event2subevent2outcome = {
            1: {  # Duel
                10: [1801, 1802],
                11: [1801, 1802],
                12: [1801, 1802],
                13: [1801, 1802],
            },
            2: [1702, 1703, 1701],  # Foul
            3: {  # Free kick
                30: [1801, 1802],
                31: [1801, 1802],
                32: [1801, 1802],
                33: [1801, 1802],
                34: [1801, 1802],
                35: [1802],
                36: [1801, 1802],
            },
            4: {40: [1801, 1802]},  # Goalkeeper leaving line
            6: {60: []},  # Offside
            7: {  # Others on the ball
                70: [1801, 1802, 101],
                71: [1801, 1802, 101],
                72: [1401, 1302, 201, 1901, 1301, 2001, 301],
            },
            8: {  # Pass
                80: [1801, 1802, 302, 301],
                81: [1801, 1802, 302, 301],
                82: [1801, 1802, 302, 301],
                83: [1801, 1802, 302, 301],
                84: [1801, 1802, 302, 301],
                85: [1801, 1802, 302, 301],
                86: [1801, 1802, 302, 301],
            },
            # 9: {  # Save attempt
            #     90: [1801, 1802],
            #     91: [1801, 1802],
            # },
            10: {100: [1801, 1802]},  # Shot
        }

        # Load players to identify goalkeepers
        players = json.load(open(players_file))
        goalkeepers_ids = [player["wyId"] for player in players if player["role"]["name"] == "Goalkeeper"]

        # Process events
        events = []
        for file in glob.glob(f"{events_path}"):
            data = json.load(open(file))
            if select:
                data = list(filter(select, data))

            # Excluding penalties events and goalkeeper events
            events += list(
                filter(lambda x: x["matchPeriod"] in ["1H", "2H"] and x["playerId"] not in goalkeepers_ids, data)
            )
            print(f"[qualityFeatures] added {len(data)} events from {file}")

        aggregated_features = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for evt in events:
            if evt["eventId"] in event2subevent2outcome:
                evtName = evt["eventName"]

                # Hierarchy as event->subevent->tags
                if isinstance(event2subevent2outcome[evt["eventId"]], dict):
                    if evt["subEventId"] not in event2subevent2outcome[evt["eventId"]]:
                        continue  # Skip malformed events

                    evtName += "-" + evt['subEventName']
                    tags = [
                        x for x in evt["tags"] if x["id"] in event2subevent2outcome[evt["eventId"]][evt["subEventId"]]
                    ]
                else:  # Hierarchy as event->tags
                    tags = [x for x in evt["tags"] if x["id"] in event2subevent2outcome[evt["eventId"]]]

                # Select entity type
                if entity == "player":
                    ent = evt["playerId"]
                else:  # entity == "team"
                    ent = evt["teamId"]

                # Aggregate features
                if len(tags) > 0:
                    for tag in tags:
                        aggregated_features[evt["matchId"]][ent][f"{evtName}-{tag2name[tag['id']]}"] += 1

                else:
                    aggregated_features[evt["matchId"]][ent][f"{evtName}"] += 1

        result = []
        for match in aggregated_features:
            for entity in aggregated_features[match]:
                for feature in aggregated_features[match][entity]:
                    document = {}
                    document["match"] = match
                    document["entity"] = entity
                    document["feature"] = feature
                    document["value"] = aggregated_features[match][entity][feature]
                    result.append(document)

        return result
