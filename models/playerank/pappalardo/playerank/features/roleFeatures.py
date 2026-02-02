import json
from collections import defaultdict

from .abstract import Feature


class roleFeatures(Feature):
    def set_features(self, collection_list):
        self.collections = collection_list

    def get_features(self):
        return self.collections

    def createFeature(self, matrix_role_file: str) -> list[dict]:
        """
        Given the matrix for roles, it computes the role of a player for each player and match.

        A role matrix is a data structure where, given x and y (between 0 and 100), it contains the corresponding roles for a player having center of performance = (x,y).

        Role_matrix is computed within the Learning Phase of the PlayeRank framework.

        Parameters:
            role_matrix: File patch for dictionary in the format `x -> y -> role`.
            feature_lists: Lists of features for each player in each match, describing players' average position.
        """
        # Load role matrix
        role_matrix = json.load(open(matrix_role_file, "r"))

        # Extract avg_x, avg_y and n_events for each player in each match
        roles = defaultdict(lambda: defaultdict(dict))
        for feature_list in self.get_features():
            for f in feature_list:
                roles[f["match"]][f["entity"]].update({f["feature"]: f["value"]})

        # Assign role based on avg_x and avg_y
        results = []
        for match in roles:
            for player in roles[match]:
                match_data = roles[match][player]
                role_label = role_matrix[str(match_data["avg_x"])][str(match_data["avg_y"])]
                document = {
                    "match": match,
                    "entity": player,
                    "feature": "roleCluster",
                    "value": role_label,
                }
                results.append(document)

        return results
