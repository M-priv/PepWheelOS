from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np

from .domain_drc import calculate_gravy, calculate_net_charge


STANDARD_AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
AA_INDEX_MAP = {aa: i for i, aa in enumerate(STANDARD_AMINO_ACIDS)}


@dataclass
class DPPSelectionStep:
    step: int
    selected_index: int
    candidate_id: str
    marginal_log_gain: float
    quality_score: float


@dataclass
class DPPBatchResult:
    selected_indices: List[int]
    selected_candidate_ids: List[str]
    selected_sequences: List[str]
    quality_scores: List[float]
    average_pairwise_distance: float
    selection_trace: List[DPPSelectionStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_indices": self.selected_indices,
            "selected_candidate_ids": self.selected_candidate_ids,
            "selected_sequences": self.selected_sequences,
            "quality_scores": [round(s, 4) for s in self.quality_scores],
            "average_pairwise_distance": round(self.average_pairwise_distance, 4),
            "batch_size": len(self.selected_indices),
            "selection_trace": [
                {
                    "step": t.step,
                    "selected_index": t.selected_index,
                    "candidate_id": t.candidate_id,
                    "marginal_log_gain": round(t.marginal_log_gain, 4),
                    "quality_score": round(t.quality_score, 4),
                }
                for t in self.selection_trace
            ],
        }


def generate_sequence_features(sequences: Sequence[str]) -> np.ndarray:
    """Generate 24-dimensional normalized biophysical & composition vectors for peptide sequences.
    
    Dimensions:
    - 0..19: Normalized amino acid frequencies
    - 20: Normalized length (clipped to [0, 50] / 50.0)
    - 21: GRAVY hydropathy index (scaled to [-4.5, 4.5] -> [0, 1])
    - 22: Net charge at pH 7.4 (scaled from [-10, +10] -> [0, 1])
    - 23: Aromatic residue fraction (F, W, Y)
    """
    n = len(sequences)
    features = np.zeros((n, 24), dtype=np.float64)

    for i, seq in enumerate(sequences):
        clean_seq = seq.strip().upper()
        l = len(clean_seq)
        if l == 0:
            continue

        # 1. Amino acid frequencies (20 dimensions)
        for aa in clean_seq:
            if aa in AA_INDEX_MAP:
                features[i, AA_INDEX_MAP[aa]] += 1.0
        features[i, :20] /= l

        # 2. Length (normalized 0..1)
        features[i, 20] = min(l, 50) / 50.0

        # 3. GRAVY hydropathy index (scaled from [-4.5, 4.5] to [0, 1])
        gravy = calculate_gravy(clean_seq)
        features[i, 21] = np.clip((gravy + 4.5) / 9.0, 0.0, 1.0)

        # 4. Net charge at pH 7.4 (scaled from [-10, 10] to [0, 1])
        charge = calculate_net_charge(clean_seq, ph=7.4)
        features[i, 22] = np.clip((charge + 10.0) / 20.0, 0.0, 1.0)

        # 5. Aromatic fraction
        aromatic_count = sum(1 for aa in clean_seq if aa in ("F", "W", "Y"))
        features[i, 23] = aromatic_count / l

    return features


def compute_diversity_kernel(
    embeddings: np.ndarray,
    gamma: Optional[float] = None,
) -> np.ndarray:
    """Compute RBF Gaussian similarity kernel K_ij = exp(-gamma * ||e_i - e_j||^2)."""
    embeddings = np.asarray(embeddings, dtype=np.float64)
    n, d = embeddings.shape

    if gamma is None:
        # Default gamma heuristic: 1 / d
        gamma = 1.0 / max(d, 1)

    # Vectorized squared Euclidean distance: ||x - y||^2 = ||x||^2 + ||y||^2 - 2 <x, y>
    norms_sq = np.sum(embeddings**2, axis=1, keepdims=True)
    dist_sq = np.maximum(0.0, norms_sq + norms_sq.T - 2.0 * np.dot(embeddings, embeddings.T))
    
    # RBF Kernel matrix (values in (0, 1], diagonal is 1.0)
    K = np.exp(-gamma * dist_sq)
    # Numerical stability safeguard: ensure exact 1.0 on diagonal
    np.fill_diagonal(K, 1.0)
    return K


def construct_l_ensemble(
    quality_scores: Union[np.ndarray, Sequence[float]],
    similarity_matrix: np.ndarray,
    temperature: float = 10.0,
) -> np.ndarray:
    """Construct symmetric positive semi-definite L-ensemble matrix: L = diag(q) @ K @ diag(q).
    
    Args:
        quality_scores: Raw scores (e.g. 0 to 100).
        similarity_matrix: N x N similarity kernel K (values in [0, 1]).
        temperature: Temperature parameter tau > 0 controlling quality scaling.
    """
    scores = np.asarray(quality_scores, dtype=np.float64)
    if temperature <= 0:
        raise ValueError(f"Temperature must be strictly positive, got {temperature}")

    # Scale quality scores to prevent numerical overflow: q_i = exp( (score_i - max_score) / tau )
    max_score = np.max(scores) if len(scores) > 0 else 0.0
    scaled_scores = (scores - max_score) / temperature
    q = np.exp(scaled_scores)

    # L_ij = q_i * K_ij * q_j
    L = np.outer(q, q) * similarity_matrix
    return L


def compute_average_pairwise_distance(embeddings: np.ndarray, indices: Sequence[int]) -> float:
    """Calculate the mean pairwise Euclidean distance of a selected subset."""
    if len(indices) <= 1:
        return 0.0
    sub_emb = embeddings[list(indices)]
    diffs = sub_emb[:, np.newaxis, :] - sub_emb[np.newaxis, :, :]
    dists = np.sqrt(np.sum(diffs**2, axis=-1))
    
    # Extract strictly upper triangle
    upper_tri_indices = np.triu_indices(len(indices), k=1)
    return float(np.mean(dists[upper_tri_indices]))


def greedy_dpp_map_selection(
    candidates: Sequence[Dict[str, Any]],
    q: int,
    quality_scores: Optional[Sequence[float]] = None,
    embeddings: Optional[np.ndarray] = None,
    temperature: float = 10.0,
    gamma: Optional[float] = None,
) -> DPPBatchResult:
    """Greedy Submodular MAP Selection for Determinantal Point Process (DPP).
    
    Selects a diverse batch Y of size q maximizing log det(L_Y) in O(q^2 * N) time.
    
    Args:
        candidates: List of candidate dictionaries (must contain 'candidate_id' and 'sequence').
        q: Target batch size.
        quality_scores: Optional quality scores (defaults to candidate's 'overall_score' or 'manufacturability_score').
        embeddings: Optional N x d feature vectors (generated automatically if None).
        temperature: Quality temperature scaling tau.
        gamma: RBF kernel bandwidth parameter.
    """
    n = len(candidates)
    if n == 0:
        return DPPBatchResult([], [], [], [], 0.0, [])

    q = min(q, n)

    # 1. Resolve Candidate IDs & Sequences
    cand_ids = [c.get("candidate_id", f"CAND-{i:03d}") for i, c in enumerate(candidates)]
    sequences = [c.get("sequence", "") for c in candidates]

    # 2. Resolve Quality Scores
    if quality_scores is None:
        quality_scores = [
            float(c.get("overall_score", c.get("manufacturability_score", 50.0)))
            for c in candidates
        ]
    scores_arr = np.asarray(quality_scores, dtype=np.float64)

    # 3. Resolve Embeddings
    if embeddings is None:
        embeddings = generate_sequence_features(sequences)
    else:
        embeddings = np.asarray(embeddings, dtype=np.float64)

    # 4. Construct L-Ensemble Matrix
    K = compute_diversity_kernel(embeddings, gamma=gamma)
    L = construct_l_ensemble(scores_arr, K, temperature=temperature)

    # 5. Greedy Submodular MAP Selection
    selected_indices: List[int] = []
    selection_trace: List[DPPSelectionStep] = []

    for step in range(q):

        best_idx = None
        best_gain = -np.inf

        for i in range(n):
            if i in selected_indices:
                continue

            current_set = selected_indices + [i]
            # Submatrix L_Y
            sub_L = L[np.ix_(current_set, current_set)]
            
            # Slogdet for numerical stability: returns (sign, logdet)
            sign, logdet = np.linalg.slogdet(sub_L)
            
            if sign > 0 and logdet > best_gain:
                best_gain = logdet
                best_idx = i

        if best_idx is None:
            # Fallback if remaining candidates produce singular determinants
            remaining = [i for i in range(n) if i not in selected_indices]
            if remaining:
                best_idx = max(remaining, key=lambda idx: scores_arr[idx])
                best_gain = 0.0
            else:
                break

        selected_indices.append(best_idx)
        selection_trace.append(
            DPPSelectionStep(
                step=step + 1,
                selected_index=best_idx,
                candidate_id=cand_ids[best_idx],
                marginal_log_gain=float(best_gain),
                quality_score=float(scores_arr[best_idx]),
            )
        )

    # 6. Compute Diversity Metrics
    avg_dist = compute_average_pairwise_distance(embeddings, selected_indices)

    return DPPBatchResult(
        selected_indices=selected_indices,
        selected_candidate_ids=[cand_ids[i] for i in selected_indices],
        selected_sequences=[sequences[i] for i in selected_indices],
        quality_scores=[float(scores_arr[i]) for i in selected_indices],
        average_pairwise_distance=avg_dist,
        selection_trace=selection_trace,
    )
