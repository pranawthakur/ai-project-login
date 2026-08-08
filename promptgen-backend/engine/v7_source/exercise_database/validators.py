"""app/engines/exercise_database/validators.py"""

from __future__ import annotations
from .models import Exercise, JointStress


def validate_exercise(exercise: Exercise) -> list[str]:
    """Returns a list of validation errors (empty = valid). Range checks
    come directly from file 16 §1.1's stated scales."""
    errors = []
    if not (1 <= exercise.difficulty <= 5):
        errors.append(f"{exercise.exercise_id}: difficulty {exercise.difficulty} outside 1-5")
    if not (1 <= exercise.fatigue_rating <= 5):
        errors.append(f"{exercise.exercise_id}: fatigue_rating {exercise.fatigue_rating} outside 1-5")
    if not (1 <= exercise.stimulus_rating <= 5):
        errors.append(f"{exercise.exercise_id}: stimulus_rating {exercise.stimulus_rating} outside 1-5")
    expected_sfr = round(exercise.stimulus_rating / exercise.fatigue_rating, 2)
    if abs(expected_sfr - exercise.sfr_score) > 0.15:
        errors.append(f"{exercise.exercise_id}: sfr_score {exercise.sfr_score} doesn't match "
                      f"stimulus/fatigue ({expected_sfr}) within tolerance — check for transcription error")
    for site, val in vars(exercise.joint_stress).items():
        if not (0 <= val <= 3):
            errors.append(f"{exercise.exercise_id}: joint_stress.{site}={val} outside 0-3")
    return errors


def equipment_is_satisfied(required: list[str], available: set[str]) -> bool:
    return set(required).issubset(available)
