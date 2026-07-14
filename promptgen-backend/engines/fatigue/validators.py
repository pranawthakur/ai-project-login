def validate_sleep_hours(v: float) -> float:
    if not isinstance(v, (int, float)) or v < 0 or v > 24:
        raise ValueError(f"sleep_hours must be 0-24, got {v!r}")
    return v


def validate_stress_level(v: str) -> str:
    if v not in ("low", "moderate", "high"):
        raise ValueError(f"stress_level must be low/moderate/high, got {v!r}")
    return v


def validate_training_age(v: float) -> float:
    if not isinstance(v, (int, float)) or v < 0:
        raise ValueError(f"training_age_years must be >= 0, got {v!r}")
    return v
