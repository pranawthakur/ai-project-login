import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.progression import (
    ClientState, SplitRecommendation, ConfidenceFactors,
    select_split, smoothed_recovery_score, resolve_split_preference_conflict,
    recommend_periodization_model, vbt_eligible, velocity_loss_cutoff, contrast_method_eligible,
    set_structure_allowed, advanced_technique_request_from_yellow_tier,
    adjust_volume_within_landmarks, compute_recommendation_confidence, effective_training_age,
)

passed = 0
failed = 0

def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {name}")

# --- orange tier always -> safe template, 99 confidence ---
r = select_split(ClientState(confidence_tier="orange", days_available=4))
check("orange tier always routes to safe template", r.split == "DEFAULT_SAFE_TEMPLATE_full_body")
check("orange tier confidence is 99", r.confidence == 99)

# --- Section 1.1 Worked Example 1 (source's own test case) ---
# 3 days, poor recovery, hypertrophy, yellow tier -> should recommend full_body_x3, NOT ppl partial
ex1 = select_split(ClientState(days_available=3, recovery_score="poor", goal="hypertrophy", confidence_tier="yellow"))
check("worked example 1: full body x3 beats ppl partial under poor recovery", ex1.split == "full_body_x3")

# --- Section 1.1 Worked Example 2 ---
# 5 days, good recovery, strength, green tier, training_age>=24mo -> upper/lower + specialization favored
ex2 = select_split(ClientState(days_available=5, recovery_score="good", goal="strength", confidence_tier="green",
                                 training_age_months=30))
check("worked example 2: 5-day good-recovery green-tier strength client gets a 5-day candidate",
      ex2.split in ("upper_lower_plus_specialization", "ppl_plus_upper"))

# --- candidate generation sanity per day count ---
check("1 day -> full_body_minimal available",
      select_split(ClientState(days_available=1)).split == "full_body_minimal")
check("6 days good recovery green tier -> ppl_x2",
      select_split(ClientState(days_available=6, recovery_score="good", confidence_tier="green")).split == "ppl_x2")
check("6 days poor recovery -> falls back to upper_lower_x3, not ppl_x2",
      select_split(ClientState(days_available=6, recovery_score="poor", confidence_tier="green")).split == "upper_lower_x3")

# --- smoothed recovery (Section 7 troubleshooting fix) ---
check("mostly good trailing scores smooth to good",
      smoothed_recovery_score(["good", "good", "moderate"]) == "good")
check("mostly poor trailing scores smooth to poor",
      smoothed_recovery_score(["poor", "poor", "moderate"]) == "poor")
check("empty trailing scores default to moderate", smoothed_recovery_score([]) == "moderate")

# --- Section 6 edge case: preference vs scored recommendation ---
pref_result = resolve_split_preference_conflict("upper_lower_x2", "bro_split", safety_flag_conflict=False)
check("client preference wins when no safety conflict", pref_result["final_split"] == "bro_split")
check("preference override logged as client-initiated", pref_result["source"] == "client_initiated_override")

pref_blocked = resolve_split_preference_conflict("upper_lower_x2", "bro_split", safety_flag_conflict=True)
check("system recommendation wins when safety flag conflicts", pref_blocked["final_split"] == "upper_lower_x2")

# --- periodization model selection ---
check("under 12mo training age -> linear regardless of other factors",
      recommend_periodization_model(6, "green", frequency_per_pattern=3)["model"] == "linear")
check("green tier, 12mo+, freq>=2 -> undulating",
      recommend_periodization_model(15, "green", frequency_per_pattern=2)["model"] == "undulating")
check("powerlifter with peaking date, 24mo+ -> block",
      recommend_periodization_model(30, "yellow", goal="powerlifting", target_date_set=True)["model"] == "block")
check("36mo+ powerlifter with staleness -> conjugate_adjacent",
      recommend_periodization_model(40, "yellow", goal="powerlifting", reported_staleness=True)["model"] == "conjugate_adjacent")

# --- VBT ---
check("VBT eligible with tracker + 24mo+", vbt_eligible(["velocity_tracker"], 24) is True)
check("VBT not eligible without tracker", vbt_eligible([], 30) is False)
check("hypertrophy velocity cutoff 20-25pct", velocity_loss_cutoff("hypertrophy") == (20, 25))
check("strength velocity cutoff 10-15pct", velocity_loss_cutoff("strength") == (10, 15))

# --- contrast methods (Section 2.6 hard rule) ---
check("contrast training blocked for yellow tier even if all else qualifies",
      contrast_method_eligible("contrast_training", "athletic_performance", 30, "yellow") is False)
check("contrast training blocked with unresolved lower-limb injury flag",
      contrast_method_eligible("contrast_training", "athletic_performance", 30, "green", True) is False)
check("contrast training allowed: green tier, athletic performance, 24mo+, no injury flag",
      contrast_method_eligible("contrast_training", "athletic_performance", 30, "green", False) is True)
check("triphasic requires 36mo even at green tier", contrast_method_eligible("triphasic", "athletic_performance", 30, "green") is False)
check("triphasic allowed at 36mo+", contrast_method_eligible("triphasic", "athletic_performance", 40, "green") is True)

# --- Section 3 set-structure gating ---
check("myo-reps blocked for orange tier", set_structure_allowed("myo_reps", "orange", 12)["allowed"] is False)
check("myo-reps allowed for yellow tier", set_structure_allowed("myo_reps", "yellow", 12)["allowed"] is True)
check("cluster sets need 6mo+ training age even at green tier",
      set_structure_allowed("cluster_sets", "green", 3)["allowed"] is False)
check("cluster sets allowed at 6mo+ green tier", set_structure_allowed("cluster_sets", "green", 6)["allowed"] is True)
check("forced reps blocked solo without spotter",
      set_structure_allowed("forced_reps", "green", 24, solo_no_spotter=True)["allowed"] is False)
check("forced reps solo flag names unsupervised_max_effort_risk",
      set_structure_allowed("forced_reps", "green", 24, solo_no_spotter=True).get("flag") == "unsupervised_max_effort_risk")
check("BFR blocked with unresolved vascular flag + no clearance",
      set_structure_allowed("bfr_occlusion", "yellow", 12, vascular_clotting_flag=True,
                              medical_clearance_resolved=False)["allowed"] is False)
check("BFR allowed with vascular flag if clearance resolved",
      set_structure_allowed("bfr_occlusion", "yellow", 12, vascular_clotting_flag=True,
                              medical_clearance_resolved=True)["allowed"] is True)
check("unknown technique defaults to not allowed",
      set_structure_allowed("made_up_technique", "green", 60)["allowed"] is False)

# --- Section 6: yellow-tier client requests gated technique by name ---
req = advanced_technique_request_from_yellow_tier("drop_sets", "yellow", 12)
check("yellow tier requesting green-only technique gets alternative, not the technique",
      req["action"] == "explain_gate_and_offer_alternative")
req2 = advanced_technique_request_from_yellow_tier("myo_reps", "yellow", 12)
check("yellow tier requesting yellow-eligible technique gets it granted",
      req2["action"] == "grant")

# --- Section 4 MEV/MAV/MRV integration ---
check("poor recovery pulls volume toward MEV",
      adjust_volume_within_landmarks(15, mev=8, mav=16, mrv=20, recovery_score="poor", weeks_since_deload=2)["action"] == "reduce_toward_mev")
check("moderate recovery 4+ weeks since deload holds, doesn't push",
      adjust_volume_within_landmarks(14, mev=8, mav=16, mrv=20, recovery_score="moderate", weeks_since_deload=5)["action"] == "hold_do_not_push_without_good_recovery")
check("good recovery under MAV increases by 1 set",
      adjust_volume_within_landmarks(10, mev=8, mav=16, mrv=20, recovery_score="good", weeks_since_deload=1)["new_volume"] == 11)
check("at or above MRV triggers deload flag",
      adjust_volume_within_landmarks(20, mev=8, mav=16, mrv=20, recovery_score="good", weeks_since_deload=1)["action"] == "trigger_deload_flag")

# --- Section 5 confidence scoring ---
high_conf = ConfidenceFactors(evidence_strength="high", client_data_completeness_pct=95, confidence_tier="green")
check("high evidence + complete data + green tier scores high (exact formula value)",
      compute_recommendation_confidence(high_conf) == 95)
exact = ConfidenceFactors(evidence_strength="high", client_data_completeness_pct=95, confidence_tier="green",
                            conflicting_flags_present=False, unresolved_safety_flag_overlap=False)
check("confidence formula computes exact expected value (95)", compute_recommendation_confidence(exact) == 95)
check("confidence never exceeds cap of 99 even with contrived extra-high inputs",
      compute_recommendation_confidence(ConfidenceFactors(evidence_strength="high", client_data_completeness_pct=100,
                                                             confidence_tier="green")) <= 99)
low_conf = ConfidenceFactors(evidence_strength="low_theoretical", client_data_completeness_pct=40,
                               confidence_tier="orange", unresolved_safety_flag_overlap=True)
check("low evidence + incomplete data + orange tier + safety overlap scores very low",
      compute_recommendation_confidence(low_conf) < 20)
check("confidence never goes below floor of 0",
      compute_recommendation_confidence(ConfidenceFactors(evidence_strength="low_theoretical",
                                                             client_data_completeness_pct=0, confidence_tier="orange",
                                                             unresolved_safety_flag_overlap=True,
                                                             conflicting_flags_present=True)) >= 0)

# --- Section 6: training age discrepancy resolution ---
check("movement-screen-derived training age wins over self-report",
      effective_training_age(36, 12) == 12)
check("falls back to self-report when no screen data available",
      effective_training_age(18, None) == 18)

print(f"\n{passed} passed, {failed} failed")
if failed:
    raise SystemExit(1)
