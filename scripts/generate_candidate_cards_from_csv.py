from __future__ import annotations

import argparse
import csv
from pathlib import Path
from textwrap import shorten

REQUIRED_COLUMNS = {
    "peptide_id",
    "name",
    "sequence",
    "target_microbe",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate markdown candidate cards from AMP seed CSV.")
    parser.add_argument(
        "--input",
        default="data/processed/amp_seed_dataset.csv",
        help="Seed dataset path",
    )
    parser.add_argument(
        "--output-dir",
        default="data/results/amp_cards",
        help="Directory for generated .md files",
    )
    return parser.parse_args()


def render_card(row: dict[str, str]) -> str:
    peptide_id = row.get("peptide_id", "AMP-UNK").strip()
    name = row.get("name", "").strip() or peptide_id
    seq = row.get("sequence", "").strip()
    target = row.get("target_microbe", "").strip()
    source = row.get("source_database", "").strip()
    organism = row.get("source_organism", "").strip()
    gram = row.get("gram_status", "").strip()
    activity = row.get("activity_type", "").strip()
    mic = row.get("mic_value", "").strip()
    mic_unit = row.get("mic_unit", "").strip()
    hem = row.get("haemolysis_value", "").strip()
    cyt = row.get("cytotoxicity_value", "").strip()
    mod = row.get("modifications", "").strip()
    topology = row.get("linear_or_cyclic", "").strip()
    charge = row.get("net_charge", "").strip()
    notes = row.get("notes", "").strip() or "No additional notes"

    summary = []
    if gram:
        summary.append(f"Gram status: {gram}")
    if source:
        summary.append(f"Source: {source}")
    if activity and mic and mic_unit:
        summary.append(f"Activity: {activity} {mic} {mic_unit}")

    if not hem:
        hem = "Not reported"
    if not cyt:
        cyt = "Not reported"

    card = f"""# {name}\n\n"""
    card += f"**Peptide ID:** `{peptide_id}`\n\n"
    card += f"**Sequence:** `{seq}`\n\n"
    card += f"**Source organism:** {organism or 'Unknown'}\n\n"
    card += f"**Target organism:** {target or 'Unknown'}\n\n"
    card += "**Key attributes**\n"
    card += f"- Length: {len(seq)}\n"
    card += f"- Topology: {topology or 'Unknown'}\n"
    card += f"- Net charge: {charge or 'Unknown'}\n"
    card += f"- Modifications: {mod or 'none'}\n"
    card += "- " + ", ".join(summary) + "\n\n" if summary else "\n"
    card += f"**Toxicity context**\n"
    card += f"- Haemolysis: {hem}\n"
    card += f"- Cytotoxicity: {cyt}\n\n"
    card += "**Curation notes**\n"
    card += f"{shorten(notes, width=1200, placeholder='...')}\n"
    return card


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_written = 0
    with input_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or []))
            raise ValueError(f"Input CSV missing required columns: {missing}")

        for row in reader:
            peptide_id = row.get("peptide_id", "").strip()
            if not peptide_id:
                continue
            if not row.get("sequence", "").strip():
                continue

            output_path = output_dir / f"{peptide_id}.md"
            output_path.write_text(render_card(row), encoding="utf-8")
            total_written += 1

    print(f"Generated {total_written} candidate cards in {output_dir}")


if __name__ == "__main__":
    main()
