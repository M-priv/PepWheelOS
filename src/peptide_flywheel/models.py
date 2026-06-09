from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CandidateStatus(str, Enum):
    DRAFT = "draft"
    SCORED = "scored"
    SELECTED = "selected"
    ORDERED = "ordered"
    TESTED = "tested"
    REJECTED = "rejected"
    ADVANCED = "advanced"


class PeptideModality(str, Enum):
    LINEAR = "linear"
    CYCLIC = "cyclic"
    STAPLED = "stapled"
    MODIFIED = "modified"
    UNKNOWN = "unknown"


class Target(BaseModel):
    target_id: str
    name: str
    organism: str = "unknown"
    use_case: str
    rationale: str
    aliases: List[str] = Field(default_factory=list)
    uniprot_id: Optional[str] = None
    pdb_ids: List[str] = Field(default_factory=list)
    known_ligands: List[str] = Field(default_factory=list)
    known_binding_sites: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)


class Hypothesis(BaseModel):
    hypothesis_id: str
    target_id: str
    claim: str
    mechanistic_rationale: str = ""
    design_strategy: str = ""
    success_criteria: List[str] = Field(default_factory=list)
    rejection_criteria: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)


class PeptideCandidate(BaseModel):
    candidate_id: str
    sequence: str
    target_id: str
    hypothesis_id: str
    modality: PeptideModality = PeptideModality.UNKNOWN
    modifications: List[str] = Field(default_factory=list)
    design_rationale: str = ""
    predicted_properties: Dict[str, Any] = Field(default_factory=dict)
    manufacturability_score: Optional[float] = None
    risk_flags: List[str] = Field(default_factory=list)
    status: CandidateStatus = CandidateStatus.DRAFT


class PredictionRun(BaseModel):
    prediction_id: str
    candidate_id: str
    tool_name: str
    tool_version: str = "unknown"
    input_refs: List[str] = Field(default_factory=list)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    interpretation: str = ""
    uncertainty: str = ""


class ManufacturabilityAssessment(BaseModel):
    assessment_id: str
    candidate_id: str
    dimension_scores: Dict[str, float] = Field(default_factory=dict)
    overall_score: float
    risk_flags: List[str] = Field(default_factory=list)
    mitigation_notes: List[str] = Field(default_factory=list)
    recommendation: str


class ExperimentalResult(BaseModel):
    result_id: str
    candidate_id: str
    result_type: str
    summary: str
    interpretation: str
    vendor_or_lab: Optional[str] = None
    raw_file_refs: List[str] = Field(default_factory=list)
    key_values: Dict[str, Any] = Field(default_factory=dict)
    failure_modes: List[str] = Field(default_factory=list)
    next_action: str = ""


class DecisionRecord(BaseModel):
    decision_id: str
    campaign_id: str
    decision: str
    rationale: str
    related_nodes: List[str] = Field(default_factory=list)
    alternatives_considered: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    approved_by: Optional[str] = None
    timestamp: Optional[str] = None
