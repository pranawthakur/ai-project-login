import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.programming import (
    classify_training_level, beginner_split_for_days, beginner_volume_for, beginner_load_increment,
    beginner_progression_check, beginner_deload_due, cardio_zone_for_hr_pct, cardio_zone_info,
    prescribe_cardio, hiit_protocol, hiit_eligibility, interference_check, cardio_volume_ceiling,
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

# --- classification ---
check("months/years progress -> advanced regardless of other markers",
      classify_training_level(True, "good", "months_years") == "advanced")
check("stalled + accurate RIR -> intermediate",
      classify_training_level(True, "reasonable", "weeks") == "intermediate")
check("not stalled, poor RIR -> beginner",
      classify_training_level(False, "poor", "weeks") == "beginner")

# --- beginner split by days ---
check("2 days -> full body AB minimum dose", beginner_split_for_days(2)["split"] == "full_body_ab")
check("3 days -> full body ABC gold standard", beginner_split_for_days(3)["split"] == "full_body_abc")
check("5+ days not recommended for true beginners, cap at 4", beginner_split_for_days(6)["split"] == "not_recommended")

# --- beginner volume ---
check("chest beginner volume 6-10", beginner_volume_for("chest") == (6, 10))
try:
    beginner_volume_for("not_a_muscle")
    check("unknown muscle raises", False)
except ValueError:
    check("unknown muscle raises", True)

# --- load increments ---
check("upper body increment 2.5kg", beginner_load_increment("upper_body") == 2.5)
check("lower body increment 5kg", beginner_load_increment("lower_body") == 5.0)

# --- progression stall rule ---
check("1 failed session -> keep linear", beginner_progression_check(1) == "continue_linear_progression")
check("2 consecutive failed sessions -> switch to double progression",
      beginner_progression_check(2) == "switch_to_double_progression")

# --- deload timing ---
check("8+ weeks since deload -> due", beginner_deload_due(9) is True)
check("under 8 weeks, no stall signals -> not due", beginner_deload_due(5, 0, False) is False)
check("under 8 weeks but 3+ lifts stalled + fatigue signs -> due early",
      beginner_deload_due(5, 3, True) is True)

# --- cardio zones ---
check("65% HRmax falls in zone 2", cardio_zone_for_hr_pct(65) == 2)
check("95% HRmax falls in zone 5", cardio_zone_for_hr_pct(95) == 5)
check("zone 2 info matches aerobic base use", cardio_zone_info(2)["use"] == "aerobic_base_fat_oxidation")

# --- cardio prescription ---
fl_cardio = prescribe_cardio("fat_loss")
check("fat loss cardio sessions 3-4", fl_cardio["sessions"] == (3, 4))
hyp_cardio = prescribe_cardio("hypertrophy")
check("hypertrophy cardio minimal, interference note present", "minimize_interference" in hyp_cardio["note"])

low_rec = prescribe_cardio("fat_loss", recovery_score="low")
check("low recovery score halves interval volume", low_rec["interval_hiit_volume_reduction_pct"] == 50)

beta = prescribe_cardio("fat_loss", on_beta_blockers=True)
check("beta blockers force RPE/talk-test instead of HR zones", beta["hr_zone_reliable"] is False)

try:
    prescribe_cardio("not_a_goal")
    check("unknown cardio goal raises", False)
except ValueError:
    check("unknown cardio goal raises", True)

# --- HIIT ---
tabata = hiit_protocol("classic_tabata")
check("tabata work:rest 20s:10s", tabata["work_rest"] == "20s:10s")

check("green tier no cv flags -> HIIT allowed",
      hiit_eligibility("green", False)["hiit_allowed"] is True)
check("yellow tier -> HIIT blocked, defaults zone2",
      hiit_eligibility("yellow", False)["hiit_allowed"] is False)
check("green tier but unresolved cv flag -> HIIT blocked",
      hiit_eligibility("green", True)["hiit_allowed"] is False)

# --- interference rule ---
check("cardio-first for hypertrophy goal (non-warmup) flags violation",
      interference_check("hypertrophy", cardio_session_is_first=True)["violation"] is not None)
check("cardio-first as short zone1 warmup is fine",
      interference_check("hypertrophy", cardio_session_is_first=True, cardio_duration_is_warmup_le_10min=True)["violation"] is None)
check("cardio-first fine when cardio IS the primary goal",
      interference_check("endurance_performance", cardio_session_is_first=True)["violation"] is None)

lo, hi = cardio_volume_ceiling(180)
check("cardio volume ceiling 150-200pct of resistance minutes", (lo, hi) == (270.0, 360.0))

print(f"\n{passed} passed, {failed} failed")
if failed:
    raise SystemExit(1)
