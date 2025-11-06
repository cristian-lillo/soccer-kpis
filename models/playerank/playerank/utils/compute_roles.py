import json
import sys
from pathlib import Path

from ..features import centerOfPerformanceFeature, plainAggregation
from ..models import Clusterer

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parents[4]))

from config import project_paths

# Define Wyscout data file paths
EVENTS_PATHS = str(project_paths.WYSCOUT_PAPPALARDO_DIR / "events" / "*.json")
PLAYERS_FILEPATH = str(project_paths.WYSCOUT_PAPPALARDO_DIR / "players.json")

# Define obtained features file paths
ROLE_MATRIX_FILEPATH = str(Path(__file__).parents[2] / "role_matrix.json")


# Compute all quality features (passes accurate, passes failed, shots, etc.)
def compute_roleMatrix(output_path):
    # Get average position for each player in each match
    centerfeat = centerOfPerformanceFeature.centerOfPerformanceFeature()
    centerfeat = centerfeat.createFeature(
        events_path=EVENTS_PATHS,
        players_file=PLAYERS_FILEPATH,
    )

    # Do plain aggregation to get a dataframe
    aggregation = plainAggregation.plainAggregation()
    aggregation.set_features([centerfeat])
    df = aggregation.aggregate(to_dataframe=True)

    # Use clustering object to get the best fit
    clusterer = Clusterer.Clusterer(verbose=True, k_range=(8, 9))
    clusterer.fit(df.entity, df.match, df[["avg_x", "avg_y"]], kind="multi")
    matrix_role = clusterer.get_clusters_matrix(kind="multi")

    json.dump(matrix_role, open(output_path, "w"))


compute_roleMatrix(ROLE_MATRIX_FILEPATH)
