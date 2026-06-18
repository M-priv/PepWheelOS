from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from peptide_flywheel.validation import build_validation_report, known_artifact_kinds, validate_json_artifacts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate structured JSON artifacts against scaffold model/schema contracts."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more JSON/JSONL files or directories to validate.",
    )
    parser.add_argument(
        "--kind",
        default="auto",
        choices=["auto"] + known_artifact_kinds(),
        help="Expected artifact kind; use auto for mixed inputs.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan directories recursively for *.json and *.jsonl files.",
    )
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="Continue on schema/model errors and report a non-zero summary only.",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Optional path to write a JSON validation report.",
    )
    return parser.parse_args()


def _maybe_dump_report(path: str | None, report: dict) -> None:
    if not path:
        return
    Path(path).write_text(json.dumps(report, indent=2), encoding="utf-8")


def _print_report(report: dict) -> None:
    print("Validation report")
    print(f"- valid: {report['valid_count']}")
    print(f"- invalid: {report['invalid_count']}")
    if report["invalid"]:
        print("Invalid items:")
        for item in report["invalid"]:
            source = item.get("source_path", "")
            message = item.get("message", "")
            payload_index = item.get("payload_index")
            location = f"{source}:{payload_index}" if payload_index is not None else source
            print(f"  - {location}: {message}")


def main() -> None:
    args = _parse_args()
    strict = not args.lenient
    artifacts, failures = validate_json_artifacts(
        args.paths,
        artifact_kind=args.kind,
        recursive=args.recursive,
        strict=False,
    )

    report = build_validation_report(
        artifacts=artifacts,
        failures=failures,
        source_paths=args.paths,
        strict=strict,
    )
    _maybe_dump_report(args.report, report)
    _print_report(report)

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
