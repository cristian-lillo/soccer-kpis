"""
Main script to run all player performance evaluation modules.
"""

from models.ea_sports_ppi import ppi_main
from models.opta_points import opta_points_main

# List of models to run
MODELS = ["ea_sports_ppi", "opta_points"]


def calculate_player_performance(models: list[str]):
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


def main():
    calculate_player_performance(MODELS)


if __name__ == "__main__":
    main()
