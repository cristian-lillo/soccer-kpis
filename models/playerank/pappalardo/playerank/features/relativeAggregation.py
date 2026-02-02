from collections import defaultdict

import pandas as pd

from .abstract import Aggregation


class relativeAggregation(Aggregation):
    """
    Compute relative feature for each match.

    `match -> team (or entity) -> featureTeam - featureOpponents`
    """

    def set_features(self, collection_list: list):
        self.collections = collection_list

    def get_features(self):
        return self.collections

    def aggregate(self, to_dataframe: bool = False) -> list[dict] | pd.DataFrame:
        """
        Compute relative aggregation: give a set of features it compute the A-B value for each entity in each team.

        This method is involved for feature weight estimation phase of playerank framework.

        Parameters:
            to_dataframe: Return a dataframe instead of a list of documents.

        Examples:
        ```
            passes for team A in match 111: 500
            passes for team B in match 111: 300
            lead to output: {'passes': 200}
        ```
        """
        featdata = []
        for collection in self.collections:
            featdata += collection
            print(f"[relativeAggregation] added {len(collection)} features")

        # Format of aggregation: match,team,feature,valueTeam-valueOppositor
        aggregated = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        for document in featdata:
            match = document["match"]
            entity = int(document["entity"])  # Selecting teamA and teamB as teams[0] and team[1]
            feature = document["feature"]
            value = document["value"]
            aggregated[match][entity][feature] = int(value)

        result = []
        for match in aggregated:
            for entity in aggregated[match]:
                for feature in aggregated[match][entity]:
                    opponents = [x for x in aggregated[match] if x != entity][0]

                    result_doc = {"match": match, "entity": entity, "name": feature}

                    value = aggregated[match][entity][feature]

                    if feature in aggregated[match][opponents]:
                        result_doc["value"] = value - aggregated[match][opponents][feature]
                    else:
                        result_doc["value"] = value

                    result.append(result_doc)

        if to_dataframe:
            featlist = defaultdict(dict)

            for data in result:
                featlist[f"{data['match']}-{data['entity']}"].update({data["name"]: data["value"]})

            print(f"[relativeAggregation] matches aggregated: {len(featlist.keys())}")

            df = pd.DataFrame(list(featlist.values())).fillna(0)
            return df
        else:
            return result
