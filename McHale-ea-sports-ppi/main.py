import index_calculator

# Example player data
player_example = {
    "position": "ST",
    "minutes_played": 90,
    "goals": 2,
    "assists": 1,
    "home_goals": 4,
    "away_goals": 2,
    "team_minutes": 990,
    "clean_sheets": 0,
}

# Calculate and print the player index
player_index = index_calculator.index_score(player_example)
print(f"Player Index: {player_index:.2f}")
