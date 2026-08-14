from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class CASLookupError(KeyError):
    """Raised when a content-addressed URI cannot be resolved."""
    pass


@dataclass
class CompactContextEnvelope:
    """Lightweight context envelope passing references instead of full serialized objects."""
    packet_id: str
    target_ref: str        # e.g., "cas://e3b0c442..."
    hypothesis_ref: str    # e.g., "cas://f1a234b8..."
    candidate_ref: str     # e.g., "cas://8c91a03e..."
    state_delta: List[Dict[str, Any]] = field(default_factory=list)  # RFC 6902 JSON Patch
    projection_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "target_ref": self.target_ref,
            "hypothesis_ref": self.hypothesis_ref,
            "candidate_ref": self.candidate_ref,
            "state_delta": self.state_delta,
            "projection_fields": self.projection_fields,
        }


class ContentAddressedStore:
    """Immutable Merkle Content-Addressed Store (CAS) indexed by SHA-256 hashes."""

    def __init__(self, root_dir: Union[str, Path] = ".flywheel_cas"):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def canonical_json_bytes(obj: Any) -> bytes:
        """Produce deterministic canonical JSON bytes with sorted keys and no whitespace."""
        if hasattr(obj, "model_dump"):
            obj = obj.model_dump()
        elif hasattr(obj, "to_dict"):
            obj = obj.to_dict()
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @classmethod
    def compute_hash(cls, obj: Any) -> str:
        """Compute SHA-256 hash of canonical serialization."""
        return hashlib.sha256(cls.canonical_json_bytes(obj)).hexdigest()

    def put(self, obj: Any) -> str:
        """Store object in CAS and return its URI: cas://<sha256>."""
        raw_bytes = self.canonical_json_bytes(obj)
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        file_path = self.root_dir / f"{content_hash}.json"
        
        if not file_path.exists():
            file_path.write_bytes(raw_bytes)
            
        return f"cas://{content_hash}"

    def get(self, uri: str) -> Dict[str, Any]:
        """Retrieve stored object by its cas:// URI."""
        if not uri.startswith("cas://"):
            raise ValueError(f"Invalid CAS URI scheme: '{uri}'. Must start with 'cas://'.")
            
        content_hash = uri.replace("cas://", "").strip()
        file_path = self.root_dir / f"{content_hash}.json"
        
        if not file_path.exists():
            raise CASLookupError(f"CAS entity not found for URI: '{uri}'")
            
        return json.loads(file_path.read_text(encoding="utf-8"))

    def exists(self, uri: str) -> bool:
        """Check if an entity exists in CAS."""
        if not uri.startswith("cas://"):
            return False
        content_hash = uri.replace("cas://", "").strip()
        return (self.root_dir / f"{content_hash}.json").exists()


# --- RFC 6902 JSON Patch Utilities ---

def apply_rfc6902_patch(source_doc: Dict[str, Any], patch_operations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply standard RFC 6902 JSON Patch operations to a dictionary."""
    import copy
    doc = copy.deepcopy(source_doc)

    for op_item in patch_operations:
        op = op_item.get("op")
        path = op_item.get("path", "")
        value = op_item.get("value")

        parts = [p for p in path.split("/") if p]
        if not parts:
            continue

        target = doc
        for p in parts[:-1]:
            if p not in target or not isinstance(target[p], dict):
                target[p] = {}
            target = target[p]

        leaf_key = parts[-1]

        if op == "add" or op == "replace":
            if leaf_key == "-" and isinstance(target, list):
                target.append(value)
            elif isinstance(target, dict):
                target[leaf_key] = value
        elif op == "remove":
            if isinstance(target, dict) and leaf_key in target:
                del target[leaf_key]

    return doc


def compute_rfc6902_diff(source_doc: Dict[str, Any], target_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compute minimal RFC 6902 JSON Patch operations transforming source_doc to target_doc."""
    patches: List[Dict[str, Any]] = []

    # Check for modified or added keys
    for k, v in target_doc.items():
        if k not in source_doc:
            patches.append({"op": "add", "path": f"/{k}", "value": v})
        elif source_doc[k] != v:
            patches.append({"op": "replace", "path": f"/{k}", "value": v})

    # Check for removed keys
    for k in source_doc:
        if k not in target_doc:
            patches.append({"op": "remove", "path": f"/{k}"})

    return patches
