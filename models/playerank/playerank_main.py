# Save ratings to output folder

import pandas as pd
from tqdm import tqdm

from config import paths, players, tournaments


def split_feature_name(feature: str) -> pd.Series:
    """Split feature into event / subevent / tag using capitalization rules."""
    if feature == "goal-scored":
        return pd.Series({"event": "Shot", "subevent": "Shot", "tag": "accurate"})

    parts = feature.split("-")
    event = parts[0]
    subevent = ""
    tag = ""

    if len(parts) > 1:
        if parts[1] and parts[1][0].isupper():
            subevent = parts[1]
            if len(parts) > 2:
                tag = parts[2]
        else:
            tag = parts[1]

    return pd.Series({"event": event, "subevent": subevent, "tag": tag})


def load_feature_weights(feature_weights_filename: str = "feature_weights.json") -> pd.DataFrame:
    """Load feature weights from a JSON file and split the feature names into event, subevent, and tag."""
    feature_weights_filepath = paths.PLAYERANK_DIR / feature_weights_filename
    feature_weights_df = (
        pd.read_json(feature_weights_filepath, typ="series").rename_axis("feature").reset_index(name="weight")
    )

    feature_parts = feature_weights_df["feature"].apply(split_feature_name)
    feature_weights_df = pd.concat(
        [feature_parts, feature_weights_df[["weight"]]],
        axis=1,
        sort=True,
    )

    return feature_weights_df


def extract_player_metrics(
    match_events_df: pd.DataFrame,
    player_info_df: pd.DataFrame,
) -> dict[str, dict[str, str | int]]:
    """Extract player metrics: team, position, minutes played and event counts for each player in the match.

    Args:
        match_events_df: DataFrame containing all events in the match.
        player_info_df: DataFrame containing player information.

    Returns:
        A dictionary mapping player nicknames to their metrics.
    """

    # Initialize dictionary to hold player metrics
    player_metrics = {}

    # Map player names to their teams and minutes played for quick access
    nickname_mapping = dict(zip(player_info_df["player_name"], player_info_df["nickname"]))
    team_mapping = dict(zip(player_info_df["player_name"], player_info_df["team_name"]))
    minutes_mapping = dict(zip(player_info_df["player_name"], player_info_df["minutes_played"]))

    for player_name in match_events_df["player"].unique():
        player_events_df = match_events_df.loc[match_events_df["player"] == player_name]

        # Use nickname, team and minutes mappings
        player_nickname = nickname_mapping[player_name] or player_name
        player_team = team_mapping[player_name]
        player_minutes = minutes_mapping[player_name]

        # Duel metrics
        duel_aerial_success = len(
            player_events_df.loc[
                (player_events_df["event_type"] == "DUEL")
                & (player_events_df["duel_type"] == "AERIAL")
                & (player_events_df["success"])
            ]
        )
        duel_aerial_failure = len(
            player_events_df.loc[
                (player_events_df["event_type"] == "DUEL")
                & (player_events_df["duel_type"] == "AERIAL")
                & (~player_events_df["success"])
            ]
        )
        duel_ground_success = len(
            player_events_df.loc[
                (player_events_df["event_type"] == "DUEL")
                & (player_events_df["duel_type"].isin(["GROUND", "SLIDING_TACKLE"]))
                & (player_events_df["success"])
            ]
        )
        duel_ground_failure = len(
            player_events_df.loc[
                (player_events_df["event_type"] == "DUEL")
                & (player_events_df["duel_type"].isin(["GROUND", "SLIDING_TACKLE"]))
                & (~player_events_df["success"])
            ]
        )
        duel_loose_ball_success = len(
            player_events_df.loc[
                (player_events_df["event_type"] == "DUEL")
                & (player_events_df["duel_type"] == "LOOSE_BALL")
                & (player_events_df["success"])
            ]
        )
        duel_loose_ball_failure = len(
            player_events_df.loc[
                (player_events_df["event_type"] == "DUEL")
                & (player_events_df["duel_type"] == "LOOSE_BALL")
                & (~player_events_df["success"])
            ]
        )

        # Foul metrics
        foul_committed = len(player_events_df.loc[player_events_df["event_type"] == "FOUL_COMMITTED"])
        foul_commited_first_yellow = len(
            player_events_df.loc[
                (player_events_df["event_type"] == "FOUL_COMMITTED") & (player_events_df["card_type"] == "FIRST_YELLOW")
            ]
        )
        foul_commited_second_yellow = len(
            player_events_df.loc[
                (player_events_df["event_type"] == "FOUL_COMMITTED")
                & (player_events_df["card_type"] == "SECOND_YELLOW")
            ]
        )
        foul_commited_red = len(
            player_events_df.loc[
                (player_events_df["event_type"] == "FOUL_COMMITTED") & (player_events_df["card_type"] == "RED")
            ]
        )

        # Set piece metrics
        corner_kick_success = len(
            player_events_df.loc[(player_events_df["set_piece_type"] == "CORNER_KICK") & (player_events_df["success"])]
        )
        corner_kick_failure = len(
            player_events_df.loc[(player_events_df["set_piece_type"] == "CORNER_KICK") & (~player_events_df["success"])]
        )
        free_kick_success = len(
            player_events_df.loc[(player_events_df["set_piece_type"] == "FREE_KICK") & (player_events_df["success"])]
        )
        free_kick_failure = len(
            player_events_df.loc[(player_events_df["set_piece_type"] == "FREE_KICK") & (~player_events_df["success"])]
        )
        free_kick_pass_success = len(
            player_events_df.loc[
                (player_events_df["set_piece_type"] == "FREE_KICK")
                & (player_events_df["event_type"] == "PASS")
                & (player_events_df["success"])
            ]
        )
        free_kick_pass_failure = len(
            player_events_df.loc[
                (player_events_df["set_piece_type"] == "FREE_KICK")
                & (player_events_df["event_type"] == "PASS")
                & (~player_events_df["success"])
            ]
        )
        free_kick_shot_success = len(
            player_events_df.loc[
                (player_events_df["set_piece_type"] == "FREE_KICK")
                & (player_events_df["event_type"] == "SHOT")
                & (player_events_df["success"])
            ]
        )
        free_kick_shot_failure = len(
            player_events_df.loc[
                (player_events_df["set_piece_type"] == "FREE_KICK")
                & (player_events_df["event_type"] == "SHOT")
                & (~player_events_df["success"])
            ]
        )
        goal_kick = len(player_events_df.loc[player_events_df["set_piece_type"] == "GOAL_KICK"])
        penalty = len(player_events_df.loc[(player_events_df["set_piece_type"] == "PENALTY")])
        penalty_failure = len(
            player_events_df.loc[(player_events_df["set_piece_type"] == "PENALTY") & (~player_events_df["success"])]
        )
        throw_in_success = len(
            player_events_df.loc[(player_events_df["set_piece_type"] == "THROW_IN") & (player_events_df["success"])]
        )
        throw_in_failure = len(
            player_events_df.loc[(player_events_df["set_piece_type"] == "THROW_IN") & (~player_events_df["success"])]
        )

        # Carry, clearance, counter-attack and interception metrics
        carry_success = len(
            player_events_df.loc[(player_events_df["event_type"] == "CARRY") & (player_events_df["success"])]
        )
        carry_failure = len(
            player_events_df.loc[(player_events_df["event_type"] == "CARRY") & (~player_events_df["success"])]
        )
        clearance = len(player_events_df.loc[player_events_df["event_type"] == "CLEARANCE"])
        clearance_success = len(
            player_events_df.loc[(player_events_df["event_type"] == "CLEARANCE") & (player_events_df["success"])]
        )
        clearance_failure = len(
            player_events_df.loc[(player_events_df["event_type"] == "CLEARANCE") & (~player_events_df["success"])]
        )
        counter_attack = len(player_events_df.loc[player_events_df["is_counter_attack"]])
        interception = len(player_events_df.loc[player_events_df["event_type"] == "INTERCEPTION"])

        # Pass metrics
        cross_success = len(
            player_events_df.loc[(player_events_df["pass_type"] == "CROSS") & (player_events_df["success"])]
        )
        cross_failure = len(
            player_events_df.loc[(player_events_df["pass_type"] == "CROSS") & (~player_events_df["success"])]
        )
        head_pass_success = len(
            player_events_df.loc[(player_events_df["pass_type"] == "HEAD_PASS") & (player_events_df["success"])]
        )
        head_pass_failure = len(
            player_events_df.loc[(player_events_df["pass_type"] == "HEAD_PASS") & (~player_events_df["success"])]
        )
        high_pass_success = len(
            player_events_df.loc[(player_events_df["pass_type"] == "HIGH_PASS") & (player_events_df["success"])]
        )
        high_pass_failure = len(
            player_events_df.loc[(player_events_df["pass_type"] == "HIGH_PASS") & (~player_events_df["success"])]
        )
        launch_success = len(
            player_events_df.loc[(player_events_df["pass_type"] == "LAUNCH") & (player_events_df["success"])]
        )
        launch_failure = len(
            player_events_df.loc[(player_events_df["pass_type"] == "LAUNCH") & (~player_events_df["success"])]
        )
        simple_pass_success = len(
            player_events_df.loc[(player_events_df["pass_type"] == "SIMPLE_PASS") & (player_events_df["success"])]
        )
        simple_pass_failure = len(
            player_events_df.loc[(player_events_df["pass_type"] == "SIMPLE_PASS") & (~player_events_df["success"])]
        )
        smart_pass_success = len(
            player_events_df.loc[(player_events_df["pass_type"] == "SMART_PASS") & (player_events_df["success"])]
        )
        smart_pass_failure = len(
            player_events_df.loc[(player_events_df["pass_type"] == "SMART_PASS") & (~player_events_df["success"])]
        )

        # Shot metrics
        shot_success = len(
            player_events_df.loc[(player_events_df["event_type"] == "SHOT") & (player_events_df["success"])]
        )
        shot_failure = len(
            player_events_df.loc[(player_events_df["event_type"] == "SHOT") & (~player_events_df["success"])]
        )

        player_metrics[player_nickname] = {
            "team": player_team,
            "minutes_played": player_minutes,
            "duel_aerial_success": duel_aerial_success,
            "duel_aerial_failure": duel_aerial_failure,
            "duel_ground_success": duel_ground_success,
            "duel_ground_failure": duel_ground_failure,
            "duel_loose_ball_success": duel_loose_ball_success,
            "duel_loose_ball_failure": duel_loose_ball_failure,
            "foul_committed": foul_committed,
            "foul_commited_first_yellow": foul_commited_first_yellow,
            "foul_commited_second_yellow": foul_commited_second_yellow,
            "foul_commited_red": foul_commited_red,
            "corner_kick_success": corner_kick_success,
            "corner_kick_failure": corner_kick_failure,
            "free_kick_success": free_kick_success,
            "free_kick_failure": free_kick_failure,
            "free_kick_pass_success": free_kick_pass_success,
            "free_kick_pass_failure": free_kick_pass_failure,
            "free_kick_shot_success": free_kick_shot_success,
            "free_kick_shot_failure": free_kick_shot_failure,
            "goal_kick": goal_kick,
            "penalty": penalty,
            "penalty_failure": penalty_failure,
            "throw_in_success": throw_in_success,
            "throw_in_failure": throw_in_failure,
            "carry_success": carry_success,
            "carry_failure": carry_failure,
            "clearance": clearance,
            "clearance_success": clearance_success,
            "clearance_failure": clearance_failure,
            "counter_attack": counter_attack,
            "interception": interception,
            "cross_success": cross_success,
            "cross_failure": cross_failure,
            "head_pass_success": head_pass_success,
            "head_pass_failure": head_pass_failure,
            "high_pass_success": high_pass_success,
            "high_pass_failure": high_pass_failure,
            "launch_success": launch_success,
            "launch_failure": launch_failure,
            "simple_pass_success": simple_pass_success,
            "simple_pass_failure": simple_pass_failure,
            "smart_pass_success": smart_pass_success,
            "smart_pass_failure": smart_pass_failure,
            "shot_success": shot_success,
            "shot_failure": shot_failure,
        }

    return player_metrics


def calculate_playerank_scores(
    player_metrics: dict[str, dict[str, str | int]],
    feature_weights_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate Playerank scores for each player based on their metrics and feature weights.

    Args:
        player_metrics: A dictionary mapping player nicknames to their metrics.
        feature_weights_df: A DataFrame containing feature weights.

    Returns:
        A DataFrame containing the Playerank scores for each player.
    """
    playerank_list = []

    for player, metrics in player_metrics.items():
        playerank_score = (
            (
                metrics["duel_aerial_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Duel")
                    & (feature_weights_df["subevent"] == "Air duel")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["duel_aerial_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Duel")
                    & (feature_weights_df["subevent"] == "Air duel")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["duel_ground_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Duel")
                    & (feature_weights_df["subevent"].isin(["Ground attacking duel", "Ground defending duel"]))
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["duel_ground_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Duel")
                    & (feature_weights_df["subevent"].isin(["Ground attacking duel", "Ground defending duel"]))
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["duel_loose_ball_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Duel")
                    & (feature_weights_df["subevent"] == "Ground loose ball duel")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["duel_loose_ball_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Duel")
                    & (feature_weights_df["subevent"] == "Ground loose ball duel")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["foul_committed"]
                * feature_weights_df.loc[
                    feature_weights_df["event"] == "Foul",
                    "weight",
                ].sum()
            )
            + (
                metrics["foul_commited_first_yellow"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Foul") & (feature_weights_df["tag"] == "yellow card"),
                    "weight",
                ].sum()
            )
            + (
                metrics["foul_commited_second_yellow"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Foul") & (feature_weights_df["tag"] == "second yellow card"),
                    "weight",
                ].sum()
            )
            + (
                metrics["foul_commited_red"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Foul") & (feature_weights_df["tag"] == "red card"),
                    "weight",
                ].sum()
            )
            + (
                metrics["corner_kick_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Corner")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["corner_kick_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Corner")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["free_kick_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Free Kick")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["free_kick_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Free Kick")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["free_kick_pass_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Free kick cross")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["free_kick_pass_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Free kick cross")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["free_kick_shot_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Free kick shot")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["free_kick_shot_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Free kick shot")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["goal_kick"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick") & (feature_weights_df["subevent"] == "Goal kick"),
                    "weight",
                ].sum()
            )
            + (
                metrics["penalty"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick") & (feature_weights_df["subevent"] == "Penalty"),
                    "weight",
                ].sum()
            )
            + (
                metrics["penalty_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Penalty")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["throw_in_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Throw in")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["throw_in_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Free Kick")
                    & (feature_weights_df["subevent"] == "Throw in")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["carry_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Others on the ball")
                    & (feature_weights_df["subevent"] == "Acceleration")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["carry_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Others on the ball")
                    & (feature_weights_df["subevent"] == "Acceleration")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["clearance"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Others on the ball")
                    & (feature_weights_df["subevent"] == "Clearance"),
                    "weight",
                ].sum()
            )
            + (
                metrics["clearance_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Others on the ball")
                    & (feature_weights_df["subevent"] == "Clearance")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["clearance_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Others on the ball")
                    & (feature_weights_df["subevent"] == "Clearance")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["counter_attack"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Others on the ball")
                    & (feature_weights_df["subevent"] == "Touch")
                    & (feature_weights_df["tag"] == "counter attack"),
                    "weight",
                ].sum()
            )
            + (
                metrics["interception"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Others on the ball")
                    & (feature_weights_df["subevent"] == "Touch")
                    & (feature_weights_df["tag"] == "interception"),
                    "weight",
                ].sum()
            )
            + (
                metrics["cross_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "Cross")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["cross_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "Cross")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["head_pass_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "Head pass")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["head_pass_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "Head pass")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["high_pass_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "High pass")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["high_pass_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "High pass")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["launch_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "Launch")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["launch_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "Launch")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["simple_pass_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "Simple pass")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["simple_pass_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "Simple pass")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["smart_pass_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "Smart pass")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["smart_pass_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Pass")
                    & (feature_weights_df["subevent"] == "Smart pass")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["shot_success"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Shot")
                    & (feature_weights_df["subevent"] == "Shot")
                    & (feature_weights_df["tag"] == "accurate"),
                    "weight",
                ].sum()
            )
            + (
                metrics["shot_failure"]
                * feature_weights_df.loc[
                    (feature_weights_df["event"] == "Shot")
                    & (feature_weights_df["subevent"] == "Shot")
                    & (feature_weights_df["tag"] == "not accurate"),
                    "weight",
                ].sum()
            )
        )

        playerank_list.append(
            {
                "player": player,
                "team": metrics["team"],
                "playerank_score": playerank_score,
                "minutes_played": metrics["minutes_played"],
                "duel_aerial_success": metrics["duel_aerial_success"],
                "duel_aerial_failure": metrics["duel_aerial_failure"],
                "duel_ground_success": metrics["duel_ground_success"],
                "duel_ground_failure": metrics["duel_ground_failure"],
                "duel_loose_ball_success": metrics["duel_loose_ball_success"],
                "duel_loose_ball_failure": metrics["duel_loose_ball_failure"],
                "foul_committed": metrics["foul_committed"],
                "foul_commited_first_yellow": metrics["foul_commited_first_yellow"],
                "foul_commited_second_yellow": metrics["foul_commited_second_yellow"],
                "foul_commited_red": metrics["foul_commited_red"],
                "corner_kick_success": metrics["corner_kick_success"],
                "corner_kick_failure": metrics["corner_kick_failure"],
                "free_kick_success": metrics["free_kick_success"],
                "free_kick_failure": metrics["free_kick_failure"],
                "free_kick_pass_success": metrics["free_kick_pass_success"],
                "free_kick_pass_failure": metrics["free_kick_pass_failure"],
                "free_kick_shot_success": metrics["free_kick_shot_success"],
                "free_kick_shot_failure": metrics["free_kick_shot_failure"],
                "goal_kick": metrics["goal_kick"],
                "penalty": metrics["penalty"],
                "penalty_failure": metrics["penalty_failure"],
                "throw_in_success": metrics["throw_in_success"],
                "throw_in_failure": metrics["throw_in_failure"],
                "carry_success": metrics["carry_success"],
                "carry_failure": metrics["carry_failure"],
                "clearance": metrics["clearance"],
                "clearance_success": metrics["clearance_success"],
                "clearance_failure": metrics["clearance_failure"],
                "counter_attack": metrics["counter_attack"],
                "interception": metrics["interception"],
                "cross_success": metrics["cross_success"],
                "cross_failure": metrics["cross_failure"],
                "head_pass_success": metrics["head_pass_success"],
                "head_pass_failure": metrics["head_pass_failure"],
                "high_pass_success": metrics["high_pass_success"],
                "high_pass_failure": metrics["high_pass_failure"],
                "launch_success": metrics["launch_success"],
                "launch_failure": metrics["launch_failure"],
                "simple_pass_success": metrics["simple_pass_success"],
                "simple_pass_failure": metrics["simple_pass_failure"],
                "smart_pass_success": metrics["smart_pass_success"],
                "smart_pass_failure": metrics["smart_pass_failure"],
                "shot_success": metrics["shot_success"],
                "shot_failure": metrics["shot_failure"],
            }
        )

    # Create DataFrame and sort by playerank_score in descending order
    playerank_df = pd.DataFrame(playerank_list)
    ranked_playerank_df = playerank_df.sort_values("playerank_score", ascending=False).reset_index(drop=True)

    return ranked_playerank_df


def calculate_playerank_ratings(playerank_df: pd.DataFrame, alpha_goals: float = 0.0) -> pd.DataFrame:
    """
    Calculate PlayeRank ratings based on PlayerRank scores and shot success, weighted by alpha_goals.

    Args:
        playerank_df (pd.DataFrame): DataFrame containing PlayerRank scores and metrics for players.
        alpha_goals (float): Weighting factor for shot success (goals scored) in the player rating calculation.

    Returns:
        pd.DataFrame: DataFrame containing PlayeRank ratings, PlayerRank scores, player metrics and a rank column.
    """
    rated_playerank_df = playerank_df.copy()

    # Add player ratings to the DataFrame and sort by playerank_rating in descending order
    playerank_ratings = rated_playerank_df.apply(
        lambda row: row["playerank_score"] * (1 - alpha_goals) + row["shot_success"] * alpha_goals, axis=1
    )
    rated_playerank_df.insert(3, "playerank_rating", playerank_ratings)
    rated_playerank_df = rated_playerank_df.sort_values("playerank_rating", ascending=False).reset_index(drop=True)

    # Add rank column based on playerank_rating
    rated_playerank_df.insert(0, "rank", range(1, len(rated_playerank_df) + 1))

    return rated_playerank_df


def get_match_playerank_scores(match_id: int):
    """Calculate PlayerRank scores for a specific match."""
    players_info_df = players.get_players_info(match_id)
    _, match_events_df = players.load_match_data(match_id)

    player_metrics = extract_player_metrics(match_events_df, players_info_df)
    feature_weights_df = load_feature_weights()

    playerank_df = calculate_playerank_scores(player_metrics, feature_weights_df)
    rated_playerank_df = calculate_playerank_ratings(playerank_df, alpha_goals=0.1)

    return rated_playerank_df


def get_tournament_playerank_scores(tournament: dict):
    """Calculate PlayerRank scores for all matches in a tournament and aggregate results."""
    match_ids = tournaments.get_all_match_ids(tournament)

    # Initialize empty DataFrame to store tournament PlayerRank scores
    all_matches_playerank_df = pd.DataFrame(
        columns=[
            "rank",
            "player",
            "team",
            "playerank_score",
            "playerank_rating",
            "minutes_played",
            "duel_aerial_success",
            "duel_aerial_failure",
            "duel_ground_success",
            "duel_ground_failure",
            "duel_loose_ball_success",
            "duel_loose_ball_failure",
            "foul_committed",
            "foul_commited_first_yellow",
            "foul_commited_second_yellow",
            "foul_commited_red",
            "corner_kick_success",
            "corner_kick_failure",
            "free_kick_success",
            "free_kick_failure",
            "free_kick_pass_success",
            "free_kick_pass_failure",
            "free_kick_shot_success",
            "free_kick_shot_failure",
            "goal_kick",
            "penalty",
            "penalty_failure",
            "throw_in_success",
            "throw_in_failure",
            "carry_success",
            "carry_failure",
            "clearance",
            "clearance_success",
            "clearance_failure",
            "counter_attack",
            "interception",
            "cross_success",
            "cross_failure",
            "head_pass_success",
            "head_pass_failure",
            "high_pass_success",
            "high_pass_failure",
            "launch_success",
            "launch_failure",
            "simple_pass_success",
            "simple_pass_failure",
            "smart_pass_success",
            "smart_pass_failure",
            "shot_success",
            "shot_failure",
        ]
    )

    # Calculate PlayerRank for each match and concatenate results
    for match_id in tqdm(match_ids, desc=f"Calculating PlayerRank for matches in {tournament['label']}", ncols=150):
        match_playerank_df = get_match_playerank_scores(match_id)

        # Save match PlayerRank scores to CSV
        match_filename = paths.PLAYERANK_OUTPUT_DIR / tournament["label"] / f"match_{match_id}_playerank_scores.csv"
        match_playerank_df.to_csv(match_filename, index=False)

        # Combine match PlayerRank scores into all matches DataFrame
        if all_matches_playerank_df.empty:
            all_matches_playerank_df = match_playerank_df
        else:
            all_matches_playerank_df = pd.concat([all_matches_playerank_df, match_playerank_df], ignore_index=True)

    # Aggregate PlayerRank scores for players across all matches in the tournament
    tournament_playerank_df = (
        all_matches_playerank_df.groupby(
            ["player", "team"],
            as_index=False,
        )
        .agg(
            {
                "playerank_score": "sum",
                "playerank_rating": "sum",
                "minutes_played": "sum",
                "duel_aerial_success": "sum",
                "duel_aerial_failure": "sum",
                "duel_ground_success": "sum",
                "duel_ground_failure": "sum",
                "duel_loose_ball_success": "sum",
                "duel_loose_ball_failure": "sum",
                "foul_committed": "sum",
                "foul_commited_first_yellow": "sum",
                "foul_commited_second_yellow": "sum",
                "foul_commited_red": "sum",
                "corner_kick_success": "sum",
                "corner_kick_failure": "sum",
                "free_kick_success": "sum",
                "free_kick_failure": "sum",
                "free_kick_pass_success": "sum",
                "free_kick_pass_failure": "sum",
                "free_kick_shot_success": "sum",
                "free_kick_shot_failure": "sum",
                "goal_kick": "sum",
                "penalty": "sum",
                "penalty_failure": "sum",
                "throw_in_success": "sum",
                "throw_in_failure": "sum",
                "carry_success": "sum",
                "carry_failure": "sum",
                "clearance": "sum",
                "clearance_success": "sum",
                "clearance_failure": "sum",
                "counter_attack": "sum",
                "interception": "sum",
                "cross_success": "sum",
                "cross_failure": "sum",
                "head_pass_success": "sum",
                "head_pass_failure": "sum",
                "high_pass_success": "sum",
                "high_pass_failure": "sum",
                "launch_success": "sum",
                "launch_failure": "sum",
                "simple_pass_success": "sum",
                "simple_pass_failure": "sum",
                "smart_pass_success": "sum",
                "smart_pass_failure": "sum",
                "shot_success": "sum",
                "shot_failure": "sum",
            }
        )
        .sort_values("playerank_rating", ascending=False)
        .reset_index(drop=True)
    )

    # Add rank column
    tournament_playerank_df.insert(0, "rank", range(1, len(tournament_playerank_df) + 1))

    # Add matches played column
    player_team_counts = all_matches_playerank_df.value_counts(["player", "team"]).reset_index(name="matches_played")
    tournament_playerank_df = pd.merge(tournament_playerank_df, player_team_counts, how="left", on=["player", "team"])

    # Save tournament PlayerRank scores to CSV
    tournament_filename = paths.PLAYERANK_OUTPUT_DIR / f"{tournament['label']}_playerank_scores.csv"
    tournament_playerank_df.to_csv(tournament_filename, index=False)

    return tournament_playerank_df


def main():
    # Calculate PlayeRank for National Team Tournaments
    for tournament in tqdm(
        tournaments.NATIONAL_TEAM_TOURNAMENTS,
        desc="Processing National Team Tournaments",
        ncols=150,
    ):
        get_tournament_playerank_scores(tournament)

    # Calculate PlayeRank for European Club Leagues
    for tournament in tqdm(
        tournaments.EUROPEAN_CLUB_LEAGUES,
        desc="Processing European Club Leagues",
        ncols=150,
    ):
        get_tournament_playerank_scores(tournament)

    pass


if __name__ == "__main__":
    main()
