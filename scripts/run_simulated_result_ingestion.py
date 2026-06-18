from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from peptide_flywheel.result_ingestion import (
    failure_mode_counts,
    ingest_simulated_results,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest simulated experimental results and classify failure modes."
    )
    parser.add_argument(
        "result_paths",
        nargs="+",
        help="One or more paths to experimental result markdown/json files.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/results/simulated",
        help="Optional output directory for normalized result artifacts.",
    )
    parser.add_argument(
        "--lenient",
        action="store_true",
        help=(
            "Skip invalid files and continue instead of failing on unknown failure codes "
            "or malformed rows."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    strict = not args.lenient
    result_paths = [Path(path) for path in args.result_paths]
    results, parse_errors = ingest_simulated_results(
        result_paths=result_paths,
        output_dir=args.output_dir,
        strict=strict,
        classify=True,
    )

    if parse_errors:
        for item in parse_errors:
            print(f"WARN: {item}")

    if not results:
        print("No valid result files parsed.")
        if parse_errors:
            raise SystemExit(1)
        return

    counts = failure_mode_counts(results)
    print(f"Ingested {len(results)} simulated result(s).")
    for result in results:
        failures = ", ".join(result.failure_modes) if result.failure_modes else "No failure modes inferred."
        print(f"- {result.result_id} -> {result.candidate_id}: {failures}")

    if counts:
        print("\nFailure mode counts:")
        for mode, count in sorted(counts.items()):
            print(f"- {mode}: {count}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"Ingestion failed: {exc}")
        sys.exit(1)
    
