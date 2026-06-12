from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Sequence

import pandas as pd

AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")
SEED_REQUIRED_COLUMNS = [
    "peptide_id",
    "name",
    "sequence",
    "length",
    "source_database",
    "source_organism",
    "target_microbe",
    "gram_status",
    "activity_type",
    "mic_value",
    "mic_unit",
    "assay_conditions",
    "haemolysis_value",
    "cytotoxicity_value",
    "modifications",
    "linear_or_cyclic",
    "net_charge",
    "hydrophobic_fraction",
    "aromatic_count",
    "cysteine_count",
    "methionine_count",
    "asparagine_glutamine_count",
    "known_stability_notes",
    "known_solubility_notes",
    "reference",
    "notes",
]

LIABILITY_REQUIRED_COLUMNS = [
    "peptide_id",
    "name",
    "source_database",
    "source_organism",
    "liability_bucket",
    "liability_type",
    "sequence",
    "target_organism",
    "severity",
    "metric",
    "reference",
    "notes",
]

ALLOWED_LINEAR_CYCLIC = {"linear", "cyclic"}
ALLOWED_SEVERITY = {"low", "medium", "high"}
ALLOWED_GRAM_STATUS = {
    "Gram-positive",
    "Gram-negative",
    "Gram+/Gram-",
    "Fungal",
    "Unknown",
}
ALLOWED_LIABILITY_BUCKET = {"liability", "near-negative"}


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _validate_columns(df: pd.DataFrame, required: Sequence[str], label: str, errors: List[str]) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        errors.append(f"[{label}] Missing columns: {', '.join(missing)}")


def _validate_sequence(sequence: str) -> str:
    sequence = _normalize_text(sequence).upper()
    if not sequence:
        return "Sequence is required"
    invalid = sorted(set(sequence) - AMINO_ACIDS)
    if invalid:
        return f"Invalid residues: {''.join(invalid)}"
    return ""


def validate_seed_rows(df: pd.DataFrame, errors: List[str], warnings: List[str]) -> Dict[str, int]:
    if df.empty:
        warnings.append("[seed] dataset is empty")
        return {"rows": 0, "unique_peptides": 0}

    seen = set()
    for idx, row in df.iterrows():
        line = idx + 2
        peptide_id = _normalize_text(row.get("peptide_id"))
        if not peptide_id:
            errors.append(f"[seed] row {line}: peptide_id is required")
        elif peptide_id in seen:
            errors.append(f"[seed] row {line}: duplicate peptide_id '{peptide_id}'")
        else:
            seen.add(peptide_id)

        sequence = _normalize_text(row.get("sequence"))
        seq_error = _validate_sequence(sequence)
        if seq_error:
            errors.append(f"[seed] row {line}: {seq_error}")

        length = _normalize_text(row.get("length"))
        if not length:
            errors.append(f"[seed] row {line}: length is required")
        else:
            try:
                length_int = int(float(length))
                if length_int != len(sequence):
                    warnings.append(f"[seed] row {line}: length '{length_int}' does not match sequence length {len(sequence)}")
            except ValueError:
                errors.append(f"[seed] row {line}: length '{length}' is not an integer-like value")

        if not _normalize_text(row.get("name")):
            warnings.append(f"[seed] row {line}: name is empty")

        linear_or_cyclic = _normalize_text(row.get("linear_or_cyclic")).lower()
        if not linear_or_cyclic:
            warnings.append(f"[seed] row {line}: linear_or_cyclic is missing")
        elif linear_or_cyclic not in ALLOWED_LINEAR_CYCLIC:
            errors.append(f"[seed] row {line}: linear_or_cyclic '{linear_or_cyclic}' must be one of {sorted(ALLOWED_LINEAR_CYCLIC)}")

        gram_status = _normalize_text(row.get("gram_status"))
        if gram_status and gram_status not in ALLOWED_GRAM_STATUS:
            warnings.append(f"[seed] row {line}: gram_status '{gram_status}' is not in the standard set")
        elif not gram_status:
            warnings.append(f"[seed] row {line}: gram_status is missing")

        if not _normalize_text(row.get("target_microbe")):
            warnings.append(f"[seed] row {line}: target_microbe is missing")

    return {"rows": len(df), "unique_peptides": len(seen)}


def validate_liability_rows(df: pd.DataFrame, seed_ids: set[str], errors: List[str], warnings: List[str]) -> Dict[str, int]:
    if df.empty:
        warnings.append("[liability] dataset is empty")
        return {"rows": 0}

    for idx, row in df.iterrows():
        line = idx + 2
        peptide_id = _normalize_text(row.get("peptide_id"))
        seq = _normalize_text(row.get("sequence"))

        if not peptide_id:
            warnings.append(f"[liability] row {line}: peptide_id is empty")
        elif seed_ids and peptide_id not in seed_ids:
            warnings.append(f"[liability] row {line}: peptide_id '{peptide_id}' not found in seed dataset")

        if not _normalize_text(row.get("name")):
            warnings.append(f"[liability] row {line}: name is empty")

        bucket = _normalize_text(row.get("liability_bucket")).lower()
        if bucket and bucket not in ALLOWED_LIABILITY_BUCKET:
            warnings.append(f"[liability] row {line}: liability_bucket '{bucket}' should be one of {sorted(ALLOWED_LIABILITY_BUCKET)}")
        elif not bucket:
            warnings.append(f"[liability] row {line}: liability_bucket is missing")

        if not _normalize_text(row.get("liability_type")):
            warnings.append(f"[liability] row {line}: liability_type is empty")

        if not seq:
            errors.append(f"[liability] row {line}: sequence is required")
        else:
            seq_error = _validate_sequence(seq)
            if seq_error:
                errors.append(f"[liability] row {line}: {seq_error}")

        severity = _normalize_text(row.get("severity")).lower()
        if severity not in ALLOWED_SEVERITY:
            errors.append(f"[liability] row {line}: severity must be one of {sorted(ALLOWED_SEVERITY)}")

        if not _normalize_text(row.get("metric")):
            warnings.append(f"[liability] row {line}: metric is empty")

        if not _normalize_text(row.get("reference")):
            warnings.append(f"[liability] row {line}: reference is empty")

    return {"rows": len(df)}


def validate(seed_csv: Path, liability_csv: Path) -> int:
    errors: List[str] = []
    warnings: List[str] = []

    seed_df = _read_csv(seed_csv)
    liability_df = _read_csv(liability_csv)

    _validate_columns(seed_df, SEED_REQUIRED_COLUMNS, "seed", errors)
    _validate_columns(liability_df, LIABILITY_REQUIRED_COLUMNS, "liability", errors)

    seed_stats = validate_seed_rows(seed_df, errors, warnings)
    liability_stats = validate_liability_rows(
        liability_df,
        set(seed_df.get("peptide_id", [])),
        errors,
        warnings,
    )

    print("AMP dataset validation report")
    print(f"- seed rows: {seed_stats['rows']}")
    print(f"- unique peptides: {seed_stats['unique_peptides']}")
    print(f"- liability rows: {liability_stats['rows']}")

    if warnings:
        print("Warnings:")
        for warn in warnings:
            print(f"  ! {warn}")

    if errors:
        print("Errors:")
        for err in errors:
            print(f"  x {err}")
        print(f"Validation failed with {len(errors)} error(s)")
        return 1

    print("Validation passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate AMP seed and liability datasets")
    parser.add_argument(
        "--seed",
        default="data/processed/amp_seed_dataset.csv",
        help="Path to amp_seed_dataset.csv",
    )
    parser.add_argument(
        "--liability",
        default="data/processed/amp_liability_examples.csv",
        help="Path to amp_liability_examples.csv",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    seed_path = Path(args.seed)
    liability_path = Path(args.liability)

    if not seed_path.exists():
        raise FileNotFoundError(f"Seed dataset missing: {seed_path}")
    if not liability_path.exists():
        raise FileNotFoundError(f"Liability dataset missing: {liability_path}")

    raise SystemExit(validate(seed_path, liability_path))


if __name__ == "__main__":
    main()
