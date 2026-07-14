"""Deterministic logic ported from KB V7 file 17 (Periodization & AI
Decision Engine)."""
from typing import Optional, List, Dict, Any
from .models import ClientState, SplitRecommendation, ConfidenceFactors
from . import lookup_tables as T


# =====================================================================
# SECTION 1 -- SPLIT SELECTION DECISION ENGINE
# =====================================================================

def _candidate_splits(days: int, goal: str, recovery: str, tier: str) -> List[str]:
    candidates = []
    if days == 1:
        candidates.append("full_body_minimal")
    if days == 2:
        candidates.append("full_body_x2")
    if days == 3:
        candidates.append("full_body_x3")
        if goal in ("hypertrophy", "aesthetics"):
            candidates.append("push_pull_legs_partial")
    if days == 4:
        candidates.append("upper_lower_x2")
        if recovery == "good":
            candidates.append("upper_lower_ppl_hybrid")
    if days == 5:
        candidates.append("upper_lower_plus_specialization")
        if recovery == "good" and tier == "green":
            candidates.append("ppl_plus_upper")
    if days >= 6:
        if recovery == "good" and tier == "green":
            candidates.append("ppl_x2")
        else:
            candidates.append("upper_lower_x3")
    return candidates


def _match_split_to_goal(candidate: str, goal: str) -> float:
    """Maps a session-plan candidate to the nearest Section 1.2 fit-matrix
    row. Unmapped candidates (e.g. full_body_minimal) default to the
    full_body_x2_3 row as the closest analog."""
    alias = {
        "full_body_minimal": "full_body_x2_3", "full_body_x2": "full_body_x2_3", "full_body_x3": "full_body_x2_3",
        "push_pull_legs_partial": "ppl_x3_per_week",
        "upper_lower_x2": "upper_lower_x4", "upper_lower_ppl_hybrid": "upper_lower_x4",
        "upper_lower_plus_specialization": "upper_lower_x4", "ppl_plus_upper": "ppl_x3_per_week",
        "ppl_x2": "ppl_x2_6days", "upper_lower_x3": "upper_lower_x4",
    }
    row_key = alias.get(candidate, "full_body_x2_3")
    row = T.SPLIT_GOAL_FIT[row_key]
    return row.get(goal, 0.5)


def _match_recovery_to_frequency(candidate: str, recovery: str) -> float:
    """Higher-frequency/higher-fatigue splits fit poorly with poor
    recovery; simpler splits fit poorly-recovered clients better.
    Includes PPL-partial per the source's own worked example (Section
    1.1): a 3-day PPL split still concentrates high per-session fatigue
    even though it isn't high-frequency, so it's penalized under poor
    recovery same as the true high-frequency splits."""
    concentrates_fatigue = {"ppl_x2", "upper_lower_ppl_hybrid", "ppl_plus_upper", "upper_lower_x3",
                             "push_pull_legs_partial"}
    if recovery == "poor":
        return 0.4 if candidate in concentrates_fatigue else 0.9
    if recovery == "moderate":
        return 0.7 if candidate in concentrates_fatigue else 0.85
    return 0.9 if candidate in concentrates_fatigue else 0.8  # good recovery favors higher-frequency options


def _match_complexity_to_history(candidate: str, tolerance: str) -> float:
    complex_splits = {"ppl_x2", "upper_lower_ppl_hybrid", "ppl_plus_upper", "upper_lower_plus_specialization"}
    if tolerance == "low":
        return 0.5 if candidate in complex_splits else 0.9
    if tolerance == "moderate":
        return 0.75 if candidate in complex_splits else 0.85
    return 0.9  # high tolerance handles anything well


def select_split(client_state: ClientState) -> SplitRecommendation:
    if client_state.confidence_tier == "orange":
        return SplitRecommendation(split="DEFAULT_SAFE_TEMPLATE_full_body", confidence=99,
                                    reason="orange_tier_always_routes_to_safe_template")

    candidates = _candidate_splits(client_state.days_available, client_state.goal,
                                     client_state.recovery_score, client_state.confidence_tier)
    if not candidates:
        return SplitRecommendation(split="full_body_x2", confidence=50, reason="no_candidates_matched_fallback")

    scored = []
    for c in candidates:
        fatigue_fit = _match_recovery_to_frequency(c, client_state.recovery_score)
        goal_fit = _match_split_to_goal(c, client_state.goal)
        adherence_fit = _match_complexity_to_history(c, client_state.training_history_complexity_tolerance)
        total = 0.4 * fatigue_fit + 0.4 * goal_fit + 0.2 * adherence_fit
        scored.append((c, total))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Section 6 edge case: tie-break using adherence_fit, favoring lower complexity
    top_score = scored[0][1]
    tied = [c for c, s in scored if abs(s - top_score) < 1e-9]
    if len(tied) > 1:
        tied_scored = [(c, _match_complexity_to_history(c, client_state.training_history_complexity_tolerance)) for c in tied]
        tied_scored.sort(key=lambda x: x[1], reverse=True)
        best = tied_scored[0][0]
        best_total = top_score
    else:
        best, best_total = scored[0]

    alt = None
    alt_conf = None
    remaining = [(c, s) for c, s in scored if c != best]
    if remaining:
        alt, alt_score = remaining[0]
        alt_conf = round(alt_score * 100)

    return SplitRecommendation(split=best, confidence=round(best_total * 100), alternative=alt,
                                 alternative_confidence=alt_conf)


def smoothed_recovery_score(trailing_scores: List[str]) -> str:
    """Section 7 troubleshooting fix: use trailing 2-week average recovery
    score for split selection, not a single volatile data point."""
    if not trailing_scores:
        return "moderate"
    weight = {"poor": 0, "moderate": 1, "good": 2}
    avg = sum(weight.get(s, 1) for s in trailing_scores) / len(trailing_scores)
    if avg < 0.67:
        return "poor"
    if avg < 1.34:
        return "moderate"
    return "good"


def resolve_split_preference_conflict(scored_split: str, stated_preference: Optional[str],
                                        safety_flag_conflict: bool = False) -> Dict[str, Any]:
    """Section 6 edge case: client's stated preference vs. scored
    recommendation. Preference wins if no safety conflict."""
    if stated_preference is None or stated_preference == scored_split:
        return {"final_split": scored_split, "source": "system_recommendation"}
    if safety_flag_conflict:
        return {"final_split": scored_split, "source": "system_recommendation",
                 "note": "preference_overridden_due_to_safety_flag_conflict"}
    return {"final_split": stated_preference, "source": "client_initiated_override",
             "note": "logged_as_client_choice_not_system_error"}


# =====================================================================
# SECTION 2 -- PERIODIZATION MODEL SELECTION
# =====================================================================

def recommend_periodization_model(training_age_months: int, confidence_tier: str,
                                    frequency_per_pattern: int = 1, goal: str = "hypertrophy",
                                    target_date_set: bool = False,
                                    reported_staleness: bool = False) -> Dict[str, Any]:
    if training_age_months < 12:
        return {"model": "linear", "reason": "training_age_lt_12mo_simpler_autoregulation_burden"}

    if goal in ("powerlifting", "olympic_lifting") and target_date_set and training_age_months >= 24:
        return {"model": "block", "reason": "competitive_lifter_with_peaking_date"}

    if (confidence_tier == "green" and training_age_months >= 12 and frequency_per_pattern >= 2):
        return {"model": "undulating", "reason": "green_tier_ge_12mo_freq_ge_2_prefers_daily_undulating"}

    if training_age_months >= 36 and goal == "powerlifting" and reported_staleness:
        return {"model": "conjugate_adjacent", "reason": "staleness_on_main_lift_offer_variant_rotation_only"}

    return {"model": "linear", "reason": "default_fallback_no_specific_gate_met"}


def vbt_eligible(equipment_available: List[str], training_age_months: int) -> bool:
    return "velocity_tracker" in equipment_available and training_age_months >= 24


def velocity_loss_cutoff(goal_bias: str) -> tuple:
    if goal_bias == "hypertrophy":
        return T.PERIODIZATION_MODELS["vbt"]["velocity_loss_cutoff_hypertrophy_pct"]
    return T.PERIODIZATION_MODELS["vbt"]["velocity_loss_cutoff_strength_power_pct"]


def contrast_method_eligible(method: str, goal: str, training_age_months: int, confidence_tier: str,
                               unresolved_lower_limb_injury_flag: bool = False) -> bool:
    """Section 2.6: none of these are ever offered to yellow/orange tier
    or anyone with an unresolved lower-limb injury/pain flag."""
    if confidence_tier != "green":
        return False
    if unresolved_lower_limb_injury_flag:
        return False
    if goal != "athletic_performance":
        return False
    if method == "triphasic":
        return training_age_months >= 36
    return training_age_months >= 24


# =====================================================================
# SECTION 3 -- ADVANCED SET-STRUCTURE GATING
# =====================================================================

def set_structure_allowed(technique: str, confidence_tier: str, training_age_months: int,
                            solo_no_spotter: bool = False, vascular_clotting_flag: bool = False,
                            medical_clearance_resolved: bool = True) -> Dict[str, Any]:
    entry = T.SET_STRUCTURE_GATES.get(technique)
    if entry is None:
        return {"allowed": False, "reason": "unknown_technique_default_no"}

    if T.TIER_ORDER.get(confidence_tier, -1) < T.TIER_ORDER.get(entry["min_tier"], 99):
        return {"allowed": False, "reason": f"requires_min_tier_{entry['min_tier']}"}

    if training_age_months < entry["min_training_age_months"]:
        return {"allowed": False, "reason": f"requires_min_training_age_months_{entry['min_training_age_months']}"}

    if entry.get("requires_supervision") and solo_no_spotter:
        return {"allowed": False, "reason": "flag_unsupervised_max_effort_risk", "flag": "unsupervised_max_effort_risk"}

    if entry.get("requires_clearance_if_vascular_flag") and vascular_clotting_flag and not medical_clearance_resolved:
        return {"allowed": False, "reason": "medical_clearance_required_vascular_flag"}

    return {"allowed": True, "fatigue_cost": entry["fatigue_cost"]}


def advanced_technique_request_from_yellow_tier(technique: str, confidence_tier: str,
                                                   training_age_months: int) -> Dict[str, str]:
    """Section 6 edge case: yellow-tier client explicitly requests a
    gated technique by name."""
    result = set_structure_allowed(technique, confidence_tier, training_age_months)
    if result["allowed"]:
        return {"action": "grant", "technique": technique}
    return {"action": "explain_gate_and_offer_alternative",
            "alternative": "standard_straight_sets_with_slightly_higher_rep_target"}


# =====================================================================
# SECTION 4 -- MEV/MAV/MRV INTEGRATION
# =====================================================================

def adjust_volume_within_landmarks(current_volume: float, mev: float, mav: float, mrv: float,
                                     recovery_score: str, weeks_since_deload: int) -> Dict[str, Any]:
    if recovery_score == "poor":
        return {"new_volume": max(mev, current_volume * 0.8), "action": "reduce_toward_mev"}
    if weeks_since_deload >= 4 and recovery_score == "moderate":
        return {"new_volume": min(mrv, current_volume), "action": "hold_do_not_push_without_good_recovery"}
    if recovery_score == "good" and current_volume < mav:
        return {"new_volume": current_volume + 1, "action": "increase_1_set_per_week_per_muscle"}
    if current_volume >= mrv:
        return {"new_volume": current_volume, "action": "trigger_deload_flag"}
    return {"new_volume": current_volume, "action": "hold"}


# =====================================================================
# SECTION 5 -- CONFIDENCE SCORING (system-wide standard)
# =====================================================================

def compute_recommendation_confidence(factors: ConfidenceFactors) -> int:
    base = T.CONFIDENCE_BASE
    base += T.CONFIDENCE_EVIDENCE_BONUS.get(factors.evidence_strength, 0)

    if factors.client_data_completeness_pct >= 90:
        base += T.CONFIDENCE_COMPLETENESS_BONUS
    elif factors.client_data_completeness_pct < 60:
        base += T.CONFIDENCE_COMPLETENESS_PENALTY

    if not factors.conflicting_flags_present:
        base += T.CONFIDENCE_NO_CONFLICT_BONUS

    if factors.unresolved_safety_flag_overlap:
        base += T.CONFIDENCE_SAFETY_OVERLAP_PENALTY

    base += T.CONFIDENCE_TIER_PENALTY.get(factors.confidence_tier, 0)

    return max(T.CONFIDENCE_FLOOR, min(T.CONFIDENCE_CAP, base))


# =====================================================================
# SECTION 6 -- remaining edge cases
# =====================================================================

def effective_training_age(self_reported_months: Optional[int], movement_screen_derived_months: Optional[int]) -> int:
    """If self-report and movement-screen-derived training age disagree
    (file 11 Section 8), the movement-screen-derived value wins."""
    if movement_screen_derived_months is not None:
        return movement_screen_derived_months
    return self_reported_months or 0
