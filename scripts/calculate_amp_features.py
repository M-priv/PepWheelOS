from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

SEED_COLUMNS = {
    "length",
    "net_charge",
    "hydrophobic_fraction",
    "aromatic_count",
    "cysteine_count",
    "methionine_count",
    "asparagine_glutamine_count",
}

HYDROPHOBIC = set("AILMFWVYCGP")
AROMATIC = set("FWY")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate antimicrobial peptide manufacturability features.")
    parser.add_argument("--input", default="data/processed/amp_seed_dataset.csv", help="Input seed dataset")
    parser.add_argument("--output", default=None, help="Output CSV path; defaults to input_with_features.csv")
    return parser.parse_args()


def normalize(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def calculate_features(seq: str) -> dict[str, float | int]:
    seq = normalize(seq)
    length = len(seq)
    if length == 0:
        raise ValueError("Empty sequence encountered while calculating features")

    net_charge = seq.count("K") + seq.count("R") + 0.1 * seq.count("H") - seq.count("D") - seq.count("E")
    hydrophobic_count = sum(1 for aa in seq if aa in HYDROPHOBIC)
    aromatic_count = sum(1 for aa in seq if aa in AROMATIC)
    cys_count = seq.count("C")
    met_count = seq.count("M")
    asparagine_glutamine_count = seq.count("N") + seq.count("Q")

    return {
        "length": length,
        "net_charge": int(math.floor(net_charge)) if net_charge.is_integer() else round(net_charge, 2),
        "hydrophobic_fraction": round(hydrophobic_count / length, 4),
        "aromatic_count": aromatic_count,
        "cysteine_count": cys_count,
        "methionine_count": met_count,
        "asparagine_glutamine_count": asparagine_glutamine_count,
    }


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    if "sequence" not in df.columns:
        raise ValueError("Input CSV must contain a 'sequence' column")

    feature_rows = []
    for idx, row in df.iterrows():
        seq = normalize(row["sequence"])
        feats = calculate_features(seq)
        feature_rows.append(feats)

    feature_df = pd.DataFrame(feature_rows)

    out = df.reset_index(drop=True).copy()
    for col in SEED_COLUMNS:
        out[col] = feature_df[col]

    output_path = Path(args.output or str(input_path.with_name(f"{input_path.stem}_with_features.csv")))
    out.to_csv(output_path, index=False)
    print(f"Wrote feature-enriched dataset: {output_path}")


if __name__ == "__main__":
    main()
