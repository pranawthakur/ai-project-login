"""Deterministic logic ported from KB V7 file 10 (Recovery & Deload).
Governs 'does this client need to back off, and how'."""
from typing import Dict, Any, List
from .models import RecoveryInputs, FatigueIndicatorReport, DeloadDecision, ClientRecoveryState
from . import lookup_tables as T


# =====================================================================
# SECTION 1 -- SLEEP
# =====================================================================

def sleep_impact(hours: float, sudden_increase_from_baseline: bool = False) -> Dict[str, str]:
    if hours < 6:
        band = "under_6h"
    elif hours < 7:
        band = "6_to_7h"
    elif hours < 8:
        band = "7_to_8h"
    elif hours < 9:
        band = "8_to_9h"
    else:
        band = "9h_plus"
    entry = dict(T.SLEEP_IMPACT[band])
    if band == "9h_plus" and sudden_increase_from_baseline:
        entry["flag"] = "screen_for_overreaching_or_illness"
    return entry


# =====================================================================
# SECTION 2 -- NUTRITION FOR RECOVERY
# =====================================================================

def protein_target_g_per_kg(in_fat_loss_phase: bool = False) -> tuple:
    return T.NUTRITION_RECOVERY["protein_g_per_kg_fat_loss"] if in_fat_loss_phase else T.NUTRITION_RECOVERY["protein_g_per_kg"]


def hydration_target_ml(bodyweight_kg: float) -> tuple:
    lo, hi = T.NUTRITION_RECOVERY["hydration_ml_per_kg_per_day"]
    return (bodyweight_kg * lo, bodyweight_kg * hi)


# =====================================================================
# SECTION 3 -- DELOAD PROTOCOLS
# =====================================================================

def training_age_band(years: float) -> str:
    if years < 2:
        return "beginner"
    if years < 5:
        return "intermediate"
    return "advanced"


def scheduled_deload_due(training_age_years: float, weeks_since_last_deload: int) -> bool:
    band = training_age_band(training_age_years)
    lo, hi = T.SCHEDULED_DELOAD_FREQUENCY_WEEKS[band]
    return weeks_since_last_deload >= lo


def check_reactive_deload_triggers(active_signals: List[str]) -> List[Dict[str, str]]:
    return [{"trigger": k, "description": v} for k, v in T.REACTIVE_DELOAD_TRIGGERS.items() if k in active_signals]


def decide_deload(client_state: ClientRecoveryState, active_reactive_signals: List[str] = None,
                    illness_active: bool = False, severe_burnout: bool = False,
                    joint_or_cns_fatigue_primary: bool = False, mental_burnout: bool = False) -> DeloadDecision:
    """Combines scheduled + reactive triggers into a single deload decision
    and method recommendation. Illness/severe cases always win (fail toward
    more rest, never less)."""
    active_reactive_signals = active_reactive_signals or []

    if illness_active:
        return DeloadDecision(True, "illness_active_always_deload_or_rest",
                                method="complete_rest", duration_days=T.DELOAD_DURATION_DAYS)

    if severe_burnout:
        return DeloadDecision(True, "severe_burnout", method="complete_rest",
                                duration_days=T.DELOAD_DURATION_DAYS)

    reactive = check_reactive_deload_triggers(active_reactive_signals)
    if reactive:
        method = "active_recovery" if mental_burnout else (
            "intensity_deload" if joint_or_cns_fatigue_primary else "combined_deload")
        return DeloadDecision(True, "reactive_trigger", method=method,
                                duration_days=T.DELOAD_DURATION_DAYS,
                                data={"triggers": reactive})

    if scheduled_deload_due(client_state.training_age_years, client_state.weeks_since_last_deload):
        return DeloadDecision(True, "scheduled_deload_due", method="combined_deload",
                                duration_days=T.DELOAD_DURATION_DAYS)

    return DeloadDecision(False, "not_yet_due")


def deload_method_protocol(method: str) -> Dict[str, str]:
    entry = T.DELOAD_METHODS.get(method)
    if entry is None:
        raise ValueError(f"unknown deload method: {method!r}")
    return dict(entry)


def standard_deload_week(current_sets: int, current_load_kg: float) -> Dict[str, Any]:
    """Applies file 10's standard combined-method deload week template."""
    tpl = T.STANDARD_DELOAD_WEEK_TEMPLATE
    new_sets = round(current_sets * (1 - tpl["sets_reduction_pct"] / 100))
    lo_pct, hi_pct = tpl["load_reduction_pct"]
    new_load_range = (current_load_kg * (1 - hi_pct / 100), current_load_kg * (1 - lo_pct / 100))
    return {
        "sets": max(new_sets, 1),
        "load_range_kg": new_load_range,
        "rir_addition_alternative": tpl["rir_addition_alternative"],
        "intensity_techniques_permitted": tpl["intensity_techniques_permitted"],
    }


# =====================================================================
# SECTION 4 -- FATIGUE INDICATORS
# =====================================================================

def evaluate_fatigue_indicators(report: FatigueIndicatorReport) -> Dict[str, Any]:
    """Returns which specific indicators are in warning territory,
    following file 10 Section 4's normal-vs-warning table exactly."""
    warnings = []
    if report.session_rpe_higher_than_expected:
        warnings.append("session_rpe_vs_planned")
    if report.bar_speed_slower_than_expected:
        warnings.append("bar_speed")
    if report.resting_hr_elevated_bpm >= 5:
        warnings.append("resting_heart_rate")
    if report.sleep_restless_or_needing_more:
        warnings.append("sleep_quality")
    if report.motivation_persistent_dread:
        warnings.append("motivation")
    if report.soreness_days >= 4 or report.soreness_worsening_across_week:
        warnings.append("soreness_pattern")
    if report.joint_tendon_new_or_worsening_pain:
        warnings.append("joint_tendon_discomfort")
    if report.appetite_significant_change:
        warnings.append("appetite")

    return {
        "warning_indicators": warnings,
        "warning_count": len(warnings),
        "overall_status": "overreaching_signals_present" if len(warnings) >= 2 else
                            ("monitor" if len(warnings) == 1 else "normal"),
    }


# =====================================================================
# SECTION 5 -- RECOVERY QUALITY TIERS
# =====================================================================

def recovery_quality_tier(sleep_hours: float, stress_level: str, nutrition_consistent: bool) -> str:
    if sleep_hours < 7 or stress_level == "high" or not nutrition_consistent:
        return "poor"
    if sleep_hours >= 8 and stress_level == "low" and nutrition_consistent:
        return "excellent"
    return "average"


def recovery_quality_adjustment(tier: str) -> Dict[str, str]:
    entry = T.RECOVERY_QUALITY_TIERS.get(tier)
    if entry is None:
        raise ValueError(f"unknown recovery quality tier: {tier!r}")
    return dict(entry)


# =====================================================================
# SECTION 6 -- AGE-SPECIFIC RECOVERY
# =====================================================================

def age_recovery_note(age_group: str) -> str:
    note = T.AGE_RECOVERY_NOTES.get(age_group)
    if note is None:
        raise ValueError(f"unknown age_group: {age_group!r}")
    return note


# =====================================================================
# SECTION 7 -- STRESS MANAGEMENT
# =====================================================================

def stress_training_adjustment(level: str) -> Dict[str, str]:
    entry = T.STRESS_TRAINING_ADJUSTMENT.get(level)
    if entry is None:
        raise ValueError(f"unknown stress level: {level!r}")
    return dict(entry)


# =====================================================================
# SECTION 8 -- TROUBLESHOOTING HELPERS
# =====================================================================

def handle_missed_deload_overreach(weeks_overdue: int) -> Dict[str, Any]:
    """Overreaching after a missed deload: insert immediate deload/complete
    rest, then resume at MEV and ramp over 2-3 weeks."""
    if weeks_overdue > 0:
        return {"action": "immediate_deload_or_complete_rest_3_7_days",
                 "resume_at": "mev", "ramp_weeks": (2, 3)}
    return {"action": "none_needed"}


def deload_frequency_anxiety_check(weeks_since_last_deload_requests: int) -> Dict[str, str]:
    """Client deloading every 2-3 weeks out of anxiety: reframe, fix schedule."""
    if weeks_since_last_deload_requests <= 3:
        return {"flag": "deloading_too_frequently_out_of_anxiety",
                 "action": "set_deloads_on_fixed_schedule_eg_every_6wk_not_reactively"}
    return {"flag": "none"}
