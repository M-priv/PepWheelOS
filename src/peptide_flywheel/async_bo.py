from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
from scipy.stats import norm

from .dpp_sampler import (
    DPPBatchResult,
    compute_average_pairwise_distance,
    generate_sequence_features,
    greedy_dpp_map_selection,
)


class CandidateExperimentState(str, Enum):
    PROPOSED = "proposed"                      # Computationally designed, not yet queued
    IN_FLIGHT_SYNTHESIS = "in_flight_synthesis" # Being synthesized at CDMO/CRO (Day 0-18)
    IN_FLIGHT_ASSAY = "in_flight_assay"        # In physical bioassay / SPR testing (Day 18-30)
    MEASURED = "measured"                      # Physical assay completed and validated
    FAILED = "failed"                          # Physical synthesis or assay drop-out



class GaussianProcessSurrogate:
    """RBF Gaussian Process regression surrogate with robust Cholesky conditioning."""

    def __init__(
        self,
        length_scale: float = 1.0,
        signal_variance: float = 1.0,
        noise_variance: float = 1e-4,
    ):
        self.length_scale = length_scale
        self.signal_variance = signal_variance
        self.noise_variance = noise_variance
        
        self.X_train: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None
        self.L_train: Optional[np.ndarray] = None
        self.alpha_weights: Optional[np.ndarray] = None

    def _kernel(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute RBF covariance matrix between X1 and X2."""
        # Squared Euclidean distance: ||x1 - x2||^2
        sq_dist = np.sum(X1**2, axis=1, keepdims=True) + np.sum(X2**2, axis=1, keepdims=True).T - 2.0 * np.dot(X1, X2.T)
        sq_dist = np.maximum(0.0, sq_dist)
        gamma = 0.5 / (self.length_scale**2)
        return self.signal_variance * np.exp(-gamma * sq_dist)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GaussianProcessSurrogate":
        """Fit GP surrogate to training data (X, y)."""
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        if len(X) == 0:
            raise ValueError("Training dataset X cannot be empty.")

        self.X_train = X
        self.y_train = y
        n = len(X)

        K = self._kernel(X, X) + (self.noise_variance + 1e-6) * np.eye(n)
        try:
            self.L_train = np.linalg.cholesky(K)
        except np.linalg.LinAlgError:
            # Fallback with increased diagonal jitter for numerical stability
            self.L_train = np.linalg.cholesky(K + 1e-4 * np.eye(n))

        # Solve L * alpha = y  and  L^T * alpha_weights = alpha
        temp = np.linalg.solve(self.L_train, y)
        self.alpha_weights = np.linalg.solve(self.L_train.T, temp)
        return self

    def predict(
        self,
        X_star: np.ndarray,
        return_cov: bool = False,
    ) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """Predict posterior mean and variance (or full covariance) for test points X_star.
        
        Returns:
            (mu, var) or (mu, var, full_cov)
        """
        if self.X_train is None or self.alpha_weights is None or self.L_train is None:
            raise RuntimeError("GP surrogate must be fitted before predict() is called.")

        X_star = np.asarray(X_star, dtype=np.float64)
        K_star = self._kernel(self.X_train, X_star)  # Shape: (N_train, N_star)
        
        # Posterior mean: mu = K_star.T @ alpha_weights
        mu = np.dot(K_star.T, self.alpha_weights)

        # Solve L_train * v = K_star
        v = np.linalg.solve(self.L_train, K_star)

        if return_cov:
            K_star_star = self._kernel(X_star, X_star)
            cov = K_star_star - np.dot(v.T, v)
            # Safeguard diagonal elements
            var = np.maximum(1e-10, np.diag(cov))
            return mu, var, cov
        else:
            K_star_diag = self.signal_variance * np.ones(len(X_star), dtype=np.float64)
            var = np.maximum(1e-10, K_star_diag - np.sum(v**2, axis=0))
            return mu, var


def sample_fantasy_outcomes(
    gp: GaussianProcessSurrogate,
    X_pending: np.ndarray,
    n_fantasies: int = 32,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Sample M correlated fantasy trajectories for in-flight points from joint GP posterior.
    
    Returns:
        np.ndarray of shape (n_fantasies, N_pending)
    """
    X_pending = np.asarray(X_pending, dtype=np.float64)
    n_pending = len(X_pending)
    if n_pending == 0:
        return np.empty((n_fantasies, 0), dtype=np.float64)

    mu_pending, _, cov_pending = gp.predict(X_pending, return_cov=True)
    
    # Add numerical stability jitter to covariance
    cov_stable = cov_pending + 1e-6 * np.eye(n_pending)
    try:
        L_cov = np.linalg.cholesky(cov_stable)
    except np.linalg.LinAlgError:
        L_cov = np.linalg.cholesky(cov_stable + 1e-4 * np.eye(n_pending))

    rng = np.random.default_rng(seed)
    eps = rng.standard_normal((n_fantasies, n_pending))
    
    # y_tilde^(m) = mu + L @ eps
    fantasy_outcomes = mu_pending[np.newaxis, :] + np.dot(eps, L_cov.T)
    return fantasy_outcomes


def _expected_improvement(
    mu: np.ndarray,
    var: np.ndarray,
    best_y: float,
    xi: float = 0.01,
) -> np.ndarray:
    """Compute Expected Improvement (EI) acquisition values."""
    sigma = np.sqrt(np.maximum(1e-10, var))
    improvement = mu - best_y - xi
    z = improvement / sigma
    ei = improvement * norm.cdf(z) + sigma * norm.pdf(z)
    return np.maximum(0.0, ei)


def _upper_confidence_bound(
    mu: np.ndarray,
    var: np.ndarray,
    kappa: float = 2.0,
) -> np.ndarray:
    """Compute Upper Confidence Bound (UCB) acquisition values."""
    sigma = np.sqrt(np.maximum(1e-10, var))
    return mu + kappa * sigma


def compute_async_acquisition(
    X_candidates: np.ndarray,
    X_historical: np.ndarray,
    y_historical: np.ndarray,
    X_pending: Optional[np.ndarray] = None,
    acquisition_type: str = "EI",
    n_fantasies: int = 32,
    xi: float = 0.01,
    kappa: float = 2.0,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Evaluate Asynchronous Acquisition function averaged across M Monte Carlo fantasy worlds.
    
    Args:
        X_candidates: Candidate feature matrix (N_candidates, d).
        X_historical: Measured feature matrix (N_hist, d).
        y_historical: Measured potency values (N_hist,).
        X_pending: In-flight candidate feature matrix (N_pending, d).
        acquisition_type: 'EI' (Expected Improvement) or 'UCB' (Upper Confidence Bound).
        n_fantasies: Number of Monte Carlo trajectories M (default: 32).
    """
    X_candidates = np.asarray(X_candidates, dtype=np.float64)
    X_historical = np.asarray(X_historical, dtype=np.float64)
    y_historical = np.asarray(y_historical, dtype=np.float64)

    base_gp = GaussianProcessSurrogate()
    base_gp.fit(X_historical, y_historical)
    best_y = float(np.max(y_historical)) if len(y_historical) > 0 else 0.0

    if X_pending is None or len(X_pending) == 0:
        # Standard sequential acquisition without pending points
        mu, var = base_gp.predict(X_candidates)
        if acquisition_type.upper() == "UCB":
            return _upper_confidence_bound(mu, var, kappa=kappa)
        return _expected_improvement(mu, var, best_y=best_y, xi=xi)

    X_pending = np.asarray(X_pending, dtype=np.float64)
    
    # 1. Sample M fantasy outcomes for X_pending
    fantasies = sample_fantasy_outcomes(base_gp, X_pending, n_fantasies=n_fantasies, seed=seed)
    
    # 2. Evaluate acquisition across all M fantasy worlds
    all_acquisitions = np.zeros((n_fantasies, len(X_candidates)), dtype=np.float64)
    # Hoist constant feature matrix stacking outside the loop
    X_aug = np.vstack([X_historical, X_pending])

    for m in range(n_fantasies):
        y_fantasy = fantasies[m]
        y_aug = np.concatenate([y_historical, y_fantasy])
        
        virtual_gp = GaussianProcessSurrogate()
        virtual_gp.fit(X_aug, y_aug)
        
        aug_best_y = float(np.max(y_aug))
        mu_m, var_m = virtual_gp.predict(X_candidates)
        
        if acquisition_type.upper() == "UCB":
            all_acquisitions[m] = _upper_confidence_bound(mu_m, var_m, kappa=kappa)
        else:
            all_acquisitions[m] = _expected_improvement(mu_m, var_m, best_y=aug_best_y, xi=xi)

    # 3. Asynchronous Acquisition = Monte Carlo mean across all fantasy worlds
    alpha_async = np.mean(all_acquisitions, axis=0)
    return alpha_async



def propose_async_batch(
    candidate_pool: Sequence[Dict[str, Any]],
    historical_candidates: Sequence[Dict[str, Any]],
    pending_candidates: Optional[Sequence[Dict[str, Any]]] = None,
    batch_size: int = 10,
    acquisition_type: str = "EI",
    n_fantasies: int = 32,
    temperature: float = 10.0,
    use_dpp: bool = True,
    gamma: Optional[float] = None,
) -> DPPBatchResult:
    """Master Asynchronous Proposer combining Monte Carlo Fantasy BO with DPP Sequence Diversity.
    
    Selects Round N+1 candidates that are repelled from in-flight Round N candidates.
    """
    if len(candidate_pool) == 0:
        return DPPBatchResult([], [], [], [], 0.0, [])

    # 1. Feature Extraction
    pool_seqs = [c.get("sequence", "") for c in candidate_pool]
    hist_seqs = [c.get("sequence", "") for c in historical_candidates]
    
    X_pool = generate_sequence_features(pool_seqs)
    X_hist = generate_sequence_features(hist_seqs)
    y_hist = np.array([
        float(c.get("potency", c.get("overall_score", c.get("manufacturability_score", 50.0))))
        for c in historical_candidates
    ], dtype=np.float64)

    X_pending: Optional[np.ndarray] = None
    if pending_candidates and len(pending_candidates) > 0:
        pending_seqs = [c.get("sequence", "") for c in pending_candidates]
        X_pending = generate_sequence_features(pending_seqs)

    # 2. Compute Asynchronous Acquisition Scores
    alpha_async = compute_async_acquisition(
        X_candidates=X_pool,
        X_historical=X_hist,
        y_historical=y_hist,
        X_pending=X_pending,
        acquisition_type=acquisition_type,
        n_fantasies=n_fantasies,
    )

    # 3. Batch Selection (DPP Diversity or Top-K)
    if use_dpp:
        return greedy_dpp_map_selection(
            candidates=candidate_pool,
            q=batch_size,
            quality_scores=alpha_async,
            embeddings=X_pool,
            temperature=temperature,
            gamma=gamma,
        )
    else:
        # Fallback: Naive Top-K by asynchronous score
        sorted_indices = np.argsort(alpha_async)[::-1][:batch_size].tolist()
        cand_ids = [candidate_pool[i].get("candidate_id", f"CAND-{i:03d}") for i in sorted_indices]
        seqs = [pool_seqs[i] for i in sorted_indices]
        scores = [float(alpha_async[i]) for i in sorted_indices]
        avg_dist = compute_average_pairwise_distance(X_pool, sorted_indices)
        
        return DPPBatchResult(
            selected_indices=sorted_indices,
            selected_candidate_ids=cand_ids,
            selected_sequences=seqs,
            quality_scores=scores,
            average_pairwise_distance=avg_dist,
        )

