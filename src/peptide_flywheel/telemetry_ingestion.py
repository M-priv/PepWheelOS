from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from .async_bo import CandidateExperimentState


class TelemetryStage(str, Enum):
    STAGE_1_CRUDE_LCMS = "stage_1_crude_lcms"   # Day 10: Yield, Crude Purity %, Mass Spec
    STAGE_2_PURIFIED_QC = "stage_2_purified_qc" # Day 18: Purified HPLC %, Solubility, DLS
    STAGE_3_BIOASSAY = "stage_3_bioassay"       # Day 30: SPR Kd, Kinetics, IC50


@dataclass
class CrudeLCMSTelemetry:
    candidate_id: str
    crude_purity_pct: float
    yield_mg: float
    mass_observed_da: float
    mass_expected_da: float
    mass_error_da: float = field(init=False)
    is_mass_matched: bool = field(init=False)
    synthesis_passed: bool = field(init=False)
    failure_codes: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.mass_error_da = abs(self.mass_observed_da - self.mass_expected_da)
        # Tolerance: ≤ 1.0 Da or < 500 ppm relative error
        rel_error = self.mass_error_da / max(1.0, self.mass_expected_da)
        self.is_mass_matched = (self.mass_error_da <= 1.0) or (rel_error < 0.0005)
        
        self.failure_codes = []
        if not self.is_mass_matched:
            self.failure_codes.append("SYN_WRONG_MASS")
        if self.crude_purity_pct < 40.0:
            self.failure_codes.append("SYN_CRUDE_PURITY_LOW")
        if self.yield_mg < 1.0:
            self.failure_codes.append("SYN_YIELD_LOW")

        self.synthesis_passed = len(self.failure_codes) == 0


@dataclass
class PurifiedQCTelemetry:
    candidate_id: str
    purified_purity_pct: float
    solubility_mg_ml: float
    aggregation_index: float
    dls_polydispersity: float = 0.15
    qc_passed: bool = field(init=False)
    failure_codes: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.failure_codes = []
        if self.purified_purity_pct < 90.0:
            self.failure_codes.append("SYN_PURITY_FAIL")
        if self.solubility_mg_ml < 0.5:
            self.failure_codes.append("SOLUBILITY_LOW")
        if self.aggregation_index > 0.30 or self.dls_polydispersity > 0.30:
            self.failure_codes.append("AGGREGATION_HIGH")

        self.qc_passed = len(self.failure_codes) == 0


@dataclass
class BioassayTelemetry:
    candidate_id: str
    kd_nm: Optional[float] = None
    kon_1_ms: Optional[float] = None
    koff_1_s: Optional[float] = None
    ic50_nm: Optional[float] = None
    is_binder: bool = True
    censored_above_limit: bool = False
    failure_codes: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.failure_codes = []
        # If Kd > 10,000 nM (10 µM) or censored above assay detection ceiling
        if self.censored_above_limit or (self.kd_nm is not None and self.kd_nm > 10000.0):
            self.is_binder = False
            self.failure_codes.append("ASSAY_NON_BINDER")
        elif self.kd_nm is None and self.ic50_nm is None:
            self.is_binder = False
            self.failure_codes.append("ASSAY_NO_ACTIVITY")


@dataclass
class IngestionBatchResult:
    stage: TelemetryStage
    updated_candidate_cards: List[Dict[str, Any]]
    passed_count: int
    failed_count: int
    delta_logs: List[str]


# ---------------------------------------------------------------------------
# Tolerant CSV / JSON Parsers
# ---------------------------------------------------------------------------

COLUMN_ALIASES = {
    "candidate_id": {"candidate_id", "candidateid", "id", "peptide_id", "name", "sample_id"},
    "crude_purity_pct": {"crude_purity", "crude_purity_pct", "crude_purity_%", "crude_purity(%)", "purity_crude"},
    "purified_purity_pct": {"purified_purity", "purified_purity_pct", "purity", "purity_%", "hplc_purity", "purity_pct"},
    "yield_mg": {"yield", "yield_mg", "yield_(mg)", "mass_yield_mg"},
    "mass_observed_da": {"mass_obs", "mass_observed", "observed_mass", "mw_obs", "m_obs"},
    "mass_expected_da": {"mass_exp", "mass_expected", "expected_mass", "mw_exp", "calc_mw", "m_exp"},
    "solubility_mg_ml": {"solubility", "solubility_mg_ml", "solubility_(mg/ml)", "sol_mg_ml"},
    "aggregation_index": {"aggregation", "aggregation_index", "agg_index", "agg_score"},
    "dls_polydispersity": {"dls_pdi", "pdi", "polydispersity", "dls_polydispersity"},
    "kd_nm": {"kd", "kd_nm", "kd_(nm)", "affinity_kd_nm"},
    "kon_1_ms": {"kon", "kon_1_ms", "k_on", "kon_(1/ms)"},
    "koff_1_s": {"koff", "koff_1_s", "k_off", "koff_(1/s)"},
    "ic50_nm": {"ic50", "ic50_nm", "ic50_(nm)"},
    "censored": {"censored", "is_censored", "above_detection_limit", "censored_above_limit"},
}


def _canonicalize_row_keys(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map arbitrary header variations to canonical internal names."""
    canonical: Dict[str, Any] = {}
    for raw_k, val in row.items():
        if val is None or str(val).strip() == "":
            continue
        cleaned_k = raw_k.strip().lower().replace(" ", "_")
        matched = False
        for canon_name, aliases in COLUMN_ALIASES.items():
            if cleaned_k in aliases:
                canonical[canon_name] = val
                matched = True
                break
        if not matched:
            canonical[cleaned_k] = val
    return canonical


def parse_telemetry_csv(csv_content: str) -> List[Dict[str, Any]]:
    """Parse CSV drop file with robust column canonicalization."""
    reader = csv.DictReader(io.StringIO(csv_content.strip()))
    records: List[Dict[str, Any]] = []
    for row in reader:
        records.append(_canonicalize_row_keys(row))
    return records


def parse_telemetry_json(json_content: str) -> List[Dict[str, Any]]:
    """Parse JSON drop file with canonicalization."""
    raw_data = json.loads(json_content)
    if isinstance(raw_data, dict):
        raw_list = raw_data.get("records", raw_data.get("candidates", [raw_data]))
    elif isinstance(raw_list := raw_data, list):
        pass
    else:
        raw_list = []

    records: List[Dict[str, Any]] = []
    for item in raw_list:
        if isinstance(item, dict):
            records.append(_canonicalize_row_keys(item))
    return records


# ---------------------------------------------------------------------------
# State Machine & Research DAG Ingestion Engine
# ---------------------------------------------------------------------------

def ingest_candidate_telemetry(
    candidate_card: Dict[str, Any],
    telemetry_record: Dict[str, Any],
    stage: TelemetryStage,
) -> Tuple[Dict[str, Any], List[str]]:
    """Ingest experimental telemetry into a single candidate card and advance lifecycle state."""
    import copy
    card = copy.deepcopy(candidate_card)
    logs: List[str] = []
    cid = card.get("candidate_id", "UNKNOWN")

    # Ensure experimental_results dict exists
    if "experimental_results" not in card or not isinstance(card["experimental_results"], dict):
        card["experimental_results"] = {}
    if "risk_flags" not in card or not isinstance(card["risk_flags"], list):
        card["risk_flags"] = []

    # 1. Stage 1: Crude LCMS
    if stage == TelemetryStage.STAGE_1_CRUDE_LCMS:
        purity = float(telemetry_record.get("crude_purity_pct", 50.0))
        yield_mg = float(telemetry_record.get("yield_mg", 5.0))
        m_obs = float(telemetry_record.get("mass_observed_da", 1000.0))
        m_exp = float(telemetry_record.get("mass_expected_da", m_obs))

        s1_obj = CrudeLCMSTelemetry(
            candidate_id=cid,
            crude_purity_pct=purity,
            yield_mg=yield_mg,
            mass_observed_da=m_obs,
            mass_expected_da=m_exp,
        )

        card["experimental_results"]["crude_lcms"] = {
            "crude_purity_pct": s1_obj.crude_purity_pct,
            "yield_mg": s1_obj.yield_mg,
            "mass_observed_da": s1_obj.mass_observed_da,
            "mass_expected_da": s1_obj.mass_expected_da,
            "mass_error_da": round(s1_obj.mass_error_da, 3),
            "is_mass_matched": s1_obj.is_mass_matched,
            "synthesis_passed": s1_obj.synthesis_passed,
        }

        if s1_obj.synthesis_passed:
            card["experiment_state"] = CandidateExperimentState.IN_FLIGHT_ASSAY.value
            logs.append(f"[{cid}] Stage 1 Crude LCMS Passed (Purity: {purity}%, Mass Match: {s1_obj.is_mass_matched})")
        else:
            card["experiment_state"] = CandidateExperimentState.FAILED.value
            card["status"] = "rejected"
            card["risk_flags"].extend(s1_obj.failure_codes)
            card["risk_flags"] = list(dict.fromkeys(card["risk_flags"]))
            logs.append(f"[{cid}] Stage 1 Crude LCMS Failed: {', '.join(s1_obj.failure_codes)}")

    # 2. Stage 2: Purified QC & DLS
    elif stage == TelemetryStage.STAGE_2_PURIFIED_QC:
        purified_purity = float(telemetry_record.get("purified_purity_pct", 95.0))
        solubility = float(telemetry_record.get("solubility_mg_ml", 2.0))
        agg_idx = float(telemetry_record.get("aggregation_index", 0.05))
        pdi = float(telemetry_record.get("dls_polydispersity", 0.12))

        s2_obj = PurifiedQCTelemetry(
            candidate_id=cid,
            purified_purity_pct=purified_purity,
            solubility_mg_ml=solubility,
            aggregation_index=agg_idx,
            dls_polydispersity=pdi,
        )

        card["experimental_results"]["purified_qc"] = {
            "purified_purity_pct": s2_obj.purified_purity_pct,
            "solubility_mg_ml": s2_obj.solubility_mg_ml,
            "aggregation_index": s2_obj.aggregation_index,
            "dls_polydispersity": s2_obj.dls_polydispersity,
            "qc_passed": s2_obj.qc_passed,
        }

        if s2_obj.qc_passed:
            card["experiment_state"] = CandidateExperimentState.IN_FLIGHT_ASSAY.value
            logs.append(f"[{cid}] Stage 2 Purified QC Passed (Purity: {purified_purity}%, Sol: {solubility} mg/mL)")
        else:
            card["experiment_state"] = CandidateExperimentState.FAILED.value
            card["status"] = "rejected"
            card["risk_flags"].extend(s2_obj.failure_codes)
            card["risk_flags"] = list(dict.fromkeys(card["risk_flags"]))
            logs.append(f"[{cid}] Stage 2 Purified QC Failed: {', '.join(s2_obj.failure_codes)}")

    # 3. Stage 3: Bioassays & SPR
    elif stage == TelemetryStage.STAGE_3_BIOASSAY:
        kd_raw = telemetry_record.get("kd_nm")
        kd_val = float(kd_raw) if kd_raw is not None else None
        kon_raw = telemetry_record.get("kon_1_ms")
        kon_val = float(kon_raw) if kon_raw is not None else None
        koff_raw = telemetry_record.get("koff_1_s")
        koff_val = float(koff_raw) if koff_raw is not None else None
        ic50_raw = telemetry_record.get("ic50_nm")
        ic50_val = float(ic50_raw) if ic50_raw is not None else None

        censored_flag = bool(str(telemetry_record.get("censored", "false")).lower() in ("true", "1", "yes"))

        s3_obj = BioassayTelemetry(
            candidate_id=cid,
            kd_nm=kd_val,
            kon_1_ms=kon_val,
            koff_1_s=koff_val,
            ic50_nm=ic50_val,
            censored_above_limit=censored_flag,
        )

        card["experimental_results"]["bioassay"] = {
            "kd_nm": s3_obj.kd_nm,
            "kon_1_ms": s3_obj.kon_1_ms,
            "koff_1_s": s3_obj.koff_1_s,
            "ic50_nm": s3_obj.ic50_nm,
            "is_binder": s3_obj.is_binder,
            "censored_above_limit": s3_obj.censored_above_limit,
        }

        # Transition candidate to MEASURED
        card["experiment_state"] = CandidateExperimentState.MEASURED.value

        if s3_obj.is_binder and s3_obj.kd_nm is not None:
            # Update measured potency score (e.g. pKd scale: -log10(Kd * 1e-9))
            import math
            pkd = -math.log10(max(1e-12, s3_obj.kd_nm * 1e-9))
            card["potency"] = round(pkd * 10.0, 2)  # Normalized potency score
            card["status"] = "evaluated"
            logs.append(f"[{cid}] Stage 3 Bioassay Measured Binder (Kd: {s3_obj.kd_nm} nM, Potency Score: {card['potency']})")
        else:
            card["status"] = "rejected"
            card["potency"] = 0.0
            card["risk_flags"].extend(s3_obj.failure_codes)
            card["risk_flags"] = list(dict.fromkeys(card["risk_flags"]))
            logs.append(f"[{cid}] Stage 3 Bioassay Non-Binder: {', '.join(s3_obj.failure_codes)}")

    return card, logs


def process_telemetry_drop(
    candidate_cards: Sequence[Dict[str, Any]],
    telemetry_content: str,
    stage: TelemetryStage,
    content_format: str = "csv",
) -> IngestionBatchResult:
    """Process batch telemetry drop file and update candidate card pool."""
    if content_format.lower() == "json":
        records = parse_telemetry_json(telemetry_content)
    else:
        records = parse_telemetry_csv(telemetry_content)

    record_map = {r.get("candidate_id", ""): r for r in records if r.get("candidate_id")}
    updated_cards: List[Dict[str, Any]] = []
    all_logs: List[str] = []
    passed_count = 0
    failed_count = 0

    for card in candidate_cards:
        cid = card.get("candidate_id", "")
        if cid in record_map:
            updated_card, logs = ingest_candidate_telemetry(card, record_map[cid], stage)
            updated_cards.append(updated_card)
            all_logs.extend(logs)
            if updated_card.get("experiment_state") == CandidateExperimentState.FAILED.value or updated_card.get("status") == "rejected":
                failed_count += 1
            else:
                passed_count += 1
        else:
            # Unmodified in this stage drop
            updated_cards.append(card)

    return IngestionBatchResult(
        stage=stage,
        updated_candidate_cards=updated_cards,
        passed_count=passed_count,
        failed_count=failed_count,
        delta_logs=all_logs,
    )
