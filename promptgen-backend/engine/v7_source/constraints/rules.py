"""Deterministic safety/constraint logic. Ports files 12, 18, 19, 20 of
KnowledgeBase V7 from pseudocode into real Python. Every branch terminates
in an explicit Decision -- no implicit fall-through to normal programming.
"""
from typing import List, Optional
from .models import Decision, GateResult, ClientState, SessionInput, HealthReport, ConfidenceTier
from . import lookup_tables as T
from engines.programming import build_default_safe_template


# =====================================================================
# FILE 12 SECTION 1 -- GLOBAL SAFETY GATE
# =====================================================================

def safety_gate(client_state: ClientState, session_input: SessionInput) -> Decision:
    if client_state.confidence_tier == ConfidenceTier.RED:
        return Decision(GateResult.BLOCK, "professional_referral_only")
    if session_input.reported_pain_scale >= 7:
        return Decision(GateResult.BLOCK, "acute_pain_stop_session")
    if session_input.contains_emergency_symptom:
        return Decision(GateResult.BLOCK, "emergency_escalation", message=EMERGENCY_MESSAGE)
    if "medical_clearance_required" in client_state.flags and not client_state.medical_clearance_resolved:
        template = build_default_safe_template(
            pain_provoking_movements=[f for f in client_state.flags if f.startswith("pain_provoking:")],
        )
        return Decision(GateResult.RESTRICT, "default_safe_template", data={"template": template})
    return Decision(GateResult.PROCEED, "proceed")


EMERGENCY_MESSAGE = (
    "This pattern is worth immediate emergency medical attention. "
    "Stop activity now and seek emergency care."
)


# =====================================================================
# FILE 12 SECTION 3 -- PAIN TRIAGE (non-emergency)
# =====================================================================

def pain_triage(session_input: SessionInput) -> Decision:
    if session_input.reported_pain_scale >= 7:
        return safety_gate(ClientState(), session_input)  # routes through emergency gate
    if session_input.pain_type == "sharp_localized_joint" and session_input.pain_onset == "sudden":
        entry = T.PAIN_TRIAGE_TABLE["sharp_localized_joint_sudden"]
        return Decision(GateResult.BLOCK, "stop_pattern_refer_to_professional", data=entry)
    if (session_input.pain_type == "dull_muscular" and session_input.reported_pain_scale <= 3
            and session_input.pain_improves_with_warmup):
        entry = T.PAIN_TRIAGE_TABLE["dull_diffuse_muscular_resolves_24_72h"]
        return Decision(GateResult.PROCEED, "likely_doms_continue_with_monitoring", data=entry)
    if session_input.pain_persists_beyond_72h or session_input.pain_worsens_with_repeated_exposure:
        entry = T.PAIN_TRIAGE_TABLE["increases_session_over_session_despite_substitution"]
        return Decision(GateResult.BLOCK, "escalate_reduce_load_recommend_professional_eval", data=entry)
    if session_input.pain_at_end_range_only:
        entry = T.PAIN_TRIAGE_TABLE["pain_only_end_range"]
        return Decision(GateResult.RESTRICT, "cap_rom_add_mobility", data=entry)
    return Decision(GateResult.PROCEED, "monitor_next_session")


# =====================================================================
# FILE 12 SECTION 4 -- CONDITION-SPECIFIC CONSTRAINTS
# =====================================================================

def condition_constraints(condition: str) -> Decision:
    entry = T.CONDITION_CONSTRAINTS.get(condition)
    if entry is None:
        return Decision(GateResult.RESTRICT, "unknown_condition_default_conservative")
    if entry.get("block"):
        return Decision(GateResult.BLOCK, entry["block"], data=entry)
    return Decision(GateResult.RESTRICT, "apply_condition_constraints", data=entry)


# =====================================================================
# FILE 12 SECTION 5 -- MEDICATION-INTERACTION FLAGS (informational only)
# =====================================================================

def medication_flags(medications: List[str]) -> List[dict]:
    out = []
    for m in medications:
        entry = T.MEDICATION_FLAGS.get(m)
        if entry:
            out.append({"medication": m, **entry})
    return out


# =====================================================================
# FILE 12 SECTION 6 -- EATING DISORDER / DISORDERED EATING ROUTING
# =====================================================================

def ed_safety_route(active_diagnosed_ed: bool, behavioral_flags: List[str]) -> Decision:
    if active_diagnosed_ed:
        return Decision(GateResult.RESTRICT, "route_supportive_non_diet_program",
                         data={"suggest_professional_referral": True})
    triggered = set(behavioral_flags) & T.ED_BEHAVIORAL_FLAGS
    if len(triggered) >= 2:  # confidence threshold per file 12 Section 12 troubleshooting note
        return Decision(GateResult.RESTRICT, "flag_possible_disordered_eating_pattern",
                         data={"avoid_numeric_targets": True, "suggest_professional_referral": True,
                               "triggered_flags": sorted(triggered)})
    return Decision(GateResult.PROCEED, "standard_routing")


# =====================================================================
# FILE 12 SECTION 7 -- INJURY RE-INTRODUCTION PROTOCOL
# =====================================================================

def reintroduce_pattern(weeks_since_last_pain: Optional[int], pain_free_sessions_at_current_step: int = 0,
                         pain_recurred: bool = False, recurrence_count: int = 0) -> Decision:
    if weeks_since_last_pain is None or weeks_since_last_pain < 2:
        return Decision(GateResult.RESTRICT, "too_early_continue_substitution")
    if pain_recurred:
        action = "reset_to_substitution_extend_timeline"
        if recurrence_count >= 2:
            action = "reset_to_substitution_recommend_professional_eval"
        return Decision(GateResult.RESTRICT, action)
    if pain_free_sessions_at_current_step >= 2:
        return Decision(GateResult.PROCEED, "increase_load_10_20_percent")
    return Decision(GateResult.RESTRICT, "reintroduce_bodyweight_or_very_light_half_volume")


# =====================================================================
# FILE 12 SECTION 8 -- AGE-BASED SAFETY OVERLAYS
# =====================================================================

def age_overlay(age: int) -> dict:
    for (lo, hi), overlay in T.AGE_OVERLAYS.items():
        if age >= lo and (hi is None or age <= hi):
            return overlay
    return {"standard_rules": True}


# =====================================================================
# FILE 12 SECTION 9 -- ENVIRONMENTAL / EXTERNAL SAFETY FLAGS
# =====================================================================

def environmental_flags(signals: List[str]) -> List[dict]:
    out = []
    for s in signals:
        entry = T.ENVIRONMENTAL_FLAGS.get(s)
        if entry:
            out.append({"signal": s, **entry})
    return out


# =====================================================================
# FILE 12 SECTION 11 -- recurring pattern-pain escalation (edge case rule)
# =====================================================================

def check_recurring_pattern_pain(client_state: ClientState) -> Optional[Decision]:
    if client_state.distinct_pattern_pain_flags_this_mesocycle >= 3:
        return Decision(GateResult.RESTRICT, "escalate_full_professional_reevaluation")
    return None


# =====================================================================
# FILE 18 -- INJURY-SPECIFIC REHAB / RETURN-TO-TRAINING
# =====================================================================

def route_injury(injury_type: Optional[str], severity: Optional[str], client_state: ClientState) -> Decision:
    if severity == "emergency_symptom":
        return Decision(GateResult.BLOCK, "emergency_escalation")
    if severity == "acute_severe":
        return Decision(GateResult.BLOCK, "urgent_care_referral", data={"halt_loading_affected_region": True})
    if injury_type in T.KNOWN_INJURY_TABLE:
        handler = _INJURY_PROTOCOLS[injury_type]
        return handler(client_state)
    if injury_type is not None:
        return generic_unclassified_injury_protocol(client_state)
    return Decision(GateResult.BLOCK, "insufficient_information", data={"request": "structured_re_report"})


def low_back_strain_protocol(cs: ClientState, pain_scale: int = 0, radiating_leg_symptoms: bool = False,
                              numbness_present: bool = False, recently_resolved: bool = False) -> Decision:
    if pain_scale >= 7 or radiating_leg_symptoms or numbness_present:
        return Decision(GateResult.BLOCK, "professional_eval_required")
    if 4 <= pain_scale <= 6:
        return Decision(GateResult.RESTRICT, "acute_phase", data={
            "remove": ["axial_loaded_spinal_flexion_extension", "deadlift_variants", "squat_variants", "loaded_carries"],
            "permit": ["walking", "pain_free_hip_mobility", "supported_cat_cow", "seated_upper_body_machine"],
            "duration": "until_pain_scale_le_3_for_48h"})
    if 1 <= pain_scale <= 3:
        return Decision(GateResult.RESTRICT, "subacute_phase", data={
            "permit": ["wall_tap_rdl", "bird_dog", "dead_bug", "goblet_squat_light", "walking", "light_cycling"],
            "remove": ["barbell_deadlift_squat", "loaded_flexion"]})
    if pain_scale == 0 and recently_resolved:
        return Decision(GateResult.RESTRICT, "return_to_load", data={
            "action": "reintroduce_pattern_hinge_squat", "caution": "resume_at_50pct_pre_injury_load"})
    return Decision(GateResult.PROCEED, "standard_programming_no_restriction")


def anterior_knee_pain_protocol(cs: ClientState, swelling_present: bool = False, locking_or_giving_way: bool = False,
                                 pain_only_end_range_deep_flexion: bool = False,
                                 pain_during_eccentric_only: bool = False, pain_scale: int = 0,
                                 worsens_with_activity: bool = False) -> Decision:
    if swelling_present or locking_or_giving_way:
        return Decision(GateResult.BLOCK, "professional_eval_required")
    if pain_only_end_range_deep_flexion and not swelling_present:
        return Decision(GateResult.RESTRICT, "cap_squat_lunge_depth", data={
            "permit": ["box_squat_higher_box", "leg_press_limited_depth", "leg_curl", "hip_thrust"],
            "avoid": ["deep_full_rom_squat", "high_rep_deep_lunges", "leg_extension_full_lockout_snap"]})
    if pain_during_eccentric_only:
        return Decision(GateResult.RESTRICT, "isometric_bias_programming", data={
            "permit": ["wall_sit_isometric", "leg_extension_isometric_hold", "cycling_low_resistance"]})
    if pain_scale <= 2 and not worsens_with_activity:
        return Decision(GateResult.PROCEED, "continue_training_monitor")
    return Decision(GateResult.BLOCK, "insufficient_information",
                     data={"request": "onset_swelling_status_mechanical_symptoms"})


def shoulder_impingement_protocol(cs: ClientState, sudden_onset_trauma: bool = False, visible_deformity: bool = False,
                                   pain_overhead_or_endrange: bool = False, pain_only_bench_flare: bool = False,
                                   pain_at_rest_or_night: bool = False) -> Decision:
    if sudden_onset_trauma or visible_deformity:
        return Decision(GateResult.BLOCK, "urgent_care_referral")
    if pain_overhead_or_endrange:
        return Decision(GateResult.RESTRICT, "remove_overhead_pressing", data={
            "permit": ["landmine_press", "neutral_grip_db_press_capped", "face_pulls", "external_rotation_band"],
            "avoid": ["barbell_overhead_press", "upright_row", "behind_neck_press"]})
    if pain_only_bench_flare:
        return Decision(GateResult.RESTRICT, "reduce_elbow_flare", data={
            "permit": ["neutral_grip_db_press", "close_grip_machine_press", "tucked_elbow_pushup"],
            "avoid": ["wide_grip_barbell_bench", "flared_elbow_dips"]})
    if pain_at_rest_or_night:
        return Decision(GateResult.BLOCK, "professional_eval_required")
    return Decision(GateResult.RESTRICT, "conservative_substitution_default", data={
        "permit": ["landmine_press", "chest_supported_row", "lower_body_unaffected"]})


def ankle_sprain_protocol(cs: ClientState, unable_to_bear_weight: bool = False, severe_swelling_1hr: bool = False,
                           swelling_moderate: bool = False, pain_scale: int = 0,
                           can_bear_weight_mild_discomfort: bool = False,
                           pain_free_at_rest_mild_balance_discomfort: bool = False) -> Decision:
    if unable_to_bear_weight or severe_swelling_1hr:
        return Decision(GateResult.BLOCK, "urgent_care_referral")
    if swelling_moderate and pain_scale >= 5:
        return Decision(GateResult.RESTRICT, "acute_phase_0_72h", data={
            "action": "no_lower_body_loaded_standing_work",
            "permit": ["seated_upper_body_machine", "seated_core", "upper_body_ergometer"]})
    if pain_scale <= 4 and can_bear_weight_mild_discomfort:
        return Decision(GateResult.RESTRICT, "subacute_phase", data={
            "permit": ["leg_press_limited_rom", "leg_curl", "leg_extension", "stationary_bike_light"],
            "avoid": ["running_jumping_cutting", "standing_unilateral_balance", "calf_raises_past_discomfort"]})
    if pain_free_at_rest_mild_balance_discomfort:
        return Decision(GateResult.RESTRICT, "return_to_load", data={
            "action": "reintroduce_double_leg_before_single_leg"})
    return Decision(GateResult.PROCEED, "standard_programming_no_restriction")


def elbow_tendinopathy_protocol(cs: ClientState, pain_scale: int = 0, pain_only_extreme_end_range: bool = False) -> Decision:
    if pain_scale >= 6:
        return Decision(GateResult.RESTRICT, "acute_phase", data={
            "action": "remove_elbow_isolation_and_heavy_gripping",
            "permit": ["lower_body_unaffected", "neutral_light_grip_machine", "isometric_wrist_holds"]})
    if 3 <= pain_scale <= 5:
        return Decision(GateResult.RESTRICT, "reduce_load_30_40pct", data={
            "permit": ["neutral_grip_pulldown_row", "isometric_tendon_loading_progressive"],
            "avoid": ["heavy_barbell_curls", "heavy_pronated_grip_rows", "thick_bar_work"]})
    if pain_only_extreme_end_range:
        return Decision(GateResult.RESTRICT, "cap_rom_short_of_pain", data={"progression": "expand_rom_5_10pct_weekly"})
    return Decision(GateResult.PROCEED, "standard_programming_no_restriction")


_INJURY_PROTOCOLS = {
    "low_back_strain_nonspecific": low_back_strain_protocol,
    "anterior_knee_pain_patellofemoral": anterior_knee_pain_protocol,
    "shoulder_impingement_anterior": shoulder_impingement_protocol,
    "ankle_sprain_lateral_grade_1_2": ankle_sprain_protocol,
    "elbow_tendinopathy": elbow_tendinopathy_protocol,
}


def generic_unclassified_injury_protocol(cs: ClientState, pain_scale: int = 0) -> Decision:
    if pain_scale >= 7:
        return Decision(GateResult.BLOCK, "professional_eval_required")
    if 4 <= pain_scale <= 6:
        return Decision(GateResult.RESTRICT, "remove_affected_region_exercise", data={
            "permit": "all_unaffected_region_training_continues"})
    if 1 <= pain_scale <= 3:
        return Decision(GateResult.RESTRICT, "reduce_load_30_50pct_monitor_1_week")
    return Decision(GateResult.PROCEED, "log_for_monitoring_only")


def detect_recurring_injury_pattern(same_region_flags_12wk: int, distinct_regions_flagged_12wk: int) -> Decision:
    if same_region_flags_12wk >= 3:
        return Decision(GateResult.RESTRICT, "flag_recurring_injury_pattern",
                         data={"recommend_full_professional_reevaluation": True})
    if same_region_flags_12wk == 2:
        return Decision(GateResult.RESTRICT, "flag_possible_underlying_contributing_factor",
                         data={"suggest_movement_re_screen": True, "suggest_professional_consult": "soft"})
    if distinct_regions_flagged_12wk >= 4:
        return Decision(GateResult.RESTRICT, "flag_possible_systemic_or_programming_error_pattern",
                         data={"audit": ["volume_progression", "recovery_score_trend"]})
    return Decision(GateResult.PROCEED, "no_special_action")


def return_to_training_step(step_number: int) -> Optional[dict]:
    for s in T.RETURN_TO_TRAINING_STEPS:
        if s["step"] == step_number:
            return s
    return None


# =====================================================================
# FILE 19 -- CHRONIC HEALTH CONDITION MANAGEMENT
# =====================================================================

def route_chronic_condition(condition: str, client_state: ClientState) -> Decision:
    if condition in T.HIGH_RISK_CONDITIONS and not client_state.medical_clearance_resolved:
        return Decision(GateResult.BLOCK, "medical_clearance_required")
    if condition in T.KNOWN_CHRONIC_CONDITION_TABLE:
        handler = _CHRONIC_PROTOCOLS[condition]
        return handler(client_state)
    return generic_chronic_condition_protocol(condition, client_state)


def type_2_diabetes_protocol(cs: ClientState, on_insulin_or_sulfonylurea: bool = False,
                              glucose_unknown: bool = True, glucose_low: bool = False,
                              glucose_normal: bool = False) -> Decision:
    if on_insulin_or_sulfonylurea and glucose_unknown:
        if glucose_low:
            return Decision(GateResult.BLOCK, "delay_session_treat_hypoglycemia")
        if glucose_normal:
            return Decision(GateResult.PROCEED, "standard_session")
        return Decision(GateResult.RESTRICT, "proceed_cautiously_rpe_le_7", data={"ensure_fast_carb_accessible": True})
    if not on_insulin_or_sulfonylurea:
        return Decision(GateResult.PROCEED, "standard_programming_general_awareness")
    return Decision(GateResult.RESTRICT, "default_moderate_intensity_cap")


def hypertension_protocol(cs: ClientState, bp_control_status: str = "borderline_variable",
                           cleared_by_physician: bool = False) -> Decision:
    if bp_control_status == "well_controlled" and cleared_by_physician:
        return Decision(GateResult.PROCEED, "standard_programming_valsalva_caution",
                         data={"max_effort_singles": "avoid_1rm_cap_rpe_8", "breath_holds": "cue_exhale_on_exertion"})
    if bp_control_status == "borderline_variable":
        return Decision(GateResult.RESTRICT, "conservative_intensity_cap_rpe_7")
    if bp_control_status == "uncontrolled":
        return Decision(GateResult.BLOCK, "medical_clearance_required")
    return Decision(GateResult.RESTRICT, "treat_as_borderline_variable_default")


def asthma_protocol(cs: ClientState, air_quality_poor: bool = False, cold_dry_air: bool = False,
                     recent_flare_up_7d: bool = False, well_controlled: bool = True) -> Decision:
    if air_quality_poor or cold_dry_air:
        return Decision(GateResult.RESTRICT, "extend_warmup_reduce_peak_intensity",
                         data={"reminder": "confirm_rescue_inhaler_accessible"})
    if recent_flare_up_7d:
        return Decision(GateResult.RESTRICT, "cap_zone_2_delay_hiit_7_days_symptom_free")
    if well_controlled and not recent_flare_up_7d:
        return Decision(GateResult.PROCEED, "standard_programming")
    return Decision(GateResult.RESTRICT, "default_extended_warmup_conservative_cap")


def osteoarthritis_protocol(cs: ClientState, pain_at_rest: int = 0, pain_with_loading: int = 0,
                             improves_with_movement: bool = False, worsens_progressively: bool = False) -> Decision:
    if pain_at_rest >= 5:
        return Decision(GateResult.BLOCK, "professional_eval_required")
    if pain_with_loading <= 4 and improves_with_movement:
        return Decision(GateResult.RESTRICT, "standard_resistance_training_encouraged", data={
            "modifications": ["favor_machine_controlled_rom", "avoid_high_impact_if_hip_knee_oa",
                               "consistent_moderate_loading"],
            "cardio_preference": ["cycling", "swimming", "elliptical"]})
    if worsens_progressively:
        return Decision(GateResult.RESTRICT, "reduce_volume_30_40pct_reassess_selection")
    return Decision(GateResult.RESTRICT, "standard_oa_informed_programming")


def pcos_protocol(cs: ClientState, primary_goal: str = "", significant_fatigue_or_cycle_irregularity: bool = False) -> Decision:
    if primary_goal == "fat_loss":
        return Decision(GateResult.PROCEED, "standard_evidence_based_deficit",
                         data={"note": "resistance_training_supported_avoid_excessive_chronic_cardio"})
    if significant_fatigue_or_cycle_irregularity:
        return Decision(GateResult.RESTRICT, "monitor_recovery_closely_avoid_deficit_plus_high_volume_stack")
    return Decision(GateResult.PROCEED, "standard_programming")


def hypothyroid_protocol(cs: ClientState, recently_diagnosed_or_med_changed_6wk: bool = False,
                          stable_6plus_weeks: bool = False) -> Decision:
    if recently_diagnosed_or_med_changed_6wk:
        return Decision(GateResult.RESTRICT, "weight_recovery_score_over_fixed_schedule")
    if stable_6plus_weeks:
        return Decision(GateResult.PROCEED, "standard_programming")
    return Decision(GateResult.RESTRICT, "default_conservative_recovery_weighted_progression")


_CHRONIC_PROTOCOLS = {
    "type_2_diabetes_managed": type_2_diabetes_protocol,
    "hypertension_controlled": hypertension_protocol,
    "asthma_managed": asthma_protocol,
    "osteoarthritis_knee_hip": osteoarthritis_protocol,
    "pcos": pcos_protocol,
    "hypothyroidism_managed": hypothyroid_protocol,
}


def generic_chronic_condition_protocol(condition: str, cs: ClientState,
                                        involves_cardio_respiratory: bool = False,
                                        involves_joint_bone_connective: bool = False,
                                        involves_metabolic_endocrine: bool = False) -> Decision:
    if involves_cardio_respiratory:
        return Decision(GateResult.BLOCK, "medical_clearance_required")
    if involves_joint_bone_connective:
        return Decision(GateResult.RESTRICT, "default_low_impact_modality_preference",
                         data={"recommend": "physician_pt_input_on_loading_limits"})
    if involves_metabolic_endocrine:
        return Decision(GateResult.RESTRICT, "weight_recovery_score_avoid_deficit_plus_high_volume_stack")
    return Decision(GateResult.RESTRICT, "standard_programming_general_caution_flag")


def resolve_multi_condition_conflict(conditions: List[str], any_triggers_clearance: bool,
                                      conflicting_modality_preferences: bool = False) -> Decision:
    if any_triggers_clearance:
        return Decision(GateResult.BLOCK, "medical_clearance_required")
    if len(conditions) >= 2 and conflicting_modality_preferences:
        return Decision(GateResult.RESTRICT, "resolve_toward_more_conservative_protocol")
    if len(conditions) >= 3:
        return Decision(GateResult.RESTRICT, "flag_complex_multi_condition_case",
                         data={"recommend": "physician_multidisciplinary_input"})
    return Decision(GateResult.PROCEED, "apply_single_protocol_normally")


def monitor_condition_stability(new_symptom_disclosed: bool, trending_worse_3_checkins: bool,
                                 stable_or_improving: bool, checkins_skipped: bool = False) -> Decision:
    if new_symptom_disclosed:
        return Decision(GateResult.RESTRICT, "rerun_route_chronic_condition_immediately")
    if trending_worse_3_checkins:
        return Decision(GateResult.RESTRICT, "flag_condition_destabilizing_reduce_training_stress")
    if stable_or_improving:
        return Decision(GateResult.PROCEED, "continue_current_protocol")
    return Decision(GateResult.RESTRICT, "default_to_last_known_protocol_downgrade_confidence")


# =====================================================================
# FILE 20 -- ACUTE SYMPTOM & FIRST-RESPONSE TRIAGE (dispatcher)
# =====================================================================

def classify_health_report(report: HealthReport) -> Decision:
    if report.matches_emergency_list:
        return Decision(GateResult.BLOCK, "handoff_emergency_gate")
    if report.is_new_and_related_to_recent_event:
        return Decision(GateResult.RESTRICT, "handoff_acute_injury_routing")
    if report.is_related_to_disclosed_chronic_condition:
        return Decision(GateResult.RESTRICT, "handoff_chronic_condition_monitoring")
    if report.is_new_with_no_clear_mechanism:
        return classify_unmechanism_symptom(report)
    if report.is_vague_or_incomplete:
        return Decision(GateResult.RESTRICT, "request_structured_follow_up")
    return Decision(GateResult.PROCEED, "log_for_monitoring",
                     message="no actionable classification reached; default to conservative session modification")


def classify_unmechanism_symptom(report: HealthReport) -> Decision:
    st = report.symptom_type
    if st == "dizziness_or_lightheadedness":
        if report.occurs_only_on_standing_quickly:
            return Decision(GateResult.RESTRICT, "hydration_electrolyte_reminder_monitor")
        if report.occurs_during_exertion:
            return Decision(GateResult.BLOCK, "handoff_emergency_gate")
        if report.occurs_at_rest_unrelated_to_training:
            return Decision(GateResult.RESTRICT, "recommend_medical_follow_up_light_session_or_rest")
        return Decision(GateResult.RESTRICT, "default_conservative_light_session_monitor")

    if st == "unexplained_joint_pain_no_injury_event":
        if (report.pain_scale or 0) >= 5:
            return Decision(GateResult.RESTRICT, "handoff_generic_unclassified_injury_protocol")
        if (report.pain_scale or 0) <= 4:
            return Decision(GateResult.RESTRICT, "reduce_load_30pct_monitor_1_week")
        return Decision(GateResult.PROCEED, "log_and_monitor_only")

    if st == "unusual_fatigue_disproportionate_to_training":
        if (report.duration_days or 0) >= 7:
            return Decision(GateResult.RESTRICT, "flag_possible_overtraining_or_illness")
        if (report.duration_days or 0) < 7 and report.recent_life_stress_or_illness_disclosed:
            return Decision(GateResult.RESTRICT, "treat_as_expected_apply_fatigue_deload_logic")
        return Decision(GateResult.PROCEED, "monitor_no_immediate_action")

    if st == "unexplained_bruising_or_prolonged_bleeding":
        return Decision(GateResult.RESTRICT, "recommend_medical_follow_up_promptly")

    return Decision(GateResult.RESTRICT, "default_conservative_light_modified_session")


def request_structured_follow_up(client_provided_answers: bool, client_unable_or_unwilling: bool) -> Decision:
    if client_provided_answers:
        return Decision(GateResult.RESTRICT, "rerun_classify_health_report_with_completed_info")
    if client_unable_or_unwilling:
        return Decision(GateResult.RESTRICT, "default_conservative_modified_session")
    return Decision(GateResult.RESTRICT, "default_conservative_session_log_incomplete")


def todays_session_decision(classification: Decision, affected_pattern_isolated: bool = True,
                             affected_pattern_central_or_wholebody: bool = False,
                             chronic_protocol_blocks: bool = False) -> Decision:
    action = classification.action
    if action == "handoff_emergency_gate":
        return Decision(GateResult.BLOCK, "cancel_session_entirely", message=EMERGENCY_MESSAGE)
    if action in ("handoff_acute_injury_routing", "handoff_generic_unclassified_injury_protocol"):
        if affected_pattern_central_or_wholebody:
            return Decision(GateResult.RESTRICT, "convert_to_rest_day_or_light_mobility_only")
        if affected_pattern_isolated:
            return Decision(GateResult.RESTRICT, "modify_session_remove_affected_pattern_only")
        return Decision(GateResult.RESTRICT, "modify_session_conservatively_remove_region_linked_exercise")
    if action == "handoff_chronic_condition_monitoring":
        if chronic_protocol_blocks:
            return Decision(GateResult.BLOCK, "cancel_or_defer_session_per_protocol_block")
        return Decision(GateResult.RESTRICT, "apply_protocol_session_modifications")
    if action in ("log_for_monitoring", "log_and_monitor_only", "monitor_no_immediate_action"):
        return Decision(GateResult.PROCEED, "proceed_with_planned_session_unmodified")
    # fail-conservative default: never fail open to a full unmodified session when uncertain
    return Decision(GateResult.RESTRICT, "apply_specified_action_or_default_light_modified_session",
                     data={"source_action": action})
