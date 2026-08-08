import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.fatigue import (
    RecoveryInputs, FatigueIndicatorReport, DeloadDecision, ClientRecoveryState,
    sleep_impact, protein_target_g_per_kg, hydration_target_ml,
    training_age_band, scheduled_deload_due, check_reactive_deload_triggers, decide_deload,
    deload_method_protocol, standard_deload_week, evaluate_fatigue_indicators,
    recovery_quality_tier, recovery_quality_adjustment, age_recovery_note,
    stress_training_adjustment, handle_missed_deload_overreach, deload_frequency_anxiety_check,
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

# --- sleep impact ---
check("under 6h sleep impairs recovery", "impaired" in sleep_impact(5)["impact"])
check("8-9h optimal", sleep_impact(8.5)["impact"] == "optimal_for_most_adults")
check("9h+ sudden increase flags overreach screen",
      sleep_impact(10, sudden_increase_from_baseline=True).get("flag") == "screen_for_overreaching_or_illness")
check("9h+ without sudden increase no flag",
      "flag" not in sleep_impact(10, sudden_increase_from_baseline=False))

# --- nutrition ---
check("standard protein range 1.6-2.2", protein_target_g_per_kg() == (1.6, 2.2))
check("fat loss protein range higher 2.0-2.6", protein_target_g_per_kg(in_fat_loss_phase=True) == (2.0, 2.6))
lo, hi = hydration_target_ml(80)
check("hydration scales with bodyweight", (lo, hi) == (2400, 3200))

# --- training age band ---
check("under 2yr = beginner", training_age_band(1) == "beginner")
check("2-5yr = intermediate", training_age_band(3) == "intermediate")
check("5+yr = advanced", training_age_band(6) == "advanced")

# --- scheduled deload ---
check("beginner deload due at 8+ weeks", scheduled_deload_due(1, 8) is True)
check("beginner not due at 5 weeks", scheduled_deload_due(1, 5) is False)
check("advanced due sooner (4-6wk band)", scheduled_deload_due(6, 4) is True)

# --- reactive triggers ---
triggered = check_reactive_deload_triggers(["performance_drop", "not_a_real_trigger"])
check("only real triggers matched", len(triggered) == 1)
check("matched trigger is performance_drop", triggered[0]["trigger"] == "performance_drop")

# --- decide_deload: priority order matters ---
cs = ClientRecoveryState(training_age_years=3, weeks_since_last_deload=1)
check("illness always wins regardless of anything else",
      decide_deload(cs, illness_active=True).method == "complete_rest")
check("severe burnout -> complete rest",
      decide_deload(cs, severe_burnout=True).method == "complete_rest")
check("reactive trigger with joint/cns fatigue -> intensity deload",
      decide_deload(cs, active_reactive_signals=["joint_pain"], joint_or_cns_fatigue_primary=True).method == "intensity_deload")
check("reactive trigger with mental burnout -> active recovery",
      decide_deload(cs, active_reactive_signals=["motivation_mood"], mental_burnout=True).method == "active_recovery")
check("reactive trigger default -> combined deload",
      decide_deload(cs, active_reactive_signals=["soreness"]).method == "combined_deload")
check("no reactive, not yet scheduled -> no deload needed",
      decide_deload(cs).deload_needed is False)
cs_due = ClientRecoveryState(training_age_years=1, weeks_since_last_deload=10)
check("scheduled deload fires when nothing else does",
      decide_deload(cs_due).reason == "scheduled_deload_due")

# --- deload method protocols ---
check("volume deload protocol correct", "40_50pct" in deload_method_protocol("volume_deload")["protocol"])
try:
    deload_method_protocol("not_a_method")
    check("unknown method raises", False)
except ValueError:
    check("unknown method raises", True)

# --- standard deload week math ---
week = standard_deload_week(current_sets=20, current_load_kg=100)
check("sets cut 40pct", week["sets"] == 12)
check("load range reflects 10-20pct reduction", week["load_range_kg"] == (80.0, 90.0))
check("no intensity techniques during deload", week["intensity_techniques_permitted"] is False)

# --- fatigue indicators ---
normal_report = FatigueIndicatorReport()
check("no signals -> normal status", evaluate_fatigue_indicators(normal_report)["overall_status"] == "normal")

one_signal = FatigueIndicatorReport(motivation_persistent_dread=True)
check("1 signal -> monitor status", evaluate_fatigue_indicators(one_signal)["overall_status"] == "monitor")

two_signals = FatigueIndicatorReport(motivation_persistent_dread=True, soreness_days=5)
result = evaluate_fatigue_indicators(two_signals)
check("2+ signals -> overreaching_signals_present", result["overall_status"] == "overreaching_signals_present")
check("soreness_pattern correctly flagged at 5 days (>=4 threshold)", "soreness_pattern" in result["warning_indicators"])

hr_report = FatigueIndicatorReport(resting_hr_elevated_bpm=6)
check("resting HR +6bpm crosses 5bpm warning threshold",
      "resting_heart_rate" in evaluate_fatigue_indicators(hr_report)["warning_indicators"])
hr_report_ok = FatigueIndicatorReport(resting_hr_elevated_bpm=3)
check("resting HR +3bpm stays under threshold",
      "resting_heart_rate" not in evaluate_fatigue_indicators(hr_report_ok)["warning_indicators"])

# --- recovery quality tiers ---
check("poor sleep alone -> poor tier", recovery_quality_tier(5, "low", True) == "poor")
check("high stress alone -> poor tier even with good sleep", recovery_quality_tier(8, "high", True) == "poor")
check("everything good -> excellent tier", recovery_quality_tier(8.5, "low", True) == "excellent")
check("mixed/moderate -> average tier", recovery_quality_tier(7.5, "moderate", True) == "average")

check("poor tier caps volume near MEV", "mev" in recovery_quality_adjustment("poor")["adjustment"])
try:
    recovery_quality_adjustment("bad_tier_name")
    check("unknown tier raises", False)
except ValueError:
    check("unknown tier raises", True)

# --- age notes ---
check("40-50 note mandates deload every 4-6wk even intermediate",
      "deload_every_4_6wk" in age_recovery_note("40_50"))
try:
    age_recovery_note("not_an_age_group")
    check("unknown age group raises", False)
except ValueError:
    check("unknown age group raises", True)

# --- stress adjustment ---
check("high stress reduces volume/intensity", "reduce_volume_intensity" in stress_training_adjustment("high")["adjustment"])

# --- troubleshooting helpers ---
check("overdue deload triggers immediate rest + MEV ramp",
      handle_missed_deload_overreach(2)["action"] == "immediate_deload_or_complete_rest_3_7_days")
check("not overdue -> no action", handle_missed_deload_overreach(0)["action"] == "none_needed")

check("deloading every 2-3wk flagged as anxiety-driven",
      deload_frequency_anxiety_check(2)["flag"] == "deloading_too_frequently_out_of_anxiety")
check("normal deload cadence -> no flag", deload_frequency_anxiety_check(6)["flag"] == "none")

print(f"\n{passed} passed, {failed} failed")
if failed:
    raise SystemExit(1)
