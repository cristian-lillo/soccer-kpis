"""Plot generation for model scores and ranking comparisons."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap

from config import paths, tournaments
from scripts.utils import filter_players_by_minutes, normalize_performance_scores

TOP10_OUTSIDE_CATEGORY = 11


def generate_plots_for_score_per_match(
    selected_tournaments: list[dict] = tournaments.ALL_TOURNAMENTS,
    per_90: bool = False,
    format: str = "pdf",
    evaluation_models: dict[str, dict] | None = None,
) -> None:
    """Compare model scores by player appearances."""
    if evaluation_models is None:
        from scripts.main import EVALUATION_MODELS_INFO

        evaluation_models = EVALUATION_MODELS_INFO

    plot_label = "score_per_match"
    dir_per_90 = "per_90" if per_90 else ""
    output_dir = paths.FIGURES_OUTPUT_DIR / plot_label / format / dir_per_90
    output_dir.mkdir(parents=True, exist_ok=True)

    for tournament in selected_tournaments:
        tournament_label = tournament["label"]
        tournament_display_name = tournament["display_name"]
        for model, model_info in evaluation_models.items():
            for file in model_info["output_directory"].glob(f"{tournament_label}_*.csv"):
                print(f"[{plot_label}] {tournament_label} | {model_info['display_name']}")
                df = pd.read_csv(file)
                if per_90:
                    df = filter_players_by_minutes(df, tournament)
                normalized_df = normalize_performance_scores(df, model_info["performance_score"], per_90=per_90)

                plt.figure(figsize=(10, 6))
                plt.scatter(
                    normalized_df["matches_played"],
                    normalized_df["normalized_score"],
                    s=18,
                    alpha=0.75,
                    color=model_info["plot_color"],
                )
                title_suffix = " por 90 Minutos" if per_90 else ""
                plt.title(
                    f"Puntaje por Partidos Jugados{title_suffix} - "
                    f"{tournament_display_name} - {model_info['display_name']}"
                )
                plt.xlabel("Cantidad de Partidos Jugados")
                plt.ylabel("Puntaje Normalizado")
                plt.grid(alpha=0.25)
                plt.tight_layout()
                suffix = "_per_90" if per_90 else ""
                plt.savefig(output_dir / f"{tournament_label}_{model}_{plot_label}{suffix}.{format}")
                plt.close()


def generate_plots_for_model_scores(
    selected_tournaments: list[dict] = tournaments.ALL_TOURNAMENTS,
    per_90: bool = False,
    format: str = "pdf",
    evaluation_models: dict[str, dict] | None = None,
) -> None:
    """Generate individual and combined score-distribution histograms."""
    if evaluation_models is None:
        from scripts.main import EVALUATION_MODELS_INFO

        evaluation_models = EVALUATION_MODELS_INFO

    plot_label = "score_distribution"
    dir_per_90 = "per_90" if per_90 else ""
    output_dir = paths.FIGURES_OUTPUT_DIR / plot_label / format / dir_per_90
    output_dir.mkdir(parents=True, exist_ok=True)

    for tournament in selected_tournaments:
        tournament_label = tournament["label"]
        tournament_display_name = tournament["display_name"]
        combined_figure = plt.figure(figsize=(10, 6))
        combined_ax = combined_figure.gca()

        for model, model_info in evaluation_models.items():
            for file in model_info["output_directory"].glob(f"{tournament_label}_*.csv"):
                print(f"[{plot_label}] {tournament_label} | {model_info['display_name']}")
                df = pd.read_csv(file)
                if per_90:
                    df = filter_players_by_minutes(df, tournament)
                normalized_df = normalize_performance_scores(df, model_info["performance_score"], per_90=per_90)
                scores = normalized_df["normalized_score"].dropna()
                weights = np.ones(len(scores)) / len(scores) if len(scores) else None

                plt.figure(figsize=(10, 6))
                plt.hist(
                    scores,
                    bins=30,
                    weights=weights,
                    color=model_info["plot_color"],
                    alpha=0.85,
                    edgecolor="white",
                )
                title_suffix = " por 90 Minutos" if per_90 else ""
                plt.title(
                    f"Distribución de puntajes{title_suffix} - {tournament_display_name} - {model_info['display_name']}"
                )
                plt.xlabel("Puntaje normalizado")
                plt.ylabel("Proporción")
                plt.ylim(0, 0.4)
                plt.grid(alpha=0.25, axis="y")
                plt.tight_layout()
                suffix = "_per_90" if per_90 else ""
                plt.savefig(output_dir / f"{tournament_label}_{model}_{plot_label}{suffix}.{format}")
                plt.close()

                combined_ax.hist(
                    scores,
                    bins=30,
                    weights=weights,
                    histtype="step",
                    linewidth=2,
                    color=model_info["plot_color"],
                    label=model_info["display_name"],
                    alpha=0.9,
                )

        combined_title_suffix = " por 90 Minutos" if per_90 else ""
        combined_ax.set_title(
            f"Comparación general de distribuciones - {tournament_display_name}{combined_title_suffix}"
        )
        combined_ax.set_xlabel("Puntaje normalizado")
        combined_ax.set_ylabel("Proporción")
        combined_ax.set_ylim(0, 0.4)
        combined_ax.grid(alpha=0.25, axis="y")
        combined_ax.legend()
        combined_figure.tight_layout()
        suffix = "_per_90" if per_90 else ""
        combined_figure.savefig(output_dir / f"{tournament_label}__{plot_label}{suffix}.{format}")
        plt.close(combined_figure)


def plot_topk_matrix(
    tournament: dict[str, str | int],
    topk_matrix: pd.DataFrame,
    per_90: bool = False,
    top_k: int = 10,
    format: str = "pdf",
) -> None:
    """Plot the top-k ranking matrix using discrete colors."""
    tournament_label = str(tournament["label"])
    tournament_display_name = str(tournament["display_name"])
    dir_per_90 = "per_90" if per_90 else ""
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
    cbar.set_ticks(list(range(1, top_k + 1)) + [TOP10_OUTSIDE_CATEGORY])
    cbar.set_ticklabels([str(i) for i in range(1, top_k + 1)] + [f"Fuera del Top {top_k}"])
    cbar.set_label("Ranking")
    cbar.ax.invert_yaxis()
    title_suffix = " por 90 Minutes" if per_90 else ""
    plt.title(f"Top {top_k} por modelo - {tournament_display_name}{title_suffix}")
    plt.tight_layout()
    plot_dir = paths.FIGURES_OUTPUT_DIR / "comparison_tables" / format / dir_per_90
    plot_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_dir / f"{tournament_label}_top{top_k}_{suffix}.{format}")
    plt.close()
