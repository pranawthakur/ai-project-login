"""Deterministic lookup tables extracted from KnowledgeBase V7 files 12, 18, 19.
Pure data. No prose. Consumed by rules.py.
"""

EMERGENCY_SYMPTOMS = [
    "chest_pain_or_pressure_radiating_arm_jaw",
    "sudden_severe_headache_worst_of_life",
    "shortness_of_breath_disproportionate_or_at_rest",
    "fainting_or_loss_of_consciousness_during_exercise",
    "sudden_numbness_weakness_one_side_slurred_speech",
    "severe_sudden_joint_deformity_or_cannot_bear_weight",
    "signs_of_anaphylaxis",
]

HIGH_RISK_CONDITIONS = [
    "hypertension_uncontrolled",
    "cardiac_history_any",
]

CONDITION_CONSTRAINTS = {
    "hypertension_controlled": {"avoid_valsalva_max_effort": True, "rpe_cap": 8, "rest": "longer", "avoid_extended_breath_holds": True},
    "hypertension_uncontrolled": {"block": "medical_clearance_required"},
    "type_2_diabetes": {"monitor": "hypoglycemia_signs", "recommend": "glucose_check_if_on_insulin_or_sulfonylurea", "avoid": "unsupervised_fasted_high_intensity"},
    "pregnancy_trimester_1": {"avoid": ["overheating", "new_high_impact"], "rpe_cap": 7},
    "pregnancy_trimester_2_3": {"avoid": ["supine_after_20_weeks", "high_fall_risk", "heavy_valsalva"], "reduce_max_intensity": True},
    "postpartum_under_6_weeks": {"avoid": ["loaded_core", "impact_work"], "note": "pelvic_floor_considerations"},
    "osteoporosis_osteopenia": {"avoid": ["loaded_spinal_flexion", "high_impact_jumping_without_clearance"]},
    "joint_replacement_active_recent": {"follow": "physician_pt_rom_and_load_restrictions_explicit"},
    "active_eating_disorder_disclosure": {"block_numeric_diet_targets": True, "block_body_comp_metrics": True, "route": "supportive_professional_referral"},
    "asthma_exercise_induced": {"ensure": "warmup_ramp", "flag": "conditioning_intensity_caps", "recommend": "inhaler_available"},
    "cardiac_history_any": {"block": "medical_clearance_required", "cap_intensity_at": "clearance_specified_level_only"},
}

MEDICATION_FLAGS = {
    "beta_blockers": {"flag": "heart_rate_response_blunted", "note": "do_not_use_hr_zones_use_rpe"},
    "diuretics": {"flag": "dehydration_risk_elevated", "note": "hydration_reminders_caution_in_heat"},
    "insulin_or_sulfonylureas": {"flag": "hypoglycemia_risk", "note": "see_type_2_diabetes_protocol"},
    "corticosteroids_long_term": {"flag": "tendon_bone_fragility_risk", "note": "conservative_loading_progression_avoid_rapid_jumps"},
    "blood_thinners": {"flag": "bruising_bleeding_risk", "note": "avoid_high_collision_high_fall_risk_activities"},
}

AGE_OVERLAYS = {
    # (min_age, max_age_inclusive_or_None): overlay
    (13, 17): {"guardian_consent_required": True, "no_max_effort_testing": True, "emphasize": "technique_mastery",
               "cap_external_load_progression_rate": True, "guardian_visibility": True},
    (18, 64): {"standard_rules": True},
    (65, None): {"mandatory_fall_risk_screen_before_unstable_surface_work": True, "extra_warmup_time": True,
                 "rpe_cap": 7, "default_osteoporosis_risk_unknown_unless_screened_negative": True},
}

ENVIRONMENTAL_FLAGS = {
    "extreme_heat_humidity_no_acclimation": {"flag": "heat_illness_risk", "response": "reduce_intensity_increase_rest_hydration_indoor_alt"},
    "unsupervised_heavy_max_attempts": {"flag": "unsupervised_max_effort_risk", "response": "recommend_spotter_safety_bars_or_machine"},
    "recent_illness_fever_under_48h_resolved": {"flag": "post_illness_deload_required", "response": "force_deload_week_no_high_intensity_until_48h_symptom_free"},
}

ED_BEHAVIORAL_FLAGS = {
    "rapid_unexplained_weight_loss",
    "extreme_restriction_language",
    "compulsive_exercise_language",
    "self_worth_tied_to_weight_language",
}

PAIN_TRIAGE_TABLE = {
    "sharp_localized_joint_sudden": {"action": "remove_exercise_pattern_entirely", "note": "do_not_substitute_lighter_version_of_same_pattern", "recommend": "professional_evaluation_before_reintroducing"},
    "dull_diffuse_muscular_resolves_24_72h": {"action": "standard_doms_continue_monitor"},
    "pain_only_end_range": {"action": "cap_rom_add_mobility_retest_1_2_weeks"},
    "increases_session_over_session_despite_substitution": {"action": "full_pattern_removal_plus_professional_referral", "note": "do_not_keep_attempting_substitutions"},
}

# --- File 18: known injury table -> protocol keys (implemented as functions in rules.py) ---
KNOWN_INJURY_TABLE = [
    "low_back_strain_nonspecific",
    "anterior_knee_pain_patellofemoral",
    "shoulder_impingement_anterior",
    "ankle_sprain_lateral_grade_1_2",
    "elbow_tendinopathy",
]

RETURN_TO_TRAINING_STEPS = [
    {"step": 1, "name": "pain_free_at_rest", "criteria": "48_consecutive_hours_pain_free_at_rest", "else_branch": "remain_at_previous_phase_recheck_48h"},
    {"step": 2, "name": "pain_free_unloaded_pattern", "criteria": "2_sessions_bodyweight_pain_le_1", "else_branch": "reset_to_step_1_load_extend_timeline"},
    {"step": 3, "name": "pain_free_50pct_prior_load", "criteria": "2_sessions_at_50pct_prior_load_pain_le_1", "else_branch": "drop_to_step_2_flag_professional_eval_if_2nd_reset"},
    {"step": 4, "name": "progressive_load_increase", "criteria": "10_20pct_load_increase_per_pain_free_block", "else_branch": "drop_back_one_step_2nd_recurrence_triggers_referral"},
    {"step": 5, "name": "full_return", "criteria": "reaches_prior_working_load_pain_free", "else_branch": "maintain_standard_monitoring_cadence"},
]

# --- File 19: known chronic condition table ---
KNOWN_CHRONIC_CONDITION_TABLE = [
    "type_2_diabetes_managed",
    "hypertension_controlled",
    "asthma_managed",
    "osteoarthritis_knee_hip",
    "pcos",
    "hypothyroidism_managed",
]
