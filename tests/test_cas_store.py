from __future__ import annotations

import tempfile
import pytest
from pathlib import Path

from peptide_flywheel.cas_store import (
    CASLookupError,
    ContentAddressedStore,
    apply_rfc6902_patch,
    compute_rfc6902_diff,
)


def test_cas_store_put_and_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ContentAddressedStore(root_dir=tmpdir)

        test_data = {"target_id": "TARG-001", "name": "Pseudomonas Target", "score": 92.5}
        uri = store.put(test_data)

        assert uri.startswith("cas://")
        assert len(uri.replace("cas://", "")) == 64  # SHA-256 length

        retrieved = store.get(uri)
        assert retrieved == test_data
        assert store.exists(uri) is True


def test_cas_store_canonical_hash_identity():
    # Different key orders should produce identical canonical hash
    doc1 = {"a": 1, "b": 2, "c": [3, 4]}
    doc2 = {"c": [3, 4], "b": 2, "a": 1}

    hash1 = ContentAddressedStore.compute_hash(doc1)
    hash2 = ContentAddressedStore.compute_hash(doc2)

    assert hash1 == hash2


def test_cas_store_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ContentAddressedStore(root_dir=tmpdir)
        with pytest.raises(CASLookupError):
            store.get("cas://0000000000000000000000000000000000000000000000000000000000000000")


def test_rfc6902_patch_and_diff():
    source = {"candidate_id": "CAND-001", "status": "draft", "score": 80.0, "flags": ["A"]}
    target = {"candidate_id": "CAND-001", "status": "scored", "score": 90.0, "flags": ["A", "B"]}

    diff = compute_rfc6902_diff(source, target)
    assert len(diff) >= 2  # status and score changes

    patched = apply_rfc6902_patch(source, diff)
    assert patched["status"] == "scored"
    assert patched["score"] == 90.0
