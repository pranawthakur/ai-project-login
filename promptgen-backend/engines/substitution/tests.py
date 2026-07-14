import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.biomechanics import MovementPattern, MovementRecord
from engines.substitution import (
    ConflictType, ConflictSeverity, SessionExercise, ConflictFlag,
    detect_joint_stress_conflicts, detect_pattern_redundancy_conflicts,
    detect_equipment_conflicts, detect_all_conflicts, has_blocking_conflict,
    suggest_substitute,
    conflict_score, worst_severity, rank_sessions_by_conflict,
    validate_joint_stress_dict, validate_session_exercise, validate_session,
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

# --- detect_joint_stress_conflicts ---
session_ok = [
    SessionExercise("a", order=0, joint_stress={"shoulder": 3}),
    SessionExercise("b", order=1, joint_stress={"shoulder": 1}),
]
check("single high-stress hit is not a conflict", detect_joint_stress_conflicts(session_ok) == [])

session_stacked = [
    SessionExercise("a", order=0, joint_stress={"shoulder": 3}),
    SessionExercise("b", order=1, joint_stress={"shoulder": 3}),
]
flags = detect_joint_stress_conflicts(session_stacked)
check("two high-stress hits on same joint flagged", len(flags) == 1)
check("flag type is JOINT_STRESS_STACK", flags[0].conflict_type == ConflictType.JOINT_STRESS_STACK)
check("flag references both exercises", set(flags[0].exercise_ids) == {"a", "b"})
check("2 hits -> moderate severity", flags[0].severity == ConflictSeverity.MODERATE)

session_stacked3 = [
    SessionExercise("a", order=0, joint_stress={"lower_back": 3}),
    SessionExercise("b", order=1, joint_stress={"lower_back": 3}),
    SessionExercise("c", order=2, joint_stress={"lower_back": 3}),
]
flags3 = detect_joint_stress_conflicts(session_stacked3)
check("3 hits -> high severity", flags3[0].severity == ConflictSeverity.HIGH)

# --- detect_pattern_redundancy_conflicts ---
session_redundant = [
    SessionExercise("a", order=0, movement_pattern=MovementPattern.SQUAT),
    SessionExercise("b", order=1, movement_pattern=MovementPattern.SQUAT),
    SessionExercise("c", order=2, movement_pattern=MovementPattern.SQUAT),
]
pr_flags = detect_pattern_redundancy_conflicts(session_redundant)
check("3x same pattern flagged (max=2)", len(pr_flags) == 1)
check("redundancy flag has correct pattern", pr_flags[0].movement_pattern == MovementPattern.SQUAT)

session_not_redundant = [
    SessionExercise("a", order=0, movement_pattern=MovementPattern.SQUAT),
    SessionExercise("b", order=1, movement_pattern=MovementPattern.SQUAT),
]
check("2x same pattern not flagged", detect_pattern_redundancy_conflicts(session_not_redundant) == [])

check("None pattern ignored", detect_pattern_redundancy_conflicts(
    [SessionExercise("a", order=0), SessionExercise("b", order=1), SessionExercise("c", order=2)]
) == [])

# --- detect_equipment_conflicts ---
session_equip_conflict = [
    SessionExercise("a", order=0, equipment=("squat_rack",), time_slot=1),
    SessionExercise("b", order=1, equipment=("squat_rack",), time_slot=1),
]
eq_flags = detect_equipment_conflicts(session_equip_conflict)
check("shared equipment same slot flagged", len(eq_flags) == 1)
check("equipment conflict is HIGH severity", eq_flags[0].severity == ConflictSeverity.HIGH)
check("equipment conflict names the equipment", eq_flags[0].equipment == "squat_rack")

session_equip_ok_different_slots = [
    SessionExercise("a", order=0, equipment=("squat_rack",), time_slot=1),
    SessionExercise("b", order=1, equipment=("squat_rack",), time_slot=2),
]
check("shared equipment different slots not flagged",
      detect_equipment_conflicts(session_equip_ok_different_slots) == [])

session_equip_ok_default_slots = [
    SessionExercise("a", order=0, equipment=("bench",)),
    SessionExercise("b", order=1, equipment=("bench",)),
]
check("default time_slot (falls back to order) means no false pairing",
      detect_equipment_conflicts(session_equip_ok_default_slots) == [])

# --- detect_all_conflicts / has_blocking_conflict ---
combined_session = session_stacked + session_equip_conflict
all_flags = detect_all_conflicts(combined_session)
check("detect_all_conflicts aggregates multiple types",
      {f.conflict_type for f in all_flags} == {ConflictType.JOINT_STRESS_STACK, ConflictType.EQUIPMENT_CONTENTION})
check("blocking conflict present (equipment is HIGH)", has_blocking_conflict(combined_session))
check("no blocking conflict when only LOW/MODERATE present", not has_blocking_conflict(session_stacked))

# --- scoring ---
check("empty flags score 0", conflict_score([]) == 0)
check("conflict_score weights HIGH >> LOW", conflict_score(flags3) > conflict_score(flags))
check("worst_severity of empty is None", worst_severity([]) is None)
check("worst_severity picks HIGH over MODERATE", worst_severity(flags + eq_flags) == ConflictSeverity.HIGH)

ranked = rank_sessions_by_conflict({"clean": [], "stacked": flags3, "mild": flags})
check("rank_sessions_by_conflict orders ascending", [label for label, _ in ranked] == ["clean", "mild", "stacked"])

# --- suggest_substitute ---
target = MovementRecord(exercise_id="sq_a", movement_pattern=MovementPattern.SQUAT, primary_movement="knee/hip extension")
same_pattern = MovementRecord(exercise_id="sq_b", movement_pattern=MovementPattern.SQUAT, primary_movement="knee/hip extension")
conflicting_candidate = MovementRecord(exercise_id="a", movement_pattern=MovementPattern.SQUAT, primary_movement="knee/hip extension")
suggestions = suggest_substitute(target, [same_pattern, conflicting_candidate], session_stacked)
check("suggest_substitute excludes exercise_ids already flagged as conflicting",
      all(r.exercise_id != "a" for r, _ in suggestions))
check("suggest_substitute keeps non-conflicting candidates",
      any(r.exercise_id == "sq_b" for r, _ in suggestions))

excluded = suggest_substitute(target, [same_pattern], [], exclude_exercise_ids=frozenset({"sq_b"}))
check("suggest_substitute respects exclude_exercise_ids", excluded == [])

# --- validators ---
try:
    validate_joint_stress_dict({"shoulder": 5})
    check("validate_joint_stress_dict rejects out-of-range value", False)
except ValueError:
    check("validate_joint_stress_dict rejects out-of-range value", True)

check("validate_joint_stress_dict accepts valid dict",
      validate_joint_stress_dict({"shoulder": 2}) == {"shoulder": 2})

errs = validate_session_exercise(SessionExercise("", order=-1, joint_stress={"knee": 9}))
check("validate_session_exercise flags missing id", any("exercise_id" in e for e in errs))
check("validate_session_exercise flags bad order", any("order" in e for e in errs))
check("validate_session_exercise flags bad joint_stress", any("knee" in e for e in errs))

dup_session = [SessionExercise("x", order=0), SessionExercise("x", order=1)]
dup_errs = validate_session(dup_session)
check("validate_session flags duplicate exercise_id", any("duplicate" in e for e in dup_errs))

print(f"\n{passed} passed, {failed} failed")
if failed:
    sys.exit(1)
