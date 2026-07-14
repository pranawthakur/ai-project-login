"""
rules.py -- Validation Engine
================================
Every pseudocode algorithm in the two source files, ported 1:1 to Python.
Each function's docstring cites its exact source section.
"""

from __future__ import annotations

from . import lookup_tables as T
from .models import (
    AdherenceRiskTier,
    CheckIn,
    CheckInResult,
    ClientState,
    ConfidenceTier,
    IntakeRecord,
    IntakeResult,
    IntakeStatus,
    OneRMEstimate,
)

SAFETY_GATE_STEP_ID = "2"  # file 0 Sec 2: safetyGate() step, never skippable


# =======================================================================
# 0_Master_Index_Versioning_and_Localization.md Sec 4 -- normalizeIntakeUnits
# =======================================================================
def normalize_weight_to_kg(value: float, unit: str) -> float:
    """unit: 'kg' | 'lb' | 'stone'. Source: file 0 Sec 4."""
    if unit == "kg":
        return value
    if unit == "lb":
        return round(value * 0.45359237, 4)
    if unit == "stone":
        return round(value * 6.35029318, 4)
    raise ValueError(f"unsupported weight unit: {unit!r}")


def normalize_height_to_cm(value: float, unit: str, inches: float = 0.0) -> float:
    """unit: 'cm' | 'ft_in' (value=feet, inches=extra inches). Source: file 0 Sec 4."""
    if unit == "cm":
        return value
    if unit == "ft_in":
        total_inches = value * 12 + inches
        return round(total_inches * 2.54, 4)
    raise ValueError(f"unsupported height unit: {unit!r}")


def normalize_distance_to_km(value: float, unit: str) -> float:
    """unit: 'km' | 'mi'. Source: file 0 Sec 4 canonical units table."""
    if unit == "km":
        return value
    if unit == "mi":
        return round(value * 1.609344, 4)
    raise ValueError(f"unsupported distance unit: {unit!r}")


def normalize_temperature_to_celsius(value: float, unit: str) -> float:
    """unit: 'celsius' | 'fahrenheit'. Source: file 0 Sec 4 canonical units table."""
    if unit == "celsius":
        return value
    if unit == "fahrenheit":
        return round((value - 32) * 5.0 / 9.0, 4)
    raise ValueError(f"unsupported temperature unit: {unit!r}")


# =======================================================================
# 0_...md Sec 2 -- CANONICAL CALL ORDER, precedence, versioning helpers
# =======================================================================
def validate_call_order(step_ids_run: list[str]) -> list[str]:
    """
    Returns a list of error strings (empty = valid). Enforces the one hard
    rule stated in file 0 Sec 2: "Step 2 (safety gate) is never skipped,
    reordered, or made conditional on tier. It is the first operation in
    every single pipeline run."
    """
    errors = []
    if not step_ids_run:
        errors.append("no steps run -- step 2 (safety gate) is mandatory")
        return errors
    if step_ids_run[0] != SAFETY_GATE_STEP_ID:
        errors.append(
            f"step {SAFETY_GATE_STEP_ID} (safety gate) must run first; "
            f"got {step_ids_run[0]!r} first"
        )
    if SAFETY_GATE_STEP_ID not in step_ids_run:
        errors.append(f"step {SAFETY_GATE_STEP_ID} (safety gate) was skipped entirely")
    return errors


def resolve_precedence(conflicting_file_ids: list) -> object:
    """
    Given a list of file ids (ints, or the string
    'programming_files_1_through_10_13_15') whose instructions conflict,
    returns the one that wins per file 0 Sec 7 FAQ: "File 12 (Safety) >
    File 11 (Intake/tiering) > File 14 (Default template/override) > all
    programming files (1-10, 13, 15)."
    """
    for candidate in T.FILE_PRECEDENCE_ORDER:
        if candidate in conflicting_file_ids:
            return candidate
    raise ValueError(
        f"none of {conflicting_file_ids} appear in the known precedence order"
    )


def is_breaking_change(old_sections: list[str], new_sections: list[str]) -> bool:
    """
    Source: file 0 Sec 3 (VERSIONING CONVENTION) -- "Any edit that
    inserts/removes/renumbers a section is a breaking change for
    cross-references." Modeled as: any change to the ordered section list
    (not just membership -- order matters, since numbering is positional)
    is breaking.
    """
    return old_sections != new_sections


# =======================================================================
# 11_Assessment_and_Intake_Engine.md Sec 2 -- processIntake / routing
# =======================================================================
def process_intake(intake: IntakeRecord) -> IntakeResult:
    """Source: 11_...md Sec 2 (INTAKE VALIDATION & ROUTING ALGORITHM),
    ported 1:1 including branch order (consent check first, age-reject
    short-circuits before other returns, etc.)."""
    flags: list[str] = []

    if not intake.consent.get("data_processing") or not intake.consent.get("liability_waiver"):
        return IntakeResult(status=IntakeStatus.BLOCKED_NO_CONSENT, flags=("consent_required",))

    if intake.health.get("pregnancy_status") == "pregnant":
        flags.append("medical_clearance_required")
    if set(intake.health.get("medical_conditions", [])) & set(T.HIGH_RISK_CONDITIONS.keys()):
        flags.append("medical_clearance_required")
    if intake.health.get("cleared_by_physician") is False:
        flags.append("medical_clearance_required")
    if intake.demographics.get("age_years", 0) < 13:
        flags.append("below_minimum_age_reject")
    elif intake.demographics.get("age_years", 0) < 18:
        flags.append("guardian_awareness_required")
    if intake.training_history.get("months_trained", 0) == 0:
        flags.append("route_to_movement_screen")
    if intake.disclosure_completeness.get("pct_fields_completed", 0) < 60:
        flags.append("incomplete_intake_low_confidence")
    # Sec 2 pseudocode reads `intake.health.refused_fields`, but the Sec 1
    # schema only defines `refused_fields` under `disclosure_completeness`
    # -- the two sections disagree on where this field lives. Both
    # locations are checked so the rule fires regardless of which the
    # caller populated; this is a documented KB inconsistency, not an
    # invented field.
    refused_fields = set(intake.health.get("refused_fields", []) or []) | set(
        intake.disclosure_completeness.get("refused_fields", []) or []
    )
    if "medical_conditions" in refused_fields:
        flags.append("medical_disclosure_refused")

    if "below_minimum_age_reject" in flags:
        return IntakeResult(status=IntakeStatus.REJECTED, reason="below_minimum_age", flags=tuple(flags))

    if "medical_disclosure_refused" in flags:
        return IntakeResult(
            status=IntakeStatus.RESTRICTED_GENERAL_GUIDANCE_ONLY,
            flags=tuple(flags),
            use_default_safe_template=True,
        )

    if "medical_clearance_required" in flags:
        return IntakeResult(
            status=IntakeStatus.PENDING_CLEARANCE,
            flags=tuple(flags),
            use_default_safe_template=True,
        )

    return IntakeResult(status=IntakeStatus.READY, flags=tuple(flags))


def resolve_confidence_tier(intake_result: IntakeResult, weeks_consistent_checkins: int,
                             missed_checkin_cycles: int) -> ConfidenceTier:
    """
    Source: 11_...md Sec 2.2 (System-Wide Confidence Tiering table).
    Deterministic mapping from processIntake() output + check-in history
    onto one of the four tiers, in the table's own precedence (red is
    checked first as the hardest gate, consistent with file 0 Sec 7's
    "safety/gating always take precedence" rule).
    """
    if intake_result.status == IntakeStatus.REJECTED:
        return ConfidenceTier.RED
    if intake_result.status == IntakeStatus.PENDING_CLEARANCE or \
            "medical_disclosure_refused" in intake_result.flags or \
            missed_checkin_cycles >= 2:
        return ConfidenceTier.ORANGE
    if "incomplete_intake_low_confidence" in intake_result.flags or \
            weeks_consistent_checkins < 8 or missed_checkin_cycles == 1:
        return ConfidenceTier.YELLOW
    return ConfidenceTier.GREEN


# =======================================================================
# 11_...md Sec 3.1 -- estimate1RM
# =======================================================================
def estimate_1rm(reps: int, load: float, rep_quality: str = "clean") -> OneRMEstimate:
    """
    Source: 11_...md Sec 3.1 (Epley formula + confidence adjustment),
    ported exactly:
        base = load * (1 + reps/30)
        if rep_quality == "form_breakdown_near_failure": base *= 0.95
        if reps > 5: confidence = "low"; base *= 0.9
        else: confidence = "moderate_to_high"
    """
    base = load * (1 + reps / 30)
    if rep_quality == "form_breakdown_near_failure":
        base *= 0.95
    if reps > 5:
        confidence = "low"
        base *= 0.9
    else:
        confidence = "moderate_to_high"
    return OneRMEstimate(est_1rm=round(base), confidence=confidence)


# =======================================================================
# 11_...md Sec 4 -- mobility flag lookup
# =======================================================================
def lookup_mobility_response(observed_limitation_key: str) -> dict | None:
    """Returns the {flag, response} entry for an observed limitation key
    from T.MOBILITY_FLAG_TABLE, or None if unrecognized."""
    return T.MOBILITY_FLAG_TABLE.get(observed_limitation_key)


# =======================================================================
# 11_...md Sec 5 -- processCheckIn
# =======================================================================
def process_check_in(checkin: CheckIn, state: ClientState) -> CheckInResult:
    """Source: 11_...md Sec 5 (processCheckIn), ported 1:1."""
    flags = []
    triggers_injury_substitution = False
    triggers_pain_triage = False

    if checkin.new_pain_flags:
        triggers_injury_substitution = True
        triggers_pain_triage = True

    if checkin.sessions_planned > 0 and (
        checkin.sessions_completed / checkin.sessions_planned < 0.7
    ):
        flags.append("adherence_risk")

    if state.goal != "fat_loss":
        # "drops >1.5% week-over-week" requires a prior bodyweight to compare
        # against; state.rolling_history[-1] holds the previous check-in if
        # present (source doesn't specify the comparison mechanism beyond
        # "week-over-week", so the most recent prior entry is used).
        if state.rolling_history:
            prev = state.rolling_history[-1]
            prev_weight = getattr(prev, "bodyweight_kg", None)
            if prev_weight and prev_weight > 0:
                pct_change = (checkin.bodyweight_kg - prev_weight) / prev_weight
                if pct_change <= -0.015:
                    flags.append("unexpected_weight_loss_review")

    if checkin.motivation_rating <= 2:
        recent_low = [
            c for c in state.rolling_history[-1:]
            if getattr(c, "motivation_rating", 99) <= 2
        ]
        if recent_low:
            flags.append("disengagement_risk")

    state.rolling_history.append(checkin)

    return CheckInResult(
        flags=tuple(flags),
        triggers_injury_substitution=triggers_injury_substitution,
        triggers_pain_triage=triggers_pain_triage,
    )


# =======================================================================
# 11_...md Sec 7 -- adherenceRiskScore
# =======================================================================
def adherence_risk_score(state: ClientState) -> tuple[int, AdherenceRiskTier]:
    """
    Source: 11_...md Sec 7 (adherenceRiskScore), ported 1:1:
        score += 20 if trailing_4wk_completion_pct < 0.7
        score += 15 if checkin_submission_streak_broken >= 2
        score += 10 if motivation_rating_avg_trailing_2wk <= 4
        score += 10 if goal_target_date has passed without goal met
        score += 15 if life_event_disclosed in last 2 weeks
        >=40 -> high_risk, >=20 -> moderate_risk, else low_risk
    """
    score = 0
    if state.trailing_4wk_completion_pct < 0.7:
        score += 20
    if state.checkin_submission_streak_broken >= 2:
        score += 15
    if state.motivation_rating_avg_trailing_2wk <= 4:
        score += 10
    if state.goal_target_date_passed_unmet:
        score += 10
    if state.life_event_disclosed_last_2wk:
        score += 15

    if score >= 40:
        tier = AdherenceRiskTier.HIGH_RISK
    elif score >= 20:
        tier = AdherenceRiskTier.MODERATE_RISK
    else:
        tier = AdherenceRiskTier.LOW_RISK
    return score, tier


def adherence_response(tier: AdherenceRiskTier) -> str:
    """Source: 11_...md Sec 7.1 (Response Ladder by Risk Tier)."""
    return T.ADHERENCE_RESPONSE_LADDER[tier]
