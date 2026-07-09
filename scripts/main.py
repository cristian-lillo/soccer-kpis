"""
Main script to run evaluation models and compare their outputs.

This script orchestrates the execution of different player performance evaluation models, normalizes their scores, and generates comparison tables and plots for analysis.

The evaluation models included are:
- EA Sports PPI
- Opta Points
- PlayeRank
- Plus-Minus
"""

import matplotlib.pyplot as plt
import pandas as pd

from config import paths, tournaments
from models.ea_sports_ppi import ppi_main
from models.opta_points import opta_points_main
from models.playerank import playerank_main
from models.plus_minus import plus_minus_main

EVALUATION_MODELS_INFO = {
    "ea_sports_ppi": {
        "display_name": "EA Sports PPI",
        "performance_score": "index_score",
        "script": ppi_main,
        "output_directory": paths.EA_SPORTS_PPI_OUTPUT_DIR,
        "plot_color": "tab:blue",
    },
    "opta_points": {
        "display_name": "Opta Points",
        "performance_score": "opta_points",
        "script": opta_points_main,
        "output_directory": paths.OPTA_POINTS_OUTPUT_DIR,
        "plot_color": "tab:orange",
    },
    "playerank": {
        "display_name": "PlayeRank",
        "performance_score": "playerank_rating",
        "script": playerank_main,
        "output_directory": paths.PLAYERANK_OUTPUT_DIR,
        "plot_color": "tab:green",
    },
    "plus_minus": {
        "display_name": "Plus-Minus",
        "performance_score": "plus_minus_score",
        "script": plus_minus_main,
        "output_directory": paths.PLUS_MINUS_OUTPUT_DIR,
        "plot_color": "tab:red",
    },
    # "vaep": {
    #     "display_name": "VAEP",
    #     "performance_score": "vaep_score",
    #     "script": None,  # Placeholder for VAEP script
    #     "output_directory": paths.VAEP_OUTPUT_DIR,
    #     "plot_color": "tab:purple",
    # },
}


def run_evaluation_models(evaluation_models: dict[str, dict] = EVALUATION_MODELS_INFO):
    """
    Calculate player performance using different models.

    Args:
        evaluation_models : Dictionary of model names and their information to run.
    """
    for model in evaluation_models:
        evaluation_models[model]["script"].main()


def normalize_performance_scores(
    df: pd.DataFrame,
    performance_score_column: str,
    per_90: bool = False,
) -> pd.DataFrame:
    """
    Normalize performance scores in the DataFrame to a 0-1 range.

    Args:
        df: DataFrame containing player performance scores.
        performance_score_column: Name of the column containing performance scores.
        per_90: If True, convert scores to a per-90 rate before normalizing.

    Returns:
        DataFrame with normalized scores and sorted in descending order.
    """
    normalized_df = df.copy()
    normalized_df = normalized_df.rename(columns={performance_score_column: "performance_score"})

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

def compare_model_score_by_minutes_played():
    normalized_df = normalized_df.sort_values(by="normalized_score", ascending=False).reset_index(drop=True)
    normalized_df["normalized_rank"] = range(1, len(normalized_df) + 1)

    return normalized_df
    """
    Compare model scores by minutes played.
    """
    for tournament in tournaments.ALL_TOURNAMENTS:
        print(f"Comparing model scores by minutes played for {tournament['label']}...")

        for model in paths.MODEL_OUTPUT_DIRECTORIES:
            for file in model.glob(f"{tournament['label']}_*.csv"):
                print(f"Comparing model output file: {file}...")

                df = pd.read_csv(file)
                standard_df = df.rename(columns=PERFORMANCE_METRIC)

                standard_df["performance_score_per_90"] = (
                    standard_df["performance_score"] / standard_df["minutes_played"]
                ) * 90.0

                min_score = standard_df["performance_score_per_90"].min()
                max_score = standard_df["performance_score_per_90"].max()
                standard_df["normalized_score_per_90"] = (standard_df["performance_score_per_90"] - min_score) / (
                    max_score - min_score
                )

                plt.figure(figsize=(10, 6))
                plt.plot(standard_df["normalized_score_per_90"])
                plt.title(f"Normalized Score vs Minutes Played - {tournament['display_name']}")
                plt.xlabel("Rank Position")
                plt.ylabel("Normalized Score per 90")
                plt.savefig(
                    paths.FIGURES_OUTPUT_DIR
                    / "score_vs_minutes_played"
                    / f"{tournament['label']}_{model.name}_score_vs_minutes_played.png"
                )


def compare_model_score_by_appearances():
    """
    Compare model scores by player appearances.
    """
    for tournament in tournaments.ALL_TOURNAMENTS:
        print(f"Comparing model scores by appearances for {tournament['label']}...")

        for model in paths.MODEL_OUTPUT_DIRECTORIES:
            for file in model.glob(f"{tournament['label']}_*.csv"):
                print(f"Comparing model output file: {file}...")

                df = pd.read_csv(file)
                standard_df = df.rename(columns=PERFORMANCE_METRIC)

                min_score = standard_df["performance_score"].min()
                max_score = standard_df["performance_score"].max()
                standard_df["normalized_score"] = (standard_df["performance_score"] - min_score) / (
                    max_score - min_score
                )
                min_score = standard_df["performance_score"].min()
                max_score = standard_df["performance_score"].max()
                standard_df["normalized_score"] = (standard_df["performance_score"] - min_score) / (
                    max_score - min_score
                )

                plt.figure(figsize=(10, 6))
                plt.scatter(standard_df["matches_played"], standard_df["normalized_score"])
                plt.title(f"Normalized Score vs Appearances - {tournament['display_name']}")
                plt.xlabel("Appearances")
                plt.ylabel("Normalized Score")
                plt.savefig(
                    paths.FIGURES_OUTPUT_DIR
                    / "score_vs_appearances"
                    / f"{tournament['label']}_{model.name}_score_vs_appearances.png"
                )


def compare_models():
    """
    Compare the outputs of different models and generate visualizations.
    """
    for tournament in tournaments.ALL_TOURNAMENTS:
        print(f"Comparing model outputs for {tournament['label']}...")
        plt.figure(figsize=(10, 6))

        for model in paths.MODEL_OUTPUT_DIRECTORIES:
            for file in model.glob(f"{tournament['label']}_*.csv"):
                print(f"Comparing model output file: {file}...")

                df = pd.read_csv(file)
                standard_df = df.rename(columns=PERFORMANCE_METRIC)

                min_score = standard_df["performance_score"].min()
                max_score = standard_df["performance_score"].max()
                standard_df["normalized_score"] = (standard_df["performance_score"] - min_score) / (
                    max_score - min_score
                )

                plt.plot(standard_df["normalized_score"], label=MODEL_DISPLAY_NAMES[model.name])

        plt.title(f"Comparación de Puntaje Total en Torneo - {tournament['display_name']}")
        plt.xlabel("Ránking de Jugadores")
        plt.ylabel("Puntaje Normalizado")
        plt.legend()

        plt.savefig(paths.FIGURES_OUTPUT_DIR / "model_comparison" / f"{tournament['label']}_model_comparison.png")


def main():
    # calculate_player_performance(MODELS)

    compare_models()
    compare_model_score_by_appearances()
    compare_model_score_by_minutes_played()


if __name__ == "__main__":
    main()
