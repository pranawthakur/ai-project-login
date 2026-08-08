"""Additional deterministic tables from KB V7 files 1 (Master Split Table),
6 (Intensity Techniques), 7 (Goal-Based Modifications), 8 (Weekly Muscle
Volume). Pure data, consumed by rules.py."""

# ---------------------------------------------------------------------
# FILE 1 -- SPLIT LIBRARY
# ---------------------------------------------------------------------

SPLIT_LIBRARY = {
    "full_body_abc": {"days_per_week": (2, 4), "best_training_age_years": (0, 1),
                       "best_goals": ["muscle_gain", "general_fitness", "fat_loss"],
                       "session_min": (30, 60), "freq_per_muscle": (2.5, 4)},
    "upper_lower": {"days_per_week": (4, 4), "best_training_age_years": (0.5, 5),
                     "best_goals": ["muscle_gain", "strength", "powerbuilding"],
                     "session_min": (45, 75), "freq_per_muscle": (2, 2)},
    "ppl_3day": {"days_per_week": (3, 3), "best_training_age_years": (1, 10),
                 "best_goals": ["bodybuilding", "hypertrophy"], "session_min": (45, 90), "freq_per_muscle": (1, 1)},
    "ppl_6day": {"days_per_week": (6, 6), "best_training_age_years": (1, 10),
                 "best_goals": ["bodybuilding", "hypertrophy"], "session_min": (45, 90), "freq_per_muscle": (2, 2)},
    "ppl_ul_hybrid": {"days_per_week": (5, 5), "best_training_age_years": (2, 10),
                      "best_goals": ["bodybuilding", "powerbuilding"], "session_min": (60, 90), "freq_per_muscle": (1.6, 1.6)},
    "bro_split": {"days_per_week": (5, 5), "best_training_age_years": (5, 99),
                  "best_goals": ["bodybuilding", "specialization"], "session_min": (60, 90), "freq_per_muscle": (1, 1)},
    "full_body_specialization": {"days_per_week": (4, 5), "best_training_age_years": (1, 5),
                                  "best_goals": ["weak_point_training", "recomp"], "session_min": (45, 75), "freq_per_muscle": (2, 3)},
    "powerlifting_sbd": {"days_per_week": (4, 4), "best_training_age_years": (1, 99),
                          "best_goals": ["strength", "powerlifting"], "session_min": (60, 120), "freq_per_muscle": (2, 2)},
    "conjugate": {"days_per_week": (4, 4), "best_training_age_years": (3, 99),
                  "best_goals": ["powerlifting", "power"], "session_min": (60, 90), "freq_per_muscle": (2, 2)},
    "minimalist_2day": {"days_per_week": (2, 2), "best_training_age_years": (0, 99),
                         "best_goals": ["maintenance", "general_fitness", "fat_loss"], "session_min": (30, 45), "freq_per_muscle": (2, 2)},
    "athletic_hybrid": {"days_per_week": (3, 5), "best_training_age_years": (0, 99),
                         "best_goals": ["athletic_performance"], "session_min": (45, 90), "freq_per_muscle": None},
}

SESSION_DURATION_MODIFIERS = {
    20: {"structure": "1_compound_plus_1_accessory_per_pattern", "rest_seconds": (45, 60), "supersets": True},
    30: {"structure": "2_compound_1_2_accessories", "rest_seconds": (60, 90)},
    45: {"structure": "standard_minimalist_4_5_exercises", "rest_seconds": (90, 120)},
    60: {"structure": "standard_full_5_6_exercises", "rest_seconds": (90, 120)},
    75: {"structure": "full_session_plus_extra_accessory_or_intensity_technique", "rest_seconds": (90, 120)},
    120: {"structure": "advanced_powerlifting_peaking_only", "note": "diminishing_returns_beyond_90min_for_pure_hypertrophy"},
}

SPLIT_SWITCH_TRIGGERS = [
    {"trigger": "training_age_crosses_1yr_on_full_body", "action": "migrate_to_upper_lower_or_ppl"},
    {"trigger": "weekly_sets_exceed_split_capacity_without_90min_sessions", "action": "add_day_or_migrate_higher_frequency_split"},
    {"trigger": "persistent_joint_pain_from_pattern_heavy_split", "action": "rebalance_push_pull_ratio_or_move_to_ppl"},
    {"trigger": "recovery_capacity_drops_poor_sleep_or_high_stress", "action": "temporarily_downshift_fewer_days"},
    {"trigger": "plateau_over_4_weeks_despite_adherence", "action": "check_recovery_first_then_consider_split_change_last_resort"},
    {"trigger": "approaching_powerlifting_meet", "action": "migrate_to_peaking_specific_split"},
]

# ---------------------------------------------------------------------
# FILE 6 -- INTENSITY TECHNIQUES
# ---------------------------------------------------------------------

# training_age bands: "beginner" (<0.5yr), "novice" (0.5-2yr), "intermediate" (2-5yr), "advanced" (5+yr)
INTENSITY_TECHNIQUE_MATRIX = {
    "drop_sets":        {"beginner": "no", "novice": "light", "intermediate": "yes", "advanced": "yes"},
    "rest_pause":       {"beginner": "no", "novice": "light", "intermediate": "yes", "advanced": "yes"},
    "myo_reps":         {"beginner": "no", "novice": "no", "intermediate": "yes", "advanced": "yes"},
    "cluster_sets":     {"beginner": "no", "novice": "no", "intermediate": "light", "advanced": "yes"},
    "supersets_antagonist": {"beginner": "light", "novice": "yes", "intermediate": "yes", "advanced": "yes"},
    "giant_sets":       {"beginner": "no", "novice": "no", "intermediate": "light", "advanced": "yes"},
    "forced_reps":      {"beginner": "no", "novice": "no", "intermediate": "no", "advanced": "yes"},
    "cheat_reps":        {"beginner": "no", "novice": "no", "intermediate": "no", "advanced": "yes"},
    "partials":         {"beginner": "no", "novice": "no", "intermediate": "light", "advanced": "yes"},
    "bfr_performance":  {"beginner": "no", "novice": "no", "intermediate": "light", "advanced": "yes"},
    "eccentric_overload": {"beginner": "no", "novice": "no", "intermediate": "no", "advanced": "yes"},
    "isometrics":       {"beginner": "light", "novice": "yes", "intermediate": "yes", "advanced": "yes"},
    "explosive_power":  {"beginner": "technique_only_no_load", "novice": "light", "intermediate": "yes", "advanced": "yes"},
}

INTENSITY_FATIGUE_BUDGET_PER_WEEK = {
    "beginner": (0, 1),
    "novice": (0, 1),       # "light only" per file 6 -- treated as beginner-tier budget
    "intermediate": (1, 2),
    "advanced": (2, 4),
}


def training_age_band(years: float) -> str:
    if years < 0.5:
        return "beginner"
    if years < 2:
        return "novice"
    if years < 5:
        return "intermediate"
    return "advanced"


# ---------------------------------------------------------------------
# FILE 7 -- GOAL-BASED MODIFICATIONS
# ---------------------------------------------------------------------

GOAL_TABLE = {
    "muscle_gain": {"calorie_offset": (100, 300), "protein_g_per_kg": (1.6, 2.2), "volume_bias": "MEV_MAV",
                     "rep_range": (6, 15), "cardio": "1-3x/week light-moderate"},
    "lean_bulk": {"calorie_offset": (100, 250), "protein_g_per_kg": (1.8, 2.2), "volume_bias": "MAV",
                  "rep_range": (6, 12), "cardio": "2-3x/week"},
    "dirty_bulk": {"calorie_offset": (500, 1000), "protein_g_per_kg": (1.6, 2.0), "volume_bias": "MAV_MRV",
                   "rep_range": (6, 15), "cardio": "minimal"},
    "strength": {"calorie_offset": (0, 100), "protein_g_per_kg": (1.6, 2.0), "volume_bias": "MEV_MAV",
                 "rep_range": (1, 6), "cardio": "minimal_low_impact_only"},
    "powerlifting": {"calorie_offset": (0, 0), "protein_g_per_kg": (1.6, 2.0), "volume_bias": "MEV",
                      "rep_range": (1, 5), "cardio": "minimal"},
    "powerbuilding": {"calorie_offset": (0, 150), "protein_g_per_kg": (1.8, 2.2), "volume_bias": "MAV",
                       "rep_range": (3, 12), "cardio": "light_1_2x_week"},
    "bodybuilding": {"calorie_offset": (-750, 500), "protein_g_per_kg": (2.0, 2.4), "volume_bias": "MAV_MRV",
                      "rep_range": (6, 15), "cardio": "phase_dependent_high_in_prep"},
    "athletic_performance": {"calorie_offset": (0, 100), "protein_g_per_kg": (1.6, 2.0), "volume_bias": "MEV_moderate",
                              "rep_range": None, "cardio": "sport_specific"},
    "fat_loss": {"calorie_offset": (-750, -300), "protein_g_per_kg": (2.0, 2.6), "volume_bias": "MEV_MAV_maintain",
                 "rep_range": (8, 15), "cardio": "3-5x/week mix steady-state + intervals"},
    "maintenance": {"calorie_offset": (0, 0), "protein_g_per_kg": (1.6, 2.0), "volume_bias": "MEV_MAV",
                     "rep_range": None, "cardio": "2-3x/week"},
    "body_recomposition": {"calorie_offset": (-10, 0), "protein_g_per_kg": (2.2, 2.6), "volume_bias": "MAV",
                             "rep_range": (6, 15), "cardio": "2-4x/week"},
    "general_fitness": {"calorie_offset": (0, 0), "protein_g_per_kg": (1.2, 1.6), "volume_bias": "MEV",
                          "rep_range": None, "cardio": "3-5x/week"},
    "sport_specific": {"calorie_offset": (0, 0), "protein_g_per_kg": (1.6, 2.0), "volume_bias": "varies_by_phase",
                         "rep_range": None, "cardio": "sport_specific"},
}

# ---------------------------------------------------------------------
# FILE 8 -- WEEKLY MUSCLE VOLUME (direct sets/week)
# ---------------------------------------------------------------------

VOLUME_TABLE = {
    #                    beginner_mev_mav  intermediate_mev_mav  advanced_mev_mav   mrv_ceiling
    "chest":             ((6, 10),         (10, 18),             (12, 22),          26),
    "back_total":        ((8, 12),         (12, 20),             (14, 25),          30),
    "lats":              ((6, 10),         (10, 16),             (12, 20),          24),
    "upper_back_traps":  ((4, 8),          (6, 12),              (8, 16),           20),
    "shoulders_direct":  ((4, 8),          (8, 16),              (10, 20),          26),
    "side_delts":        ((4, 6),          (8, 12),              (10, 16),          20),
    "biceps":            ((4, 8),          (8, 14),              (10, 20),          26),
    "triceps":           ((4, 8),          (8, 14),              (10, 20),          24),
    "forearms":          ((2, 4),          (4, 8),               (6, 12),           16),
    "quads":             ((6, 10),         (10, 18),             (12, 22),          26),
    "hamstrings":        ((4, 8),          (8, 14),              (10, 18),          22),
    "glutes_direct":     ((2, 6),          (4, 10),              (6, 14),           18),
    "calves":            ((4, 8),          (8, 16),              (10, 20),          25),
    "abs":               ((4, 8),          (6, 12),              (8, 16),           20),
}

VOLUME_FREQUENCY_RULES = {
    "beginner": (2.5, 4),
    "intermediate": (2, 2),
    "advanced": (1.6, 2),
}

VOLUME_GOAL_MODIFIERS = {
    "muscle_gain": "standard_aim_mav",
    "bodybuilding": "standard_aim_mav",
    "strength": "reduce_accessory_isolation_30_40pct_keep_compound_volume",
    "powerlifting": "reduce_accessory_isolation_30_40pct_keep_compound_volume",
    "fat_loss": "maintain_near_current_mev_mav_do_not_increase",
    "athletic_performance": "reduce_isolation_favor_compound_power_lower_total_sets_ok",
    "general_fitness": "mev_sufficient_no_need_for_mav",
}

RECOVERY_VOLUME_ADJUSTMENTS = {
    "poor_sleep_under_6_7h": -0.20,       # -15% to -25%, midpoint used
    "high_life_stress": -0.20,
    "excellent_recovery": 0.10,           # push toward upper MAV/MRV
    "returning_from_layoff_deload": "start_at_mev_ramp_to_mav_over_2_3_weeks",
}

# secondary-muscle volume credit multiplier range (file 8 section 2 note)
INDIRECT_VOLUME_MULTIPLIER = (0.25, 0.5)
