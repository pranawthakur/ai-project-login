"""Deterministic data from KB V7 file 17 (Periodization & AI Decision
Engine) -- the sole real source for the `progression` module. Its
originally-mapped sources (11_progression_engine, 17_plateau_engine,
18_weakpoint_engine, 24_periodization_engine) are 1-2 line stubs with
nothing to port; file 17 covers this domain for real."""

# Section 1.2 -- split-to-goal fit matrix (0.0-1.0)
SPLIT_GOAL_FIT = {
    "full_body_x2_3":  {"strength": 0.8, "powerlifting": 0.7, "hypertrophy": 0.6, "fat_loss": 0.8, "general_health": 0.95, "athletic_performance": 0.7},
    "upper_lower_x4":  {"strength": 0.9, "powerlifting": 0.9, "hypertrophy": 0.85, "fat_loss": 0.75, "general_health": 0.8, "athletic_performance": 0.85},
    "ppl_x3_per_week": {"strength": 0.6, "powerlifting": 0.5, "hypertrophy": 0.85, "fat_loss": 0.65, "general_health": 0.6, "athletic_performance": 0.6},
    "ppl_x2_6days":    {"strength": 0.7, "powerlifting": 0.6, "hypertrophy": 0.95, "fat_loss": 0.6, "general_health": 0.5, "athletic_performance": 0.6},
    "bro_split":       {"strength": 0.4, "powerlifting": 0.3, "hypertrophy": 0.75, "fat_loss": 0.5, "general_health": 0.4, "athletic_performance": 0.4},
}

# Section 2 -- periodization models and their AI gate rules
PERIODIZATION_MODELS = {
    "linear": {
        "who": "beginners_intermediates_single_goal_blocks",
        "use_for": ["contest_prep", "off_season_base_building", "simple_progression_needed"],
        "not_for": ["multi_goal_concurrent", "elite_simultaneous_quality_maintenance"],
    },
    "undulating": {
        "who": "intermediate_advanced_concurrent_goals",
        "use_for": ["3plus_sessions_per_week_same_pattern", "plateau_breaking", "variety_driven_adherence"],
        "not_for": ["true_beginners_too_much_variable_management", "fatigue_priority_orange_yellow_tier"],
    },
    "block": {
        "who": "advanced_competitive_powerlifters_olympic_lifters",
        "use_for": ["pre_competition_cycles", "advanced_with_established_base"],
        "not_for": ["general_fitness", "beginners", "no_competition_or_peaking_date"],
    },
    "conjugate_adjacent": {
        "who": "advanced_managing_staleness_on_primary_lifts",
        "note": "offer_simplified_variant_rotation_not_full_westside_system_unless_coach_override",
    },
    "vbt": {
        "who": "advanced_with_velocity_tracking_equipment",
        "velocity_loss_cutoff_hypertrophy_pct": (20, 25),
        "velocity_loss_cutoff_strength_power_pct": (10, 15),
    },
}

CONTRAST_METHODS = {
    "contrast_training": {"gate": "athletic_performance_and_24mo_and_green_tier"},
    "french_contrast": {"gate": "athletic_performance_and_24mo_and_green_tier_and_no_lower_limb_injury_flag"},
    "triphasic": {"gate": "36mo_and_athletic_performance_not_general_population"},
}

# Section 3 -- advanced set-structure gate table (technique -> min tier + min training age months)
SET_STRUCTURE_GATES = {
    "top_set_backoff":        {"min_tier": "orange", "min_training_age_months": 0, "fatigue_cost": "moderate"},
    "cluster_sets":           {"min_tier": "green", "min_training_age_months": 6, "fatigue_cost": "moderate_high"},
    "myo_reps":               {"min_tier": "yellow", "min_training_age_months": 0, "fatigue_cost": "high_local", "prefer": "isolation_over_compound"},
    "drop_sets":              {"min_tier": "green", "min_training_age_months": 0, "fatigue_cost": "high_local", "prefer": "isolation_machine"},
    "mechanical_drop_sets":   {"min_tier": "green", "min_training_age_months": 0, "fatigue_cost": "high_local"},
    "superset_same_muscle":   {"min_tier": "yellow", "min_training_age_months": 0, "fatigue_cost": "moderate_high"},
    "superset_antagonist":    {"min_tier": "orange", "min_training_age_months": 0, "fatigue_cost": "moderate"},
    "tri_giant_sets":         {"min_tier": "green", "min_training_age_months": 0, "fatigue_cost": "high", "note": "hypertrophy_blocks_only"},
    "rest_pause":             {"min_tier": "green", "min_training_age_months": 6, "fatigue_cost": "high"},
    "forced_reps":            {"min_tier": "green", "min_training_age_months": 0, "fatigue_cost": "very_high", "requires_supervision": True},
    "cheat_reps":             {"min_tier": "green", "min_training_age_months": 0, "fatigue_cost": "high_elevated_injury_risk", "discouraged_for": "large_compound_barbell_lifts"},
    "partial_reps":           {"min_tier": "green", "min_training_age_months": 0, "fatigue_cost": "moderate_high"},
    "bfr_occlusion":          {"min_tier": "yellow", "min_training_age_months": 0, "fatigue_cost": "moderate_local", "requires_clearance_if_vascular_flag": True},
    "isometrics":             {"min_tier": "orange", "min_training_age_months": 0, "fatigue_cost": "low_moderate"},
    "explosive_compensatory": {"min_tier": "yellow", "min_training_age_months": 0, "fatigue_cost": "low_moderate", "requires_clean_technique_baseline": True},
}

TIER_ORDER = {"orange": 0, "yellow": 1, "green": 2}

# Section 5 -- confidence scoring constants
CONFIDENCE_BASE = 50
CONFIDENCE_EVIDENCE_BONUS = {"high": 20, "moderate": 10, "low_theoretical": 0}
CONFIDENCE_COMPLETENESS_BONUS = 15   # if >= 90%
CONFIDENCE_COMPLETENESS_PENALTY = -15  # if < 60%
CONFIDENCE_NO_CONFLICT_BONUS = 10
CONFIDENCE_SAFETY_OVERLAP_PENALTY = -25
CONFIDENCE_TIER_PENALTY = {"yellow": -10, "orange": -25, "green": 0}
CONFIDENCE_CAP = 99
CONFIDENCE_FLOOR = 0
