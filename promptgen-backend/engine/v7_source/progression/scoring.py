"""Confidence-scoring re-export point -- the real formula lives in
rules.py (Section 5 of file 17). Kept as a thin wrapper since other
modules may expect scoring.py to exist."""
from .rules import compute_recommendation_confidence
