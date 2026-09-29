"""Measure the wall-clock execution time of every evaluation model."""

import argparse
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from config import paths
from scripts.main import EVALUATION_MODELS_INFO


class BenchmarkResult(TypedDict):
    model: str
    display_name: str
    status: str
    started_at: str
    finished_at: str
    elapsed_seconds: float
    error: str


def _save_results(output_path: Path, results: list[BenchmarkResult]) -> None:
    """Persist the current results after each model."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    with temporary_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=BenchmarkResult.__annotations__)
        writer.writeheader()
        writer.writerows(results)
    temporary_path.replace(output_path)


def benchmark_models(
    output_path: Path | None = None,
    failed_only: bool = False,
    resume: bool = False,
) -> list[BenchmarkResult]:
    """Run selected models and save a checkpoint after each execution."""
    results_by_model: dict[str, BenchmarkResult] = {}
    if output_path is not None and output_path.exists():
        with output_path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                results_by_model[row["model"]] = {
                    "model": row["model"],
                    "display_name": row["display_name"],
                    "status": row["status"],
                    "started_at": row.get("started_at", ""),
                    "finished_at": row.get("finished_at", ""),
                    "elapsed_seconds": float(row["elapsed_seconds"]),
                    "error": row.get("error", ""),
                }

    for model, model_info in EVALUATION_MODELS_INFO.items():
        previous_result = results_by_model.get(model)
        if failed_only and (previous_result is None or previous_result["status"] != "failed"):
            print(f"Omitiendo {model_info['display_name']}: no está marcado como fallido.")
            continue
        if resume and previous_result is not None and previous_result["status"] == "completed":
            print(f"Omitiendo {model_info['display_name']}: ya está completado.")
            continue

        print(f"Ejecutando {model_info['display_name']}...")
        started_at = datetime.now().astimezone()
        started = time.perf_counter()
        try:
            model_info["script"].main()
        except Exception as error:  # noqa: BLE001
            elapsed = time.perf_counter() - started
            finished_at = datetime.now().astimezone()
            result: BenchmarkResult = {
                "model": model,
                "display_name": model_info["display_name"],
                "status": "failed",
                "started_at": started_at.isoformat(timespec="seconds"),
                "finished_at": finished_at.isoformat(timespec="seconds"),
                "elapsed_seconds": round(elapsed, 3),
                "error": f"{type(error).__name__}: {error}",
            }
            print(f"  FALLÓ después de {elapsed:.3f} s: {result['error']}")
        else:
            elapsed = time.perf_counter() - started
            finished_at = datetime.now().astimezone()
            result = {
                "model": model,
                "display_name": model_info["display_name"],
                "status": "completed",
                "started_at": started_at.isoformat(timespec="seconds"),
                "finished_at": finished_at.isoformat(timespec="seconds"),
                "elapsed_seconds": round(elapsed, 3),
                "error": "",
            }
            print(f"  completado en {elapsed:.3f} s")

        results_by_model[model] = result
        if output_path is not None:
            _save_results(output_path, list(results_by_model.values()))

    return list(results_by_model.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=paths.OUTPUT_DIR / "model_runtime_benchmark.csv",
        help="CSV path for the measured times.",
    )
    parser.add_argument(
        "--failed-only",
        action="store_true",
        help="Run only models marked as failed in the existing CSV.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip models already marked as completed in the existing CSV.",
    )
    args = parser.parse_args()
    benchmark_models(args.output, failed_only=args.failed_only, resume=args.resume)
