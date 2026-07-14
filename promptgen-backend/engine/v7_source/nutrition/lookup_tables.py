"""Deterministic data from KB V7 file 15 (Supplement Safety & Interaction
Engine) -- the sole real source for the `nutrition` module."""

TIER_1_SUPPLEMENTS = {
    "protein_powder": {
        "range": "contributes_to_daily_protein_target_per_file_2_7",
        "note": "position_as_food_gap_filler_not_mandatory_flag_lactose_intolerance_before_recommending_whey",
    },
    "creatine_monohydrate": {
        "range": "3-5g_day_ongoing_loading_phase_optional_not_required",
        "note": "consistent_daily_timing_mild_water_retention_expected_benign",
        "contraindication": "kidney_disease_disclosed_route_to_medical_clearance_required",
    },
    "caffeine": {
        "range": "pre_training_only_general_population_range",
        "note": "flag_if_anxiety_sleep_issues_or_hypertension_reduce_avoid_never_stack_undisclosed",
    },
    "electrolytes": {
        "range": "as_needed_with_heat_heavy_sweat_loss_or_fasted_training",
        "note": "straightforward_low_risk",
    },
    "vitamin_d": {
        "range": "only_with_disclosed_deficiency_or_limited_sun_exposure",
        "note": "recommend_testing_physician_guidance_rather_than_blind_supplementation",
    },
}

TIER_2_SUPPLEMENTS = {
    "multi_ingredient_preworkout": {
        "condition": "no_cardiovascular_anxiety_sleep_flags",
        "flag": "stacked_stimulants_never_recommend_alongside_separate_caffeine_without_total_dose_awareness",
    },
    "beta_alanine": {
        "condition": "endurance_or_high_rep_hypertrophy_goals",
        "flag": "harmless_paresthesia_tingling_expected_not_a_reaction_requiring_stopping",
    },
    "omega_3": {
        "condition": "general_health_or_joint_support_goals",
        "flag": "blood_thinners_bruising_bleeding_risk_recommend_physician_check",
    },
    "zma_magnesium_blend": {
        "condition": "sleep_support_goals_only",
        "flag": "avoid_stacking_other_magnesium_sources_gi_distress_risk",
    },
}

TIER_3_SUBSTANCES = {
    "fat_burner_thermogenic": {
        "behavior": "do_not_recommend_if_asked_general_caution_redirect_to_tier1_protein_deficit_activity",
    },
    "sarms_prohormones_research_chemicals": {
        "behavior": "do_not_recommend_no_dosing_under_any_framing_unregulated_unstudied_risk_recommend_physician",
    },
    "anabolic_androgenic_steroids": {
        "behavior": "no_dosing_cycling_pct_under_any_framing_including_harm_reduction",
        "if_disclosed": ["do_not_judge_or_refuse_basic_training_nutrition_support",
                          "flag_anabolic_use_disclosed", "recommend_physician_supervised_bloodwork",
                          "do_not_adjust_programming_for_assumed_enhanced_recovery_without_explicit_coach_override"],
    },
    "injectable_peptides": {
        "behavior": "same_as_steroids_no_dosing_protocol_flag_and_recommend_physician_oversight",
    },
    "proprietary_blend_mass_gainers": {
        "behavior": "caution_undisclosed_amounts_prevent_safe_interaction_checking_recommend_transparent_label_products",
    },
}

# Section 4 -- interaction matrix (supplement -> conflicting med/condition -> flag)
INTERACTION_MATRIX = {
    "creatine_monohydrate": {"kidney_disease": "medical_clearance_required"},
    "caffeine": {"hypertension": "stimulant_caution_reduce_avoid", "anxiety_disorder": "stimulant_caution_reduce_avoid",
                  "beta_blockers": "stimulant_caution_reduce_avoid"},
    "multi_ingredient_preworkout": {"hypertension": "stimulant_caution_reduce_avoid",
                                      "anxiety_disorder": "stimulant_caution_reduce_avoid",
                                      "beta_blockers": "stimulant_caution_reduce_avoid"},
    "omega_3": {"blood_thinners": "bruising_bleeding_risk_physician_check"},
    "high_dose_magnesium": {"kidney_disease": "avoid_without_physician_guidance"},
    "zma_magnesium_blend": {"kidney_disease": "avoid_without_physician_guidance"},
    "any_stimulant_containing_product": {"pregnancy": "avoid_entirely_per_file_12_section_4"},
}

# Section 5 -- GI distress fallback logic
GI_DISTRESS_RESPONSES = {
    "nausea_after_preworkout": "reduce_dose_50pct_or_split_dose_ensure_not_fasted_check_total_caffeine_across_stack",
    "bloating_after_protein_shake": "test_lactose_sensitivity_suggest_isolate_or_plant_based_alternative",
    "GI_upset_after_creatine": "split_5g_dose_into_2x2.5g_across_day_ensure_adequate_water_intake",
}
GI_MULTIPLE_SUPPLEMENTS_RESPONSE = "reintroduce_one_at_a_time_3_5_days_apart_to_isolate_cause"

# Section 8 -- edge cases
EDGE_CASE_STEROID_REQUEST_RESPONSE = "decline_protocol_give_physician_referral_response_restate_once_if_persists_redirect"
EDGE_CASE_MIDCYCLE_RESPONSE = {
    "do_not_adjust_volume_intensity_for_assumed_enhanced_recovery": True,
    "log_flag": "anabolic_use_disclosed",
    "offer": "standard_evidence_based_programming",
    "flag_for_coach_awareness": True,
}

CREATINE_LOADING_PHASE_REQUIRED = False  # FAQ: flat 3-5g daily maintenance, no loading phase needed
