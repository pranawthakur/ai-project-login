def validate_confidence_tier(v: str) -> str:
    if v not in ("orange", "yellow", "green"):
        raise ValueError(f"confidence_tier must be orange/yellow/green, got {v!r}")
    return v


def validate_recovery_score(v: str) -> str:
    if v not in ("poor", "moderate", "good"):
        raise ValueError(f"recovery_score must be poor/moderate/good, got {v!r}")
    return v


def validate_days_available(v: int) -> int:
    if not isinstance(v, int) or v < 1 or v > 7:
        raise ValueError(f"days_available must be int 1-7, got {v!r}")
    return v
