import abc


class Feature(object):
    __metaclass__ = abc.ABCMeta
    """
    Class to wrap all the scripts/method to aggregate features from the database.
    """

    @abc.abstractmethod
    def createFeature(self, collectionName, param):
        """
        Method to define how a feature/set of features is computed.

        Features have to be stored into a collection of documents in the form:
        ```
        {
            _id: {
                match (numeric): Unique identifier of the match,
                name (string): Name of the feature,
                entity (string): Name of the entity target of the aggregation.
                                    It could be teamId, playerID, teamID + role or whatever significant for an aggregation
            },
            value (numeric): The count for the feature
        }
        ```

        Args:
            param: Contains eventual parameters for querying database competion, subset of teams, whatever.


        Returns:
            The name of the collection where the features have been stored.
        """
        return


class Aggregation(object):
    __metaclass__ = abc.ABCMeta
    """
    Defines the methods to aggregate one/more collection of features for each match.
    It has to provide results as a DataFrame.

    For example:
    It is used to compute relative feature for each match
    `match -> team (or entity) -> featureTeam - featureOppositor`
    """

    @property
    @abc.abstractmethod
    def get_features(self):
        """
        Return the list of feature collections to use.
        """
        return "Should never get here"

    @abc.abstractmethod
    def set_features(self, collection_list):
        """
        Set the list of collection to use for relative features computing.

        For example:
        We could have a collection of quality features, one for quantity features, one for goals scored etc.
        """
        return

    @abc.abstractmethod
    def aggregate(self):
        """
        Merge the collections of feature and aggregate by match and team, computing the relative value for each team.

        For example:
        `match -> team (or entity) -> featureTeam - featureOppositor`

        Returns a DataFrame.
        """
        return
