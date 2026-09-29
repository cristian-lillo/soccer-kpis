"""Comparison tables, correlations, rankings, and LaTeX output."""

from itertools import combinations

import numpy as np
import pandas as pd

from config import paths, tournaments
from scripts import plots
from scripts.utils import get_min_minutes_threshold, normalize_performance_scores

TOP10_OUTSIDE_CATEGORY = 11


def generate_comparison_tables(
    evaluation_models: dict[str, dict],
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
            evaluation_models=evaluation_models,
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
            plots.plot_topk_matrix(
                tournament=tournament,
                topk_matrix=tables["topk_matrix"],
                per_90=per_90,
                top_k=top_k,
                format=format,
            )


def build_comparison_tables_for_tournament(
    evaluation_models: dict[str, dict],
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

    for model, model_info in evaluation_models.items():
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
    dir_per_90 = "per_90" if per_90 else ""
    suffix = "per_90" if per_90 else "total"

    comparison_root_dir = paths.OUTPUT_DIR / "comparisons" / dir_per_90
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


def _latex_value(value: float | None, decimals: int = 3) -> str:
    if value is None or pd.isna(value):
        return "---"
    text = f"{float(value):.{decimals}f}"
    return text.rstrip("0").rstrip(".")


def _matrix_to_latex_tabular(
    title: str,
    matrix: pd.DataFrame,
    labels: list[str],
) -> str:
    column_spec = "c | " + " ".join(["c"] * len(labels))
    lines = [
        f"    \\begin{{tabular}}{{{column_spec}}}",
        f"        \\textbf{{{title}}} & " + " & ".join(labels) + " \\\\ \\hline",
    ]

    for row_label in labels:
        row_values = [row_label]
        for col_label in labels:
            if row_label == col_label:
                row_values.append("---")
            else:
                row_values.append(_latex_value(matrix.loc[row_label, col_label]))
        lines.append("        " + " & ".join(row_values) + " \\\\")
    lines.append("    \\end{tabular}")
    return "\n".join(lines)


def _build_symmetric_matrix(
    df: pd.DataFrame,
    labels: list[str],
    left_col: str,
    right_col: str,
    value_col: str,
) -> pd.DataFrame:
    matrix = pd.DataFrame(index=labels, columns=labels, dtype=float)
    for label in labels:
        matrix.loc[label, label] = np.nan

    for _, row in df.iterrows():
        left = row[left_col]
        right = row[right_col]
        if left not in labels or right not in labels:
            continue
        matrix.loc[left, right] = row[value_col]
        matrix.loc[right, left] = row[value_col]

    return matrix


def _get_tournament_group(tournament: dict[str, str | int]) -> str:
    national_labels = {t["label"] for t in tournaments.NATIONAL_TEAM_TOURNAMENTS}
    return "selecciones" if tournament["label"] in national_labels else "ligas"


def generate_latex_comparison_tables(
    evaluation_models: dict[str, dict],
    selected_tournaments: list[dict[str, str | int]] = tournaments.ALL_TOURNAMENTS,
    top_k: int = 10,
    output_filename: str = "comparison_tables_total.tex",
) -> str:
    """
    Generate LaTeX tables for total-score comparisons.

    - Jaccard tables are grouped by competition type.
    - Pearson and Spearman tables are generated per competition.
    """
    comparison_dir = paths.OUTPUT_DIR / "comparisons" / "latex"
    comparison_dir.mkdir(parents=True, exist_ok=True)
    output_path = comparison_dir / output_filename

    short_names = {key: info["short_name"] for key, info in evaluation_models.items()}
    normalized_score_names = {f"{key}_normalized_score": info["short_name"] for key, info in evaluation_models.items()}
    normalized_rank_names = {f"{key}_normalized_rank": info["short_name"] for key, info in evaluation_models.items()}

    grouped_jaccard_blocks: dict[str, list[str]] = {"selecciones": [], "ligas": []}
    pearson_blocks: list[str] = []

    for tournament in selected_tournaments:
        tables = build_comparison_tables_for_tournament(
            evaluation_models=evaluation_models,
            tournament=tournament,
            per_90=False,
            top_k=top_k,
        )
        if tables["merged_table"].empty:
            continue

        tournament_label = str(tournament["label"])
        tournament_name = str(tournament["display_name"])

        # ---- Jaccard ----
        jaccard_df = tables["jaccard_df"].copy()
        jaccard_df["model_1"] = jaccard_df["model_1"].map(short_names)
        jaccard_df["model_2"] = jaccard_df["model_2"].map(short_names)

        jaccard_matrix = _build_symmetric_matrix(
            jaccard_df.rename(
                columns={
                    "model_1": "left_model",
                    "model_2": "right_model",
                }
            ),
            labels=list(short_names.values()),
            left_col="left_model",
            right_col="right_model",
            value_col="jaccard_top_k",
        )

        jaccard_block = "\n".join(
            [
                "\\begin{table}[ht]",
                "    \\centering",
                f"{_matrix_to_latex_tabular(tournament_name, jaccard_matrix, list(short_names.values()))}",
                "",
                f"    \\caption{{Índice de Jaccard para top {top_k} jugadores de {tournament_name}}}",
                f"    \\label{{tab:jaccard-{tournament_label}}}",
                "\\end{table}",
            ]
        )
        grouped_jaccard_blocks[_get_tournament_group(tournament)].append(jaccard_block)

        # ---- Pearson / Spearman ----
        pearson_matrix = (
            tables["pearson_df"]
            .rename(
                index=normalized_score_names,
                columns=normalized_score_names,
            )
            .reindex(index=list(short_names.values()), columns=list(short_names.values()))
        )

        spearman_matrix = (
            tables["spearman_df"]
            .rename(
                index=normalized_rank_names,
                columns=normalized_rank_names,
            )
            .reindex(index=list(short_names.values()), columns=list(short_names.values()))
        )

        pearson_blocks.append(
            "\n".join(
                [
                    "\\begin{table}[ht]",
                    "    \\centering",
                    f"{_matrix_to_latex_tabular('Pearson', pearson_matrix, list(short_names.values()))}",
                    "",
                    "\\bigskip",
                    "",
                    f"{_matrix_to_latex_tabular('Spearman', spearman_matrix, list(short_names.values()))}",
                    "",
                    f"    \\caption{{Coeficientes de Pearson y Spearman para {tournament_name}}}",
                    f"    \\label{{tab:coeficientes-{tournament_label}}}",
                    "\\end{table}",
                ]
            )
        )

    latex_sections: list[str] = []

    for group_name, blocks in grouped_jaccard_blocks.items():
        if not blocks:
            continue
        title = "selecciones" if group_name == "selecciones" else "ligas"
        latex_sections.append(
            "\n".join(
                [
                    f"% --- Jaccard: {title} ---",
                    "\n\\bigskip\n".join(blocks),
                ]
            )
        )

    latex_sections.append("% --- Pearson / Spearman por competencia ---")
    latex_sections.extend(pearson_blocks)

    output_text = "\n\n".join(latex_sections)
    output_path.write_text(output_text, encoding="utf-8")
    return output_text
