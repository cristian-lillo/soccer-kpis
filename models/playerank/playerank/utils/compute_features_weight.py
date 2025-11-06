import sys
from pathlib import Path

from ..features import goalScoredFeatures, qualityFeatures, relativeAggregation
from ..models import Weighter

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parents[4]))

from config import project_paths

# Define Wyscout data file paths
EVENTS_PATHS = str(project_paths.WYSCOUT_PAPPALARDO_DIR / "events" / "*.json")
PLAYERS_FILEPATH = str(project_paths.WYSCOUT_PAPPALARDO_DIR / "players.json")

# Define obtained features file paths
FEATURE_WEIGHTS_FILEPATH = str(Path(__file__).parents[2] / "feature_weights.json")


def compute_feature_weights(output_path):
    qualityFeat = qualityFeatures.qualityFeatures()
    quality = qualityFeat.createFeature(
        events_path=EVENTS_PATHS,
        players_file=PLAYERS_FILEPATH,
        entity="team",
    )

    # Compute goals scored for each team in each match
    gs = goalScoredFeatures.goalScoredFeatures()
    goals = gs.createFeature("playerank/data/matches")

    # Merge quality features and goals scored
    aggregation = relativeAggregation.relativeAggregation()
    aggregation.set_features([quality, goals])
    df = aggregation.aggregate(to_dataframe=True)

    # Compute features weights
    weighter = Weighter.Weighter(label_type="wd-l")
    weighter.fit(df, "goal-scored", filename=output_path)
    print(f"Features weights stored in {output_path}")


compute_feature_weights(FEATURE_WEIGHTS_FILEPATH)
