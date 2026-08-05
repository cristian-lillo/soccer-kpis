import warnings
from enum import Enum

import pandas as pd
from kloppy import statsbomb
from kloppy.domain import (
    CardType,
    Event,
    EventDataset,
    EventType,
    Qualifier,
    ResultType,
)
from socceraction.data.statsbomb import StatsBombLoader

from config import paths

# Columns to extract from the StatsBomb event data
COLUMNS_TO_EXTRACT = [
    "player_id",
    "player",
    "team_id",
    "team",
    "event_id",
    "event_type",
    "result",
    "success",
    "body_part_type",
    "pass_type",
    "duel_type",
    "set_piece_type",
    "goalkeeper_type",
    "card_type",
    "replacement_player",
    "is_counter_attack",
    "is_under_pressure",
    "coordinates_x",
    "coordinates_y",
    "time",
]

# Data types for each column
DTYPE_MAPPING = {
    "player_id": "Int64",
    "player": "string",
    "team_id": "Int64",
    "team": "string",
    "event_id": "string",
    "event_type": "category",
    "result": "category",
    "success": "boolean",
    "body_part_type": "category",
    "pass_type": "category",
    "duel_type": "category",
    "set_piece_type": "category",
    "goalkeeper_type": "category",
    "card_type": "category",
    "replacement_player": "string",
    "is_counter_attack": "boolean",
    "is_under_pressure": "boolean",
    "coordinates_x": "Float64",
    "coordinates_y": "Float64",
    "time": "string",
}

warnings.filterwarnings(
    "ignore",
    message="Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated and will change in a future version.",
    category=FutureWarning,
)


def get_players_info(match_id: int) -> pd.DataFrame:
    """
    Retrieve player information for a given match.

    Args:
        match_id (int): StatsBomb match ID.

    Returns:
        DataFrame containing player names, nicknames, team names, and minutes played.
    """
    SBL = StatsBombLoader(getter="local", root=str(paths.STATSBOMB_DIR))

    players_df = SBL.players(game_id=match_id)
    teams_df = SBL.teams(game_id=match_id)

    merged_df = players_df.merge(teams_df, on="team_id", how="left")

    return merged_df[["player_name", "nickname", "team_name", "minutes_played"]]


def load_match_data(match_id: int) -> tuple[EventDataset, pd.DataFrame]:
    """
    Load the event dataset and convert it to a DataFrame for a given match.

    Args:
        match_id: StatsBomb match ID.

    Returns:
        A tuple containing the EventDataset and a DataFrame of events for the match.
    """
    dataset = statsbomb.load(
        event_data=paths.STATSBOMB_EVENTS_DIR / f"{match_id}.json",
        lineup_data=paths.STATSBOMB_LINEUPS_DIR / f"{match_id}.json",
    )

    filtered_dataset = dataset.filter(lambda event: event.period.id != 5)  # Filter out events from penalty shootouts
    events_df = filtered_dataset.to_df(*COLUMNS_TO_EXTRACT).astype(DTYPE_MAPPING)

    return filtered_dataset, events_df


def get_players_position_group(dataset: EventDataset) -> dict[str, str]:
    """
    Determine the main position group of all players based on time spent in each position.

    Args:
        dataset: The event dataset containing player position data.

    Returns:
        The main position group of each player as a dictionary.
    """
    player_positions = {}

    for team in dataset.metadata.teams:
        for player in team.players:
            player_position = ("Unknown", 0)

            for start_time, end_time, position in player.positions.ranges():
                position_duration = (end_time - start_time).total_seconds()
                position_group = position.position_group.name

                # Compare and update the variable if this position has longer duration
                prev_position, prev_duration = player_position
                if position_group != prev_position and position_duration > prev_duration:
                    player_position = (position_group, position_duration)

            player_positions[player.name] = player_position[0]

    return player_positions


def calculate_metric_for_player_dataset(
    dataset: EventDataset,
    type_filter: EventType,
    result_filter: list[ResultType] | ResultType | None = None,
    qualifier_filter: list[Enum] | Enum | None = None,
    card_filter: list[CardType] | CardType | None = None,
    exclude_qualifier: bool = False,
) -> int:
    """
    Count the number of specific events for a player in the dataset.

    Args:
        dataset: The specific player's event dataset.
        type_filter: The event type to filter for (e.g., EventType.PASS, EventType.SHOT).
        result_filter: The result or list of results of the event to filter for (e.g., PassResult.COMPLETE).
        qualifier_filter: The qualifier or list of qualifiers to count (e.g., PassType.ASSIST).
        card_filter: The card type or list of card types to filter for (e.g., CardType.FIRST_YELLOW, CardType.RED).
        exclude_qualifier: If True, counts events that do not have the specified qualifier(s).

    Returns:
        The count of the specified event.
    """

    def compare_type_filter(
        event_type: EventType,
        type_filter: EventType | None,
    ) -> bool:
        """Compare the event type with the type filter."""
        if type_filter is None:
            return True
        return event_type == type_filter

    def compare_result_filter(
        event_result: ResultType,
        result_filter: list[ResultType] | ResultType | None,
    ) -> bool:
        """Compare the event result with the result filter."""
        if result_filter is None:
            return True
        if not hasattr(event_result, "value"):
            return False
        if isinstance(result_filter, list):
            return event_result in result_filter
        return event_result == result_filter

    def compare_qualifier_filter(
        event_qualifiers: list[Qualifier] | None,
        qualifier_filter: list[Qualifier] | Qualifier | None,
        exclude_qualifier: bool,
    ) -> bool:
        """Compare the event qualifiers with the qualifier filter."""
        if qualifier_filter is None:
            return True
        if not hasattr(event_qualifiers, "__iter__"):
            return False
        if isinstance(qualifier_filter, list):
            has_match = any(q.value in qualifier_filter for q in event_qualifiers)  # type: ignore
        else:
            has_match = any(q.value == qualifier_filter for q in event_qualifiers)  # type: ignore

        return not has_match if exclude_qualifier else has_match

    def compare_card_filter(
        event: Event,
        card_filter: list[CardType] | CardType | None,
    ):
        """Compare the event card type with the card filter."""
        if card_filter is None:
            return True
        if not hasattr(event, "card_type"):
            return False
        if isinstance(card_filter, list):
            return event.card_type in card_filter  # type: ignore
        return event.card_type == card_filter  # type: ignore

    filtered_dataset = dataset.filter(
        lambda event: (
            event.period.id != 5
            and compare_type_filter(event.event_type, type_filter)
            and compare_result_filter(event.result, result_filter)  # type: ignore
            and compare_qualifier_filter(event.qualifiers, qualifier_filter, exclude_qualifier)  # type: ignore
            and compare_card_filter(event, card_filter)  # type: ignore
        )
    )

    return len(filtered_dataset.events)
