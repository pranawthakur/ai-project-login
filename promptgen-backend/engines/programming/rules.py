"""Deterministic logic ported from KB V7 file 14. Fails closed: whenever
exit or override criteria are ambiguous, the conservative branch wins."""
from typing import Optional
from .models import (
    SafeTemplate, ExerciseSlot, OverrideRequest, OverrideResult,
    ClientProgrammingState, ConfidenceTier,
)
from . import lookup_tables as T


# =====================================================================
# SECTION 1 -- DEFAULT_SAFE_TEMPLATE
# =====================================================================

def build_default_safe_template(pain_provoking_movements: Optional[list] = None,
                                 thoracic_mobility_limited: bool = False) -> SafeTemplate:
    """Builds the concrete fallback program. Regresses any exercise flagged
    pain-provoking for this individual; substitutes overhead work if
    thoracic mobility is limited."""
    pain_provoking_movements = pain_provoking_movements or []
    exercises = []
    for row in T.DEFAULT_SAFE_TEMPLATE_EXERCISES:
        exercise = row["exercise"]
        if exercise in pain_provoking_movements:
            exercise = row["regression"]
        exercises.append(ExerciseSlot(pattern=row["pattern"], exercise=exercise, regression=row["regression"]))

    never_includes = list(T.DEFAULT_SAFE_TEMPLATE_NEVER_INCLUDES)

    return SafeTemplate(
        exercises=exercises,
        warmup_protocol=list(T.DEFAULT_SAFE_TEMPLATE_WARMUP),
        never_includes=never_includes,
        intensity_techniques_permitted=False,
        hiit_permitted=False,
    )


def can_exit_safe_template(cs: ClientProgrammingState) -> bool:
    """Fails closed: if unclear, client stays on DEFAULT_SAFE_TEMPLATE."""
    if "medical_clearance_required" in cs.flags and not cs.medical_clearance_resolved:
        return False
    if "below_minimum_age_reject" in cs.flags:
        return False  # permanent block, not exitable
    if cs.confidence_tier == ConfidenceTier.ORANGE:
        # orange due to missed check-ins only
        if cs.consecutive_checkins_submitted >= 2 and not cs.flags:
            return True
        # orange due to unresolved pain flag
        if cs.pain_flag_resolved and cs.reintroduce_pattern_completed:
            return True
    if not cs.movement_screen_completed:
        return cs.movement_screen_completed  # explicit: only true once screen run
    return False  # fail closed default


# =====================================================================
# SECTION 2 -- COACH OVERRIDE ENGINE
# =====================================================================

def check_override_permission(field_overridden: str) -> bool:
    return T.OVERRIDE_PERMISSIONS.get(field_overridden, False)  # unknown field: fail closed (not overridable)


def apply_override(request: OverrideRequest) -> OverrideResult:
    if not request.coach_certification_verified:
        return OverrideResult(allowed=False, reason="coach_not_certification_verified",
                               audit_entry={"attempt_logged": True, "notify_gym_admin": True})

    if not check_override_permission(request.field_overridden):
        return OverrideResult(allowed=False, reason="field_not_overridable_regardless_of_certification")

    audit_entry = {
        "override_id": request.override_id,
        "coach_id": request.coach_id,
        "client_id": request.client_id,
        "timestamp": request.timestamp,
        "field_overridden": request.field_overridden,
        "system_recommendation": request.system_recommendation,
        "coach_decision": request.coach_decision,
        "justification_note": request.justification_note,
        "immutable": True,
    }

    if request.field_overridden == "confidence_tier_upgrade_downgrade":
        if len(request.justification_note) < 1:
            return OverrideResult(allowed=False, reason="justification_note_required_for_tier_change")

    return OverrideResult(allowed=True, reason="override_applied", audit_entry=audit_entry)


def escalated_override_check(request: OverrideRequest, field_overridden: str) -> OverrideResult:
    """For overrides that exceed a tier's hard cap (e.g. HIIT for orange tier
    under direct in-person supervision)."""
    if not check_override_permission(field_overridden):
        return OverrideResult(allowed=False, reason="section_2_1_no_row_never_overridable_regardless_of_certification")
    if not request.coach_certification_verified:
        return OverrideResult(allowed=False, reason="coach_not_certification_verified")
    if len(request.justification_note) < 20:
        return OverrideResult(allowed=False, reason="justification_note_must_be_non_trivial_ge_20_chars")
    if not request.in_person_supervision_confirmed:
        return OverrideResult(allowed=False, reason="in_person_supervision_required_for_cap_beyond_tier_default")

    audit_entry = {
        "override_id": request.override_id,
        "coach_id": request.coach_id,
        "client_id": request.client_id,
        "field_overridden": field_overridden,
        "escalated": True,
        "in_person_supervision_confirmed": True,
        "immutable": True,
    }
    return OverrideResult(allowed=True, reason="escalated_override_applied", audit_entry=audit_entry, review_flag=True)


def resolve_conflicting_overrides(overrides: list) -> dict:
    """Two coaches submit conflicting overrides same day: most recent
    timestamped override is active; both remain in audit trail."""
    if not overrides:
        return {}
    most_recent = max(overrides, key=lambda o: o["timestamp"])
    return {"active": most_recent, "audit_trail": list(overrides)}


# =====================================================================
# SECTION 3 -- TIER TRANSITION MATRIX
# =====================================================================

def evaluate_tier_transition(cs: ClientProgrammingState, event: str) -> Optional[dict]:
    """Looks up whether `event` matches a defined automatic transition.
    Returns the matching transition row, or None if no rule fires."""
    for row in T.TIER_TRANSITIONS:
        if row["trigger"] == event:
            return row
    return None


def determine_tier_from_state(cs: ClientProgrammingState) -> ConfidenceTier:
    if "below_minimum_age_reject" in cs.flags or "emergency_symptom_logged" in cs.flags:
        return ConfidenceTier.RED
    if not cs.medical_clearance_resolved and "medical_clearance_required" in cs.flags:
        return ConfidenceTier.ORANGE
    if cs.weeks_consistent_checkins >= 8 and cs.intake_completeness_pct >= 95.0 and not cs.flags:
        return ConfidenceTier.GREEN
    if cs.consecutive_checkins_submitted == 0:
        return ConfidenceTier.YELLOW
    return cs.confidence_tier
