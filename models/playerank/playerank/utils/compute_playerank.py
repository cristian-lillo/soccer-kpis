import sys
from pathlib import Path

from ..features import (
    centerOfPerformanceFeature,
    matchPlayedFeatures,
    plainAggregation,
    playerankFeatures,
    qualityFeatures,
    roleFeatures,
)

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parents[4]))

from config import project_paths

# Define Wyscout data file paths
EVENTS_PATHS = str(project_paths.WYSCOUT_PAPPALARDO_DIR / "events" / "*.json")
MATCHES_PATHS = str(project_paths.WYSCOUT_PAPPALARDO_DIR / "matches" / "*.json")
PLAYERS_FILEPATH = str(project_paths.WYSCOUT_PAPPALARDO_DIR / "players.json")

# Define obtained features file paths
FEATURE_WEIGHTS_FILEPATH = str(Path(__file__).parents[2] / "feature_weights.json")
ROLE_MATRIX_FILEPATH = str(Path(__file__).parents[2] / "role_matrix.json")

qualityFeat = qualityFeatures.qualityFeatures()
quality = qualityFeat.createFeature(
    events_path=EVENTS_PATHS,
    players_file=PLAYERS_FILEPATH,
    entity="player",
)

prFeat = playerankFeatures.playerankFeatures()
prFeat.set_features([quality])
pr = prFeat.createFeature(weights_file=FEATURE_WEIGHTS_FILEPATH)

matchPlayedFeat = matchPlayedFeatures.matchPlayedFeatures()
matchplayed = matchPlayedFeat.createFeature(
    matches_path=MATCHES_PATHS,
    players_file=PLAYERS_FILEPATH,
)

center_performance = centerOfPerformanceFeature.centerOfPerformanceFeature()
center_performance = center_performance.createFeature(
    events_path=EVENTS_PATHS,
    players_file=PLAYERS_FILEPATH,
)

roleFeat = roleFeatures.roleFeatures()
roleFeat.set_features([center_performance])
roles = roleFeat.createFeature(matrix_role_file=ROLE_MATRIX_FILEPATH)

aggregation = plainAggregation.plainAggregation()
aggregation.set_features([matchplayed, pr, roles])
df = aggregation.aggregate(to_dataframe=True)

print(df.head())
