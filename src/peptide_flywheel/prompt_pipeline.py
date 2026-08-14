from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .models import Hypothesis, PeptideCandidate, Target


class TargetDossierOutput(BaseModel):
    target_id: str
    use_case: str
    key_constraints: list[str] = Field(default_factory=list)
    assay_options: list[str] = Field(default_factory=list)
    rationale: str
    risks: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    next_action: str = ""


class CandidateCardOutput(BaseModel):
    candidate_id: str
    sequence: str
    target_id: str
    hypothesis_id: str
    modality: str
    design_rationale: str = ""
    predicted_properties: dict[str, Any] = Field(default_factory=dict)
    manufacturability_score: float | None = None
    risk_flags: list[str] = Field(default_factory=list)


class RedTeamOutput(BaseModel):
    candidate_id: str
    target_id: str
    hypothesis_id: str
    critique: str
    risk_flags: list[str] = Field(default_factory=list)
    evidence_required: list[str] = Field(default_factory=list)
    failure_hypotheses: list[str] = Field(default_factory=list)
    go_no_go: str = "needs_review"


class AssayPackOutput(BaseModel):
    candidate_id: str
    target_id: str
    hypothesis_id: str
    assay_plan_type: str = "focused_confirmation"
    assay_types: list[str] = Field(default_factory=lambda: ["activity_assay"])
    acceptance_criteria: list[str] = Field(default_factory=list)
    rejection_criteria: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    priority: str = "medium"


@dataclass
class PromptTieredLayout:
    """3-Tier KV-cache compliant layout separating invariant prefixes from dynamic tails."""
    tier1_static_system_prefix: str    # Invariant persona, output schema & ontology (Permanently Cached)
    tier2_campaign_context: str        # Target dossier & standard controls (Cached per Campaign)
    tier3_dynamic_tail: str            # Candidate sequence & specific task instruction (Dynamic)

    def render(self) -> str:
        """Combine all 3 tiers in strict prefix order."""
        return f"{self.tier1_static_system_prefix}\n\n{self.tier2_campaign_context}\n\n{self.tier3_dynamic_tail}".strip()


@dataclass
class PromptPacket:
    packet_id: str
    agent: str
    artifact: str
    instruction: str
    input_payload: dict[str, Any]
    output_schema: dict[str, Any]
    context_envelope_ref: str | None = None
    created_at: str = datetime.now(tz=timezone.utc).isoformat()

    def get_tiered_layout(self) -> PromptTieredLayout:
        """Render prompt text structured for optimal KV prefix caching."""
        tier1 = (
            f"=== SYSTEM ROLE: {self.agent.upper()} ===\n"
            f"Artifact Target: {self.artifact}\n"
            f"Output Contract: Respond ONLY with a valid JSON object strictly conforming to this schema:\n"
            f"{self.output_schema}"
        )
        
        campaign_info = {
            "campaign_id": self.input_payload.get("campaign_id", "default"),
            "target": self.input_payload.get("target"),
            "hypothesis": self.input_payload.get("hypothesis"),
        }
        tier2 = (
            f"=== CAMPAIGN CONTEXT ===\n"
            f"Campaign Data:\n{campaign_info}"
        )
        
        dynamic_info = {
            "packet_id": self.packet_id,
            "run_id": self.input_payload.get("run_id"),
            "candidate": self.input_payload.get("candidate"),
            "instruction": self.instruction,
        }
        tier3 = (
            f"=== TASK INSTRUCTION & CANDIDATE ===\n"
            f"Instruction: {self.instruction}\n"
            f"Candidate Data:\n{dynamic_info}"
        )
        return PromptTieredLayout(
            tier1_static_system_prefix=tier1,
            tier2_campaign_context=tier2,
            tier3_dynamic_tail=tier3,
        )

    def render_prompt_text(self) -> str:
        """Render full prefix-cached prompt string."""
        return self.get_tiered_layout().render()

    def model_dump(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "agent": self.agent,
            "artifact": self.artifact,
            "instruction": self.instruction,
            "input_payload": self.input_payload,
            "output_schema": self.output_schema,
            "context_envelope_ref": self.context_envelope_ref,
            "created_at": self.created_at,
        }


def _build_packet(
    *,
    packet_id: str,
    agent: str,
    artifact: str,
    instruction: str,
    input_payload: dict[str, Any],
    output_model: type[BaseModel],
    context_envelope_ref: str | None = None,
) -> PromptPacket:
    return PromptPacket(
        packet_id=packet_id,
        agent=agent,
        artifact=artifact,
        instruction=instruction,
        input_payload=input_payload,
        output_schema=output_model.model_json_schema(),
        context_envelope_ref=context_envelope_ref,
    )



def build_target_dossier_prompt(
    *,
    target: Target,
    hypothesis: Hypothesis,
    run_id: str,
    campaign_id: str,
) -> PromptPacket:
    packet_id = f"target-dossier-{target.target_id}-{run_id}"
    instruction = (
        "Populate a structured target dossier draft. Output strictly JSON only, using "
        "the schema below. Preserve constraints, risks and unknowns as bullet-style arrays."
    )
    input_payload = {
        "campaign_id": campaign_id,
        "run_id": run_id,
        "target": target.model_dump(mode="json"),
        "hypothesis": hypothesis.model_dump(mode="json"),
    }
    return _build_packet(
        packet_id=packet_id,
        agent="target-dossier",
        artifact="target_dossier",
        instruction=instruction,
        input_payload=input_payload,
        output_model=TargetDossierOutput,
    )


def build_candidate_card_prompt(
    *,
    candidate: PeptideCandidate,
    target: Target,
    hypothesis: Hypothesis,
    run_id: str,
    campaign_id: str,
) -> PromptPacket:
    packet_id = f"candidate-card-{candidate.candidate_id}-{run_id}"
    instruction = (
        "Generate a structured candidate-card payload for this candidate. Keep JSON compact. "
        "Include sequence rationale, properties, manufacturability summary and risk flags."
    )
    input_payload = {
        "campaign_id": campaign_id,
        "run_id": run_id,
        "candidate": candidate.model_dump(mode="json"),
        "target": target.model_dump(mode="json"),
        "hypothesis": hypothesis.model_dump(mode="json"),
    }
    return _build_packet(
        packet_id=packet_id,
        agent="candidate-card",
        artifact="candidate_card",
        instruction=instruction,
        input_payload=input_payload,
        output_model=CandidateCardOutput,
    )


def build_red_team_prompt(
    *,
    candidate: PeptideCandidate,
    target: Target,
    hypothesis: Hypothesis,
    run_id: str,
    campaign_id: str,
) -> PromptPacket:
    packet_id = f"red-team-{candidate.candidate_id}-{run_id}"
    instruction = (
        "Provide a strict pre-spend red-team critique for this candidate. "
        "List likely failure hypotheses, confidence limitations and required evidence."
    )
    input_payload = {
        "campaign_id": campaign_id,
        "run_id": run_id,
        "candidate": candidate.model_dump(mode="json"),
        "target": target.model_dump(mode="json"),
        "hypothesis": hypothesis.model_dump(mode="json"),
    }
    return _build_packet(
        packet_id=packet_id,
        agent="red-team",
        artifact="red_team_review",
        instruction=instruction,
        input_payload=input_payload,
        output_model=RedTeamOutput,
    )


def build_assay_pack_prompt(
    *,
    candidate: PeptideCandidate,
    target: Target,
    hypothesis: Hypothesis,
    run_id: str,
    campaign_id: str,
) -> PromptPacket:
    packet_id = f"assay-pack-{candidate.candidate_id}-{run_id}"
    instruction = (
        "Generate a structured assay pack draft. Define primary assays, controls, acceptance/rejection "
        "criteria and priority."
    )
    input_payload = {
        "campaign_id": campaign_id,
        "run_id": run_id,
        "candidate": candidate.model_dump(mode="json"),
        "target": target.model_dump(mode="json"),
        "hypothesis": hypothesis.model_dump(mode="json"),
    }
    return _build_packet(
        packet_id=packet_id,
        agent="assay-planning",
        artifact="assay_pack",
        instruction=instruction,
        input_payload=input_payload,
        output_model=AssayPackOutput,
    )


def build_prompt_batch(
    *,
    target: Target,
    hypothesis: Hypothesis,
    candidates: list[PeptideCandidate],
    campaign_id: str,
    run_id: str,
) -> list[PromptPacket]:
    packets = [
        build_target_dossier_prompt(
            target=target,
            hypothesis=hypothesis,
            campaign_id=campaign_id,
            run_id=run_id,
        )
    ]
    for candidate in candidates:
        packets.extend(
            [
                build_candidate_card_prompt(
                    candidate=candidate,
                    target=target,
                    hypothesis=hypothesis,
                    campaign_id=campaign_id,
                    run_id=run_id,
                ),
                build_red_team_prompt(
                    candidate=candidate,
                    target=target,
                    hypothesis=hypothesis,
                    campaign_id=campaign_id,
                    run_id=run_id,
                ),
                build_assay_pack_prompt(
                    candidate=candidate,
                    target=target,
                    hypothesis=hypothesis,
                    campaign_id=campaign_id,
                    run_id=run_id,
                ),
            ]
        )
    return packets


def prompt_manifest(packets: list[PromptPacket]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "packet_count": len(packets),
        "agents": sorted({packet.agent for packet in packets}),
        "artifacts": [packet.artifact for packet in packets],
        "packet_ids": [packet.packet_id for packet in packets],
    }

