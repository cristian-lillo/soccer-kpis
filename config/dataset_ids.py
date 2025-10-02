"""
Dataset IDs configuration for model training and testing.
Contains match and player IDs from different providers and competitions.
"""

# StatsBomb Dataset IDs
STATSBOMB = {
    "big_5_leagues_2015_16": {
        "matches": [],  # Match IDs from big 5 European leagues 2015/16
        "players": [],  # Player IDs
    },
    "world_cup_2018": {
        "matches": [],
        "players": [],
    },
    "world_cup_2022": {
        "matches": [],
        "players": [],
    },
    "euro_2020": {
        "matches": [],
        "players": [],
    },
    "euro_2024": {
        "matches": [3943043],  # Example: Final
        "players": [316046],  # Example: Lamine Yamal
    },
}

# Chilean League Dataset IDs (Wyscout format)
CHILE_WYSCOUT = {
    "season_2022": {
        "matches": [],
        "players": [],
    },
    "season_2023": {
        "matches": [],
        "players": [],
    },
    "season_2024": {
        "matches": [],
        "players": [],
    },
}

# Training/Testing split configuration
TRAINING_TEST_SPLIT = {
    "train_ratio": 0.8,
    "test_ratio": 0.2,
    "random_seed": 42,
}
