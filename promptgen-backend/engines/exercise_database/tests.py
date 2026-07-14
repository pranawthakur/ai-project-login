"""app/engines/exercise_database/tests.py — run directly: python3 tests.py"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.exercise_database.lookup_tables import EXERCISES, PATTERN_WEEKLY_MINIMUMS
from engines.exercise_database.models import MovementPattern
from engines.exercise_database.rules import equipment_substitute, injury_substitute, classify_tier, weekly_pattern_coverage_met
from engines.exercise_database.algorithms import select_exercise_for_slot, compute_confidence
from engines.exercise_database.validators import validate_exercise

passed = 0
failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {name}")


# ── pinned to file 16 §2.1/§3.1/§4.1 literal values ─────────────────────────
check("sq_001 sfr_score == 1.0 per file 16 §2.1", EXERCISES["sq_001"].sfr_score == 1.0)
check("hg_001 joint_stress.lower_back == 3 (highest) per file 16 §3.1", EXERCISES["hg_001"].joint_stress.lower_back == 3)
check("hp_001 fatigue_rating == 3 per file 16 §4.1", EXERCISES["hp_001"].fatigue_rating == 3)
check("all 5 KB worked examples present", set(EXERCISES.keys()) == {"sq_001", "hg_001", "hp_001", "vp_001", "hpl_001"})

# ── every populated Exercise record passes its own validator ───────────────
all_errors = [e for ex in EXERCISES.values() for e in validate_exercise(ex)]
check("no validation errors across populated exercises", all_errors == [])

# ── file 9 §2 pattern minimums ───────────────────────────────────────────────
check("squat minimum weekly touches == 2 per file 9 §2", PATTERN_WEEKLY_MINIMUMS[MovementPattern.SQUAT] == (2, None))
check("vertical push minimum == 1-2 per file 9 §2", PATTERN_WEEKLY_MINIMUMS[MovementPattern.VERTICAL_PUSH] == (1, 2))
check("3 touches meets squat 2+ minimum", weekly_pattern_coverage_met(MovementPattern.SQUAT, 3))
check("1 touch fails squat 2+ minimum", not weekly_pattern_coverage_met(MovementPattern.SQUAT, 1))

# ── file 9 §4/§5 substitution ─────────────────────────────────────────────────
check("Back Squat dumbbell sub per file 9 §4", equipment_substitute("Back Squat", "dumbbell") == "Goblet Squat / DB Split Squat")
check("unknown exercise substitute returns None", equipment_substitute("Nonexistent Lift", "dumbbell") is None)
check("lower back flare-up substitution per file 9 §5", injury_substitute("lower_back_pain_flareup")["substitute"][0] == "Trap Bar Deadlift")

# ── file 9 §1 classification ─────────────────────────────────────────────────
check("Back Squat classifies as primary per file 9 §1", classify_tier("Back Squat").value == "primary")
check("Leg Extension classifies as isolation per file 9 §1", classify_tier("Leg Extension").value == "isolation")

# ── file 16 §12 selection algorithm — using the KB's own §12.1 example trace ──
result = select_exercise_for_slot(
    pattern=MovementPattern.SQUAT,
    available_equipment=set(),                    # client has no barbell/rack per the example
    mobility_flags={"ankle_mobility_limited"},
    confidence_tier="green",
    months_trained=1,
)
# sq_001 (Barbell Back Squat) requires barbell+rack, which this client doesn't have,
# so it must be filtered out entirely — this matches KB §12.1's stated exclusion
# of Box Squat/Leg Press for the same equipment reason.
check("barbell squat correctly excluded when no equipment available", result is None)

result2 = select_exercise_for_slot(
    pattern=MovementPattern.SQUAT,
    available_equipment={"barbell", "squat_rack"},
    mobility_flags=set(),
    confidence_tier="green",
    months_trained=6,
)
check("with equipment available, sq_001 is selected", result2 is not None and result2.exercise_id == "sq_001")
check("confidence formula: 70 base + 15 high-evidence + 10 equipment-match = 95", result2.confidence == 95)

# ── orange tier caps difficulty at 2 per file 16 §12 ─────────────────────────
result3 = select_exercise_for_slot(
    pattern=MovementPattern.SQUAT,
    available_equipment={"barbell", "squat_rack"},
    mobility_flags=set(),
    confidence_tier="orange",
    months_trained=6,
)
check("orange tier excludes sq_001 (difficulty 4 > cap of 2)", result3 is None)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
