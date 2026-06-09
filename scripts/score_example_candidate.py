from peptide_flywheel.scoring import heuristic_manufacturability_score

sequence = "ACDEFGHIKLMNPQRSTVWY"
result = heuristic_manufacturability_score(sequence)

print("Sequence:", sequence)
print("Overall score:", result.overall_score)
print("Recommendation:", result.recommendation)
print("Risk flags:", result.risk_flags)
print("Dimension scores:", result.dimension_scores)
