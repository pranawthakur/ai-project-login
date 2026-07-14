"""Deterministic logic ported from KB V7 files 3, 4, 5 (level classification
and beginner specifics) and 13 (cardio & conditioning)."""
from typing import Dict, Any, Optional
from . import lookup_tables_levels_cardio as L


# =====================================================================
# FILES 3/4/5 -- TRAINING LEVEL CLASSIFICATION
# =====================================================================

def classify_training_level(linear_progression_stalled_most_lifts: bool,
                             rir_estimation_accuracy: str = "poor",
                             progress_timescale: str = "weeks") -> str:
    """progress_timescale: 'weeks' | 'months_years'"""
    if progress_timescale == "months_years":
        return "advanced"
    if linear_progression_stalled_most_lifts and rir_estimation_accuracy in ("reasonable", "good"):
        return "intermediate"
    return "beginner"


def beginner_split_for_days(days_available: int) -> Dict[str, str]:
    if days_available in L.BEGINNER_SPLIT_BY_DAYS:
        return dict(L.BEGINNER_SPLIT_BY_DAYS[days_available])
    if days_available >= 5:
        return dict(L.BEGINNER_SPLIT_BY_DAYS[5])
    # fallback for 1 or negative -- treat conservatively as the 2-day floor
    return dict(L.BEGINNER_SPLIT_BY_DAYS[2])


def beginner_volume_for(muscle: str) -> tuple:
    entry = L.BEGINNER_VOLUME.get(muscle)
    if entry is None:
        raise ValueError(f"unknown muscle: {muscle!r}")
    return entry


def beginner_load_increment(lift_category: str) -> float:
    """lift_category: 'upper_body' | 'lower_body'"""
    val = L.BEGINNER_LOAD_INCREMENT_KG.get(lift_category)
    if val is None:
        raise ValueError(f"unknown lift_category: {lift_category!r}")
    return val


def beginner_progression_check(consecutive_sessions_no_progress: int) -> str:
    if consecutive_sessions_no_progress >= L.BEGINNER_FAILURE_TO_PROGRESS_SESSIONS:
        return "switch_to_double_progression"
    return "continue_linear_progression"


def beginner_deload_due(weeks_since_last_deload: int, lifts_stalled_simultaneously: int = 0,
                          fatigue_signs_present: bool = False) -> bool:
    lo, hi = L.BEGINNER_DELOAD_FREQUENCY_WEEKS
    if weeks_since_last_deload >= lo:
        return True
    if lifts_stalled_simultaneously >= 3 and fatigue_signs_present:
        return True
    return False


# =====================================================================
# FILE 13 -- CARDIO & CONDITIONING
# =====================================================================

def cardio_zone_for_hr_pct(hr_pct: float) -> int:
    for zone, entry in L.CARDIO_ZONES.items():
        lo, hi = entry["hr_pct"]
        if lo <= hr_pct <= hi:
            return zone
    if hr_pct < 50:
        return 1
    return 5


def cardio_zone_info(zone: int) -> Dict[str, Any]:
    entry = L.CARDIO_ZONES.get(zone)
    if entry is None:
        raise ValueError(f"unknown zone: {zone!r}")
    return dict(entry)


def prescribe_cardio(goal: str, recovery_score: str = "normal", on_beta_blockers: bool = False) -> Dict[str, Any]:
    """Ports file 13 Section 3's prescribeCardio() function."""
    base = L.CARDIO_PRESCRIPTION_BASE.get(goal)
    if base is None:
        raise ValueError(f"unknown cardio goal: {goal!r}")
    result = dict(base)

    if recovery_score == "low":
        result["interval_hiit_volume_reduction_pct"] = 50
        result["zone_cap"] = "zone2"

    if on_beta_blockers:
        result["hr_zone_reliable"] = False
        result["use_instead"] = "rpe_and_talk_test_exclusively"

    return result


def hiit_protocol(name: str) -> Dict[str, Any]:
    entry = L.HIIT_PROTOCOLS.get(name)
    if entry is None:
        raise ValueError(f"unknown HIIT protocol: {name!r}")
    return dict(entry)


def hiit_eligibility(confidence_tier: str, unresolved_cardiovascular_flags: bool) -> Dict[str, Any]:
    """Rule: HIIT requires confidence_tier == 'green' and no unresolved
    cardiovascular flags. Yellow/orange default to Zone 2 only."""
    if confidence_tier == "green" and not unresolved_cardiovascular_flags:
        return {"hiit_allowed": True}
    return {"hiit_allowed": False, "default": "zone2_only"}


def interference_check(primary_goal: str, cardio_session_is_first: bool = False,
                        cardio_duration_is_warmup_le_10min: bool = False) -> Dict[str, Any]:
    """file 13 Section 4: resistance-before-cardio sequencing rule."""
    if cardio_session_is_first and primary_goal not in ("endurance_performance", "general_health") \
            and not cardio_duration_is_warmup_le_10min:
        return {"violation": "cardio_first_only_valid_if_primary_goal_or_le_10min_zone1_warmup",
                 "recommendation": "resequence_resistance_training_before_cardio"}
    return {"violation": None}


def cardio_volume_ceiling(resistance_training_weekly_minutes: float) -> tuple:
    lo_pct, hi_pct = L.INTERFERENCE_RULES["volume_ceiling_pct_of_resistance_duration"]
    return (resistance_training_weekly_minutes * lo_pct / 100, resistance_training_weekly_minutes * hi_pct / 100)
