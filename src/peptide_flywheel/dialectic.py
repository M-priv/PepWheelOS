from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .domain_drc import DRCSeverity, run_biological_drc_suite
from .models import Hypothesis, PeptideCandidate, Target


class DialecticDecision(str, Enum):
    PASS = "PASS"                                              # Low risk, high advocate fit
    REJECT = "REJECT"                                          # Hard DRC stop or overwhelming liabilities
    DISCRIMINATIVE_ASSAY = "DISCRIMINATIVE_ASSAY"              # High dissensus requiring experimental tie-breaker


@dataclass
class AdvocateCase:
    candidate_id: str
    affinity_score: float  # [0.0, 1.0]
    rationale: str
    target_fit_mechanisms: List[str]
    supporting_motifs: List[str]
    confidence: float = 0.85


@dataclass
class ScepticCase:
    candidate_id: str
    liability_score: float  # [0.0, 1.0] (higher means more dangerous)
    critique: str
    identified_liabilities: List[str]
    falsification_experiments: List[str]
    confidence: float = 0.85


@dataclass
class DialecticVerdict:
    candidate_id: str
    target_id: str
    advocate_score: float
    sceptic_score: float
    dissensus_delta: float
    decision: DialecticDecision
    hard_drc_passed: bool
    reasons: List[str]
    liabilities: List[str]
    falsification_tests: List[str]
    created_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "target_id": self.target_id,
            "advocate_score": round(self.advocate_score, 3),
            "sceptic_score": round(self.sceptic_score, 3),
            "dissensus_delta": round(self.dissensus_delta, 3),
            "decision": self.decision.value,
            "hard_drc_passed": self.hard_drc_passed,
            "reasons": self.reasons,
            "liabilities": self.liabilities,
            "falsification_tests": self.falsification_tests,
            "created_at": self.created_at,
        }


class AdvocateAgentRunner:
    """Advocate Agent: Generates the strongest biophysical fit & binding case."""

    def build_case(
        self,
        candidate: PeptideCandidate,
        target: Target,
        hypothesis: Optional[Hypothesis] = None,
        custom_affinity_score: Optional[float] = None,
    ) -> AdvocateCase:
        seq = candidate.sequence.upper().strip()
        
        # Default heuristic affinity estimation if no custom model score provided
        if custom_affinity_score is not None:
            score = max(0.0, min(1.0, float(custom_affinity_score)))
        else:
            # Positive charge + amphipathic motifs boost score for AMP targets
            pos_charge = sum(aa in "KRH" for aa in seq)
            score = 0.70 + min(0.25, (pos_charge / len(seq)) * 0.5)
            score = max(0.0, min(1.0, score))

        mechanisms = [
            f"Sequence '{seq}' presents basic residues compatible with {target.name} interaction surface.",
            f"Modality '{candidate.modality.value}' aligns with hypothesis design strategy '{hypothesis.design_strategy if hypothesis else 'unconstrained'}'.",
        ]

        return AdvocateCase(
            candidate_id=candidate.candidate_id,
            affinity_score=score,
            rationale=candidate.design_rationale or f"Designed to target {target.name}.",
            target_fit_mechanisms=mechanisms,
            supporting_motifs=[seq[i:i+3] for i in range(0, len(seq)-2, 3)],
        )


class ScepticAgentRunner:
    """Sceptic Agent: Adversarially attacks the candidate to discover failure modes & liabilities."""

    def falsify_candidate(
        self,
        candidate: PeptideCandidate,
        target: Target,
        advocate_case: Optional[AdvocateCase] = None,
        custom_liability_score: Optional[float] = None,
    ) -> ScepticCase:
        seq = candidate.sequence.upper().strip()
        
        # 1. Run Domain DRC
        drc = run_biological_drc_suite(seq, modality=candidate.modality.value)
        liabilities = [v.message for v in drc.violations]
        
        # Calculate liability score
        if custom_liability_score is not None:
            lib_score = max(0.0, min(1.0, float(custom_liability_score)))
        else:
            fatal_count = sum(1 for v in drc.violations if v.severity == DRCSeverity.FATAL)
            high_count = sum(1 for v in drc.violations if v.severity == DRCSeverity.HIGH_RISK)
            lib_score = min(1.0, (fatal_count * 0.5) + (high_count * 0.25))

        falsification_tests = [
            f"Measure exact crude purity via LC-MS to verify no on-resin aggregation during SPPS.",
            f"Conduct DLS / Turbidity assay at pH 7.4 to falsify colloidal precipitation.",
            f"Run counter-screen against mammalian RBCs (Hemolysis assay) to test off-target toxicity.",
        ]

        critique = (
            f"Candidate {candidate.candidate_id} exhibits {len(liabilities)} identifiable physical liabilities. "
            f"Advocate's claimed affinity relies on unproven electrostatic interactions without accounting for "
            f"solubility boundaries at physiological pH."
        )

        return ScepticCase(
            candidate_id=candidate.candidate_id,
            liability_score=lib_score,
            critique=critique,
            identified_liabilities=liabilities,
            falsification_experiments=falsification_tests,
        )


class DialecticArbiter:
    """Adjudicates between Advocate and Sceptic using physical invariants and dissensus metrics."""

    def __init__(self, dissensus_threshold: float = 0.35):
        self.dissensus_threshold = dissensus_threshold

    def adjudicate(
        self,
        candidate: PeptideCandidate,
        target: Target,
        advocate_case: AdvocateCase,
        sceptic_case: ScepticCase,
    ) -> DialecticVerdict:
        # 1. Run Biological DRC for hard constraints
        drc = run_biological_drc_suite(candidate.sequence, modality=candidate.modality.value)
        
        s_A = advocate_case.affinity_score
        s_S = sceptic_case.liability_score
        
        # Dissensus calculation: Difference between advocate affinity and inverted sceptic liability
        dissensus_delta = abs(s_A - (1.0 - s_S))

        reasons = []
        all_liabilities = list(sceptic_case.identified_liabilities)

        # 2. Decision Logic
        if not drc.passed_hard_drc:
            decision = DialecticDecision.REJECT
            reasons.append("Hard Biological DRC Invariant violated: " + "; ".join(drc.hard_stop_reasons))
        elif s_S >= 0.70:
            decision = DialecticDecision.REJECT
            reasons.append(f"Sceptic identified overwhelming chemical/synthesis liabilities (Score: {s_S:.2f}).")
        elif dissensus_delta > self.dissensus_threshold:
            decision = DialecticDecision.DISCRIMINATIVE_ASSAY
            reasons.append(
                f"High epistemic dissensus (Δ = {dissensus_delta:.2f} > {self.dissensus_threshold:.2f}): "
                f"Advocate affinity ({s_A:.2f}) conflicts with Sceptic liability ({s_S:.2f}). "
                f"Requires wet-lab discriminative assay to break tie."
            )
        elif s_A >= 0.75 and s_S <= 0.30:
            decision = DialecticDecision.PASS
            reasons.append(f"Consensus Pass: High advocate fit ({s_A:.2f}) and low sceptic liability ({s_S:.2f}).")
        else:
            decision = DialecticDecision.PASS if s_A >= 0.60 else DialecticDecision.REJECT
            reasons.append(f"Moderate score consensus: Advocate={s_A:.2f}, Sceptic={s_S:.2f}.")

        return DialecticVerdict(
            candidate_id=candidate.candidate_id,
            target_id=target.target_id,
            advocate_score=s_A,
            sceptic_score=s_S,
            dissensus_delta=dissensus_delta,
            decision=decision,
            hard_drc_passed=drc.passed_hard_drc,
            reasons=reasons,
            liabilities=all_liabilities,
            falsification_tests=sceptic_case.falsification_experiments,
        )
