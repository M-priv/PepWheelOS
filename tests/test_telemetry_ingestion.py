from peptide_flywheel.async_bo import CandidateExperimentState
from peptide_flywheel.telemetry_ingestion import (
    BioassayTelemetry,
    CrudeLCMSTelemetry,
    PurifiedQCTelemetry,
    TelemetryStage,
    ingest_candidate_telemetry,
    parse_telemetry_csv,
    parse_telemetry_json,
    process_telemetry_drop,
)



def test_crude_lcms_mass_matching_and_thresholds():
    # 1. Exact mass match & good purity
    t1 = CrudeLCMSTelemetry(
        candidate_id="CAND-001",
        crude_purity_pct=65.0,
        yield_mg=12.5,
        mass_observed_da=1542.8,
        mass_expected_da=1542.5,
    )
    assert t1.is_mass_matched is True
    assert t1.synthesis_passed is True
    assert len(t1.failure_codes) == 0

    # 2. Mass mismatch (truncation / deletion sequence)
    t2 = CrudeLCMSTelemetry(
        candidate_id="CAND-002",
        crude_purity_pct=70.0,
        yield_mg=10.0,
        mass_observed_da=1420.0,
        mass_expected_da=1542.5,
    )
    assert t2.is_mass_matched is False
    assert t2.synthesis_passed is False
    assert "SYN_WRONG_MASS" in t2.failure_codes

    # 3. Poor crude purity (< 40%)
    t3 = CrudeLCMSTelemetry(
        candidate_id="CAND-003",
        crude_purity_pct=25.0,
        yield_mg=8.0,
        mass_observed_da=1542.5,
        mass_expected_da=1542.5,
    )
    assert t3.is_mass_matched is True
    assert t3.synthesis_passed is False
    assert "SYN_CRUDE_PURITY_LOW" in t3.failure_codes


def test_parse_stage_1_crude_lcms_csv_drop():
    csv_text = """Candidate_ID,Crude_Purity,Yield (mg),Observed_Mass,Expected_Mass
CAND-001,68.5,14.2,1850.2,1850.0
CAND-002,28.0,2.1,1850.1,1850.0
CAND-003,72.0,11.0,1720.0,1850.0
"""
    candidate_cards = [
        {"candidate_id": "CAND-001", "sequence": "KWKLFKKIEKWLFLG", "experiment_state": "in_flight_synthesis"},
        {"candidate_id": "CAND-002", "sequence": "KWKLFKKIEKWLFLA", "experiment_state": "in_flight_synthesis"},
        {"candidate_id": "CAND-003", "sequence": "KWKLFKKIEKWLFLV", "experiment_state": "in_flight_synthesis"},
    ]

    result = process_telemetry_drop(
        candidate_cards=candidate_cards,
        telemetry_content=csv_text,
        stage=TelemetryStage.STAGE_1_CRUDE_LCMS,
        content_format="csv",
    )

    assert result.passed_count == 1
    assert result.failed_count == 2

    # Verify CAND-001 passed
    c1 = next(c for c in result.updated_candidate_cards if c["candidate_id"] == "CAND-001")
    assert c1["experiment_state"] == CandidateExperimentState.IN_FLIGHT_ASSAY.value
    assert c1["experimental_results"]["crude_lcms"]["synthesis_passed"] is True

    # Verify CAND-002 failed with low purity
    c2 = next(c for c in result.updated_candidate_cards if c["candidate_id"] == "CAND-002")
    assert c2["experiment_state"] == CandidateExperimentState.FAILED.value
    assert c2["status"] == "rejected"
    assert "SYN_CRUDE_PURITY_LOW" in c2["risk_flags"]

    # Verify CAND-003 failed with wrong mass
    c3 = next(c for c in result.updated_candidate_cards if c["candidate_id"] == "CAND-003")
    assert c3["experiment_state"] == CandidateExperimentState.FAILED.value
    assert "SYN_WRONG_MASS" in c3["risk_flags"]


def test_parse_stage_2_purified_qc_json_drop():
    json_text = """{
      "records": [
        {"id": "CAND-001", "purified_purity": 96.5, "solubility_mg_ml": 4.5, "aggregation_index": 0.05, "dls_pdi": 0.08},
        {"id": "CAND-004", "purified_purity": 94.0, "solubility_mg_ml": 0.1, "aggregation_index": 0.45, "dls_pdi": 0.38}
      ]
    }"""
    candidate_cards = [
        {"candidate_id": "CAND-001", "experiment_state": "in_flight_assay"},
        {"candidate_id": "CAND-004", "experiment_state": "in_flight_assay"},
    ]

    result = process_telemetry_drop(
        candidate_cards=candidate_cards,
        telemetry_content=json_text,
        stage=TelemetryStage.STAGE_2_PURIFIED_QC,
        content_format="json",
    )

    c1 = next(c for c in result.updated_candidate_cards if c["candidate_id"] == "CAND-001")
    assert c1["experimental_results"]["purified_qc"]["qc_passed"] is True

    c4 = next(c for c in result.updated_candidate_cards if c["candidate_id"] == "CAND-004")
    assert c4["experiment_state"] == CandidateExperimentState.FAILED.value
    assert "SOLUBILITY_LOW" in c4["risk_flags"]
    assert "AGGREGATION_HIGH" in c4["risk_flags"]


def test_parse_stage_3_bioassay_and_lifecycle():
    candidate_card = {
        "candidate_id": "CAND-001",
        "sequence": "KWKLFKKIEKWLFLG",
        "experiment_state": "in_flight_assay",
        "status": "in_review",
    }

    # Ingest Stage 3 SPR binding telemetry (Kd = 45 nM)
    telemetry_record = {
        "kd_nm": 45.0,
        "kon_1_ms": 1.2e5,
        "koff_1_s": 5.4e-3,
        "ic50_nm": 60.0,
        "censored": False,
    }

    updated_card, logs = ingest_candidate_telemetry(
        candidate_card=candidate_card,
        telemetry_record=telemetry_record,
        stage=TelemetryStage.STAGE_3_BIOASSAY,
    )

    assert updated_card["experiment_state"] == CandidateExperimentState.MEASURED.value
    assert updated_card["status"] == "evaluated"
    assert updated_card["potency"] > 70.0  # pKd score ~7.35 * 10 = 73.47
    assert updated_card["experimental_results"]["bioassay"]["is_binder"] is True
