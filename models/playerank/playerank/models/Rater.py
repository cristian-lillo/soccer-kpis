import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


class Rater:
    """
    Performance rating.

    Parameters
    ----------
    alpha_goal : float, default=0.0
        Importance of the goal in the evaluation of performance, in the range [0, 1].

    Attributes
    ----------
    ratings_ : numpy array
        Ratings of the performances.
    """

    def __init__(self, alpha_goal=0.0):
        self.alpha_goal = alpha_goal
        self.ratings_ = []

    def get_rating(self, weighted_sum: float, goals: float) -> float:
        return weighted_sum * (1 - self.alpha_goal) + self.alpha_goal * goals

    def predict(self, dataframe: pd.DataFrame, goal_feature: str, score_feature: str) -> np.ndarray:
        """
        Compute the rating of each performance in X.

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame of PlayeRank scores.
        goal_feature : str
            Column name for goal scored DataFrame column.
        score_feature : str
            Column name for playerank score DataFrame column.

        Returns
        -------
        ratings_ : numpy array
        """
        # Extract feature names and values
        feature_names = dataframe.columns
        X = dataframe.values

        # Get indices for goal and score features
        goal_index = feature_names.get_loc(goal_feature)
        pr_index = feature_names.get_loc(score_feature)

        # Compute ratings for each performance
        ratings = []
        for row in X:
            rating = self.get_rating(
                float(row[pr_index]),
                float(row[goal_index]),
            )
            ratings.append(rating)

        # Scale ratings to [0, 1] range
        self.ratings_ = MinMaxScaler().fit_transform(np.array(ratings).reshape(-1, 1))[:, 0]

        return self.ratings_
