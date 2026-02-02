from collections import defaultdict

import pandas as pd

from .abstract import Aggregation


class plainAggregation(Aggregation):
    """
    Merge features for each player and return a DataFrame.

    `match -> team (or entity) -> feature (playerank, timestamp, team, etc..)`
    """

    def set_features(self, collection_list):
        self.collections = collection_list

    def get_features(self):
        return self.collections

    def set_aggregated_collection(self, collection):
        self.aggregated_collection = collection

    def get_aggregated_collection(self):
        return self.aggregated_collection

    def aggregate(self, to_dataframe: bool = False) -> list[dict[str, int | dict]] | pd.DataFrame:
        """
        Single stage: Transform aggregated feature per match into a collection of the form
        `match -> player -> {feature: value}`
        """
        # Merge all the features collections
        featdata = []
        for collection in self.collections:
            featdata += collection
            print(f"[plainAggregation] added {len(collection)} features")

        # Aggregate features per match and player
        aggregated = defaultdict(lambda: defaultdict(dict))
        for document in featdata:
            match = document["match"]
            entity = int(document["entity"])
            feature = document["feature"]
            value = document["value"]
            aggregated[match][entity].update({feature: value})

        # Prepare result as a list of JSON documents
        result = []
        for match in aggregated:
            for entity in aggregated[match]:
                document = {"match": match, "entity": entity}
                document.update(aggregated[match][entity])
                result.append(document)
        print(f"[plainAggregation] matches aggregated: {len(result)}")

        # Convert to DataFrame if required
        if to_dataframe:
            df = pd.DataFrame(result).fillna(0)
            return df
        else:
            return result
