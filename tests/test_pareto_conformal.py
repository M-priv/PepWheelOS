from __future__ import annotations

import numpy as np
import pytest

from peptide_flywheel.conformal import SplitConformalCalibrator
from peptide_flywheel.pareto_sort import (
    MultiObjectiveCandidate,
    dominates,
    fast_non_dominated_sort,
    select_top_pareto_candidates,
)


def test_dominates_relationship():
    c_good = MultiObjectiveCandidate(
        candidate_id="C1",
        sequence="KWK",
        objectives={"potency": 0.90, "manufacturability": 0.85},
    )
    c_bad = MultiObjectiveCandidate(
        candidate_id="C2",
        sequence="KWL",
        objectives={"potency": 0.50, "manufacturability": 0.50},
    )
    c_tradeoff = MultiObjectiveCandidate(
        candidate_id="C3",
        sequence="KWA",
        objectives={"potency": 0.95, "manufacturability": 0.40},
    )

    assert dominates(c_good, c_bad) is True
    assert dominates(c_bad, c_good) is False
    # Neither dominates the other between c_good (0.90, 0.85) and c_tradeoff (0.95, 0.40)
    assert dominates(c_good, c_tradeoff) is False
    assert dominates(c_tradeoff, c_good) is False


def test_fast_non_dominated_sort_and_selection():
    c1 = MultiObjectiveCandidate(candidate_id="C1", sequence="A", objectives={"p": 0.9, "m": 0.9})  # Front 1
    c2 = MultiObjectiveCandidate(candidate_id="C2", sequence="B", objectives={"p": 0.95, "m": 0.4}) # Front 1
    c3 = MultiObjectiveCandidate(candidate_id="C3", sequence="C", objectives={"p": 0.4, "m": 0.95}) # Front 1
    c4 = MultiObjectiveCandidate(candidate_id="C4", sequence="D", objectives={"p": 0.5, "m": 0.5})  # Front 2 (dominated by C1)

    candidates = [c1, c2, c3, c4]
    fronts = fast_non_dominated_sort(candidates)

    assert len(fronts) == 2
    front1_ids = {c.candidate_id for c in fronts[0]}
    assert front1_ids == {"C1", "C2", "C3"}
    assert fronts[1][0].candidate_id == "C4"

    # Select top 2
    selected = select_top_pareto_candidates(fronts, k=2)
    assert len(selected) == 2
    assert all(c.candidate_id in {"C1", "C2", "C3"} for c in selected)


def test_split_conformal_prediction_coverage():
    calibrator = SplitConformalCalibrator(alpha=0.10)  # 90% target coverage

    # Synthetic validation dataset
    np.random.seed(42)
    y_true = np.random.uniform(0.5, 0.9, size=100).tolist()
    # Predictions with Gaussian noise (std = 0.05)
    y_pred = [yt + float(np.random.normal(0, 0.05)) for yt in y_true]

    margin = calibrator.fit(y_true, y_pred)
    assert margin > 0.0
    assert calibrator.calibrated is True

    # Test coverage on new test samples
    test_y_true = np.random.uniform(0.5, 0.9, size=100).tolist()
    test_y_pred = [yt + float(np.random.normal(0, 0.05)) for yt in test_y_true]

    covered_count = 0
    for yt, yp in zip(test_y_true, test_y_pred):
        pred_interval = calibrator.predict(yp)
        if pred_interval.lower_bound <= yt <= pred_interval.upper_bound:
            covered_count += 1

    empirical_coverage = covered_count / len(test_y_true)
    # Empirical coverage should be near 90% (>= 85%)
    assert empirical_coverage >= 0.85
