from pathlib import Path

from peptide_flywheel.result_ingestion import (
    classify_failure_modes,
    parse_experimental_result_file,
)


def test_parse_and_classify_simulated_result(tmp_path: Path) -> None:
    payload = """# Simulated Experimental Result

Result ID: RESULT-TEST-001
Candidate ID: CAND-TEST-001
Campaign ID: CAMPAIGN-TEST
Result type: Simulated assay result

## Summary

No antimicrobial activity was observed at the top dose tested.

## Key values

| Metric | Value | Notes |
|---|---:|---|
| Yield (%) | 12 | Low yield at prep scale |
| Solubility (mg/mL) | 0.3 | Precipitated near max test concentration |

## Interpretation

Interpretation was inconsistent with intermittent high background across repeats.

## Failure modes

- NO_BINDING
"""
    result_file = tmp_path / "sim_result.md"
    result_file.write_text(payload, encoding="utf-8")

    result = parse_experimental_result_file(result_file, strict=False)
    result.failure_modes = classify_failure_modes(result, strict=False)

    assert result.result_id == "RESULT-TEST-001"
    assert result.candidate_id == "CAND-TEST-001"
    assert "NO_BINDING" in result.failure_modes
    assert "SYN_LOW_YIELD" in result.failure_modes
    assert "LOW_AQUEOUS_SOLUBILITY" in result.failure_modes
