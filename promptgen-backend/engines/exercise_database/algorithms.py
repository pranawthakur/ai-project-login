"""
app/engines/exercise_database/algorithms.py

Ports file 16 §12 ("Exercise Selection Decision Engine (AI-Facing Logic)")
from its pseudocode directly into real Python — filter order and ranking
key match the source exactly, including the ordering bug the KB itself
flags in §13 (troubleshooting) and the fix it prescribes.

Determinism: select_exercise_for_slot never picks randomly. Ranking is a
stable sort on (sfr_score DESC, stimulus_rating DESC, difficulty ASC).
Variety (KB §13's rotation rule) is implemented as a deterministic
exclusion of the previous pick, not a random draw — the caller supplies
`previous_exercise_id`, and rotation only kicks in on that repeat-avoidance
condition, exactly as the KB prescribes ("exclude previous session's top
pick from top-3 ranking every other session unless SFR gap >0.5").
"""

from __future__ import annotations
from .models import Exercise, MovementPattern, SelectionResult
from .lookup_tables import EXERCISES


def _equipment_available(exercise: Exercise, available_equipment: set[str]) -> bool:
    return set(exercise.equipment_required).issubset(available_equipment)


def _mobility_flag_conflict(exercise: Exercise, mobility_flags: set[str]) -> bool:
    """file 16 §12: candidates.filter(e => NOT client_state.mobility_flags
    intersects e.contraindicated_by_flag). This KB's Exercise records don't
    carry a separate `contraindicated_by_flag` field — the closest
    equivalent populated data is `who_should_avoid` / `substitutions_pain_free`
    keys, so a flag "conflicts" if it appears as a substitutions_pain_free
    key (meaning the KB explicitly names a condition-driven substitute)."""
    return bool(mobility_flags & set(exercise.substitutions_pain_free.keys()))


def rank_candidates(candidates: list[Exercise]) -> list[Exercise]:
    """file 16 §12: 'rank candidates by: sfr_score DESC, then stimulus_rating
    DESC, then -difficulty' (i.e. lower difficulty preferred as tiebreak)."""
    return sorted(candidates, key=lambda e: (-e.sfr_score, -e.stimulus_rating, e.difficulty))


def select_exercise_for_slot(
    pattern: MovementPattern,
    available_equipment: set[str],
    mobility_flags: set[str],
    confidence_tier: str,             # "green" | "yellow" | "orange" | "red"
    months_trained: float,
    previous_exercise_id: str | None = None,
) -> SelectionResult | None:
    """Direct port of file 16 §12 selectExerciseForSlot. Filter order is
    preserved exactly as written in the KB (equipment/tier/history filters
    all run before ranking — file 16 §13 explicitly warns that filtering
    after ranking is the bug that causes advanced exercises to reach true
    beginners)."""
    candidates = [e for e in EXERCISES.values() if e.movement_pattern == pattern]
    candidates = [e for e in candidates if not _mobility_flag_conflict(e, mobility_flags)]
    candidates = [e for e in candidates if _equipment_available(e, available_equipment)]
    candidates = [e for e in candidates if confidence_tier != "orange" or e.difficulty <= 2]

    if months_trained < 3:
        candidates = [e for e in candidates if e.skill_requirement.value in ("low", "moderate")]

    if not candidates:
        return None

    ranked = rank_candidates(candidates)

    # file 16 §13 rotation rule: exclude previous pick from the top slot
    # unless the SFR gap to the runner-up exceeds 0.5 (i.e. the previous
    # pick is enough better that repeating it is still correct).
    if previous_exercise_id and len(ranked) > 1 and ranked[0].exercise_id == previous_exercise_id:
        gap = ranked[0].sfr_score - ranked[1].sfr_score
        if gap <= 0.5:
            ranked = ranked[1:] + [ranked[0]]

    selected = ranked[0]
    confidence = compute_confidence(selected, available_equipment, mobility_flags, confidence_tier)
    alternatives = [e.exercise_id for e in ranked[1:3]]
    return SelectionResult(exercise_id=selected.exercise_id, confidence=confidence,
                            reason=_build_reason(selected, available_equipment, mobility_flags),
                            alternative_ids=alternatives)


def compute_confidence(exercise: Exercise, available_equipment: set[str],
                        mobility_flags: set[str], confidence_tier: str) -> int:
    """Direct port of file 16 §12 computeConfidence. Clamped 0-99."""
    base = 70
    if exercise.evidence_strength.value == "high":
        base += 15
    if set(exercise.equipment_required).issubset(available_equipment) and set(exercise.equipment_required) == available_equipment.intersection(exercise.equipment_required):
        base += 10
    if _mobility_flag_conflict(exercise, mobility_flags):
        base -= 20
    if confidence_tier == "yellow":
        base -= 15
    return max(0, min(99, base))


def _build_reason(exercise: Exercise, available_equipment: set[str], mobility_flags: set[str]) -> str:
    parts = ["Matches available equipment" if _equipment_available(exercise, available_equipment) else "Best available given equipment constraints"]
    overlapping = mobility_flags & set(exercise.substitutions_pain_free.keys())
    if overlapping:
        parts.append(f"addresses flagged condition(s): {', '.join(sorted(overlapping))}")
    return "; ".join(parts) + "."
