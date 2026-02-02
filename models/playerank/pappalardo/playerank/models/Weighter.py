import json

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC


class Weighter(BaseEstimator):
    """
    Automatic weighting of performance features.

    Parameters
    ----------
    label_type : str, default: "w-dl"
        The label type associated to the game outcome.
        Options: w-dl (victory vs draw or defeat), wd-l (victory or draw vs defeat), w-d-l (victory, draw, defeat).

    random_state : int, RandomState instance or None, default: 42
        If int, random_state is the seed used by the random number generator;
        If RandomState instance, random_state is the random number generator;
        If None, the random number generator is the RandomState instance used by `np.random`.

    Attributes
    ----------
    feature_names_ : array, [n_features]
        Names of the features

    label_type_ : str, default: "w-dl"
        The label type associated to the game outcome.
        Options: w-dl (victory vs draw or defeat), wd-l (victory or draw vs defeat), w-d-l (victory, draw, defeat).

    clf_: LinearSVC object
        The object of the trained classifier.

    weights_ : array, [n_features]
        Weights of the features computed by the classifier.

    random_state_ : int, RandomState instance or None, optional, default: 42.
        If int, random_state is the seed used by the random number generator;
        If RandomState instance, random_state is the random number generator;
        If None, the random number generator is the RandomState instance used by `np.random`.
    """

    def __init__(self, label_type: str = "w-dl", random_state: int = 42):
        self.label_type_ = label_type
        self.random_state_ = random_state

    def fit(
        self,
        dataframe: pd.DataFrame,
        target: str,
        scaled: bool = False,
        var_threshold: float = 0.001,
        filename: str = "weights.json",
    ):
        """
        Compute weights of features.

        Parameters
        ----------
        dataframe : pandas DataFrame
            A dataframe containing the feature values and the target values.
        target : str
            A string indicating the name of the target variable in the DataFrame.
        scaled : boolean, default: False
            True if X must be normalized, False otherwise.
        filename : str, default: "weights.json"
            The name of the files to be saved (the json file containing the feature weights).
        """
        # Feature selection based on variance threshold
        sel = VarianceThreshold(var_threshold)
        X = sel.fit_transform(dataframe)

        # Get selected feature names
        feature_names = list(dataframe.columns)
        selected_feature_names = [feature_names[i] for i, var in enumerate(list(sel.variances_)) if var > var_threshold]

        # Print filtered features
        filtered_features = [
            (feature_names[i], var) for i, var in enumerate(list(sel.variances_)) if var <= var_threshold
        ]
        print("[Weighter] filtered features:")
        print(*filtered_features, sep="\n")

        # Create new dataframe with selected features
        dataframe = pd.DataFrame(X, columns=selected_feature_names)

        # Create labels based on label type
        if self.label_type_ == "w-dl":
            y = dataframe[target].apply(lambda x: 1 if x > 0 else -1)
        elif self.label_type_ == "wd-l":
            y = dataframe[target].apply(lambda x: 1 if x >= 0 else -1)
        else:
            y = dataframe[target].apply(lambda x: 1 if x > 0 else 0 if x == 0 else 2)

        X = dataframe.loc[:, dataframe.columns != target].values
        y = y.values

        if scaled:
            X = StandardScaler().fit_transform(X)

        self.feature_names_ = dataframe.loc[:, dataframe.columns != target].columns
        self.clf_ = LinearSVC(
            dual=False,
            fit_intercept=True,
            random_state=self.random_state_,
            max_iter=50000,
        )

        # f1_score = np.mean(cross_val_score(self.clf_, X, y, cv=2, scoring='f1_weighted'))
        # self.f1_score_ = f1_score

        self.clf_.fit(X, y)

        outcome = 0
        if self.label_type_ == "w-d-l":
            outcome = 1

        importances = self.clf_.coef_[outcome]
        sum_importances = sum(np.abs(importances))
        self.weights_ = importances / sum_importances

        # Save the computed weights into a json file
        features_and_weights = {}
        for feature, weight in sorted(zip(self.feature_names_, self.weights_), key=lambda x: x[1]):
            features_and_weights[feature] = weight

        json.dump(features_and_weights, open(f"{filename}", "w"), indent=2)

        # Save the object
        # pkl.dump(self, open(f"{filename}.pkl", "wb"))

    def get_weights(self):
        return self.weights_

    def get_feature_names(self):
        return self.feature_names_
