# Data

This directory contains local inputs for the thesis analyses. It is excluded from Git (`/data/*`) because the repository should not redistribute provider data, private Wyscout data, or large derived HDF5 files. The directory layout below is nevertheless part of the expected interface of the code.

## Directory layout

```text
data/
├── statsbomb/
│   ├── competitions.json
│   ├── matches/<competition_id>/<season_id>.json
│   ├── lineups/<match_id>.json
│   ├── events/<match_id>.json
│   └── three-sixty/<match_id>.json       # optional
├── pappalardo/                           # Auxiliary data for PlayeRank weights
│   ├── competitions.json
│   ├── matches/
│   ├── events/
│   └── players.json, teams.json, ...
├── papers/                               # systematic-review input
└── socceraction/                         # generated SPADL/features/labels
```

The StatsBomb loader is configured in `config/tournaments.py` and `config/paths.py`. The ten competition-season pairs used by the comparative tests are five 2015/2016 European leagues (Premier League, La Liga, Serie A, 1. Bundesliga, and Ligue 1) plus World Cups 2018/2022, UEFA Euros 2020/2024, and Copa America 2024. Every comparative model receives its input from the corresponding local StatsBomb matches, lineups, and events.

## StatsBomb Open Data

Source: [statsbomb/open-data](https://github.com/statsbomb/open-data). It is event data with match metadata, lineups, player information, and tactical annotations. Download or obtain the data directly from StatsBomb, preserve the directory structure above, and follow the provider's terms before using or publishing it. The optional `three-sixty` files are not required by every model.

### Snapshot summary

The current local snapshot, restricted to the ten competition-season datasets used in the comparative evaluation, was counted with `python -m scripts.dataset_summary`:

| Measure | Count |
| --- | ---: |
| Competitions | 10 |
| Seasons/editions | 10 |
| Matches | 2,085 |
| Players (unique `player_id` in lineups) | 4,814 |
| Events | 7,334,694 |

These counts describe the local files selected for the thesis, not a permanent claim about StatsBomb Open Data: future provider updates can change them. The script counts unique match IDs, player IDs, and event records only when the match belongs to one of the ten configured competition-season pairs in `config/tournaments.py`.

## Pappalardo / Wyscout auxiliary data

`pappalardo/` stores the academic Wyscout event dataset and supporting metadata used only to obtain the PlayeRank training weights. Its source is the [Soccer match event dataset](https://figshare.com/collections/Soccer_match_event_dataset/4415000/2). It is not used as an input dataset in the comparative evaluation reported by this project. Verify the original licence and citation requirements before redistribution.

The project may also use a private Wyscout export for Chilean Primera División in local experiments. That data must not be committed or published; it is not required for the public repository to install.

## Other referenced datasets

The following public projects are references or examples rather than required inputs for the main pipeline:

| Dataset | Format/use |
| --- | --- |
| [Metrica Sports sample data](https://github.com/metrica-sports/sample-data) | Tracking and event-data examples |
| [SkillCorner Open Data](https://github.com/SkillCorner/opendata) | Tracking-data examples |
| [Sportec Solutions / DFL](https://doi.org/10.6084/m9.figshare.28196177) | Bundesliga XML match-data example |

## Generated data

The `socceraction/` HDF5 files are derived intermediates used by VAEP (SPADL, features, labels, and predictions). Model CSV outputs are written under `output/`; figures are written under `figures/`. Both are generated locally and ignored by Git. Do not treat these derived files as authoritative inputs: regenerate them after changing data, dependencies, or model code.
