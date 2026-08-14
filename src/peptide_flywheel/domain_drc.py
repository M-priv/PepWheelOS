from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple


class DRCSeverity(str, Enum):
    FATAL = "fatal"          # Hard stop; peptide should not be synthesized as designed
    HIGH_RISK = "high_risk"  # Significant liability requiring special synthesis/formulation conditions
    WARNING = "warning"      # Moderate liability requiring monitoring
    INFO = "info"


# Kyte & Doolittle Hydropathicity Scale (J. Mol. Biol. 1982)
KYTE_DOOLITTLE = {
    "A": 1.8, "C": 2.5, "D": -3.5, "E": -3.5, "F": 2.8,
    "G": -0.4, "H": -3.2, "I": 4.5, "K": -3.9, "L": 3.8,
    "M": 1.9, "N": -3.5, "P": -1.6, "Q": -3.5, "R": -4.5,
    "S": -0.8, "T": -0.7, "V": 4.2, "W": -0.9, "Y": -1.3,
}

# Standard pKa values (EMBOSS / Lehninger)
PKA_N_TERM = 9.69
PKA_C_TERM = 2.34
PKA_SIDE_CHAINS = {
    "K": 10.53, "R": 12.48, "H": 6.00,  # Basic (positive when protonated)
    "D": 3.86, "E": 4.25, "C": 8.33, "Y": 10.07,  # Acidic (negative when deprotonated)
}


@dataclass
class DRCRuleViolation:
    rule_id: str
    rule_name: str
    severity: DRCSeverity
    failure_code: str  # maps to docs/04_failure_ontology.md
    message: str
    culprit_motif: Optional[str] = None
    positions: List[int] = field(default_factory=list)  # 1-indexed


@dataclass
class DRCSummary:
    sequence: str
    modality: str
    passed_hard_drc: bool
    violations: List[DRCRuleViolation]
    net_charge_ph74: float
    gravy_index: float
    hard_stop_reasons: List[str]
    suggested_remediations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence": self.sequence,
            "modality": self.modality,
            "passed_hard_drc": self.passed_hard_drc,
            "net_charge_ph74": round(self.net_charge_ph74, 3),
            "gravy_index": round(self.gravy_index, 3),
            "violation_count": len(self.violations),
            "hard_stop_reasons": self.hard_stop_reasons,
            "suggested_remediations": self.suggested_remediations,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                    "severity": v.severity.value,
                    "failure_code": v.failure_code,
                    "message": v.message,
                    "culprit_motif": v.culprit_motif,
                    "positions": v.positions,
                }
                for v in self.violations
            ],
        }


# --- Biological DRC Invariant Rule Checkers ---

def calculate_net_charge(sequence: str, ph: float = 7.4) -> float:
    """Calculate net molecular charge using Henderson-Hasselbalch equilibrium."""
    from collections import Counter
    counts = Counter(sequence)
    charge = (1.0 / (1.0 + 10.0 ** (ph - PKA_N_TERM))) - (1.0 / (1.0 + 10.0 ** (PKA_C_TERM - ph)))

    for aa in ("K", "R", "H"):
        if counts[aa]:
            charge += counts[aa] / (1.0 + 10.0 ** (ph - PKA_SIDE_CHAINS[aa]))
    for aa in ("D", "E", "C", "Y"):
        if counts[aa]:
            charge -= counts[aa] / (1.0 + 10.0 ** (PKA_SIDE_CHAINS[aa] - ph))

    return charge



def calculate_gravy(sequence: str) -> float:
    """Calculate Grand Average of Hydropathicity (GRAVY)."""
    if not sequence:
        return 0.0
    return sum(KYTE_DOOLITTLE.get(aa, 0.0) for aa in sequence) / len(sequence)


def check_aspartimide_motifs(sequence: str) -> List[DRCRuleViolation]:
    """DRC Rule 1: Detect base-catalyzed aspartimide formation motifs (DG, DS, DN)."""
    violations = []
    # Asp-Gly, Asp-Ser, Asp-Asn are prime substrates for base-catalyzed aspartimide ring closure
    for match in re.finditer(r"D[GSN]", sequence):
        motif = match.group(0)
        start_pos = match.start() + 1  # 1-indexed
        end_pos = match.end()
        violations.append(
            DRCRuleViolation(
                rule_id="DRC-001",
                rule_name="Aspartimide Cyclization Liability",
                severity=DRCSeverity.FATAL if motif == "DG" else DRCSeverity.HIGH_RISK,
                failure_code="SYN_MODIFICATION_FAILED",
                message=(
                    f"High risk of base-catalyzed aspartimide formation at '{motif}' under piperidine Fmoc-deprotection."
                ),
                culprit_motif=motif,
                positions=[start_pos, end_pos],
            )
        )
    return violations


def check_hydrophobic_runs(sequence: str, max_consecutive: int = 5) -> List[DRCRuleViolation]:
    """DRC Rule 2: Detect SPPS on-resin beta-sheet interchain collapse."""
    violations = []
    pattern = rf"[VILFYW]{{{max_consecutive},}}"
    for match in re.finditer(pattern, sequence):
        motif = match.group(0)
        start_pos = match.start() + 1
        end_pos = match.end()
        violations.append(
            DRCRuleViolation(
                rule_id="DRC-002",
                rule_name="SPPS Interchain Beta-Sheet Collapse",
                severity=DRCSeverity.FATAL,
                failure_code="SYN_HYDROPHOBIC_SEQUENCE",
                message=(
                    f"Severe SPPS coupling failure risk: run of {len(motif)} consecutive hydrophobic residues '{motif}' causes resin aggregation."
                ),
                culprit_motif=motif,
                positions=list(range(start_pos, end_pos + 1)),
            )
        )
    return violations


def check_isoelectric_precipitation(sequence: str) -> List[DRCRuleViolation]:
    """DRC Rule 3: Detect neutral insolubility / precipitation risk at physiological pH 7.4."""
    violations = []
    net_charge = calculate_net_charge(sequence, ph=7.4)
    gravy = calculate_gravy(sequence)

    if abs(net_charge) < 0.5 and gravy > 0.3:
        violations.append(
            DRCRuleViolation(
                rule_id="DRC-003",
                rule_name="Isoelectric Precipitation Liability",
                severity=DRCSeverity.FATAL if gravy > 0.6 else DRCSeverity.HIGH_RISK,
                failure_code="LOW_AQUEOUS_SOLUBILITY",
                message=(
                    f"Near-neutral net charge (z={net_charge:.2f}) combined with positive GRAVY ({gravy:.2f}) causes high precipitation risk at pH 7.4."
                ),
                culprit_motif=None,
                positions=[],
            )
        )
    return violations


def check_cysteine_pairing(sequence: str, modality: str = "linear") -> List[DRCRuleViolation]:
    """DRC Rule 4: Detect unpaired free cysteines causing disulfide scrambling."""
    violations = []
    cys_count = sequence.count("C")
    if cys_count % 2 != 0:
        cys_positions = [i + 1 for i, aa in enumerate(sequence) if aa == "C"]
        violations.append(
            DRCRuleViolation(
                rule_id="DRC-004",
                rule_name="Unpaired Cysteine Disulfide Scrambling",
                severity=DRCSeverity.HIGH_RISK,
                failure_code="OXIDATION_LIABILITY",
                message=(
                    f"Odd number of cysteines ({cys_count}) yields unpaired reactive thiol prone to air oxidation and oligomerization."
                ),
                culprit_motif="C",
                positions=cys_positions,
            )
        )
    return violations


def check_steric_hindrance(sequence: str) -> List[DRCRuleViolation]:
    """DRC Rule 5: Detect consecutive sterically hindered residues (e.g., PPP or bulky runs)."""
    violations = []
    for match in re.finditer(r"P{3,}", sequence):
        motif = match.group(0)
        violations.append(
            DRCRuleViolation(
                rule_id="DRC-005",
                rule_name="Poly-Proline Steric Coupling Hindrance",
                severity=DRCSeverity.WARNING,
                failure_code="SYN_LOW_YIELD",
                message=f"Consecutive proline run '{motif}' causes steric hindrance and reduced SPPS coupling efficiency.",
                culprit_motif=motif,
                positions=list(range(match.start() + 1, match.end() + 1)),
            )
        )
    return violations


# --- Master DRC Suite Runner ---

def run_biological_drc_suite(sequence: str, modality: str = "linear") -> DRCSummary:
    """Run full Biological Design Rule Checking (DRC) suite over a candidate peptide sequence."""
    clean_seq = sequence.strip().upper()
    violations: List[DRCRuleViolation] = []

    # Run individual rule checkers
    violations.extend(check_aspartimide_motifs(clean_seq))
    violations.extend(check_hydrophobic_runs(clean_seq))
    violations.extend(check_isoelectric_precipitation(clean_seq))
    violations.extend(check_cysteine_pairing(clean_seq, modality=modality))
    violations.extend(check_steric_hindrance(clean_seq))

    net_charge = calculate_net_charge(clean_seq, ph=7.4)
    gravy = calculate_gravy(clean_seq)

    hard_stops = [v.message for v in violations if v.severity == DRCSeverity.FATAL]
    passed_hard_drc = len(hard_stops) == 0

    remediations = []
    for v in violations:
        if v.rule_id == "DRC-001":
            remediations.append("Replace Gly/Ser with Ala, or utilize alpha-methyl aspartate to block aspartimide cyclization.")
        elif v.rule_id == "DRC-002":
            remediations.append("Insert pseudoproline dipeptides (e.g., Fmoc-Ser(tBu)-Thr(psiMe,Mepro)-OH) or PEG spacers to break on-resin aggregation.")
        elif v.rule_id == "DRC-003":
            remediations.append("Incorporate basic (Lys/Arg) or acidic (Glu) capping residues at termini to shift pI away from pH 7.4.")
        elif v.rule_id == "DRC-004":
            remediations.append("Cap free cysteine or replace with Ser/Ala to prevent oxidation scrambling.")

    return DRCSummary(
        sequence=clean_seq,
        modality=modality,
        passed_hard_drc=passed_hard_drc,
        violations=violations,
        net_charge_ph74=net_charge,
        gravy_index=gravy,
        hard_stop_reasons=hard_stops,
        suggested_remediations=list(dict.fromkeys(remediations)),  # deduplicated
    )
