from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass
class ConformalPrediction:
    mean_prediction: float
    lower_bound: float
    upper_bound: float
    interval_width: float
    confidence_level: float
    is_high_uncertainty: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean_prediction": round(self.mean_prediction, 4),
            "lower_bound": round(self.lower_bound, 4),
            "upper_bound": round(self.upper_bound, 4),
            "interval_width": round(self.interval_width, 4),
            "confidence_level": self.confidence_level,
            "is_high_uncertainty": self.is_high_uncertainty,
        }


class SplitConformalCalibrator:
    """Distribution-free Split Conformal Prediction calibrator providing finite-sample coverage guarantees."""

    def __init__(self, alpha: float = 0.10):
        """
        Args:
            alpha: Miscoverage rate (e.g. alpha=0.10 gives 90% statistical coverage).
        """
        self.alpha = alpha
        self.quantile_margin: float = 0.15  # default conservative margin before calibration
        self.calibrated = False

    def fit(self, y_true: List[float], y_pred: List[float]) -> float:
        """Calibrate non-conformity scores on historical validation dataset."""
        if len(y_true) != len(y_pred):
            raise ValueError(f"Length mismatch between y_true ({len(y_true)}) and y_pred ({len(y_pred)}).")
        if len(y_true) == 0:
            raise ValueError("Calibration set cannot be empty.")

        n = len(y_true)
        # Compute absolute non-conformity errors
        non_conformity_scores = [abs(yt - yp) for yt, yp in zip(y_true, y_pred)]
        
        # Conformal quantile level: ceil((n + 1) * (1 - alpha)) / n
        p_level = min(1.0, math.ceil((n + 1) * (1.0 - self.alpha)) / n)
        
        # Calculate empirical quantile
        self.quantile_margin = float(np.quantile(non_conformity_scores, p_level))
        self.calibrated = True
        return self.quantile_margin

    def predict(
        self,
        mean_pred: float,
        uncertainty_threshold: float = 0.35,
    ) -> ConformalPrediction:
        """Generate calibrated prediction interval with coverage guarantee."""
        q = self.quantile_margin
        lower = max(0.0, mean_pred - q)
        upper = min(1.0, mean_pred + q)
        width = upper - lower
        is_high_uncertainty = (2 * q) > uncertainty_threshold

        return ConformalPrediction(
            mean_prediction=mean_pred,
            lower_bound=lower,
            upper_bound=upper,
            interval_width=width,
            confidence_level=1.0 - self.alpha,
            is_high_uncertainty=is_high_uncertainty,
        )
