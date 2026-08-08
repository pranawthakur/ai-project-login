"""
rules.py -- Biomechanics Engine
=================================
Deterministic classification and comparison logic over MovementPattern /
MovementRecord. No natural-language rules -- every KB bullet this engine
is responsible for is ported to a real function.
"""

from __future__ import annotations

from . import lookup_tables as T
from .models import (
    ComplexityTier,
    FunctionalCategory,
    MovementPattern,
    MovementRecord,
)

PUSH_PATTERNS = frozenset({MovementPattern.HORIZONTAL_PUSH, MovementPattern.VERTICAL_PUSH})
PULL_PATTERNS = frozenset({MovementPattern.HORIZONTAL_PULL, MovementPattern.VERTICAL_PULL})
LOWER_BODY_PATTERNS = frozenset(
    {MovementPattern.SQUAT, MovementPattern.HIP_HINGE, MovementPattern.LUNGE}
)
CORE_PATTERNS = frozenset({MovementPattern.ROTATION, MovementPattern.ANTI_ROTATION})


def is_push_pattern(pattern: MovementPattern) -> bool:
    return pattern in PUSH_PATTERNS


def is_pull_pattern(pattern: MovementPattern) -> bool:
    return pattern in PULL_PATTERNS


def is_lower_body_pattern(pattern: MovementPattern) -> bool:
    return pattern in LOWER_BODY_PATTERNS


def is_core_pattern(pattern: MovementPattern) -> bool:
    return pattern in CORE_PATTERNS


def opposing_pattern(pattern: MovementPattern) -> MovementPattern | None:
    """
    Returns the complementary/antagonist pattern for weekly-balance checks
    (e.g. flag a program that has horizontal push volume but zero
    horizontal pull volume). Returns None for patterns with no defined
    pair in this taxonomy (Carry, Lunge). See lookup_tables.OPPOSING_PATTERN.
    """
    return T.OPPOSING_PATTERN[pattern]


def default_functional_category(pattern: MovementPattern) -> FunctionalCategory:
    """Engineering-default functional category for a pattern; see
    lookup_tables.PATTERN_DEFAULTS docstring re: KB provenance."""
    return T.PATTERN_DEFAULTS[pattern]["functional_category"]


def apply_pattern_defaults(record: MovementRecord) -> MovementRecord:
    """
    Returns a new MovementRecord with any unset schema fields
    (plane_of_motion, force_vector, bilaterality, chain_type,
    functional_category) filled in from the pattern-level engineering
    defaults in lookup_tables.PATTERN_DEFAULTS. Fields the caller already
    set are left untouched -- this never overwrites curated data, it only
    fills gaps.
    """
    defaults = T.PATTERN_DEFAULTS[record.movement_pattern]
    from dataclasses import replace

    updates = {}
    for key, default_value in defaults.items():
        if getattr(record, key) is None:
            updates[key] = default_value
    return replace(record, **updates) if updates else record


def is_ready_for_classification(record: MovementRecord) -> bool:
    """
    Minimum bar for using a MovementRecord in similarity/pairing logic:
    movement_pattern is always required by the dataclass; this additionally
    requires functional_category (either curated or pattern-defaulted via
    apply_pattern_defaults) since most rules in this module branch on it.
    """
    return record.functional_category is not None


def pattern_coverage_gaps(
    patterns_used: list[MovementPattern],
) -> list[MovementPattern]:
    """
    Given the distinct movement patterns present in a program/week, returns
    the core patterns (of the 10-pattern taxonomy) that are entirely
    absent. Pure set-difference gap check for the exercise-selection /
    programming engines to consume.
    """
    used = set(patterns_used)
    return [p for p in MovementPattern if p not in used]


def complexity_at_least(record: MovementRecord, tier: ComplexityTier) -> bool:
    """True if record.complexity is curated and >= the given tier. False
    (not an error) if complexity hasn't been curated yet -- callers that
    need a hard requirement should check is_complete() first."""
    if record.complexity is None:
        return False
    return int(record.complexity) >= int(tier)
