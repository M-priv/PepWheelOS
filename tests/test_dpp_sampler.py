from __future__ import annotations

import numpy as np
import pytest

from peptide_flywheel.dpp_sampler import (
    compute_average_pairwise_distance,
    compute_diversity_kernel,
    construct_l_ensemble,
    generate_sequence_features,
    greedy_dpp_map_selection,
)


def test_generate_sequence_features():
    sequences = [
        "KWKLFKKIEKWLFLG",
        "ACDEFGHIKLMNPQR",
        "YYYYFFFFWWWW",
        "",
    ]
    features = generate_sequence_features(sequences)
    assert features.shape == (4, 24)
    # Check all feature values are finite and within reasonable bounds [0, 1]
    assert np.all(np.isfinite(features))
    assert np.all(features >= 0.0)
    assert np.all(features <= 1.0)

    # Distinct sequences should have non-zero distance
    dist = np.linalg.norm(features[0] - features[1])
    assert dist > 0.1


def test_diversity_kernel_and_l_ensemble_psd():
    embeddings = np.array([
        [0.1, 0.2, 0.3],
        [0.12, 0.21, 0.29],
        [0.9, 0.8, 0.7],
    ])
    K = compute_diversity_kernel(embeddings)
    assert K.shape == (3, 3)
    np.testing.assert_allclose(np.diag(K), 1.0)
    assert np.all(K >= 0.0) and np.all(K <= 1.0)

    scores = [90.0, 88.0, 75.0]
    L = construct_l_ensemble(scores, K, temperature=10.0)
    assert L.shape == (3, 3)
    # Check symmetry
    np.testing.assert_allclose(L, L.T, atol=1e-10)
    # Check Positive Semi-Definiteness (eigenvalues >= 0)
    eigenvalues = np.linalg.eigvalsh(L)
    assert np.all(eigenvalues >= -1e-10)


def test_dpp_selection_breaks_redundancy_vs_naive_greedy():
    # Construct a dataset with:
    # Cluster A: 4 near-identical variants of top sequence (Score 95.0)
    cluster_a = [
        {"candidate_id": "A1", "sequence": "KWKLFKKIEKWLFLG", "overall_score": 95.0},
        {"candidate_id": "A2", "sequence": "KWKLFKKIEKWLFLA", "overall_score": 94.8},
        {"candidate_id": "A3", "sequence": "KWKLFKKIEKWLFLV", "overall_score": 94.5},
        {"candidate_id": "A4", "sequence": "KWKLFKKIEKWLFLI", "overall_score": 94.2},
    ]
    # Cluster B: 3 completely diverse sequences with slightly lower score (Score 88.0)
    cluster_b = [
        {"candidate_id": "B1", "sequence": "ACDEFGHIKLMNPQR", "overall_score": 88.0},
        {"candidate_id": "B2", "sequence": "YYYYFFFFWWWWKKK", "overall_score": 87.5},
        {"candidate_id": "B3", "sequence": "RRRKKKAAAVVVGGG", "overall_score": 87.0},
    ]
    candidates = cluster_a + cluster_b

    # Naive top-3 selection picks only from Cluster A (A1, A2, A3)
    naive_top3_ids = [c["candidate_id"] for c in sorted(candidates, key=lambda x: x["overall_score"], reverse=True)[:3]]
    assert naive_top3_ids == ["A1", "A2", "A3"]

    features = generate_sequence_features([c["sequence"] for c in candidates])
    naive_indices = [0, 1, 2]
    naive_diversity = compute_average_pairwise_distance(features, naive_indices)

    # DPP selection with q=3
    dpp_result = greedy_dpp_map_selection(
        candidates=candidates,
        q=3,
        embeddings=features,
        temperature=10.0,
    )

    assert len(dpp_result.selected_candidate_ids) == 3
    # DPP must select the best lead from Cluster A AND explore diverse leads from Cluster B
    selected_set = set(dpp_result.selected_candidate_ids)
    assert "A1" in selected_set  # Best lead preserved
    assert any(b_id in selected_set for b_id in ["B1", "B2", "B3"])  # Diverse lead selected

    # DPP diversity must be significantly higher than naive top-K
    assert dpp_result.average_pairwise_distance > naive_diversity * 2.0


def test_dpp_temperature_extremes():
    candidates = [
        {"candidate_id": "C1", "sequence": "KWK", "overall_score": 100.0},
        {"candidate_id": "C2", "sequence": "KWL", "overall_score": 99.0},
        {"candidate_id": "C3", "sequence": "YYY", "overall_score": 50.0},
    ]

    # Extreme low temperature -> Pure quality exploitation (selects top 2 scores: C1, C2)
    low_temp_res = greedy_dpp_map_selection(candidates, q=2, temperature=0.1)
    assert low_temp_res.selected_candidate_ids == ["C1", "C2"]

    # High temperature -> Pure diversity exploration (repels C2, selects C1 and C3)
    high_temp_res = greedy_dpp_map_selection(candidates, q=2, temperature=100.0)
    assert "C1" in high_temp_res.selected_candidate_ids
    assert "C3" in high_temp_res.selected_candidate_ids


def test_dpp_edge_cases():
    candidates = [
        {"candidate_id": "C1", "sequence": "ACD", "overall_score": 80.0},
        {"candidate_id": "C2", "sequence": "EFG", "overall_score": 85.0},
    ]

    # q = 1
    res1 = greedy_dpp_map_selection(candidates, q=1)
    assert len(res1.selected_candidate_ids) == 1
    assert res1.selected_candidate_ids[0] == "C2"  # Higher score

    # q > N
    res_large = greedy_dpp_map_selection(candidates, q=10)
    assert len(res_large.selected_candidate_ids) == 2

    # Empty list
    res_empty = greedy_dpp_map_selection([], q=5)
    assert len(res_empty.selected_candidate_ids) == 0
