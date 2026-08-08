"""
app/engines/exercise_database/rules.py

Deterministic lookup functions over the tables in lookup_tables.py.
Ports file 9 §4/§5 substitution rules and §1 classification rule into
callable functions instead of leaving them as tables the caller has to
know how to query correctly.
"""

from __future__ import annotations
from .lookup_tables import (
    EQUIPMENT_SUBSTITUTION, INJURY_SUBSTITUTION, TIER_EXAMPLES,
    PATTERN_WEEKLY_MINIMUMS, GYM_CONTEXT_ADJUSTMENT,
)
from .models import Tier, MovementPattern


def equipment_substitute(exercise_name: str, available: str) -> str | None:
    """file 9 §4. `available` is one of 'dumbbell' | 'machine' | 'bodyweight_band'."""
    row = EQUIPMENT_SUBSTITUTION.get(exercise_name)
    if row is None:
        return None
    return row.get(available)


def injury_substitute(condition: str) -> dict | None:
    """file 9 §5. Returns {"avoid": [...], "substitute": [...]} or None if
    the condition isn't one the KB covers. Rule from the same section: pain
    during an exercise means stop and substitute immediately regardless of
    program design — general fatigue/burn is NOT the same signal and must
    not trigger this path."""
    return INJURY_SUBSTITUTION.get(condition)


def classify_tier(exercise_name: str) -> Tier | None:
    """file 9 §1. Only returns a tier for the KB's own worked examples —
    None means the KB doesn't classify this specific exercise name, not
    that it has no tier at all."""
    for tier_key, names in TIER_EXAMPLES.items():
        if exercise_name in names:
            return Tier(tier_key)
    return None


def weekly_pattern_coverage_met(pattern: MovementPattern, planned_touches: int) -> bool:
    """file 9 §2. True if planned_touches meets the KB's stated minimum
    weekly touches for this pattern (upper bound, if given, is informational
    only — the KB states these as floors, e.g. '2+', not caps)."""
    minimum = PATTERN_WEEKLY_MINIMUMS.get(pattern)
    if minimum is None:
        return True  # pattern not covered by this table — no stated minimum to fail
    lo, _hi = minimum
    return planned_touches >= lo


def gym_context_adjustment(context: str) -> str | None:
    """file 9 §6. `context` is one of the GYM_CONTEXT_ADJUSTMENT keys."""
    return GYM_CONTEXT_ADJUSTMENT.get(context)
