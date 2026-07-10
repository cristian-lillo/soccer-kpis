"""
Main script to run evaluation models and compare their outputs.

This script orchestrates the execution of different player performance evaluation models, normalizes their scores, and generates comparison tables and plots for analysis.

The evaluation models included are:
- EA Sports PPI
- Opta Points
- PlayeRank
- Plus-Minus
"""

from itertools import combinations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap

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

TOP10_OUTSIDE_CATEGORY = 11


def get_min_minutes_threshold(tournament: dict[str, str | int]) -> int:
    if tournament in tournaments.NATIONAL_TEAM_TOURNAMENTS:
        return 90 * 2  # Minimum 2 matches for national team tournaments
    else:
        return 90 * 5  # Minimum 5 matches for club leagues


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


def generate_plots_for_score_per_match(
    selected_tournaments: list[dict] = tournaments.ALL_TOURNAMENTS,
    format: str = "pdf",
) -> None:
    """
    Compare model scores by player appearances, one figure per model and tournament.

    Args:
        selected_tournaments: List of tournaments to process.
        format: The format in which to save the charts (default is "pdf").
    """
    plot_label = "score_per_match"
    output_dir = paths.FIGURES_OUTPUT_DIR / plot_label / format
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

                plt.savefig(output_dir / f"{tournament_label}_{model}_{plot_label}.{format}")
                plt.close()


def generate_plots_for_model_scores(
    selected_tournaments: list[dict] = tournaments.ALL_TOURNAMENTS,
    per_90: bool = False,
    format: str = "pdf",
) -> None:
    """
    Generate one plot per model and an additional combined plot per tournament.

    Args:
        selected_tournaments: List of tournaments to process.
        per_90: If True, normalize scores to a per-90 rate.
        format: The format in which to save the charts (default is "pdf").
    """
    plot_label = "score_per_90" if per_90 else "total_score"
    output_dir = paths.FIGURES_OUTPUT_DIR / plot_label / format
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
                plt.savefig(output_dir / f"{tournament_label}_{model}_{suffix}.{format}")
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
        combined_figure.savefig(output_dir / f"{tournament_label}_{suffix}.{format}")
        plt.close(combined_figure)


def generate_comparison_tables(
    selected_tournaments: list[dict[str, str | int]] = tournaments.ALL_TOURNAMENTS,
    per_90: bool = False,
    top_k: int = 10,
    save_plots: bool = True,
    format: str = "pdf",
) -> None:
    """
    Orchestrate comparison table generation, saving and plotting.

    Args:
        selected_tournaments: List of tournaments to process.
        per_90: If True, normalize scores to a per-90 rate.
        top_k: Number of top players to consider for Jaccard similarity and plotting.
        save_plots: If True, generate and save plots for the top-k ranking matrix.
        format: The format in which to save the charts (default is "pdf").
    """

    for tournament in selected_tournaments:
        tables = build_comparison_tables_for_tournament(
            tournament=tournament,
            per_90=per_90,
            top_k=top_k,
        )

        if tables["merged_table"].empty:
            continue

        save_comparison_tables(
            tournament=tournament,
            tables=tables,
            per_90=per_90,
            top_k=top_k,
        )

        if save_plots:
            plot_topk_matrix(
                tournament=tournament,
                topk_matrix=tables["topk_matrix"],
                per_90=per_90,
                top_k=top_k,
                format=format,
            )


def build_comparison_tables_for_tournament(
    tournament: dict[str, str | int],
    per_90: bool = False,
    top_k: int = 10,
) -> dict[str, pd.DataFrame]:
    """
    Build all comparison tables for one tournament.

    Args:
        tournament: Dictionary containing tournament information.
        per_90: If True, normalize scores to a per-90 rate.
        top_k: Number of top players to consider for Jaccard similarity and plotting.

    Returns:
        Dictionary containing merged table, Pearson correlation, Spearman correlation,
        Jaccard similarity, and top-k ranking matrix.
    """
    function_label = "comparison_tables"
    tournament_label = str(tournament["label"])
    min_minutes = get_min_minutes_threshold(tournament)

    model_tables: list[pd.DataFrame] = []
    topk_rows: list[pd.DataFrame] = []

    for model in EVALUATION_MODELS_INFO:
        model_info = EVALUATION_MODELS_INFO[model]
        model_output_directory = model_info["output_directory"]
        performance_score_column = model_info["performance_score"]
        model_display_name = model_info["display_name"]

        for file in model_output_directory.glob(f"{tournament_label}_*.csv"):
            print(f"[{function_label}] {tournament_label} | {model_display_name}")

            df = pd.read_csv(file)
            df = df[df["minutes_played"] >= min_minutes].copy()

            normalized_df = normalize_performance_scores(
                df,
                performance_score_column,
                per_90=per_90,
            )

            table = normalized_df[["player", "performance_score", "normalized_score", "normalized_rank"]].copy()
            table = table.rename(
                columns={
                    "performance_score": f"{model}_score",
                    "normalized_score": f"{model}_normalized_score",
                    "normalized_rank": f"{model}_normalized_rank",
                }
            )
            model_tables.append(table)

            topk_df = normalized_df.head(top_k)[["player", "normalized_rank"]].copy()
            topk_df["model"] = model_display_name
            topk_rows.append(topk_df)

    if not model_tables:
        return {
            "merged_table": pd.DataFrame(),
            "pearson_df": pd.DataFrame(),
            "spearman_df": pd.DataFrame(),
            "jaccard_df": pd.DataFrame(),
            "topk_matrix": pd.DataFrame(),
        }

    merged_table = model_tables[0]
    for table in model_tables[1:]:
        merged_table = merged_table.merge(table, on="player", how="outer")

    norm_cols = [col for col in merged_table.columns if col.endswith("_normalized_score")]
    rank_cols = [col for col in merged_table.columns if col.endswith("_normalized_rank")]

    pearson_df = merged_table[norm_cols].corr(method="pearson")
    spearman_df = merged_table[rank_cols].corr(method="spearman")

    jaccard_rows = []
    for c1, c2 in combinations(rank_cols, 2):
        model_1 = c1.replace("_normalized_rank", "")
        model_2 = c2.replace("_normalized_rank", "")

        top1 = set(merged_table.nsmallest(top_k, c1)["player"].dropna())
        top2 = set(merged_table.nsmallest(top_k, c2)["player"].dropna())

        union = top1 | top2
        intersection = top1 & top2
        jaccard_score = len(intersection) / len(union) if union else 0.0

        jaccard_rows.append(
            {
                "model_1": model_1,
                "model_2": model_2,
                "jaccard_top_k": jaccard_score,
            }
        )

    jaccard_df = pd.DataFrame(jaccard_rows)

    topk_df = pd.concat(topk_rows, ignore_index=True)
    topk_matrix = topk_df.pivot_table(
        index="player",
        columns="model",
        values="normalized_rank",
        aggfunc="min",
    )

    topk_matrix = topk_matrix.fillna(TOP10_OUTSIDE_CATEGORY).astype(int)
    row_order = topk_matrix.sum(axis=1).sort_values().index
    topk_matrix = topk_matrix.loc[row_order]

    return {
        "merged_table": merged_table,
        "pearson_df": pearson_df,
        "spearman_df": spearman_df,
        "jaccard_df": jaccard_df,
        "topk_matrix": topk_matrix,
    }


def save_comparison_tables(
    tournament: dict[str, str | int],
    tables: dict[str, pd.DataFrame],
    per_90: bool = False,
    top_k: int = 10,
) -> None:
    """
    Save comparison tables to CSV.

    Args:
        tournament: Dictionary containing tournament information.
        tables: Dictionary containing comparison tables.
        per_90: If True, normalize scores to a per-90 rate.
        top_k: Number of top players to consider for Jaccard similarity and plotting.
    """
    tournament_label = str(tournament["label"])
    suffix = "per_90" if per_90 else "total"

    comparison_root_dir = paths.OUTPUT_DIR / "comparisons"
    comparison_root_dir.mkdir(parents=True, exist_ok=True)

    tournament_dir = comparison_root_dir / tournament_label
    tournament_dir.mkdir(parents=True, exist_ok=True)

    tables["merged_table"].to_csv(
        tournament_dir / f"{tournament_label}_{suffix}_model_table.csv",
        index=False,
    )
    tables["pearson_df"].to_csv(
        tournament_dir / f"{tournament_label}_{suffix}_pearson.csv",
    )
    tables["spearman_df"].to_csv(
        tournament_dir / f"{tournament_label}_{suffix}_spearman.csv",
    )
    tables["jaccard_df"].to_csv(
        tournament_dir / f"{tournament_label}_{suffix}_jaccard.csv",
        index=False,
    )
    tables["topk_matrix"].to_csv(
        tournament_dir / f"{tournament_label}_{suffix}_top{top_k}_matrix.csv",
    )


def plot_topk_matrix(
    tournament: dict[str, str | int],
    topk_matrix: pd.DataFrame,
    per_90: bool = False,
    top_k: int = 10,
    format: str = "pdf",
) -> None:
    """
    Plot the top-k ranking matrix using discrete colors.

    Args:
        tournament: Dictionary containing tournament information.
        topk_matrix: DataFrame containing the top-k ranking matrix.
        per_90: If True, normalize scores to a per-90 rate.
        top_k: Number of top players to consider for Jaccard similarity and plotting.
        format: The format in which to save the charts (default is "pdf").
    """
    tournament_label = str(tournament["label"])
    tournament_display_name = str(tournament["display_name"])
    suffix = "per_90" if per_90 else "total"

    colors = [
        "#1a9850",
        "#66bd63",
        "#a6d96a",
        "#d9ef8b",
        "#ffffbf",
        "#fee08b",
        "#fdae61",
        "#f46d43",
        "#d73027",
        "#a50026",
        "#ffffff",
    ]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.arange(0.5, TOP10_OUTSIDE_CATEGORY + 1.5, 1), cmap.N)

    plt.figure(figsize=(12, max(6, 0.4 * len(topk_matrix))))
    ax = plt.gca()
    im = ax.imshow(topk_matrix.values, aspect="auto", cmap=cmap, norm=norm)

    ax.set_xticks(range(len(topk_matrix.columns)))
    ax.set_xticklabels(topk_matrix.columns.tolist(), rotation=30, ha="right")
    ax.set_yticks(range(len(topk_matrix.index)))
    ax.set_yticklabels(topk_matrix.index.tolist())

    for row_idx in range(topk_matrix.shape[0]):
        for col_idx in range(topk_matrix.shape[1]):
            cell_value = topk_matrix.iloc[row_idx, col_idx]
            if cell_value <= top_k:
                text_color = "white" if cell_value <= 2 or cell_value >= 8 else "black"
                ax.text(
                    col_idx,
                    row_idx,
                    str(cell_value),
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=text_color,
                    fontweight="bold",
                )

    cbar = plt.colorbar(im, ax=ax)
    tick_positions = list(range(1, top_k + 1)) + [TOP10_OUTSIDE_CATEGORY]
    tick_labels = [str(i) for i in range(1, top_k + 1)] + [f"Fuera del Top {top_k}"]
    cbar.set_ticks(tick_positions)
    cbar.set_ticklabels(tick_labels)
    cbar.set_label("Ranking")
    cbar.ax.invert_yaxis()

    title_suffix = " por 90 Minutes" if per_90 else ""
    plt.title(f"Top {top_k} por modelo - {tournament_display_name}{title_suffix}")
    plt.tight_layout()

    plot_dir = paths.FIGURES_OUTPUT_DIR / f"comparison_tables_{suffix}" / format
    plot_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_dir / f"{tournament_label}_top{top_k}_{suffix}.{format}")
    plt.close()


def main():
    """Main function to execute the evaluation models and compare their outputs."""

    run_models_flag = False
    if run_models_flag:
        run_evaluation_models(EVALUATION_MODELS_INFO)

    compare_models_flag = True
    if compare_models_flag:
        selected_tournaments = tournaments.ALL_TOURNAMENTS

        for format in ["pdf", "png"]:
            generate_plots_for_score_per_match(selected_tournaments, format=format)

            generate_plots_for_model_scores(selected_tournaments, per_90=False, format=format)
            generate_plots_for_model_scores(selected_tournaments, per_90=True, format=format)

            generate_comparison_tables(selected_tournaments, per_90=False, top_k=10, save_plots=True, format=format)
            generate_comparison_tables(selected_tournaments, per_90=True, top_k=10, save_plots=True, format=format)


if __name__ == "__main__":
    main()
