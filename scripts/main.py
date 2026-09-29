"""
Main script to run evaluation models and compare their outputs.

This script orchestrates the execution of different player performance evaluation models, normalizes their scores, and generates comparison tables and plots for analysis.

The evaluation models included are:
- Plus-Minus
- Pentagonal Score
- PlayeRank
- VAEP
- EA Sports PPI
- Opta Points
"""

from itertools import product

from config import paths, tournaments
from models.ea_sports_ppi import ppi_main
from models.opta_points import opta_points_main
from models.pentagonal import pentagonal_main
from models.playerank import playerank_main
from models.plus_minus import plus_minus_main
from models.vaep import vaep_main
from scripts import plots

EVALUATION_MODELS_INFO = {
    "plus_minus": {
        "display_name": "Plus-Minus",
        "short_name": "PM",
        "performance_score": "plus_minus_score",
        "script": plus_minus_main,
        "output_directory": paths.PLUS_MINUS_OUTPUT_DIR,
        "plot_color": "tab:red",
    },
    "pentagonal": {
        "display_name": "Pentagonal Score",
        "short_name": "PS",
        "performance_score": "pentagonal_score",
        "script": pentagonal_main,
        "output_directory": paths.PENTAGONAL_SCORE_OUTPUT_DIR,
        "plot_color": "tab:cyan",
    },
    "playerank": {
        "display_name": "PlayeRank",
        "short_name": "PR",
        "performance_score": "playerank_rating",
        "script": playerank_main,
        "output_directory": paths.PLAYERANK_OUTPUT_DIR,
        "plot_color": "tab:green",
    },
    "vaep": {
        "display_name": "VAEP",
        "short_name": "VAEP",
        "performance_score": "vaep_value",
        "script": vaep_main,
        "output_directory": paths.VAEP_OUTPUT_DIR,
        "plot_color": "tab:purple",
    },
    "ea_sports_ppi": {
        "display_name": "EA Sports PPI",
        "short_name": "PPI",
        "performance_score": "index_score",
        "script": ppi_main,
        "output_directory": paths.EA_SPORTS_PPI_OUTPUT_DIR,
        "plot_color": "tab:blue",
    },
    "opta_points": {
        "display_name": "Opta Points",
        "short_name": "OP",
        "performance_score": "opta_points",
        "script": opta_points_main,
        "output_directory": paths.OPTA_POINTS_OUTPUT_DIR,
        "plot_color": "tab:orange",
    },
}


def run_evaluation_models(evaluation_models: dict[str, dict] = EVALUATION_MODELS_INFO):
    """
    Calculate player performance using different models.

    Args:
        evaluation_models : Dictionary of model names and their information to run.
    """
    for model_info in evaluation_models.values():
        model_info["script"].main()


def main():
    """Main function to execute the evaluation models and compare their outputs."""

    run_models_flag = False
    if run_models_flag:
        run_evaluation_models(EVALUATION_MODELS_INFO)

    compare_models_flag = True
    if compare_models_flag:
        selected_tournaments = tournaments.ALL_TOURNAMENTS

        for format, per_90 in product(["pdf", "png"], [False, True]):
            print(f"\nGenerando gráficos | formato={format} | per_90={per_90}")

            plots.generate_plots_for_score_per_match(
                selected_tournaments,
                per_90=per_90,
                format=format,
                evaluation_models=EVALUATION_MODELS_INFO,
            )

            plots.generate_plots_for_model_scores(
                selected_tournaments,
                per_90=per_90,
                format=format,
                evaluation_models=EVALUATION_MODELS_INFO,
            )

            # comparisons.generate_comparison_tables(
            #     EVALUATION_MODELS_INFO,
            #     selected_tournaments,
            #     per_90=per_90,
            #     top_k=10,
            #     save_plots=True,
            #     format=format,
            # )

        # comparisons.generate_latex_comparison_tables(
        #     EVALUATION_MODELS_INFO,
        #     selected_tournaments,
        #     top_k=10,
        #     output_filename="comparison_tables_total.tex",
        # )


if __name__ == "__main__":
    main()
