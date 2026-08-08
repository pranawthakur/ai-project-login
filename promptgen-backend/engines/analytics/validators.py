"""app/engines/analytics/validators.py"""

from __future__ import annotations
from .models import AdherenceReport


def validate_adherence_report(report: AdherenceReport) -> list[str]:
    errors = []
    if report.sets_prescribed < 0:
        errors.append("sets_prescribed cannot be negative")
    if report.sets_logged < 0:
        errors.append("sets_logged cannot be negative")
    if report.streak_weeks < 0:
        errors.append("streak_weeks cannot be negative")
    return errors
