import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.biomechanics import (
    MovementPattern, Plane, ForceVector, Bilaterality, ChainType,
    FunctionalCategory, ComplexityTier, MovementRecord,
    is_push_pattern, is_pull_pattern, is_lower_body_pattern, is_core_pattern,
    opposing_pattern, default_functional_category, apply_pattern_defaults,
    is_ready_for_classification, pattern_coverage_gaps, complexity_at_least,
    pattern_similarity, rank_by_pattern_similarity,
    validate_movement_pattern, validate_movement_record_required_fields,
    validate_pattern_list,
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

# --- taxonomy classification ---
check("horizontal push is a push pattern", is_push_pattern(MovementPattern.HORIZONTAL_PUSH))
check("horizontal pull is not a push pattern", not is_push_pattern(MovementPattern.HORIZONTAL_PULL))
check("horizontal pull is a pull pattern", is_pull_pattern(MovementPattern.HORIZONTAL_PULL))
check("squat is lower body", is_lower_body_pattern(MovementPattern.SQUAT))
check("carry is not lower body", not is_lower_body_pattern(MovementPattern.CARRY))
check("rotation is a core pattern", is_core_pattern(MovementPattern.ROTATION))

# --- opposing_pattern ---
check("horizontal push <-> horizontal pull",
      opposing_pattern(MovementPattern.HORIZONTAL_PUSH) == MovementPattern.HORIZONTAL_PULL)
check("squat <-> hip hinge", opposing_pattern(MovementPattern.SQUAT) == MovementPattern.HIP_HINGE)
check("carry has no defined pair", opposing_pattern(MovementPattern.CARRY) is None)

# --- default_functional_category ---
check("squat defaults to knee_dominant",
      default_functional_category(MovementPattern.SQUAT) == FunctionalCategory.KNEE_DOMINANT)
check("hip hinge defaults to hip_dominant",
      default_functional_category(MovementPattern.HIP_HINGE) == FunctionalCategory.HIP_DOMINANT)

# --- apply_pattern_defaults ---
bare_record = MovementRecord(
    exercise_id="sq_001", movement_pattern=MovementPattern.SQUAT, primary_movement="knee/hip extension"
)
filled = apply_pattern_defaults(bare_record)
check("apply_pattern_defaults fills plane_of_motion", filled.plane_of_motion == Plane.SAGITTAL)
check("apply_pattern_defaults fills chain_type", filled.chain_type == ChainType.CLOSED)
check("apply_pattern_defaults does not mutate original", bare_record.plane_of_motion is None)

curated_record = MovementRecord(
    exercise_id="sq_002",
    movement_pattern=MovementPattern.SQUAT,
    primary_movement="knee/hip extension",
    chain_type=ChainType.OPEN,  # e.g. a leg-extension-style variation, overriding the pattern default
)
filled_curated = apply_pattern_defaults(curated_record)
check("apply_pattern_defaults never overwrites a curated field",
      filled_curated.chain_type == ChainType.OPEN)

# --- is_ready_for_classification ---
check("bare record not ready (no functional_category yet)",
      not is_ready_for_classification(bare_record))
check("pattern-defaulted record is ready", is_ready_for_classification(filled))

# --- pattern_coverage_gaps ---
gaps = pattern_coverage_gaps([MovementPattern.SQUAT, MovementPattern.HORIZONTAL_PUSH])
check("coverage gaps excludes patterns used", MovementPattern.SQUAT not in gaps)
check("coverage gaps includes patterns not used", MovementPattern.HIP_HINGE in gaps)
check("coverage gaps has 8 missing of 10", len(gaps) == 8)

# --- complexity_at_least ---
check("unset complexity is never >= any tier", not complexity_at_least(bare_record, ComplexityTier.LOW))
high_complexity = MovementRecord(
    exercise_id="hg_001", movement_pattern=MovementPattern.HIP_HINGE,
    primary_movement="hip extension", complexity=ComplexityTier.HIGH,
)
check("HIGH complexity >= LOW", complexity_at_least(high_complexity, ComplexityTier.LOW))
check("HIGH complexity >= HIGH", complexity_at_least(high_complexity, ComplexityTier.HIGH))

# --- pattern_similarity / rank_by_pattern_similarity ---
squat_a = apply_pattern_defaults(MovementRecord(
    exercise_id="sq_a", movement_pattern=MovementPattern.SQUAT, primary_movement="knee/hip extension"))
squat_b = apply_pattern_defaults(MovementRecord(
    exercise_id="sq_b", movement_pattern=MovementPattern.SQUAT, primary_movement="knee/hip extension"))
lunge = apply_pattern_defaults(MovementRecord(
    exercise_id="lg_a", movement_pattern=MovementPattern.LUNGE, primary_movement="knee/hip extension"))
row = apply_pattern_defaults(MovementRecord(
    exercise_id="row_a", movement_pattern=MovementPattern.HORIZONTAL_PULL, primary_movement="elbow flexion/scapular retraction"))

check("same pattern scores 1.0", pattern_similarity(squat_a, squat_b) == 1.0)
check("squat vs lunge share knee_dominant category -> 0.5",
      pattern_similarity(squat_a, lunge) == 0.5)
check("squat vs horizontal pull unrelated -> 0.0", pattern_similarity(squat_a, row) == 0.0)

ranked = rank_by_pattern_similarity(squat_a, [squat_b, lunge, row])
check("ranked excludes target itself", all(r[0].exercise_id != "sq_a" for r in ranked))
check("ranked is descending", ranked[0][1] >= ranked[1][1] >= ranked[2][1])
check("exact pattern match ranks first", ranked[0][0].exercise_id == "sq_b")

# --- validators ---
check("validate_movement_pattern accepts valid string",
      validate_movement_pattern("squat") == MovementPattern.SQUAT)
try:
    validate_movement_pattern("bench_press")
    check("validate_movement_pattern rejects invalid value", False)
except ValueError:
    check("validate_movement_pattern rejects invalid value", True)

errors = validate_movement_record_required_fields(
    MovementRecord(exercise_id="", movement_pattern=MovementPattern.SQUAT, primary_movement="")
)
check("required-field validator flags missing exercise_id", any("exercise_id" in e for e in errors))
check("required-field validator flags missing primary_movement",
      any("primary_movement" in e for e in errors))

check("validate_pattern_list coerces a list", validate_pattern_list(["squat", "lunge"]) ==
      [MovementPattern.SQUAT, MovementPattern.LUNGE])

print(f"\n{passed} passed, {failed} failed")
if failed:
    sys.exit(1)
