"""
VAEP Main Script
This script calculates VAEP values for soccer actions and aggregates them to compute player ratings.
"""

import warnings

import pandas as pd
import socceraction.vaep.features as fs
import socceraction.vaep.formula as vaep_formula
import socceraction.vaep.labels as lab
import xgboost as xgb
from socceraction import spadl
from socceraction.data.statsbomb import StatsBombLoader
from tqdm import tqdm

from config import paths, tournaments

warnings.filterwarnings("ignore")

SBL = StatsBombLoader(getter="local", root=str(paths.STATSBOMB_DIR))


def build_spadl_store(tournaments_list: list[dict]) -> None:
    """
    Builds the SPADL store for the specified tournaments and saves it to an HDF5 file.

    Args:
        tournaments_list: A list of dictionaries containing tournament information.
    """

    # Retrieve competitions and filter for the specified tournaments
    competitions_df = SBL.competitions()
    competition_name_list = [tournament["competition_name"] for tournament in tournaments_list]
    season_name_list = [tournament["season_name"] for tournament in tournaments_list]

    selected_competitions_df = competitions_df[
        (competitions_df["competition_name"].isin(competition_name_list))
        & (competitions_df["season_name"].isin(season_name_list))
    ]

    all_games_df = pd.concat(
        [
            SBL.games(
                int(tournament["competition_id"]),
                int(tournament["season_id"]),
            )
            for tournament in tournaments_list
        ]
    )
    all_teams_list = []
    all_players_list = []
    game_actions_dict = {}

    for game in tqdm(
        list(all_games_df.itertuples()),
        desc="Converting Game Events to SPADL Actions",
        ncols=150,
    ):
        all_teams_list.append(SBL.teams(game.game_id))  # type: ignore
        all_players_list.append(SBL.players(game.game_id))  # type: ignore
        game_events_df = SBL.events(game.game_id)  # type: ignore

        game_actions_dict[game.game_id] = spadl.statsbomb.convert_to_actions(
            game_events_df,
            home_team_id=game.home_team_id,  # type: ignore
            xy_fidelity_version=1,
            shot_fidelity_version=1,
        )

    all_teams_df = pd.concat(all_teams_list).drop_duplicates(subset="team_id")
    all_players_df = pd.concat(all_players_list)

    with pd.HDFStore(paths.SPADL_H5) as spadl_store:
        spadl_store["competitions"] = selected_competitions_df
        spadl_store["games"] = all_games_df
        spadl_store["teams"] = all_teams_df
        spadl_store["players"] = all_players_df[["player_id", "player_name", "nickname"]].drop_duplicates(
            subset="player_id"
        )
        spadl_store["player_games"] = all_players_df[
            [
                "player_id",
                "game_id",
                "team_id",
                "is_starter",
                "starting_position_id",
                "starting_position_name",
                "minutes_played",
            ]
        ]

        for game_id, game_actions in game_actions_dict.items():
            spadl_store[f"actions/game_{game_id}"] = game_actions


def generate_features(all_games_df: pd.DataFrame) -> None:
    """
    Generates features for the specified games and saves them to an HDF5 file.

    Args:
        all_games_df: A DataFrame containing information about the games for which to generate features.
    """
    x_fns = [
        fs.actiontype,
        fs.actiontype_onehot,
        fs.bodypart,
        fs.bodypart_onehot,
        fs.result,
        fs.result_onehot,
        fs.goalscore,
        fs.startlocation,
        fs.endlocation,
        fs.movement,
        fs.space_delta,
        fs.startpolar,
        fs.endpolar,
        fs.team,
        fs.time,
        fs.time_delta,
    ]

    with pd.HDFStore(paths.SPADL_H5) as spadl_store, pd.HDFStore(paths.FEATURES_H5) as feature_store:
        for game in tqdm(
            list(all_games_df.itertuples()),
            desc=f"Generating and storing features in {paths.FEATURES_H5}",
            ncols=150,
        ):
            game_actions = spadl_store[f"actions/game_{game.game_id}"]
            gamestates = fs.gamestates(spadl.add_names(game_actions), 3)  # type: ignore
            gamestates = fs.play_left_to_right(gamestates, game.home_team_id)  # type: ignore

            X = pd.concat([fn(gamestates) for fn in x_fns], axis=1)
            feature_store.put(f"game_{game.game_id}", X, format="table")


def generate_labels(all_games_df: pd.DataFrame) -> None:
    """
    Generates labels for the specified games and saves them to an HDF5 file.

    Args:
        all_games_df: A DataFrame containing information about the games for which to generate labels.
    """
    y_fns = [
        lab.scores,
        lab.concedes,
        lab.goal_from_shot,
    ]

    with pd.HDFStore(paths.SPADL_H5) as spadl_store, pd.HDFStore(paths.LABELS_H5) as label_store:
        for game in tqdm(
            list(all_games_df.itertuples()),
            desc=f"Computing and storing labels in {paths.LABELS_H5}",
            ncols=150,
        ):
            game_actions = spadl_store[f"actions/game_{game.game_id}"]

            Y = pd.concat([fn(spadl.add_names(game_actions)) for fn in y_fns], axis=1)  # type: ignore
            label_store.put(f"game_{game.game_id}", Y, format="table")


def get_X_and_Y(train_games_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Gets the features and labels for the specified games.

    Args:
        train_games_df: A DataFrame containing information about the games for which to get features and labels.

    Returns:
        A tuple of (features, labels).
    """
    # Get the features for all games
    x_fns = [
        fs.actiontype,
        fs.actiontype_onehot,
        # fs.bodypart,
        fs.bodypart_onehot,
        fs.result,
        fs.result_onehot,
        fs.goalscore,
        fs.startlocation,
        fs.endlocation,
        fs.movement,
        fs.space_delta,
        fs.startpolar,
        fs.endpolar,
        fs.team,
        # fs.time,
        fs.time_delta,
        # fs.actiontype_result_onehot,
    ]
    x_cols = fs.feature_column_names(x_fns, nb_prev_actions=1)
    x_list = []

    for game_id in tqdm(train_games_df.game_id, desc="Selecting features", ncols=150):
        x_i = pd.read_hdf(paths.FEATURES_H5, f"game_{game_id}")
        x_list.append(x_i[x_cols])

    X = pd.concat(x_list).reset_index(drop=True)

    # Get the labels for all games
    y_cols = ["scores", "concedes"]
    y_list = []

    for game_id in tqdm(train_games_df.game_id, desc="Selecting labels", ncols=150):
        y_i = pd.read_hdf(paths.LABELS_H5, f"game_{game_id}")
        y_list.append(y_i[y_cols])

    Y = pd.concat(y_list).reset_index(drop=True)

    return X, Y


def train_models(x: pd.DataFrame, y: pd.DataFrame) -> dict[str, xgb.XGBClassifier]:
    """
    Trains a separate XGBoost classifier for scoring and conceding.

    Args:
        x: The features.
        y: The labels.

    Returns:
        A dictionary of trained XGBoost classifiers.
    """
    params = {"n_estimators": 50, "max_depth": 3, "n_jobs": -1, "verbosity": 1, "enable_categorical": True}
    models: dict[str, xgb.XGBClassifier] = {}

    for col in y.columns:
        model = xgb.XGBClassifier(**params)
        model.fit(x, y[col])
        models[col] = model

    return models


def evaluate_models(
    models: dict[str, xgb.XGBClassifier],
    test_x: pd.DataFrame,
    test_y: pd.Series,
) -> pd.DataFrame:
    """
    Evaluates the model using log loss and prints the result.

    Args:
        models: A dictionary of trained XGBoost classifiers.
        test_x: The test features.
        test_y: The test labels.
    """
    y_hat = pd.DataFrame()

    # def evaluate(y, y_hat):
    #     p = sum(y) / len(y)
    #     base = [p] * len(y)
    #     brier = brier_score_loss(y, y_hat)
    #     print(f"  Brier score: {brier:.5f} ({brier / brier_score_loss(y, base):.5f})")
    #     ll = log_loss(y, y_hat)
    #     print(f"  Log Loss score: {ll:.5f} ({ll / log_loss(y, base):.5f})")
    #     print(f"  ROC AUC: {roc_auc_score(y, y_hat):.5f}")

    for col in test_y.columns:
        y_hat[col] = [p[1] for p in models[col].predict_proba(test_x)]
        # evaluate(test_y[col], y_hat[col])

    return y_hat


def save_models_predictions(
    all_games_df: pd.DataFrame,
    y_hat: pd.DataFrame,
) -> None:
    """
    Saves the predictions for each game to an HDF5 file.

    Args:
        all_games_df: A DataFrame containing information about the games for which to save predictions.
        y_hat: A DataFrame containing the predicted probabilities for each game.
    """
    # Get the game_id for each action in the all_games_df
    all_actions_list = []

    for game_id in tqdm(all_games_df.game_id, "Loading game ids"):
        a_i = pd.read_hdf(paths.SPADL_H5, f"actions/game_{game_id}")
        all_actions_list.append(a_i[["game_id"]])

    all_actions_df = pd.concat(all_actions_list).reset_index(drop=True)

    # Group the predictions by game_id and save them to an HDF5 file
    grouped_predictions = pd.concat(
        [all_actions_df, y_hat],
        axis=1,
    ).groupby("game_id")

    with pd.HDFStore(paths.PREDICTIONS_H5) as prediction_store:
        for game_id, df in tqdm(grouped_predictions, desc="Saving predictions per game"):
            df = df.reset_index(drop=True)
            prediction_store.put(f"game_{int(game_id)}", df[y_hat.columns])


def calculate_actions_vaep_values() -> pd.DataFrame:
    with pd.HDFStore(paths.SPADL_H5) as spadl_store:
        games_df = (
            spadl_store["games"]
            .merge(spadl_store["competitions"], how="left")
            .merge(spadl_store["teams"].add_prefix("home_"), how="left")
            .merge(spadl_store["teams"].add_prefix("away_"), how="left")
        )
        players_df = spadl_store["players"]
        teams_df = spadl_store["teams"]

    vaep_list = []

    for game in tqdm(list(games_df.itertuples()), desc="Rating actions"):
        actions_df = pd.read_hdf(paths.SPADL_H5, f"actions/game_{game.game_id}")
        actions_df = (
            spadl.add_names(actions_df)  # type: ignore
            .merge(players_df, how="left")
            .merge(teams_df, how="left")
            .sort_values(["game_id", "period_id", "action_id"])
            .reset_index(drop=True)
        )
        predictions_df = pd.read_hdf(paths.PREDICTIONS_H5, f"game_{game.game_id}")
        value_df = vaep_formula.value(actions_df, predictions_df.scores, predictions_df.concedes)  # type: ignore
        vaep_list.append(pd.concat([actions_df, predictions_df, value_df], axis=1))

    vaep_df = (
        pd.concat(vaep_list)
        .sort_values(
            [
                "game_id",
                "period_id",
                "time_seconds",
            ]
        )
        .reset_index(drop=True)
    )

    return vaep_df


def get_match_vaep_values(match_id: int, actions_vaep_df: pd.DataFrame) -> pd.DataFrame:
    """
    Obtain VAEP values for all players in a given match.

    Args:
        match_id: StatsBomb match ID.
        actions_vaep_df: A DataFrame containing VAEP values for all actions.

    Returns:
        DataFrame containing VAEP values for each player in the match.
    """
    # Filter the actions_vaep_df for the specified match_id
    game_actions_vaep_df = actions_vaep_df[actions_vaep_df["game_id"] == match_id]

    # Add a count column and sum the VAEP values for each player
    game_actions_vaep_df["n_actions"] = 1
    players_vaep_df = (
        game_actions_vaep_df[
            [
                "player_id",
                "player_name",
                "nickname",
                "team_name",
                "vaep_value",
                "offensive_value",
                "defensive_value",
                "n_actions",
            ]
        ]
        .groupby("player_id", as_index=False)
        .agg(
            {
                "player_name": "first",
                "nickname": "first",
                "team_name": "first",
                "vaep_value": "sum",
                "offensive_value": "sum",
                "defensive_value": "sum",
                "n_actions": "sum",
            }
        )
        .reset_index(drop=True)
    )

    # Add minutes played for each player in the match
    game_players_df = SBL.players(game_id=match_id)
    player_metrics_df = players_vaep_df.merge(
        game_players_df[["player_id", "minutes_played"]],
        how="left",
        on="player_id",
    )

    # Replace player_name with nickname if nickname is available and not empty
    player_metrics_df["player_name"] = player_metrics_df["nickname"].where(
        player_metrics_df["nickname"].notna() & (player_metrics_df["nickname"].astype(str) != ""),
        player_metrics_df["player_name"],
    )
    player_metrics_df = player_metrics_df.rename(columns={"player_name": "player", "team_name": "team"})
    player_metrics_df = player_metrics_df.drop(columns=["player_id", "nickname"])

    # Add rank column based on VAEP value
    player_metrics_df = player_metrics_df.sort_values("vaep_value", ascending=False).reset_index(drop=True)
    player_metrics_df.insert(0, "rank", range(1, len(player_metrics_df) + 1))

    return player_metrics_df


def get_tournament_vaep_values(tournament: dict, actions_vaep_df: pd.DataFrame) -> pd.DataFrame:
    """
    Obtain VAEP values for all players in a given tournament.

    Args:
        tournament: A dictionary containing competition and season IDs.
        actions_vaep_df: A DataFrame containing VAEP values for all actions.

    Returns:
        DataFrame containing VAEP values for each player in the tournament.
    """
    # Get all match IDs for the tournament
    match_ids = tournaments.get_all_match_ids(tournament)

    # Initialize empty DataFrame to store tournament VAEP values
    all_matches_vaep_df = pd.DataFrame(
        columns=[
            "rank",
            "player",
            "team",
            "vaep_value",
            "offensive_value",
            "defensive_value",
            "n_actions",
            "minutes_played",
        ]
    )

    # Calculate VAEP values for each match and concatenate results
    for match_id in tqdm(match_ids, desc=f"Calculating VAEP values for matches in {tournament['label']}", ncols=150):
        match_vaep_df = get_match_vaep_values(match_id, actions_vaep_df)

        # Save match VAEP values to CSV
        match_filename = paths.VAEP_OUTPUT_DIR / tournament["label"] / f"match_{match_id}_vaep_values.csv"
        match_vaep_df.to_csv(match_filename, index=False)

        # Combine match VAEP values into all matches DataFrame
        if all_matches_vaep_df.empty:
            all_matches_vaep_df = match_vaep_df
        else:
            all_matches_vaep_df = pd.concat(
                [all_matches_vaep_df, match_vaep_df],
                ignore_index=True,
            )

    # Aggregate VAEP values for players across all matches in the tournament
    tournament_vaep_df = (
        all_matches_vaep_df.groupby(
            ["player", "team"],
            as_index=False,
        )
        .agg(
            {
                "vaep_value": "sum",
                "offensive_value": "sum",
                "defensive_value": "sum",
                "n_actions": "sum",
                "minutes_played": "sum",
            }
        )
        .sort_values("vaep_value", ascending=False)
        .reset_index(drop=True)
    )

    # Add rank column
    tournament_vaep_df.insert(0, "rank", range(1, len(tournament_vaep_df) + 1))

    # Add matches played column
    player_team_counts = all_matches_vaep_df.value_counts(["player", "team"]).reset_index(name="matches_played")
    tournament_vaep_df = pd.merge(tournament_vaep_df, player_team_counts, how="left", on=["player", "team"])

    # Save tournament VAEP values to CSV
    tournament_filename = paths.VAEP_OUTPUT_DIR / f"{tournament['label']}_vaep_values.csv"
    tournament_vaep_df.to_csv(tournament_filename, index=False)

    return tournament_vaep_df


def main():
    # build_spadl_store(tournaments.ALL_TOURNAMENTS)

    # all_games_df = pd.read_hdf(paths.SPADL_H5, "games")

    # generate_features(all_games_df)  # type: ignore
    # generate_labels(all_games_df)  # type: ignore

    # train_games_df = all_games_df  # For now, using all data for training
    # X, Y = get_X_and_Y(train_games_df)  # type: ignore
    # models = train_models(X, Y)

    # test_x, test_y = X, Y # For now, using the same data for testing
    # y_hat = evaluate_models(models, test_x, test_y)  # type: ignore

    # save_models_predictions(all_games_df, y_hat)

    actions_vaep_df = calculate_actions_vaep_values()

    # Calculate VAEP values for National Team Tournaments
    for tournament in tqdm(
        tournaments.NATIONAL_TEAM_TOURNAMENTS,
        desc="Processing National Team Tournaments",
        ncols=150,
    ):
        get_tournament_vaep_values(tournament, actions_vaep_df)

    # Calculate VAEP values for European Club Leagues
    for tournament in tqdm(
        tournaments.EUROPEAN_CLUB_LEAGUES,
        desc="Processing European Club Leagues",
        ncols=150,
    ):
        get_tournament_vaep_values(tournament, actions_vaep_df)


if __name__ == "__main__":
    main()
