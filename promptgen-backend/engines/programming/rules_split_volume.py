"""Deterministic logic ported from KB V7 files 1, 6, 7, 8."""
from typing import Optional, List, Dict, Any
from . import lookup_tables_split_volume as V


# =====================================================================
# FILE 1 -- SPLIT SELECTION DECISION TREE
# =====================================================================

def select_split(days_available: int, training_age_years: float, goal: str = "muscle_gain",
                  wants_specialization: bool = False, meeting_mav_elsewhere: bool = False) -> Dict[str, Any]:
    """Ports Section 2's decision tree exactly, including the hardwired
    'never assign bro split under 2yrs training age' and '7-day = 6-day PPL
    + 1 recovery day, never 7 hard days' rules."""
    if days_available <= 2:
        return {"split": "minimalist_2day", "reason": "days_available_eq_2_always_no_exceptions"}

    if days_available == 3:
        if training_age_years < 1:
            return {"split": "full_body_abc", "reason": "training_age_lt_1yr"}
        if goal in ("strength", "powerlifting"):
            return {"split": "full_body_abc", "reason": "strength_focused_3day"}
        return {"split": "ppl_3day", "reason": "training_age_ge_1yr"}

    if days_available == 4:
        if goal in ("strength", "powerlifting"):
            return {"split": "powerlifting_sbd", "reason": "goal_strength_powerlifting",
                     "alternative": "upper_lower"}
        if goal in ("hypertrophy", "bodybuilding") and training_age_years < 2:
            return {"split": "upper_lower", "reason": "hypertrophy_training_age_lt_2yr"}
        if goal in ("hypertrophy", "bodybuilding") and training_age_years >= 2:
            return {"split": "upper_lower", "reason": "hypertrophy_training_age_ge_2yr_higher_volume",
                     "alternative": "full_body_specialization"}
        return {"split": "upper_lower", "reason": "default_4day"}

    if days_available == 5:
        if training_age_years < 2:
            return {"split": "upper_lower", "reason": "training_age_lt_2yr_plus_1_full_body",
                     "alternative": "ppl_ul_hybrid"}
        if training_age_years >= 2 and goal == "hypertrophy":
            return {"split": "ppl_ul_hybrid", "reason": "training_age_ge_2yr_hypertrophy"}
        if training_age_years >= 5 and wants_specialization:
            if meeting_mav_elsewhere:
                return {"split": "bro_split", "reason": "advanced_specialization_mav_already_met"}
            return {"split": "ppl_ul_hybrid", "reason": "advanced_but_mav_not_met_elsewhere_stay_hybrid"}
        return {"split": "ppl_ul_hybrid", "reason": "default_5day"}

    if days_available == 6:
        return {"split": "ppl_6day", "reason": "standard_intermediate_advanced_bodybuilder"}

    if days_available >= 7:
        return {"split": "ppl_6day", "reason": "6day_ppl_plus_1_active_recovery_day",
                 "note": "never_program_7_hard_days_hardwired_rule",
                 "extra_day": "active_recovery_mobility"}

    return {"split": "full_body_abc", "reason": "fallback_default"}


def block_bro_split_if_undertrained(training_age_years: float) -> Optional[Dict[str, str]]:
    """Hard rule (Coach Note, Section 2): never assign bro split under 2yrs
    training age regardless of what select_split returns elsewhere."""
    if training_age_years < 2:
        return {"blocked": "bro_split", "reason": "training_age_lt_2yr_insufficient_volume_tolerance"}
    return None


def session_duration_modifier(minutes: int) -> Dict[str, Any]:
    """Returns the modifier for the nearest defined duration bucket at or
    below `minutes` (never rounds up to a longer session than available)."""
    buckets = sorted(V.SESSION_DURATION_MODIFIERS.keys())
    chosen = buckets[0]
    for b in buckets:
        if minutes >= b:
            chosen = b
    return {"bucket_minutes": chosen, **V.SESSION_DURATION_MODIFIERS[chosen]}


def check_split_switch_triggers(active_triggers: List[str]) -> List[Dict[str, str]]:
    return [row for row in V.SPLIT_SWITCH_TRIGGERS if row["trigger"] in active_triggers]


# =====================================================================
# FILE 6 -- INTENSITY TECHNIQUES
# =====================================================================

def intensity_technique_permission(technique: str, training_age_years: float) -> str:
    band = V.training_age_band(training_age_years)
    matrix = V.INTENSITY_TECHNIQUE_MATRIX.get(technique)
    if matrix is None:
        return "unknown_technique_default_no"
    return matrix[band]


def max_intensity_instances_per_week(training_age_years: float) -> tuple:
    band = V.training_age_band(training_age_years)
    return V.INTENSITY_FATIGUE_BUDGET_PER_WEEK[band]


def can_prescribe_intensity_technique(technique: str, training_age_years: float,
                                       instances_already_used_this_week: int = 0) -> bool:
    permission = intensity_technique_permission(technique, training_age_years)
    if permission == "no":
        return False
    lo, hi = max_intensity_instances_per_week(training_age_years)
    return instances_already_used_this_week < hi


# =====================================================================
# FILE 7 -- GOAL-BASED MODIFICATIONS
# =====================================================================

def goal_modifiers(goal: str) -> Dict[str, Any]:
    entry = V.GOAL_TABLE.get(goal)
    if entry is None:
        raise ValueError(f"unknown goal: {goal!r}")
    return dict(entry)


def rate_of_gain_check(weekly_bodyweight_change_pct: float) -> Dict[str, Any]:
    """File 7 Section 2: >0.5-1%/week bodyweight gain signals excess fat
    gain relative to muscle in a natural lifter."""
    if weekly_bodyweight_change_pct > 1.0:
        return {"flag": "excess_fat_gain_likely", "action": "reduce_surplus"}
    if weekly_bodyweight_change_pct > 0.5:
        return {"flag": "monitor_closely", "action": "consider_reducing_surplus_if_trend_continues"}
    return {"flag": "within_expected_range", "action": "none"}


def fat_loss_deficit_size(body_fat_level: str) -> Dict[str, Any]:
    """File 7 Section 6: deficit sizing by starting body-fat level."""
    table = {
        "higher_body_fat": {"deficit_kcal": (500, 750)},
        "moderate_body_fat": {"deficit_kcal": (300, 500)},
        "lean_approaching_goal": {"deficit_kcal": (150, 300), "note": "smaller_10_15pct_deficit_to_protect_muscle"},
    }
    return table.get(body_fat_level, {"deficit_kcal": (300, 500), "note": "default_conservative"})


# =====================================================================
# FILE 8 -- WEEKLY MUSCLE VOLUME
# =====================================================================

def volume_target(muscle: str, training_age_years: float) -> Dict[str, Any]:
    entry = V.VOLUME_TABLE.get(muscle)
    if entry is None:
        raise ValueError(f"unknown muscle: {muscle!r}")
    beginner, intermediate, advanced, mrv = entry
    band = V.training_age_band(training_age_years)
    if band in ("beginner", "novice"):
        mev_mav = beginner
    elif band == "intermediate":
        mev_mav = intermediate
    else:
        mev_mav = advanced
    return {"mev": mev_mav[0], "mav": mev_mav[1], "mrv_ceiling": mrv}


def apply_volume_goal_modifier(base_range: Dict[str, Any], goal: str) -> Dict[str, Any]:
    modifier = V.VOLUME_GOAL_MODIFIERS.get(goal, "standard_aim_mav")
    result = dict(base_range)
    if "reduce_accessory" in modifier:
        result["accessory_isolation_adjustment_pct"] = -0.35  # midpoint of 30-40%
    result["modifier_rule"] = modifier
    return result


def apply_recovery_adjustment(base_sets: int, factor: str) -> int:
    adj = V.RECOVERY_VOLUME_ADJUSTMENTS.get(factor)
    if isinstance(adj, float):
        return round(base_sets * (1 + adj))
    return base_sets  # non-numeric factors (e.g. "returning_from_layoff") handled by caller as a phase, not a multiplier


def count_indirect_volume(direct_sets: int) -> tuple:
    lo, hi = V.INDIRECT_VOLUME_MULTIPLIER
    return (round(direct_sets * lo, 2), round(direct_sets * hi, 2))


def check_volume_status(muscle: str, training_age_years: float, current_weekly_sets: float) -> Dict[str, str]:
    target = volume_target(muscle, training_age_years)
    if current_weekly_sets > target["mrv_ceiling"]:
        return {"status": "above_mrv", "action": "cut_volume_30_40pct_for_1_2_weeks"}
    if current_weekly_sets < target["mev"]:
        return {"status": "below_mev", "action": "increase_volume_20_30pct_reassess_2_3_weeks"}
    return {"status": "within_mev_mav_range", "action": "none"}
