"""
scoring.py -- Biomechanics Engine
===================================
Deterministic similarity scoring over MovementRecord/MovementPattern.
Consumed by the substitution engine to rank candidate replacement
exercises before that engine layers on its own fatigue/equipment/pain
filters.
"""

from __future__ import annotations

from . import rules
from .models import MovementRecord

_SAME_PATTERN_SCORE = 1.0
_SAME_FUNCTIONAL_CATEGORY_SCORE = 0.5
_NO_RELATION_SCORE = 0.0


def pattern_similarity(record_a: MovementRecord, record_b: MovementRecord) -> float:
    """
    0.0-1.0 taxonomy-level similarity between two exercises' movement
    patterns:
      1.0 -- identical movement_pattern (true substitutes, e.g. back squat
             vs front squat)
      0.5 -- different pattern, same engineering-default functional
             category (e.g. horizontal push vs vertical push -- both PUSH)
      0.0 -- unrelated

    This only uses movement_pattern + functional_category (curated or
    pattern-defaulted via rules.apply_pattern_defaults) -- it does not
    consider muscle overlap or joint stress, since those belong to
    exercise_database's data, not this engine's scope.
    """
    if record_a.movement_pattern == record_b.movement_pattern:
        return _SAME_PATTERN_SCORE

    cat_a = record_a.functional_category or rules.default_functional_category(
        record_a.movement_pattern
    )
    cat_b = record_b.functional_category or rules.default_functional_category(
        record_b.movement_pattern
    )
    if cat_a == cat_b:
        return _SAME_FUNCTIONAL_CATEGORY_SCORE
    return _NO_RELATION_SCORE


def rank_by_pattern_similarity(
    target: MovementRecord, candidates: list[MovementRecord]
) -> list[tuple[MovementRecord, float]]:
    """Ranks candidates by pattern_similarity to target, descending.
    Excludes the target itself if present (by exercise_id)."""
    scored = [
        (c, pattern_similarity(target, c))
        for c in candidates
        if c.exercise_id != target.exercise_id
    ]
    return sorted(scored, key=lambda pair: pair[1], reverse=True)
