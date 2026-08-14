from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from peptide_flywheel.agent_contracts import (
    AgentRetryPolicy,
    evaluate_agent_output,
    load_prompt_packet,
)
from peptide_flywheel.ast_repair import deterministic_ast_normalization


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an agent JSON output against a prompt packet contract."
    )
    parser.add_argument("--packet", required=True, help="Prompt packet JSON file.")
    parser.add_argument("--output", required=True, help="Agent output JSON file.")
    parser.add_argument("--attempt", type=int, default=1, help="Attempt number for retry policy.")
    parser.add_argument("--max-attempts", type=int, default=3, help="Maximum retry attempts.")
    parser.add_argument(
        "--no-auto-repair",
        action="store_true",
        help="Disable automatic deterministic AST normalization before evaluation.",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Optional path to write the contract evaluation JSON.",
    )
    parser.add_argument(
        "--retry-packet",
        default=None,
        help="Optional path to write a retry packet when retry is recommended.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    packet = load_prompt_packet(args.packet)
    raw_text = Path(args.output).read_text(encoding="utf-8")

    # Apply deterministic AST repair if enabled and valid JSON
    raw_output = raw_text
    repairs_log = []
    if not args.no_auto_repair:
        try:
            parsed_json = json.loads(raw_text)
            if isinstance(parsed_json, dict):
                expected_ctx = packet.input_payload
                normalized_doc, repairs_log = deterministic_ast_normalization(parsed_json, expected_ctx)
                raw_output = json.dumps(normalized_doc)
        except Exception:
            pass  # Fall through to standard contract evaluation error reporting

    evaluation = evaluate_agent_output(
        packet=packet,
        raw_output=raw_output,
        attempt=args.attempt,
        retry_policy=AgentRetryPolicy(max_attempts=args.max_attempts),
    )
    payload = evaluation.to_dict()
    payload["deterministic_repairs"] = repairs_log


    if args.report:
        Path(args.report).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.retry_packet and evaluation.retry_packet is not None:
        Path(args.retry_packet).write_text(
            json.dumps(evaluation.retry_packet.model_dump(), indent=2),
            encoding="utf-8",
        )

    print("Agent contract evaluation")
    print(f"- packet: {evaluation.packet_id}")
    print(f"- artifact: {evaluation.artifact}")
    print(f"- passed: {evaluation.passed}")
    print(f"- retry recommended: {evaluation.retry_recommended}")
    for error in evaluation.errors:
        print(f"  - ERROR: {error}")
    for warning in evaluation.warnings:
        print(f"  - WARN: {warning}")

    if not evaluation.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
