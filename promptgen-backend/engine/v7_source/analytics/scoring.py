"""app/engines/analytics/scoring.py"""

from __future__ import annotations
from .models import AdherenceReport, AdherenceTier
from . import constants as C


def _tier_for_pct(pct: float) -> AdherenceTier:
    if pct >= C.HIGH_THRESHOLD:
        return AdherenceTier.HIGH
    if pct >= C.MODERATE_THRESHOLD:
        return AdherenceTier.MODERATE
    return AdherenceTier.LOW


def compute_adherence(member_id: str, week_number: int, sets_prescribed: int,
                       sets_logged: int, prior_weekly_tiers: list[AdherenceTier] | None = None) -> AdherenceReport:
    """`prior_weekly_tiers` should be ordered most-recent-first, covering
    the weeks immediately before this one, if you want streak_weeks
    computed. Pass None/empty if unavailable — streak just comes back 0
    or 1 in that case rather than erroring."""
    if sets_prescribed <= 0:
        pct = 0.0
    else:
        pct = round((sets_logged / sets_prescribed) * 100, 1)

    tier = _tier_for_pct(pct)

    streak = 1 if tier == AdherenceTier.HIGH else 0
    if tier == AdherenceTier.HIGH and prior_weekly_tiers:
        for prior in prior_weekly_tiers:
            if prior == AdherenceTier.HIGH:
                streak += 1
            else:
                break

    return AdherenceReport(member_id=member_id, week_number=week_number,
                            sets_prescribed=sets_prescribed, sets_logged=sets_logged,
                            adherence_pct=pct, tier=tier, streak_weeks=streak)
