def validate_supplement_name(v: str) -> str:
    if not isinstance(v, str) or not v:
        raise ValueError(f"supplement name must be a non-empty string, got {v!r}")
    return v


def validate_age(v) -> int:
    if v is not None and (not isinstance(v, int) or v < 0 or v > 120):
        raise ValueError(f"age must be int 0-120 or None, got {v!r}")
    return v
