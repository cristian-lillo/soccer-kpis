"""
Main script to run all player performance evaluation modules.
"""

import matplotlib.pyplot as plt
import pandas as pd

from config import paths, tournaments
from models.ea_sports_ppi import ppi_main
from models.opta_points import opta_points_main

# List of models to run
MODELS = ["ea_sports_ppi", "opta_points"]
MODEL_DISPLAY_NAMES = {
    "ea_sports_ppi": "EA Sports PPI",
    "opta_points": "Opta Points",
    "playerank": "Playerank",
    "plus_minus": "Plus-Minus",
}
PERFORMANCE_METRIC = {
    "index_score": "performance_score",
    "opta_points": "performance_score",
    "player_rating": "performance_score",  # Update later to "playerank_rating"
    "plus_minus_score": "performance_score",
}


def calculate_player_performance(models: list[str] = MODELS):
    """
    Calculate player performance using different models.

    Args:
        models : List of model names to run.
    """
    for model in models:
        if model == "ea_sports_ppi":
            ppi_main.main()

        elif model == "opta_points":
            opta_points_main.main()


def compare_model_score_by_minutes_played():
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
