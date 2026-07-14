"""
validators.py -- Validation Engine
=====================================
Input validation. Raises ValueError on malformed input, consistent with
the constraints engine's convention.
"""

from __future__ import annotations

from .models import CheckIn, IntakeRecord


def validate_intake_consent(intake: IntakeRecord) -> list[str]:
    """Returns error strings (empty = valid). Source: 11_...md Sec 2 --
    consent is checked before anything else in processIntake."""
    errors = []
    if "data_processing" not in intake.consent:
        errors.append("consent.data_processing missing")
    if "liability_waiver" not in intake.consent:
        errors.append("consent.liability_waiver missing")
    return errors


def validate_intake_demographics(intake: IntakeRecord) -> list[str]:
    errors = []
    age = intake.demographics.get("age_years")
    if age is None or not isinstance(age, (int, float)) or age < 0:
        errors.append(f"demographics.age_years invalid: {age!r}")
    return errors


def validate_disclosure_completeness(intake: IntakeRecord) -> list[str]:
    errors = []
    pct = intake.disclosure_completeness.get("pct_fields_completed")
    if pct is None or not (0 <= pct <= 100):
        errors.append(f"disclosure_completeness.pct_fields_completed must be 0-100, got {pct!r}")
    return errors


def validate_intake(intake: IntakeRecord) -> list[str]:
    """Full validation pass, aggregating the field-group validators above."""
    errors = []
    errors.extend(validate_intake_consent(intake))
    errors.extend(validate_intake_demographics(intake))
    errors.extend(validate_disclosure_completeness(intake))
    return errors


def validate_check_in(checkin: CheckIn) -> list[str]:
    """Source: 11_...md Sec 5 (ONGOING CHECK-IN SCHEMA) field bounds
    implied by usage elsewhere in the same section (ratios, ratings)."""
    errors = []
    if checkin.sessions_planned < 0:
        errors.append("sessions_planned must be >= 0")
    if checkin.sessions_completed < 0:
        errors.append("sessions_completed must be >= 0")
    if checkin.sessions_planned > 0 and checkin.sessions_completed > checkin.sessions_planned:
        errors.append("sessions_completed cannot exceed sessions_planned")
    if not (0 <= checkin.motivation_rating <= 10):
        errors.append(f"motivation_rating out of expected 0-10 range: {checkin.motivation_rating}")
    return errors
