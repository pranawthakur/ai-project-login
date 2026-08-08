"""
models.py -- Substitution (Exercise Conflict) Engine
======================================================
Scope note (per engines/manifest.json): this engine's sole source is

    22_conflict_engine/README.md

whose entire content is:
    "# Exercise Conflict Engine
     Rules to avoid conflicting exercise combinations."

manifest.json records "tables_extracted": 0 and rules_raw.json for this
engine is an empty {} -- there is no populated rule set, threshold, or
example anywhere in this KB drop for what counts as a "conflicting"
combination. Every concrete rule/threshold in this module is therefore an
engineering design choice built to satisfy that one-line mandate, not a
transcription of KB content -- each is labeled as such below and in
constants.py. This mirrors how the biomechanics engine handled fields the
KB names but never defines a value set for.

Design: this engine consumes a lightweight SessionExercise description
(populated by whichever engine is planning a session -- programming or
exercise_database) and the MovementPattern taxonomy from engines.biomechanics.
It does not own exercise data itself, consistent with the manifest's
per-engine source boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from engines.biomechanics import MovementPattern


class ConflictType(str, Enum):
    """Categories of "conflicting exercise combination" this engine can
    detect. Engineering taxonomy -- not KB-enumerated (see module docstring)."""
    JOINT_STRESS_STACK = "joint_stress_stack"
    PATTERN_REDUNDANCY = "pattern_redundancy"
    EQUIPMENT_CONTENTION = "equipment_contention"


class ConflictSeverity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class SessionExercise:
    """
    Minimal per-exercise description needed to detect conflicts within a
    planned session. Callers (programming / exercise_database) populate
    this from their own richer records -- this engine only reads the
    fields below.

    time_slot: exercises sharing the same time_slot are being performed
    concurrently or back-to-back with no separation (e.g. a superset or
    circuit pairing). Exercises with different time_slot values are
    assumed sequenced with normal rest between them. Defaults to a unique
    slot per exercise (i.e. "not paired with anything") when the caller
    doesn't specify pairing.
    """
    exercise_id: str
    order: int
    movement_pattern: Optional[MovementPattern] = None
    joint_stress: dict = field(default_factory=dict)  # e.g. {"shoulder": 3}
    equipment: tuple[str, ...] = field(default_factory=tuple)
    time_slot: Optional[int] = None

    def effective_time_slot(self) -> int:
        """Falls back to `order` when time_slot isn't set, so every
        exercise is its own slot (no assumed pairing) unless the caller
        explicitly groups exercises together."""
        return self.time_slot if self.time_slot is not None else self.order


@dataclass(frozen=True)
class ConflictFlag:
    conflict_type: ConflictType
    severity: ConflictSeverity
    exercise_ids: tuple[str, ...]
    joint: Optional[str] = None
    movement_pattern: Optional[MovementPattern] = None
    equipment: Optional[str] = None
    message: str = ""
