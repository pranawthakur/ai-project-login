import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.programming import (
    sets_reps_for_goal, rir_band_for_age, rir_guidelines, rpe_to_rir, true_failure_allowed,
    tempo_for_goal, rest_for_exercise_type, progression_model_for, linear_progression_end_condition,
    failure_policy, plateau_decision_tree, recovery_quality_adjustment, sleep_adjustment,
    stress_adjustment, age_programming_note,
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

# --- sets/reps by goal ---
check("strength rep range 1-6", sets_reps_for_goal("strength")["rep_range"] == (1, 6))
check("hypertrophy effective range 5-30", sets_reps_for_goal("hypertrophy")["effective_range"] == (5, 30))
try:
    sets_reps_for_goal("nonsense")
    check("unknown goal raises", False)
except ValueError:
    check("unknown goal raises", True)

# --- RIR by training age ---
check("true beginner RIR band", rir_band_for_age(0.2) == "beginner")
check("5+ yr -> advanced band", rir_band_for_age(6) == "advanced")
check("beginner avoids failure entirely", rir_guidelines(0.2)["failure_frequency"] == "avoid_entirely")
check("advanced uses programmed failure tools", "forced_reps" in rir_guidelines(6)["failure_frequency"])

# --- RPE <-> RIR ---
check("RPE 10 = 0 RIR", rpe_to_rir(10) == 0)
check("RPE 8 = 2 RIR", rpe_to_rir(8) == 2)
check("RPE <=5 = 5+ RIR (warmup territory)", rpe_to_rir(4) == 5.0)
check("RPE 8.5 interpolates between 8 and 9", 1 < rpe_to_rir(8.5) < 2)

# --- true failure safety rule ---
check("unspotted free-weight compound never allows true failure",
      true_failure_allowed("unspotted_free_weight_compound") is False)
check("spotted compound allows failure only with spotter confirmed",
      true_failure_allowed("spotted_free_weight_compound", has_spotter_or_safety=True) is True)
check("spotted compound without spotter confirmed disallows failure",
      true_failure_allowed("spotted_free_weight_compound", has_spotter_or_safety=False) is False)
check("machine/isolation allows failure", true_failure_allowed("machine_isolation") is True)

# --- tempo / rest ---
check("general hypertrophy tempo", tempo_for_goal("general_hypertrophy") == "2-0-1-0")
check("heavy compound rest 3-5min", rest_for_exercise_type("heavy_compound_ge_85pct") == (180, 300))

# --- progression models ---
check("true beginner -> linear", progression_model_for(0.2) == "linear")
check("0.5-5yr no plateau -> double progression", progression_model_for(2) == "double_progression")
check("plateaued -> undulating DUP", progression_model_for(3, plateaued_on_current_model=True) == "undulating_dup")
check("2 failed linear attempts -> move to double progression",
      linear_progression_end_condition(2) == "move_to_double_progression")
check("1 failed attempt -> no transition yet", linear_progression_end_condition(1) is None)

# --- failure policy ---
check("beginner never trains to failure", failure_policy(0.2, "compound") == "avoid_stop_3plus_reps_shy")
check("intermediate compound: rare, spotter only", failure_policy(3, "compound") == "rare_only_last_set_with_spotter")
check("advanced isolation: common with forced reps/drop sets",
      failure_policy(6, "isolation") == "common_including_forced_reps_and_drop_sets")
check("fatigue/illness overrides everything regardless of training age",
      failure_policy(6, "isolation", fatigue_or_illness_or_poor_sleep=True) == "never_autoregulate_down_regardless_of_program")

# --- PLATEAU DECISION TREE (file 2 Section 7) -- exercised in strict branch order ---
check("less than 2 weeks stalled -> not a plateau yet",
      plateau_decision_tree(1, True, 8, False, 2, False, "within_range", 4)["result"] == "not_yet_a_plateau")
check("adherence broken -> fix adherence first (checked before recovery)",
      plateau_decision_tree(3, False, 4, True, 10, True, "below_mev", 12)["result"] == "adherence_issue")
check("adherence ok but poor sleep -> recovery issue (checked before nutrition)",
      plateau_decision_tree(3, True, 5, False, 2, True, "below_mev", 12)["result"] == "recovery_issue")
check("recovery ok but deload overdue (>8wk) -> still recovery issue",
      plateau_decision_tree(3, True, 8, False, 10, False, "within_range", 4)["result"] == "recovery_issue")
check("recovery fine, aggressive deficit -> nutrition mismatch (checked before volume)",
      plateau_decision_tree(3, True, 8, False, 2, True, "below_mev", 4)["result"] == "nutrition_mismatch")
check("all fine except below MEV -> increase volume",
      plateau_decision_tree(3, True, 8, False, 2, False, "below_mev", 4)["action"] == "increase_volume")
check("all fine except above MRV -> reduce volume",
      plateau_decision_tree(3, True, 8, False, 2, False, "above_mrv", 4)["action"] == "reduce_volume")
check("volume fine but same scheme >8wk -> rotate variation (checked before genuine plateau)",
      plateau_decision_tree(3, True, 8, False, 2, False, "within_range", 10)["result"] == "staleness")
check("everything ruled out -> genuine plateau, deload + new mesocycle",
      plateau_decision_tree(3, True, 8, False, 2, False, "within_range", 4)["result"] == "genuine_plateau")

# --- recovery/sleep/stress adjustments ---
check("poor recovery reduces volume and adds RIR",
      recovery_quality_adjustment("poor")["rir_addition"] == 1)
check("under 6h sleep avoids failure entirely",
      sleep_adjustment(5)["action"] == "reduce_intensity_avoid_failure_entirely")
check("8-9h+ sleep full capacity", sleep_adjustment(9)["action"] == "full_capacity_ideal_for_pushing_progression")
check("high stress treated like poor sleep", "reduce_volume_intensity" in stress_adjustment("high")["action"])

# --- age notes ---
check("teen note emphasizes technique before intensity",
      "emphasize_technique" in age_programming_note("teen"))
check("50+ note mentions more frequent deloads", "deload_every_4_6wk" in age_programming_note("50_plus"))

print(f"\n{passed} passed, {failed} failed")
if failed:
    raise SystemExit(1)
