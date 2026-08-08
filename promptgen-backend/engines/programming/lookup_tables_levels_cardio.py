"""Deterministic data from KB V7 files 3/4/5 (Beginner/Intermediate/Advanced
classification) and 13 (Cardio & Conditioning)."""

# --- files 3/4/5: training-age classification markers ---
CLASSIFICATION_MARKERS = {
    "beginner": "linear_progression_working_most_lifts_rir_estimation_poor",
    "intermediate": "linear_progression_stalled_most_lifts_rir_estimation_reasonably_accurate_weekly_progression_via_double_progression",
    "advanced": "progress_measured_months_years_not_weeks_high_rir_accuracy_mrv_frequently_bumped_often_old_injuries_needs_real_periodization",
}

# file 3 Section 3: beginner-specific split recommendation by days available
BEGINNER_SPLIT_BY_DAYS = {
    2: {"split": "full_body_ab", "note": "minimum_effective_dose_fine_for_true_beginners"},
    3: {"split": "full_body_abc", "note": "gold_standard_allows_technique_repetition"},
    4: {"split": "full_body_abab_or_early_upper_lower", "note": "only_once_movement_competency_established_8_12wk_in"},
    5: {"split": "not_recommended", "note": "cap_at_4_quality_days_recovery_and_technique_not_yet_built"},
}

# file 3 Section 5: beginner-specific weekly volume (lower than general MEV table)
BEGINNER_VOLUME = {
    "chest": (6, 10), "back": (8, 12), "shoulders": (4, 8), "quads": (6, 10),
    "hamstrings_glutes": (4, 8), "biceps": (4, 6), "triceps": (4, 6), "calves": (4, 8), "abs": (4, 8),
}

# file 3 Section 6: load increment rule
BEGINNER_LOAD_INCREMENT_KG = {"upper_body": 2.5, "lower_body": 5.0}
BEGINNER_FAILURE_TO_PROGRESS_SESSIONS = 2  # 2 consecutive sessions same weight/reps -> switch to double progression
BEGINNER_DELOAD_FREQUENCY_WEEKS = (8, 12)

# --- file 13: cardio modality classification ---
CARDIO_MODALITIES = {
    "walking_incline": {"type": "liss", "impact": "low"},
    "cycling": {"type": "liss_miss", "impact": "low"},
    "rowing": {"type": "miss_hiit_capable", "impact": "low_moderate"},
    "jogging_running": {"type": "miss_hiit_capable", "impact": "high"},
    "jump_rope": {"type": "hiit_capable", "impact": "high"},
    "sled_push_drag": {"type": "hiit_strength_hybrid", "impact": "low_joint_high_metabolic"},
    "swimming": {"type": "liss_miss_hiit_capable", "impact": "very_low"},
    "circuit_complex": {"type": "hiit_hybrid", "impact": "variable"},
}

CARDIO_ZONES = {
    1: {"hr_pct": (50, 60), "rpe": (2, 3), "talk_test": "full_conversation", "use": "recovery_warmup"},
    2: {"hr_pct": (60, 70), "rpe": (4, 5), "talk_test": "comfortable_conversation", "use": "aerobic_base_fat_oxidation"},
    3: {"hr_pct": (70, 80), "rpe": (6, 7), "talk_test": "broken_sentences", "use": "tempo_threshold_building"},
    4: {"hr_pct": (80, 90), "rpe": (8, 8), "talk_test": "few_words_only", "use": "vo2max_threshold_intervals"},
    5: {"hr_pct": (90, 100), "rpe": (9, 10), "talk_test": "cannot_talk", "use": "max_anaerobic_intervals"},
}

CARDIO_PRESCRIPTION_BASE = {
    "fat_loss": {"sessions": (3, 4), "zone": "zone2_primary_plus_1x_zone4_interval", "duration_min": (25, 40)},
    "hypertrophy": {"sessions": (1, 2), "zone": "zone2_only", "duration_min": (15, 25),
                     "note": "minimize_interference_low_impact_separate_from_leg_days"},
    "strength": {"sessions": (1, 2), "zone": "zone2_only", "duration_min": (15, 25),
                  "note": "minimize_interference_low_impact_separate_from_leg_days"},
    "general_health": {"sessions": (3, 5), "zone": "zone2_primary", "duration_min": (20, 30)},
    "endurance_performance": {"sessions": (4, 6), "zone": "polarized_80pct_zone2_20pct_zone4_5", "duration_min": (30, 90)},
}

HIIT_PROTOCOLS = {
    "classic_tabata": {"work_rest": "20s:10s", "rounds": (8, 8), "use_case": "advanced_time_efficient_high_fatigue"},
    "30_30": {"work_rest": "30s:30s", "rounds": (8, 12), "use_case": "intermediate_moderate_fatigue"},
    "ratio_1_2": {"work_rest": "30s:60s", "rounds": (6, 10), "use_case": "beginner_intermediate_anaerobic_intro"},
    "long_intervals": {"work_rest": "3-5min:2-3min", "rounds": (4, 6), "use_case": "vo2max_development_endurance_athletes"},
    "sled_sprint_intervals": {"work_rest": "15-20s:90s+", "rounds": (4, 8), "use_case": "power_conditioning_joint_friendly"},
}

INTERFERENCE_RULES = {
    "sequencing": "resistance_before_cardio_when_both_matter_cardio_first_only_if_primary_goal_or_le_10min_zone1_warmup",
    "same_day_proximity": "separate_hiit_and_heavy_lower_body_by_ge_6h_where_possible",
    "weekly_distribution": "place_hiit_on_non_leg_heavy_days_for_hypertrophy_strength_clients",
    "volume_ceiling_pct_of_resistance_duration": (150, 200),
    "fat_loss_with_strength_secondary": "cap_hiit_to_1x_week_favor_zone2_remaining_sessions",
}
