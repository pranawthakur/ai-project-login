"""
app/engines/exercise_database/models.py

Schema for KB V7 file 16 (Exercise Intelligence Database) + file 9
(Exercise Selection Rules). Two record types, because the source data
itself is two-tier:

  - Exercise: the full ~30-field record. Only 5 exist in this KB (one per
    pattern that got a worked example): sq_001, hg_001, hp_001, vp_001,
    hpl_001.
  - AlternativeEntry: the lighter per-pattern "alternatives matrix" rows
    (name, skill, fatigue, sfr_score, use_case only) — every other named
    exercise in the KB is one of these, not a full Exercise.

Do not upgrade an AlternativeEntry into a fake full Exercise by filling
absent fields with guesses — that's exactly the fabrication this project
is trying to avoid. See GAPS.md for the explicit list of what's missing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class MovementPattern(str, Enum):
    SQUAT = "squat"
    HINGE = "hinge"
    HORIZONTAL_PUSH = "horizontal_push"
    VERTICAL_PUSH = "vertical_push"
    HORIZONTAL_PULL = "horizontal_pull"
    VERTICAL_PULL = "vertical_pull"
    LUNGE = "lunge"                              # KB calls this "Lunge/Unilateral"
    CORE_ANTI_EXTENSION = "core_anti_extension"
    CORE_ANTI_ROTATION = "core_anti_rotation"
    CORE_ANTI_LATERAL_FLEXION = "core_anti_lateral_flexion"
    CARRY = "carry"
    HIP_DOMINANT_ISOLATION = "hip_dominant_isolation"
    KNEE_DOMINANT_ISOLATION = "knee_dominant_isolation"
    SHOULDER_ISOLATION = "shoulder_isolation"
    ELBOW_FLEXION = "elbow_flexion"
    ELBOW_EXTENSION = "elbow_extension"
    CALF = "calf"


class SkillRequirement(str, Enum):
    LOW = "low"
    LOW_MODERATE = "low_moderate"
    MODERATE = "moderate"
    MODERATE_HIGH = "moderate_high"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Tier(str, Enum):
    """file 9 §1 classification — session-ordering rule: Primary before
    Secondary before Isolation, so the highest-stimulus, most technically
    demanding movements happen while freshest."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ISOLATION = "isolation"


class EvidenceStrength(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW_THEORETICAL = "low_theoretical"


@dataclass(frozen=True)
class JointStress:
    """0-3 scale per file 16 §1.1: 0=negligible, 1=mild, 2=moderate
    (monitor), 3=high (requires clean technique/limited volume)."""
    knee: int = 0
    shoulder: int = 0
    lower_back: int = 0
    elbow: int = 0
    wrist: int = 0


@dataclass(frozen=True)
class Exercise:
    """Full record — only populated for the 5 exercises the KB actually
    worked an example for. See lookup_tables.EXERCISES."""
    exercise_id: str
    name: str
    movement_pattern: MovementPattern
    primary_muscles: list[str]
    secondary_muscles: list[str]
    stabilizers: list[str]
    skill_requirement: SkillRequirement
    difficulty: int                 # 1-5
    fatigue_rating: int             # 1-5, per file 16 §1.1
    stimulus_rating: int            # 1-5
    sfr_score: float                # stimulus_rating / fatigue_rating; >1.5 excellent, 1.0-1.5 good, <1.0 sparingly
    joint_stress: JointStress
    equipment_required: list[str]
    strength_curve: str
    resistance_profile_notes: str
    rom_notes: str
    tempo_default: str
    rep_range_optimal: str
    warmup_sets_recommended: int
    execution_cues: list[str]
    common_mistakes: list[str]
    coaching_tips: list[str]
    regressions: list[str]
    progressions: list[str]
    substitutions_equipment: list[str]
    substitutions_pain_free: dict[str, str]   # flag/condition -> substitute
    machine_alternative: str
    home_alternative: str
    who_should_avoid: list[str]
    who_benefits_most: list[str]
    best_goals: list[str]
    best_splits: list[str]
    advanced_variations: list[str]
    evidence_strength: EvidenceStrength


@dataclass(frozen=True)
class AlternativeEntry:
    """Partial record from a pattern's 'alternatives matrix' table
    (file 16 §2.2, 3.2, 4.2, 7.1, 8, 9, 10, 11). Fields beyond these five
    are genuinely absent from the KB for these exercises — do not infer
    them. use_case is the KB's free-text "Best Use Case" column."""
    name: str
    movement_pattern: MovementPattern
    skill_requirement: SkillRequirement
    fatigue_rating: int
    sfr_score: float
    use_case: str
    sub_pattern: str | None = None   # only populated for core patterns (file 16 §9)


@dataclass(frozen=True)
class SelectionResult:
    """Output of algorithms.select_exercise_for_slot — mirrors file 16
    §12's return shape exactly (exercise/confidence/alternatives)."""
    exercise_id: str
    confidence: int              # 0-99, per computeConfidence formula
    reason: str
    alternative_ids: list[str] = field(default_factory=list)
