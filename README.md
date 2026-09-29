# Soccer KPIs

Soccer KPIs is the code repository for Cristian Lillo's Master of Science in Computer Science thesis at the University of Chile. It implements and compares player-performance measures derived from event data, using a common StatsBomb processing pipeline and a reproducible set of analyses and figures.

## What is included

The repository contains six evaluation models:

- **Plus-Minus**
- **Pentagonal Score**
- **PlayeRank**
- **VAEP** (Valuing Actions by Estimating Probabilities)
- **EA Sports PPI**
- **Opta Points**

`config/` centralizes project paths, the competitions/seasons used in the thesis, and player extraction helpers. `models/` contains one implementation per method. `scripts/main.py` runs models when enabled, normalizes their scores, produces comparison tables, computes Pearson/Spearman correlations and Jaccard similarity, and generates figures. `notebooks/` contains exploratory and presentation material.

## Repository layout

```text
soccer-kpis/
├── config/       # Paths, tournament definitions, and player utilities
├── data/         # Local datasets; see data/README.md
├── models/       # Six player-performance model implementations
├── notebooks/    # Exploration and thesis analyses
├── scripts/      # Analysis, plotting, summary, and benchmark scripts
├── output/       # Generated model tables and comparisons
├── figures/      # Generated PDF/PNG figures
├── pyproject.toml
└── README.md
```

`data/`, `output/` CSV/TEX files, and `figures/` are intentionally ignored by Git. They are local inputs or generated artefacts, not source code. A fresh clone therefore needs the datasets and generated model outputs to be restored locally before reproducing all analyses. See [`data/README.md`](data/README.md).

## Requirements and installation

The project is tested with **Python 3.12**. Python 3.13 is not currently supported by all analytical dependencies.

```bash
git clone https://github.com/cristian-lillo/soccer-kpis.git
cd soccer-kpis
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install the project and its dependencies:

```bash
python -m pip install -e .
```

The local StatsBomb snapshot must be placed under `data/statsbomb/` with `competitions.json`, `matches/`, `lineups/`, `events/`, and, when available, `three-sixty/`. The repository does not redistribute provider data; consult StatsBomb's [Open Data repository](https://github.com/statsbomb/open-data) and its terms of use.

## Running the analyses

From the repository root, use module execution so the local packages resolve correctly:

```bash
python -m scripts.main
```

Python normally creates `__pycache__/` directories when importing modules. They are ignored by Git, but can be disabled during local runs with `-B` or `PYTHONDONTWRITEBYTECODE=1`:

```bash
# Windows PowerShell
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m scripts.main

# One command, any shell
python -B -m scripts.main
```

The script currently runs comparisons and figures for the ten configured competition-season datasets. Model execution is guarded by `run_models_flag` in `scripts/main.py`; set it to `True` only when model outputs need to be regenerated. The resulting tables are written under `output/comparisons/`, and figures under `figures/`, in PDF and PNG formats. Per-90 analyses use the same minimum-playing-time population as the correlations: 450 minutes for club leagues and 180 minutes for national-team tournaments.

Two local utility scripts provide the requested dataset and computational summaries:

```bash
python -m scripts.dataset_summary
python -m scripts.benchmark_models
```

To retry only models recorded as failed in the existing checkpoint, use:

```bash
python -m scripts.benchmark_models --failed-only
```

To skip completed models and run everything else, use `--resume`. The plotting functions are kept in `scripts/plots.py`, while `scripts/comparisons.py` calculates correlations, Jaccard similarities, ranking tables, and LaTeX output. Shared filtering and score-normalization helpers are in `scripts/utils.py`; `scripts/main.py` only orchestrates model execution and calls these modules. The first utility prints the number of competitions, seasons/editions, matches, players, and events in the local StatsBomb snapshot. The second executes each model over the configured dataset, measures wall-clock time with `time.perf_counter()`, records each model's start and finish timestamps, and writes checkpoint results to `output/model_runtime_benchmark.csv`. These files are supplementary local tooling and can be omitted from a final source release if only the thesis artefacts are required.

## Data sources

The comparative evaluation uses the local StatsBomb Open Data snapshot for all competitions, seasons, matches, players, and events. The Wyscout/Pappalardo dataset is retained only as an auxiliary source for the PlayeRank training weights; it is not part of the comparative tests. Detailed provenance, directory conventions, licensing notes, and the current StatsBomb snapshot summary are documented in [`data/README.md`](data/README.md).

## Reproducibility notes

Model scores depend on the exact local data snapshot, Python version, dependency versions, and machine. Runtime measurements are therefore descriptive rather than hardware-independent complexity claims. Generated CSV, TEX, and figure files should be regenerated locally rather than committed as source inputs.

## Author and acknowledgement

**Cristian Lillo Ciero**
Master of Science in Computer Science, University of Chile

This work acknowledges the University of Chile Department of Computer Science, the [PySport](https://github.com/PySport) community, StatsBomb, Wyscout, and the authors of the methods implemented in this repository.

## License and data use

The source code is provided for academic and research purposes. Each external dataset remains subject to its provider's licence and terms. In particular, publishing this code does not grant permission to redistribute StatsBomb or private Wyscout data.
