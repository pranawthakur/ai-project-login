"""
rules.py -- Substitution (Exercise Conflict) Engine
======================================================
Deterministic conflict detection over a planned session, plus a
substitute-suggestion function that leans on engines.biomechanics for
the actual similarity ranking rather than re-implementing it here.
"""

from __future__ import annotations

from collections import defaultdict

from engines.biomechanics import MovementRecord, rank_by_pattern_similarity

from . import constants as C
from .models import ConflictFlag, ConflictSeverity, ConflictType, SessionExercise


def detect_joint_stress_conflicts(session: list[SessionExercise]) -> list[ConflictFlag]:
    """
    Flags any joint that receives more than
    constants.MAX_HIGH_STRESS_HITS_PER_JOINT exercises at or above
    constants.HIGH_JOINT_STRESS_THRESHOLD within the same session.
    """
    hits_by_joint: dict[str, list[str]] = defaultdict(list)
    for item in session:
        for joint, value in item.joint_stress.items():
            if value >= C.HIGH_JOINT_STRESS_THRESHOLD:
                hits_by_joint[joint].append(item.exercise_id)

    flags = []
    for joint, exercise_ids in hits_by_joint.items():
        if len(exercise_ids) > C.MAX_HIGH_STRESS_HITS_PER_JOINT:
            flags.append(
                ConflictFlag(
                    conflict_type=ConflictType.JOINT_STRESS_STACK,
                    severity=_stack_severity(len(exercise_ids)),
                    exercise_ids=tuple(exercise_ids),
                    joint=joint,
                    message=(
                        f"{len(exercise_ids)} exercises hit '{joint}' at high stress "
                        f"(>= {C.HIGH_JOINT_STRESS_THRESHOLD}) in one session: "
                        f"{', '.join(exercise_ids)}"
                    ),
                )
            )
    return flags


def _stack_severity(hit_count: int) -> ConflictSeverity:
    if hit_count >= 3:
        return ConflictSeverity.HIGH
    if hit_count == 2:
        return ConflictSeverity.MODERATE
    return ConflictSeverity.LOW


def detect_pattern_redundancy_conflicts(session: list[SessionExercise]) -> list[ConflictFlag]:
    """
    Flags a movement_pattern that appears as the primary driver more than
    constants.MAX_PATTERN_REPEATS_PER_SESSION times in one session.
    Exercises with movement_pattern=None are ignored (nothing to compare).
    """
    by_pattern: dict = defaultdict(list)
    for item in session:
        if item.movement_pattern is not None:
            by_pattern[item.movement_pattern].append(item.exercise_id)

    flags = []
    for pattern, exercise_ids in by_pattern.items():
        if len(exercise_ids) > C.MAX_PATTERN_REPEATS_PER_SESSION:
            flags.append(
                ConflictFlag(
                    conflict_type=ConflictType.PATTERN_REDUNDANCY,
                    severity=ConflictSeverity.MODERATE,
                    exercise_ids=tuple(exercise_ids),
                    movement_pattern=pattern,
                    message=(
                        f"movement pattern '{pattern.value}' repeated "
                        f"{len(exercise_ids)}x in one session: {', '.join(exercise_ids)}"
                    ),
                )
            )
    return flags


def detect_equipment_conflicts(session: list[SessionExercise]) -> list[ConflictFlag]:
    """
    Flags two or more exercises sharing the same time_slot (i.e. paired
    as a superset/circuit with no rest between them) that also require
    the same physical equipment -- they cannot actually be performed
    concurrently as scheduled.
    """
    by_slot: dict[int, list[SessionExercise]] = defaultdict(list)
    for item in session:
        by_slot[item.effective_time_slot()].append(item)

    flags = []
    for slot, items in by_slot.items():
        if len(items) < 2:
            continue
        equipment_to_exercises: dict[str, list[str]] = defaultdict(list)
        for item in items:
            for eq in item.equipment:
                equipment_to_exercises[eq].append(item.exercise_id)
        for equipment, exercise_ids in equipment_to_exercises.items():
            if len(exercise_ids) > 1:
                flags.append(
                    ConflictFlag(
                        conflict_type=ConflictType.EQUIPMENT_CONTENTION,
                        severity=ConflictSeverity.HIGH,
                        exercise_ids=tuple(exercise_ids),
                        equipment=equipment,
                        message=(
                            f"exercises {', '.join(exercise_ids)} are paired in the same "
                            f"time slot but both require '{equipment}'"
                        ),
                    )
                )
    return flags


def detect_all_conflicts(session: list[SessionExercise]) -> list[ConflictFlag]:
    """Runs every conflict detector and returns the combined flag list."""
    return [
        *detect_joint_stress_conflicts(session),
        *detect_pattern_redundancy_conflicts(session),
        *detect_equipment_conflicts(session),
    ]


def has_blocking_conflict(session: list[SessionExercise]) -> bool:
    """True if any detected conflict is HIGH severity."""
    return any(f.severity == ConflictSeverity.HIGH for f in detect_all_conflicts(session))


def suggest_substitute(
    target: MovementRecord,
    candidates: list[MovementRecord],
    session: list[SessionExercise],
    exclude_exercise_ids: frozenset[str] = frozenset(),
) -> list[tuple[MovementRecord, float]]:
    """
    Ranks candidate replacement exercises for `target` by biomechanical
    pattern similarity (engines.biomechanics.rank_by_pattern_similarity),
    filtering out:
      - the exercise_ids already flagged as conflicting in `session`
      - any exercise_id in exclude_exercise_ids (e.g. already used today)

    This engine intentionally delegates similarity scoring to
    engines.biomechanics rather than re-scoring here -- conflict
    detection and similarity ranking are separate concerns.
    """
    conflicting_ids = {
        eid for flag in detect_all_conflicts(session) for eid in flag.exercise_ids
    }
    blocked_ids = conflicting_ids | set(exclude_exercise_ids)

    ranked = rank_by_pattern_similarity(target, candidates)
    return [(record, score) for record, score in ranked if record.exercise_id not in blocked_ids]
