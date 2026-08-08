"""
validators.py -- Biomechanics Engine
======================================
Input validation. Raises ValueError on malformed input -- fail loud at the
boundary (consistent with the constraints engine's convention).
"""

from __future__ import annotations

from typing import Any

from .models import MovementPattern, MovementRecord


def validate_movement_pattern(value: Any) -> MovementPattern:
    if isinstance(value, MovementPattern):
        return value
    try:
        return MovementPattern(value)
    except ValueError:
        valid = [p.value for p in MovementPattern]
        raise ValueError(f"invalid movement_pattern {value!r}; must be one of {valid}")


def validate_movement_record_required_fields(record: MovementRecord) -> list[str]:
    """Returns a list of error strings (empty = valid). Only checks fields
    the dataclass itself requires (exercise_id, movement_pattern) plus
    primary_movement, which the KB schema lists first and treats as
    mandatory descriptive text."""
    errors = []
    if not record.exercise_id:
        errors.append("missing exercise_id")
    if not isinstance(record.movement_pattern, MovementPattern):
        errors.append(f"{record.exercise_id}: movement_pattern must be a MovementPattern")
    if not record.primary_movement:
        errors.append(f"{record.exercise_id}: primary_movement must not be empty")
    return errors


def validate_pattern_list(patterns: list) -> list[MovementPattern]:
    """Validates a list of raw pattern values (e.g. from an API payload),
    returning the coerced MovementPattern list or raising on the first bad
    entry."""
    return [validate_movement_pattern(p) for p in patterns]
