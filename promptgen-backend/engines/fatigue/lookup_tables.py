"""Deterministic data from KB V7 file 10 (Recovery & Deload). This is the
single real source for both the 'fatigue' and 'recovery' modules -- the
KB does not actually separate these into distinct specs (see manifest.json
note)."""

SLEEP_IMPACT = {
    "under_6h": {"impact": "significantly_impaired_strength_recovery_rir_accuracy_elevated_injury_risk",
                 "response": "reduce_volume_15_25pct_avoid_failure_entirely_prioritize_technique"},
    "6_to_7h": {"impact": "mild_moderate_impairment", "response": "standard_programming_no_pr_attempts"},
    "7_to_8h": {"impact": "adequate_for_most_adults", "response": "standard_programming"},
    "8_to_9h": {"impact": "optimal_for_most_adults", "response": "full_capacity_good_day_for_pushing_progression"},
    "9h_plus": {"impact": "excellent_or_may_indicate_under_recovery_illness_if_sudden_increase",
                "response": "full_capacity_screen_for_overreaching_illness_if_sudden_increase"},
}

NUTRITION_RECOVERY = {
    "protein_g_per_kg": (1.6, 2.2),
    "protein_g_per_kg_fat_loss": (2.0, 2.6),
    "hydration_ml_per_kg_per_day": (30, 40),
    "alcohol_note": "occasional_moderate_compatible_with_progress_frequent_heavy_hidden_cause_of_stalled_recovery",
}

# Section 3.1 -- when to deload, by training age (scheduled/proactive cadence, weeks)
SCHEDULED_DELOAD_FREQUENCY_WEEKS = {
    "beginner": (8, 12),
    "intermediate": (5, 8),
    "advanced": (4, 6),
}

REACTIVE_DELOAD_TRIGGERS = {
    "performance_drop": "2plus_consecutive_sessions_unexpected_strength_rep_dropoff_multiple_lifts",
    "soreness": "doms_not_resolved_within_48_72h_or_worsening_session_to_session",
    "joint_pain": "new_or_worsening_joint_discomfort_not_from_single_acute_incident",
    "motivation_mood": "persistent_low_motivation_dread_of_training_irritability",
    "sleep_hrv": "elevated_resting_hr_depressed_hrv_or_subjectively_poor_sleep_1plus_week",
    "illness": "any_active_illness_always_deload_or_fully_rest",
}

DELOAD_METHODS = {
    "volume_deload": {"protocol": "keep_intensity_similar_cut_sets_40_50pct", "best_for": "most_common_preserves_strength_skill"},
    "intensity_deload": {"protocol": "keep_sets_similar_reduce_load_40_50pct", "best_for": "joint_or_cns_fatigue_primary_issue"},
    "combined_deload": {"protocol": "reduce_both_volume_and_intensity_30pct_each", "best_for": "simplest_default"},
    "complete_rest": {"protocol": "3_7_days_off_entirely", "best_for": "illness_high_injury_risk_severe_burnout"},
    "active_recovery": {"protocol": "light_movement_mobility_easy_cardio_no_structured_lifting", "best_for": "mental_burnout_in_season_athletic"},
}

STANDARD_DELOAD_WEEK_TEMPLATE = {
    "sets_reduction_pct": 40,
    "load_reduction_pct": (10, 20),
    "rir_addition_alternative": (2, 3),
    "intensity_techniques_permitted": False,
}

FATIGUE_INDICATORS = {
    "session_rpe_vs_planned": {"normal": "matches_expectation", "warning": "1_2_points_higher_than_expected_same_load"},
    "bar_speed": {"normal": "consistent_for_given_pct_1rm", "warning": "noticeably_slower_on_submaximal_loads"},
    "resting_heart_rate": {"normal": "stable_baseline", "warning": "elevated_5plus_bpm_above_baseline_several_days"},
    "sleep_quality": {"normal": "restful_consistent_duration", "warning": "restless_frequent_waking_or_needing_more_sleep"},
    "motivation": {"normal": "present_even_if_mild_reluctance", "warning": "persistent_dread_avoidance"},
    "soreness_pattern": {"normal": "resolves_24_72h", "warning": "lasting_4plus_days_or_worsening_across_week"},
    "joint_tendon_discomfort": {"normal": "absent_or_minor_stable", "warning": "new_sharp_or_worsening_pain"},
    "appetite": {"normal": "stable_normal", "warning": "significant_change_without_other_explanation"},
}

RECOVERY_QUALITY_TIERS = {
    "poor": {"description": "under_6_7h_sleep_regularly_high_stress_inconsistent_nutrition",
             "adjustment": "cap_volume_near_mev_avoid_failure_deload_every_4_5wk_even_intermediate"},
    "average": {"description": "7_8h_sleep_moderate_stress_adequate_nutrition",
                "adjustment": "standard_mev_mav_programming_deload_per_standard_schedule"},
    "excellent": {"description": "8h_plus_sleep_low_stress_dialed_nutrition_good_training_age",
                  "adjustment": "can_approach_mav_mrv_extend_time_between_deloads_tolerate_more_intensity_techniques"},
}

AGE_RECOVERY_NOTES = {
    "teen": "excellent_recovery_capacity_but_protect_sleep_from_school_social_schedule",
    "18_30": "highest_general_recovery_capacity_standard_rules",
    "30_40": "still_robust_more_attention_to_tendon_specific_recovery",
    "40_50": "deload_every_4_6wk_even_at_intermediate_prioritize_protein_sleep_consistency",
    "50_plus": "longer_recovery_windows_deload_every_3_5wk_in_high_volume_blocks_ongoing_tendon_health_work",
}

STRESS_TRAINING_ADJUSTMENT = {
    "low": {"adjustment": "standard_programming"},
    "moderate": {"adjustment": "monitor_standard_unless_combined_with_poor_sleep"},
    "high": {"adjustment": "reduce_volume_intensity_15_25pct_protect_adherence_consider_extra_rest_day"},
}

DELOAD_DURATION_DAYS = (5, 7)  # typical; 2 weeks may be warranted for advanced/older with significant markers
DELOAD_DURATION_EXTENDED_DAYS = (10, 14)
