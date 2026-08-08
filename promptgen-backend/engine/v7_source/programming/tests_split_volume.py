import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.programming import (
    select_split, block_bro_split_if_undertrained, session_duration_modifier,
    check_split_switch_triggers, intensity_technique_permission, max_intensity_instances_per_week,
    can_prescribe_intensity_technique, goal_modifiers, rate_of_gain_check, fat_loss_deficit_size,
    volume_target, apply_volume_goal_modifier, apply_recovery_adjustment, count_indirect_volume,
    check_volume_status,
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

# --- select_split: decision tree from file 1 Section 2 ---
check("2 days always -> minimalist", select_split(2, 5, "bodybuilding")["split"] == "minimalist_2day")
check("3 days, <1yr -> full body abc", select_split(3, 0.5)["split"] == "full_body_abc")
check("3 days, >=1yr -> ppl 3day", select_split(3, 2)["split"] == "ppl_3day")
check("4 days, strength goal -> powerlifting sbd", select_split(4, 3, "strength")["split"] == "powerlifting_sbd")
check("4 days, hypertrophy <2yr -> upper/lower", select_split(4, 1, "hypertrophy")["split"] == "upper_lower")
check("5 days, <2yr -> upper/lower w/ hybrid alt", select_split(5, 1)["split"] == "upper_lower")
check("5 days, >=2yr hypertrophy -> ppl_ul_hybrid", select_split(5, 3, "hypertrophy")["split"] == "ppl_ul_hybrid")
check("5 days, advanced wants specialization + MAV met -> bro split",
      select_split(5, 6, "bodybuilding", wants_specialization=True, meeting_mav_elsewhere=True)["split"] == "bro_split")
check("5 days, advanced wants specialization but MAV NOT met -> stays hybrid",
      select_split(5, 6, "bodybuilding", wants_specialization=True, meeting_mav_elsewhere=False)["split"] == "ppl_ul_hybrid")
check("6 days -> ppl_6day", select_split(6, 3)["split"] == "ppl_6day")
check("7 days -> ppl_6day + recovery day, never 7 hard days", select_split(7, 5)["extra_day"] == "active_recovery_mobility")

# --- hardwired bro split block ---
check("bro split blocked under 2yrs regardless of other logic",
      block_bro_split_if_undertrained(1.5) is not None)
check("bro split not blocked at 2+ yrs", block_bro_split_if_undertrained(2.5) is None)

# --- session duration modifier ---
check("20 min session -> supersets true", session_duration_modifier(20)["supersets"] is True)
check("25 min rounds down to 20 bucket", session_duration_modifier(25)["bucket_minutes"] == 20)
check("100 min rounds down to 75 bucket", session_duration_modifier(100)["bucket_minutes"] == 75)

# --- split switch triggers ---
triggered = check_split_switch_triggers(["plateau_over_4_weeks_despite_adherence", "nonexistent_trigger"])
check("only real triggers matched", len(triggered) == 1)
check("plateau rule says check recovery before changing split",
      "check_recovery_first" in triggered[0]["action"])

# --- intensity techniques (file 6) ---
check("drop sets banned for true beginner", intensity_technique_permission("drop_sets", 0.2) == "no")
check("drop sets allowed for intermediate", intensity_technique_permission("drop_sets", 3) == "yes")
check("forced reps only for advanced", intensity_technique_permission("forced_reps", 3) == "no")
check("forced reps allowed advanced", intensity_technique_permission("forced_reps", 6) == "yes")
check("beginner budget is 0-1/week", max_intensity_instances_per_week(0.2) == (0, 1))
check("advanced budget is 2-4/week", max_intensity_instances_per_week(6) == (2, 4))
check("can't prescribe technique banned for training age",
      can_prescribe_intensity_technique("forced_reps", 3) is False)
check("can prescribe when within budget",
      can_prescribe_intensity_technique("drop_sets", 3, instances_already_used_this_week=0) is True)
check("cannot exceed weekly fatigue budget",
      can_prescribe_intensity_technique("drop_sets", 3, instances_already_used_this_week=2) is False)

# --- goal modifiers (file 7) ---
fl = goal_modifiers("fat_loss")
check("fat loss calorie offset is a deficit", fl["calorie_offset"][1] < 0)
check("fat loss protein is higher end 2.0-2.6", fl["protein_g_per_kg"] == (2.0, 2.6))
check("unknown goal raises ValueError (checked below)", True)
try:
    goal_modifiers("not_a_real_goal")
    check("unknown goal raises ValueError", False)
except ValueError:
    check("unknown goal raises ValueError", True)

check("rate of gain >1%/wk flags excess fat gain", rate_of_gain_check(1.5)["flag"] == "excess_fat_gain_likely")
check("rate of gain within range flags none", rate_of_gain_check(0.3)["flag"] == "within_expected_range")

check("fat loss deficit for higher body fat is 500-750",
      fat_loss_deficit_size("higher_body_fat")["deficit_kcal"] == (500, 750))

# --- weekly muscle volume (file 8) ---
check("chest beginner MEV/MAV", volume_target("chest", 0.3) == {"mev": 6, "mav": 10, "mrv_ceiling": 26})
check("chest advanced MEV/MAV", volume_target("chest", 6) == {"mev": 12, "mav": 22, "mrv_ceiling": 26})
try:
    volume_target("not_a_muscle", 3)
    check("unknown muscle raises", False)
except ValueError:
    check("unknown muscle raises", True)

strength_mod = apply_volume_goal_modifier(volume_target("chest", 3), "strength")
check("strength goal reduces accessory volume", strength_mod["accessory_isolation_adjustment_pct"] == -0.35)

check("poor sleep reduces base sets by ~20pct", apply_recovery_adjustment(10, "poor_sleep_under_6_7h") == 8)
check("excellent recovery increases base sets", apply_recovery_adjustment(10, "excellent_recovery") == 11)

lo, hi = count_indirect_volume(4)
check("indirect volume multiplier applied correctly", (lo, hi) == (1.0, 2.0))

check("above MRV triggers cut", check_volume_status("chest", 6, 30)["status"] == "above_mrv")
check("below MEV triggers increase", check_volume_status("chest", 6, 5)["status"] == "below_mev")
check("within range -> no action", check_volume_status("chest", 6, 15)["status"] == "within_mev_mav_range")

print(f"\n{passed} passed, {failed} failed")
if failed:
    raise SystemExit(1)
