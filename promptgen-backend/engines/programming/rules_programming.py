"""Deterministic logic ported from KB V7 file 2 (Programming Rules)."""
from typing import Optional, Dict, Any
from . import lookup_tables_programming_rules as P


def sets_reps_for_goal(goal: str) -> Dict[str, Any]:
    entry = P.SETS_REPS_BY_GOAL.get(goal)
    if entry is None:
        raise ValueError(f"unknown goal: {goal!r}")
    return dict(entry)


def rir_band_for_age(training_age_years: float) -> str:
    for lo, hi, band in P.RIR_AGE_BOUNDARIES:
        if training_age_years >= lo and (hi is None or training_age_years < hi):
            return band
    return "beginner"


def rir_guidelines(training_age_years: float) -> Dict[str, Any]:
    band = rir_band_for_age(training_age_years)
    return dict(P.RIR_BY_TRAINING_AGE[band])


def rpe_to_rir(rpe: float) -> float:
    if rpe in P.RPE_TO_RIR:
        return P.RPE_TO_RIR[rpe]
    if rpe <= 5:
        return 5.0  # "5+" warm-up territory
    # interpolate for values not in the table (e.g. 8.5)
    keys = sorted(P.RPE_TO_RIR.keys())
    for i in range(len(keys) - 1):
        lo, hi = keys[i], keys[i + 1]
        if lo <= rpe <= hi:
            lo_rir, hi_rir = P.RPE_TO_RIR[lo], P.RPE_TO_RIR[hi]
            frac = (rpe - lo) / (hi - lo)
            return round(hi_rir + frac * (lo_rir - hi_rir), 2)
    return 0.0


def true_failure_allowed(exercise_context: str, has_spotter_or_safety: bool = False) -> bool:
    """Never program true concentric failure (RPE 10) on an unspotted
    free-weight compound (squat, deadlift, unspotted bench)."""
    if exercise_context == "unspotted_free_weight_compound":
        return False
    if exercise_context == "spotted_free_weight_compound":
        return has_spotter_or_safety
    return True  # machines, isolation, spotted lifts


def tempo_for_goal(goal: str) -> str:
    tempo = P.TEMPO_BY_GOAL.get(goal)
    if tempo is None:
        raise ValueError(f"unknown tempo goal: {goal!r}")
    return tempo


def rest_for_exercise_type(exercise_type: str) -> tuple:
    entry = P.REST_BY_EXERCISE_TYPE.get(exercise_type)
    if entry is None:
        raise ValueError(f"unknown exercise_type: {exercise_type!r}")
    return entry


def progression_model_for(training_age_years: float, plateaued_on_current_model: bool = False,
                            variety_needed: bool = False) -> str:
    if training_age_years < 0.5:
        return "linear"
    if training_age_years < 5 and not (plateaued_on_current_model or variety_needed):
        return "double_progression"
    if plateaued_on_current_model or variety_needed:
        return "undulating_dup"
    return "double_progression"


def linear_progression_end_condition(consecutive_failed_attempts: int) -> Optional[str]:
    if consecutive_failed_attempts >= 2:
        return "move_to_double_progression"
    return None


def failure_policy(training_age_years: float, exercise_category: str, fatigue_or_illness_or_poor_sleep: bool = False) -> str:
    """exercise_category: 'compound' | 'isolation' | 'any'"""
    if fatigue_or_illness_or_poor_sleep:
        return P.FAILURE_OVERRIDE_FATIGUE_PRESENT
    band = rir_band_for_age(training_age_years)
    coarse_band = "beginner" if band == "beginner" else ("advanced" if band == "advanced" else "intermediate")
    key = (coarse_band, exercise_category)
    if key in P.FAILURE_POLICY:
        return P.FAILURE_POLICY[key]
    fallback_key = ("beginner", "any")
    return P.FAILURE_POLICY.get(fallback_key, "avoid_failure_default_conservative")


# =====================================================================
# SECTION 7 -- PLATEAU DECISION TREE
# =====================================================================

def plateau_decision_tree(
    weeks_stalled: int,
    adherence_ok: bool,
    sleep_hours: float,
    stress_high: bool,
    weeks_since_last_deload: int,
    in_aggressive_deficit_while_seeking_gains: bool,
    current_volume_status: str,        # "below_mev" | "above_mrv" | "within_range"
    same_exercise_scheme_weeks: int,
) -> Dict[str, str]:
    """Ports Section 7 exactly, in order, terminating at the first
    matching branch -- never falls through to 'no action' by omission."""
    if weeks_stalled < 2:
        return {"result": "not_yet_a_plateau", "action": "continue_current_program"}

    if not adherence_ok:
        return {"result": "adherence_issue", "action": "fix_adherence_before_touching_programming"}

    if sleep_hours < 7 or stress_high or weeks_since_last_deload > 8:
        return {"result": "recovery_issue", "action": "address_recovery_or_insert_deload_before_program_change"}

    if in_aggressive_deficit_while_seeking_gains:
        return {"result": "nutrition_mismatch", "action": "adjust_calories_or_expectations_not_a_programming_failure"}

    if current_volume_status == "below_mev":
        return {"result": "volume_too_low", "action": "increase_volume"}
    if current_volume_status == "above_mrv":
        return {"result": "volume_too_high", "action": "reduce_volume"}

    if same_exercise_scheme_weeks > 8:
        return {"result": "staleness", "action": "rotate_exercise_variation_or_switch_periodization_model"}

    return {"result": "genuine_plateau", "action": "implement_planned_deload_then_new_mesocycle_adjusted_variables"}


# =====================================================================
# SECTION 8-9 -- RECOVERY / SLEEP / STRESS / AGE ADJUSTMENTS
# =====================================================================

def recovery_quality_adjustment(quality: str) -> Dict[str, Any]:
    entry = P.RECOVERY_QUALITY_ADJUSTMENTS.get(quality)
    if entry is None:
        raise ValueError(f"unknown recovery quality: {quality!r}")
    return dict(entry)


def sleep_adjustment(hours: float) -> Dict[str, Any]:
    if hours < 6:
        return dict(P.SLEEP_ADJUSTMENTS["under_6h"])
    if hours < 7:
        return dict(P.SLEEP_ADJUSTMENTS["6_to_7h"])
    if hours < 8:
        return dict(P.SLEEP_ADJUSTMENTS["7_to_8h"])
    return dict(P.SLEEP_ADJUSTMENTS["8_to_9h_plus"])


def stress_adjustment(level: str) -> Dict[str, Any]:
    entry = P.STRESS_ADJUSTMENTS.get(level)
    if entry is None:
        raise ValueError(f"unknown stress level: {level!r}")
    return dict(entry)


def age_programming_note(age_group: str) -> str:
    note = P.AGE_PROGRAMMING_NOTES.get(age_group)
    if note is None:
        raise ValueError(f"unknown age_group: {age_group!r}")
    return note
