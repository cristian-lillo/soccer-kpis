import json
from collections import defaultdict

from .abstract import Feature


class playerankFeatures(Feature):
    """
    Given a method to aggregate features and the corresponding weight of each feature, it computes playerank for each player and match.

    Parameters:
        weights_file: Feature weights computed within learning phase of PlayeRank framework.

    Returns:
        A collection of JSON documents in the following format:
        ```
        {
            match: match_id,
            entity: player_id,
            feature: 'playerankScore',
            value: playerankScore (float)
        }
        ```
    """

    def set_features(self, collection_list):
        self.collections = collection_list

    def get_features(self):
        return self.collections

    def createFeature(self, weights_file: str) -> list[dict[str, str | int | float]]:
        # Load feature weights from JSON file
        weights = json.load(open(weights_file))

        # Compute PlayeRank scores for each player in a match
        playerank_scores = defaultdict(lambda: defaultdict(float))
        for feature_list in self.get_features():
            for f in feature_list:
                if f["feature"] in weights:  # Check if feature has a weight
                    playerank_scores[f["match"]][f["entity"]] += f["value"] * weights[f["feature"]]

        # Prepare result as a list of JSON documents
        result = []
        for match in playerank_scores:
            for player in playerank_scores[match]:
                document = {
                    "match": match,
                    "entity": player,
                    "feature": "playerankScore",
                    "value": float(playerank_scores[match][player]),
                }
                result.append(document)

        print(f"[playerankFeatures] playerank scores computed. {len(result)} performance processed")
        return result
