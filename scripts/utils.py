"""Shared helpers for score processing and playing-time filters."""

import pandas as pd

from config import tournaments


def get_min_minutes_threshold(tournament: dict[str, str | int]) -> int:
    """Return the minimum minutes used for the tournament's player population."""
    return 90 * 2 if tournament in tournaments.NATIONAL_TEAM_TOURNAMENTS else 90 * 5


def filter_players_by_minutes(
    df: pd.DataFrame,
    tournament: dict[str, str | int],
) -> pd.DataFrame:
    """Keep the same minimum-playing-time population used in comparisons."""
    return df[df["minutes_played"] >= get_min_minutes_threshold(tournament)].copy()


def normalize_performance_scores(
    df: pd.DataFrame,
    performance_score_column: str,
    per_90: bool = False,
) -> pd.DataFrame:
    """Normalize model scores and optionally convert them to a per-90 rate."""
    normalized_df = df.copy().rename(columns={performance_score_column: "performance_score"})

    if per_90:
        normalized_df["performance_score"] = (
            normalized_df["performance_score"] / normalized_df["minutes_played"]
        ) * 90.0

    min_score = normalized_df["performance_score"].min()
    max_score = normalized_df["performance_score"].max()
    if max_score == min_score:
        normalized_df["normalized_score"] = 0.0
    else:
        normalized_df["normalized_score"] = (normalized_df["performance_score"] - min_score) / (max_score - min_score)

    normalized_df = normalized_df.sort_values(by="normalized_score", ascending=False).reset_index(drop=True)
    normalized_df["normalized_rank"] = range(1, len(normalized_df) + 1)
    return normalized_df
