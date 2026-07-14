"""
validators.py -- Substitution (Exercise Conflict) Engine
============================================================
Input validation. Raises ValueError on malformed input -- fail loud at the
boundary (consistent with the constraints engine's convention).
"""

from __future__ import annotations

from .models import SessionExercise


def validate_joint_stress_dict(joint_stress: dict) -> dict:
    for joint, value in joint_stress.items():
        if not isinstance(joint, str):
            raise ValueError(f"joint_stress keys must be str, got {type(joint)}")
        if not isinstance(value, int) or not (0 <= value <= 3):
            raise ValueError(
                f"joint_stress['{joint}']={value!r} must be an int in 0-3"
            )
    return joint_stress


def validate_session_exercise(item: SessionExercise) -> list[str]:
    """Returns a list of error strings (empty = valid)."""
    errors = []
    if not item.exercise_id:
        errors.append("missing exercise_id")
    if item.order < 0:
        errors.append(f"{item.exercise_id}: order must be >= 0, got {item.order}")
    try:
        validate_joint_stress_dict(item.joint_stress)
    except ValueError as e:
        errors.append(f"{item.exercise_id}: {e}")
    return errors


def validate_session(session: list[SessionExercise]) -> list[str]:
    """Validates every item, plus checks exercise_id uniqueness within
    the session (a session can't legitimately contain the same exercise
    twice under the same id -- that's a caller bug, not a conflict to
    detect)."""
    errors = []
    seen = set()
    for item in session:
        errors.extend(validate_session_exercise(item))
        if item.exercise_id in seen:
            errors.append(f"duplicate exercise_id in session: {item.exercise_id}")
        seen.add(item.exercise_id)
    return errors
