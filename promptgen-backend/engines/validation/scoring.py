"""
scoring.py -- Validation Engine
==================================
adherence_risk_score in rules.py already returns a numeric score; this
module holds the small amount of pure-scoring logic that doesn't belong
in rules.py's algorithm ports -- currently just a confidence-tier ranking
helper used when multiple tier signals need to be compared/merged.
"""

from __future__ import annotations

from .models import ConfidenceTier

# Ordinal ranking, worst (most restrictive) first -- lower index = more
# restrictive. Source: tier ordering implied by file 11 Sec 2.2's own
# row order (green -> yellow -> orange -> red) and file 0 Sec 7's
# "safety and gating always take precedence" rule (red/orange should win
# when merging signals from multiple sources).
_TIER_RESTRICTIVENESS = {
    ConfidenceTier.RED: 0,
    ConfidenceTier.ORANGE: 1,
    ConfidenceTier.YELLOW: 2,
    ConfidenceTier.GREEN: 3,
}


def most_restrictive_tier(tiers: list[ConfidenceTier]) -> ConfidenceTier:
    """
    Given multiple confidence_tier signals (e.g. one derived from intake,
    one from check-in cadence), returns the most restrictive -- i.e. the
    system should never silently use a looser tier than any single signal
    warrants.
    """
    if not tiers:
        raise ValueError("at least one tier is required")
    return min(tiers, key=lambda t: _TIER_RESTRICTIVENESS[t])
