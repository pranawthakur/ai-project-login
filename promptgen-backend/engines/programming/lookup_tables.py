"""Deterministic data extracted from KB V7 file 14 (Default Safe Template &
Coach Override Engine). Pure data -- consumed by rules.py."""

DEFAULT_SAFE_TEMPLATE_EXERCISES = [
    {"pattern": "squat", "exercise": "bodyweight_box_squat_sit_to_stand",
     "regression": "assisted_sit_to_stand_hands_on_support"},
    {"pattern": "hinge", "exercise": "glute_bridge",
     "regression": "supported_glute_bridge_feet_elevated_less"},
    {"pattern": "horizontal_push", "exercise": "incline_or_wall_pushup",
     "regression": "wall_pushup"},
    {"pattern": "horizontal_pull", "exercise": "band_row_or_supported_light_db_row",
     "regression": "band_pull_apart_only"},
    {"pattern": "core_anti_extension", "exercise": "dead_bug_or_bird_dog",
     "regression": "marching_bird_dog_reduced_rom"},
    {"pattern": "loaded_carry_conditioning", "exercise": "light_farmer_carry_or_brisk_walk",
     "regression": "walk_only"},
]

DEFAULT_SAFE_TEMPLATE_WARMUP = [
    "5min_zone1_walking_or_marching_in_place",
    "dynamic_mobility_hip_circles_arm_circles_squat_to_stand_x8_cat_cow_x8",
    "one_light_ramp_up_set_first_exercise_50pct_effort",
]

DEFAULT_SAFE_TEMPLATE_NEVER_INCLUDES = [
    "pain_provoking_movement_for_individual",
    "barbell_max_or_near_max_effort_work",
    "unsupervised_overhead_loaded_work_if_thoracic_mobility_limited",
    "numeric_calorie_macro_targets_if_ed_flag_present",
    "body_composition_tracking_prompts_if_ed_flag_present",
]

# category -> overridable_by_certified_coach?
OVERRIDE_PERMISSIONS = {
    "exercise_selection_substitution": True,
    "volume_intensity_within_same_tier": True,
    "confidence_tier_upgrade_downgrade": True,   # requires justification note
    "emergency_symptom_stop": False,             # file 12 Sec 2 -- never overridable
    "below_minimum_age_reject": False,           # hard block
    "active_unresolved_medical_clearance_required": False,
}

TIER_TRANSITIONS = [
    {"from": "red", "to": "orange", "trigger": "age_corrected_verified_ge_13_with_guardian_consent_or_referral_resolved",
     "mode": "coach_admin_initiated_requires_documentation"},
    {"from": "orange", "to": "yellow", "trigger": "exit_criteria_met_section_1_5", "mode": "automatic"},
    {"from": "yellow", "to": "green",
     "trigger": "8_consecutive_weeks_consistent_checkins_and_intake_completeness_ge_95pct_and_no_unresolved_flags",
     "mode": "automatic"},
    {"from": "green", "to": "yellow", "trigger": "missed_checkin_cycle_or_new_minor_flag", "mode": "automatic"},
    {"from": "yellow_or_green", "to": "orange",
     "trigger": "new_high_risk_condition_or_new_unresolved_pain_flag_or_2_missed_checkin_cycles", "mode": "automatic"},
    {"from": "any", "to": "red", "trigger": "emergency_symptom_logged_or_below_age_discovered",
     "mode": "automatic_immediate"},
]
