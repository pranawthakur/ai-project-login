"""Input validation for constraints engine. Raises ValueError on malformed
input -- fail loud at the boundary, fail conservative inside rules.py."""
from typing import Any
from . import lookup_tables as T


def validate_pain_scale(v: int) -> int:
    if not isinstance(v, int) or v < 0 or v > 10:
        raise ValueError(f"pain_scale must be int 0-10, got {v!r}")
    return v


def validate_condition(condition: str) -> str:
    if not isinstance(condition, str):
        raise ValueError(f"condition must be str, got {type(condition)}")
    return condition


def validate_injury_type(injury_type: Any) -> Any:
    if injury_type is not None and not isinstance(injury_type, str):
        raise ValueError(f"injury_type must be str or None, got {type(injury_type)}")
    return injury_type


def validate_age(age: int) -> int:
    if not isinstance(age, int) or age < 0 or age > 120:
        raise ValueError(f"age must be int 0-120, got {age!r}")
    return age


def validate_medications(medications) -> list:
    if not isinstance(medications, (list, tuple)):
        raise ValueError("medications must be a list")
    return list(medications)
