import numpy as np

from peptide_flywheel.async_bo import (
    GaussianProcessSurrogate,
    compute_async_acquisition,
    propose_async_batch,
    sample_fantasy_outcomes,
)



def test_gp_surrogate_interpolation_and_variance():
    X = np.array([[0.0], [1.0], [2.0]])
    y = np.array([5.0, 10.0, 15.0])

    gp = GaussianProcessSurrogate(length_scale=1.0, signal_variance=1.0, noise_variance=1e-5)
    gp.fit(X, y)

    # Predictions at training points must interpolate accurately with near-zero variance
    mu_train, var_train = gp.predict(X)
    np.testing.assert_allclose(mu_train, y, atol=1e-3)
    assert np.all(var_train < 1e-3)

    # Prediction at unobserved midpoint (x=0.5) must have strictly higher uncertainty than at training points
    X_mid = np.array([[0.5]])
    _, var_mid = gp.predict(X_mid)
    assert var_mid[0] > np.max(var_train) * 10

    # Prediction far outside training domain (x=5.0) must approach full prior variance (1.0)
    X_far = np.array([[5.0]])
    _, var_far = gp.predict(X_far)
    assert var_far[0] > 0.90



def test_fantasy_sampling_empirical_consistency():
    X_train = np.array([[0.0], [2.0]])
    y_train = np.array([0.0, 10.0])

    gp = GaussianProcessSurrogate(length_scale=1.0, signal_variance=1.0)
    gp.fit(X_train, y_train)

    X_pending = np.array([[1.0]])
    mu_expected, _ = gp.predict(X_pending)

    # Sample M=2000 fantasy trajectories
    fantasies = sample_fantasy_outcomes(gp, X_pending, n_fantasies=2000, seed=42)
    assert fantasies.shape == (2000, 1)

    empirical_mean = np.mean(fantasies, axis=0)
    np.testing.assert_allclose(empirical_mean, mu_expected, atol=0.08)


def test_variance_collapse_and_inter_round_repulsion():
    # Historical data measured near x=0.0
    X_hist = np.array([[0.0]])
    y_hist = np.array([10.0])

    # Round N is in-flight at x=0.8
    X_pending = np.array([[0.8]])

    # Candidate 1 is an uncreative clone of in-flight Round N (x=0.82)
    # Candidate 2 is in an unexplored region (x=0.45)
    X_candidates = np.array([[0.82], [0.45]])

    # 1. Without knowing about X_pending (naive sequential), candidate 1 has high uncertainty
    alpha_naive = compute_async_acquisition(
        X_candidates=X_candidates,
        X_historical=X_hist,
        y_historical=y_hist,
        X_pending=None,
        acquisition_type="EI",
    )

    # 2. With X_pending accounted for, uncertainty at x=0.82 collapses
    alpha_async = compute_async_acquisition(
        X_candidates=X_candidates,
        X_historical=X_hist,
        y_historical=y_hist,
        X_pending=X_pending,
        acquisition_type="EI",
        n_fantasies=64,
        seed=42,
    )

    # In async BO, the unexplored candidate (Candidate 2) must receive a higher score than the redundant clone (Candidate 1)
    # whereas in naive sequential, Candidate 1 was unfairly favoured due to uncollapsed ignorance
    assert alpha_async[1] > alpha_async[0]


def test_propose_async_batch_end_to_end():
    historical_candidates = [
        {"candidate_id": "HIST-1", "sequence": "KWKLFKKIEKWLFLG", "potency": 85.0},
        {"candidate_id": "HIST-2", "sequence": "KWKLFKKIEKWLFLA", "potency": 82.0},
    ]
    pending_candidates = [
        {"candidate_id": "PEND-1", "sequence": "KWKLFKKIEKWLFLV"},  # In-flight Round N
    ]
    candidate_pool = [
        {"candidate_id": "POOL-1", "sequence": "KWKLFKKIEKWLFLI"},  # Redundant clone of pending
        {"candidate_id": "POOL-2", "sequence": "ACDEFGHIKLMNPQR"},  # Distinct family A
        {"candidate_id": "POOL-3", "sequence": "YYYYFFFFWWWWKKK"},  # Distinct family B
        {"candidate_id": "POOL-4", "sequence": "RRRKKKAAAVVVGGG"},  # Distinct family C
    ]

    result = propose_async_batch(
        candidate_pool=candidate_pool,
        historical_candidates=historical_candidates,
        pending_candidates=pending_candidates,
        batch_size=2,
        use_dpp=True,
        n_fantasies=32,
    )

    assert len(result.selected_candidate_ids) == 2
    assert result.average_pairwise_distance > 0.1
    # Must propose distinct sequences, not just the redundant clone
    assert any(c_id in ["POOL-2", "POOL-3", "POOL-4"] for c_id in result.selected_candidate_ids)
