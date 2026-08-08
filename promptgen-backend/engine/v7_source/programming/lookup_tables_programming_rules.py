"""Deterministic data from KB V7 file 2 (Programming Rules): sets/reps by
goal, RIR by training age, tempo, rest, progression models, plateau tree
inputs, recovery/sleep/stress adjustments, age modifications."""

SETS_REPS_BY_GOAL = {
    "strength": {"rep_range": (1, 6), "sets": (3, 6), "load_pct_1rm": (80, 95), "rest_seconds": (180, 300)},
    "power": {"rep_range": (1, 5), "sets": (3, 5), "load_pct_1rm": (30, 95), "rest_seconds": (180, 300)},
    "hypertrophy": {"rep_range": (6, 12), "effective_range": (5, 30), "sets": (3, 5), "load_pct_1rm": (65, 85),
                    "rest_seconds_compound": (60, 120), "rest_seconds_isolation": (45, 90)},
    "muscular_endurance": {"rep_range": (15, 25), "sets": (2, 4), "load_pct_1rm": (40, 60), "rest_seconds": (30, 60)},
    "fat_loss": {"rep_range": (8, 15), "sets": (3, 4), "load_pct_1rm": (60, 75), "rest_seconds": (45, 90)},
    "general_fitness": {"rep_range": (8, 15), "sets": (2, 4), "load_pct_1rm": (60, 75), "rest_seconds": (60, 90)},
}

# training_age_band -> (compound_rir_range, isolation_rir_range, failure_frequency)
RIR_BY_TRAINING_AGE = {
    "beginner":     {"compound_rir": (3, 4), "isolation_rir": (2, 3), "failure_frequency": "avoid_entirely"},
    "novice_early": {"compound_rir": (2, 3), "isolation_rir": (1, 2), "failure_frequency": "occasional_last_set_isolation_only"},
    "novice_late":  {"compound_rir": (1, 2), "isolation_rir": (0, 1), "failure_frequency": "regularly_last_set_isolation"},
    "intermediate": {"compound_rir": (1, 2), "isolation_rir": (0, 1), "failure_frequency": "common_isolation_selective_compound"},
    "advanced":     {"compound_rir": (0, 2), "isolation_rir": (0, 0), "failure_frequency": "programmed_failure_forced_reps_drop_sets"},
}
# maps training age in years to the RIR band key above (distinct from the 4-band
# training_age_band() used in file 6/8 -- file 2 defines 5 finer bands)
RIR_AGE_BOUNDARIES = [
    (0, 0.5, "beginner"),
    (0.5, 1.0, "novice_early"),
    (1.0, 2.0, "novice_late"),
    (2.0, 5.0, "intermediate"),
    (5.0, None, "advanced"),
]

RPE_TO_RIR = {10: 0, 9.5: 0.5, 9: 1, 8: 2, 7: 3, 6: 4}  # <=5 -> 5+ handled in code

TEMPO_BY_GOAL = {
    "general_hypertrophy": "2-0-1-0",
    "strength_power": "1-0-X-0",
    "time_under_tension": "3-1-1-0",
    "tendon_joint_rehab": "3-2-2-0",
    "explosive_athletic_power": "0-0-X-0",
}

REST_BY_EXERCISE_TYPE = {
    "heavy_compound_ge_85pct": (180, 300),
    "moderate_compound_65_80pct": (90, 150),
    "isolation_accessory": (45, 90),
    "superset_circuit_density": (15, 45),
    "antagonist_superset": (0, 15),
}

PROGRESSION_MODELS = {
    "linear": {"who": "0-0.5yr", "end_condition": "2_consecutive_failed_progression_attempts_move_to_double"},
    "double_progression": {"who": "0.5-5yr", "primary_hypertrophy_model": True},
    "undulating_dup": {"who": "intermediate_advanced_plateauing_or_needing_variety"},
    "block_periodization": {"who": "advanced_especially_strength_powerlifting", "block_length_weeks": (3, 6)},
    "conjugate_concurrent": {"who": "advanced_strength_athletes"},
    "autoregulation_rpe_rir": {"who": "any_age_6mo_plus_with_body_awareness"},
}

FAILURE_POLICY = {
    ("beginner", "any"): "avoid_stop_3plus_reps_shy",
    ("intermediate", "compound"): "rare_only_last_set_with_spotter",
    ("intermediate", "isolation"): "regular_especially_final_set",
    ("advanced", "compound"): "occasional_programmed_eg_last_week_of_block",
    ("advanced", "isolation"): "common_including_forced_reps_and_drop_sets",
}
FAILURE_OVERRIDE_FATIGUE_PRESENT = "never_autoregulate_down_regardless_of_program"

RECOVERY_QUALITY_ADJUSTMENTS = {
    "poor": {"weekly_sets_pct": (-30, -20), "rir_addition": 1, "prioritize": "compounds_over_accessories"},
    "average": {"note": "standard_programming"},
    "excellent": {"note": "push_toward_mrv_lower_rir_more_often_tolerate_higher_frequency"},
}

SLEEP_ADJUSTMENTS = {
    "under_6h": {"action": "reduce_intensity_avoid_failure_entirely", "volume_trim_pct": (-20, -10)},
    "6_to_7h": {"action": "slight_caution_avoid_maximal_rir_pushes"},
    "7_to_8h": {"action": "standard_programming"},
    "8_to_9h_plus": {"action": "full_capacity_ideal_for_pushing_progression"},
}

STRESS_ADJUSTMENTS = {
    "high": {"action": "treat_like_poor_sleep_reduce_volume_intensity_protect_adherence"},
    "moderate": {"action": "standard_monitor"},
    "low": {"action": "full_programming_capacity"},
}

AGE_PROGRAMMING_NOTES = {
    "teen": "emphasize_technique_before_intensity_avoid_true_failure_and_max_singles_faster_recovery_ok_higher_frequency",
    "18_30": "full_programming_range_highest_work_capacity",
    "30_40": "slightly_longer_warmups_monitor_joint_feedback",
    "40_50": "extra_warmup_sets_joint_friendly_variations_more_conservative_failure_policy",
    "50_plus": "machines_controlled_ranges_for_higher_risk_lifts_longer_warmup_10_15min_deload_every_4_6wk_vs_6_8",
}
