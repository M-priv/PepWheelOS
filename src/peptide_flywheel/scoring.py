from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


HYDROPHOBIC = set("AILMFWYV")
CHARGED_POSITIVE = set("KRH")
CHARGED_NEGATIVE = set("DE")
OXIDATION_RISK = set("MWC")
DEAMIDATION_RISK = set("NQ")


@dataclass
class ScoreResult:
    dimension_scores: Dict[str, float]
    risk_flags: List[str]
    overall_score: float
    recommendation: str


def calculate_basic_sequence_features(sequence: str) -> Dict[str, float]:
    sequence = sequence.upper().strip()
    length = len(sequence)
    if length == 0:
        raise ValueError("Sequence cannot be empty.")

    hydrophobic_fraction = sum(aa in HYDROPHOBIC for aa in sequence) / length
    net_charge_proxy = sum(aa in CHARGED_POSITIVE for aa in sequence) - sum(aa in CHARGED_NEGATIVE for aa in sequence)
    oxidation_count = sum(aa in OXIDATION_RISK for aa in sequence)
    deamidation_count = sum(aa in DEAMIDATION_RISK for aa in sequence)
    cysteine_count = sequence.count("C")

    return {
        "length": float(length),
        "hydrophobic_fraction": hydrophobic_fraction,
        "net_charge_proxy": float(net_charge_proxy),
        "oxidation_count": float(oxidation_count),
        "deamidation_count": float(deamidation_count),
        "cysteine_count": float(cysteine_count),
    }


def heuristic_manufacturability_score(sequence: str, modality: str = "linear") -> ScoreResult:
    features = calculate_basic_sequence_features(sequence)
    risk_flags: List[str] = []

    score = 100.0

    length = features["length"]
    hydrophobic_fraction = features["hydrophobic_fraction"]
    net_charge_abs = abs(features["net_charge_proxy"])
    oxidation_count = features["oxidation_count"]
    deamidation_count = features["deamidation_count"]
    cysteine_count = features["cysteine_count"]

    if length > 35:
        score -= 15
        risk_flags.append("SEQUENCE_LENGTH_RISK")
    if length > 50:
        score -= 20
        risk_flags.append("LONG_PEPTIDE_HIGH_COMPLEXITY")

    if hydrophobic_fraction > 0.45:
        score -= 20
        risk_flags.append("HYDROPHOBIC_AGGREGATION_RISK")
    if hydrophobic_fraction < 0.15:
        score -= 5
        risk_flags.append("VERY_LOW_HYDROPHOBICITY_CHECK_BINDING_PLAUSIBILITY")

    if net_charge_abs > 6:
        score -= 10
        risk_flags.append("HIGH_NET_CHARGE_RISK")

    if oxidation_count >= 3:
        score -= 8
        risk_flags.append("OXIDATION_LIABILITY")

    if deamidation_count >= 3:
        score -= 8
        risk_flags.append("DEAMIDATION_LIABILITY")

    if cysteine_count not in (0, 2, 4):
        score -= 10
        risk_flags.append("CYSTEINE_PAIRING_COMPLEXITY")

    if modality in {"cyclic", "stapled", "modified"}:
        score -= 5
        risk_flags.append("MODIFICATION_COMPLEXITY_REVIEW")

    score = max(0.0, min(100.0, score))

    if score >= 80:
        recommendation = "test_or_keep"
    elif score >= 60:
        recommendation = "revise_or_test_with_caution"
    else:
        recommendation = "revise_before_testing"

    dimension_scores = {
        "length_risk": max(0.0, 100.0 - max(0.0, length - 35) * 2),
        "hydrophobicity_risk": max(0.0, 100.0 - max(0.0, hydrophobic_fraction - 0.45) * 200),
        "charge_risk": max(0.0, 100.0 - max(0.0, net_charge_abs - 6) * 8),
        "oxidation_risk": max(0.0, 100.0 - oxidation_count * 5),
        "deamidation_risk": max(0.0, 100.0 - deamidation_count * 5),
        "cysteine_complexity_risk": max(0.0, 100.0 - cysteine_count * 4),
    }

    return ScoreResult(
        dimension_scores=dimension_scores,
        risk_flags=risk_flags,
        overall_score=score,
        recommendation=recommendation,
    )
