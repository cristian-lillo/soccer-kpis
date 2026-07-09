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

    normalized_df = normalized_df.sort_values(by="normalized_score", ascending=False).reset_index(drop=True)
    normalized_df["normalized_rank"] = range(1, len(normalized_df) + 1)

    return normalized_df


def generate_plots_for_score_per_match(selected_tournaments: list[dict] = tournaments.ALL_TOURNAMENTS):
    """
    Compare model scores by player appearances, one figure per model and tournament.
    """
    plot_label = "score_per_match"
    output_dir = paths.FIGURES_OUTPUT_DIR / plot_label
    output_dir.mkdir(parents=True, exist_ok=True)

    for tournament in selected_tournaments:
        tournament_label = tournament["label"]
        tournament_display_name = tournament["display_name"]

        for model in EVALUATION_MODELS_INFO:
            model_info = EVALUATION_MODELS_INFO[model]
            model_output_directory = model_info["output_directory"]
            performance_score_column = model_info["performance_score"]
            model_display_name = model_info["display_name"]
            model_plot_color = model_info["plot_color"]

            for file in model_output_directory.glob(f"{tournament_label}_*.csv"):
                print(f"[{plot_label}] {tournament_label} | {model_display_name}")

                df = pd.read_csv(file)
                normalized_df = normalize_performance_scores(df, performance_score_column)

                plt.figure(figsize=(10, 6))
                plt.scatter(
                    normalized_df["matches_played"],
                    normalized_df["normalized_score"],
                    s=18,
                    alpha=0.75,
                    color=model_plot_color,
                )
                plt.title(f"Puntaje por Partidos Jugados - {tournament_display_name} - {model_display_name}")
                plt.xlabel("Cantidad de Partidos Jugados")
                plt.ylabel("Puntaje Normalizado")
                plt.grid(alpha=0.25)
                plt.tight_layout()

                plt.savefig(output_dir / f"{tournament_label}_{model}_{plot_label}.pdf")
                plt.close()


def generate_plots_for_model_scores(
    selected_tournaments: list[dict] = tournaments.ALL_TOURNAMENTS,
    per_90: bool = False,
) -> None:
    """
    Generate one plot per model and an additional combined plot per tournament.

    Args:
        selected_tournaments: List of tournaments to process.
        per_90: If True, normalize scores to a per-90 rate.
    """
    plot_label = "score_per_90" if per_90 else "total_score"
    output_dir = paths.FIGURES_OUTPUT_DIR / plot_label
    output_dir.mkdir(parents=True, exist_ok=True)

    for tournament in selected_tournaments:
        tournament_label = tournament["label"]
        tournament_display_name = tournament["display_name"]

        combined_figure = plt.figure(figsize=(10, 6))
        combined_ax = combined_figure.gca()

        for model in EVALUATION_MODELS_INFO:
            model_info = EVALUATION_MODELS_INFO[model]
            model_output_directory = model_info["output_directory"]
            performance_score_column = model_info["performance_score"]
            model_display_name = model_info["display_name"]
            model_plot_color = model_info["plot_color"]

            for file in model_output_directory.glob(f"{tournament_label}_*.csv"):
                print(f"[{plot_label}] {tournament_label} | {model_display_name}")

                df = pd.read_csv(file)
                normalized_df = normalize_performance_scores(
                    df,
                    performance_score_column,
                    per_90=per_90,
                )

                plt.figure(figsize=(10, 6))
                plt.plot(
                    normalized_df["normalized_rank"] / len(normalized_df),
                    normalized_df["normalized_score"],
                    color=model_plot_color,
                    linewidth=2,
                )

                title_suffix = " por 90 Minutos" if per_90 else ""
                plt.title(f"{model_display_name} - {tournament_display_name}{title_suffix}")
                plt.xlabel("Percentil de ranking")
                plt.ylabel("Puntaje normalizado")
                plt.grid(alpha=0.25)
                plt.tight_layout()

                suffix = "per_90" if per_90 else "total"
                plt.savefig(output_dir / f"{tournament_label}_{model}_{suffix}.pdf")
                plt.close()

                combined_ax.plot(
                    normalized_df["normalized_rank"] / len(normalized_df),
                    normalized_df["normalized_score"],
                    color=model_plot_color,
                    linewidth=1.6,
                    alpha=0.85,
                    label=model_display_name,
                )

        combined_title_suffix = " por 90 Minutos" if per_90 else ""
        combined_ax.set_title(f"Comparación general de puntajes - {tournament_display_name}{combined_title_suffix}")
        combined_ax.set_xlabel("Percentil de ranking")
        combined_ax.set_ylabel("Puntaje normalizado")
        combined_ax.grid(alpha=0.25)
        combined_ax.legend()
        combined_figure.tight_layout()

        suffix = "per_90" if per_90 else "total"
        combined_figure.savefig(output_dir / f"{tournament_label}_{suffix}.pdf")
        plt.close(combined_figure)
    """
    """



                )





def main():
    # calculate_player_performance(MODELS)

    compare_models()
    compare_model_score_by_appearances()
    compare_model_score_by_minutes_played()


if __name__ == "__main__":
    main()
