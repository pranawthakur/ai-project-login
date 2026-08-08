"""
models.py -- Biomechanics Engine
==================================
Scope note (per engines/manifest.json): this engine's sources are exactly

    16_biomechanics_engine/README.md
    10_movement_engine/movement_patterns.md
    10_movement_engine/movement_schema.md
    22_Movement_Intelligence_Engine/README.md

manifest.json records "tables_extracted": 0 for this engine -- these four
source files define a *taxonomy* (movement pattern names + the field
schema every exercise should carry) but contain zero populated exercise
records. Actual per-exercise data (joint_stress, strength_curve, muscles,
etc.) is sourced from 16_Exercise_Intelligence_Database.md, which
manifest.json assigns to the exercise_database engine, not this one.

So this module owns: the movement-pattern taxonomy, the biomechanical
field schema (MovementRecord), and enums for the schema's categorical
fields. It does NOT own populated exercise instances -- exercise_database
imports MovementRecord/MovementPattern from here and fills one in per
exercise.

Fields whose value sets are not defined anywhere in the KB (Complexity,
Functional category) are modeled with an explicit "engineering default"
enum/range documented as such in each docstring, not asserted as KB fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MovementPattern(str, Enum):
    """
    Core movement pattern taxonomy.
    Source: 10_movement_engine/movement_patterns.md ("Movement Patterns")
    and 10_movement_engine/movement_schema.md ("Core Patterns") -- both
    list the identical 10 patterns.
    """
    SQUAT = "squat"
    HIP_HINGE = "hip_hinge"
    HORIZONTAL_PUSH = "horizontal_push"
    HORIZONTAL_PULL = "horizontal_pull"
    VERTICAL_PUSH = "vertical_push"
    VERTICAL_PULL = "vertical_pull"
    LUNGE = "lunge"
    CARRY = "carry"
    ROTATION = "rotation"
    ANTI_ROTATION = "anti_rotation"


class Plane(str, Enum):
    """
    Plane of motion. Source: movement_schema.md lists "Plane of motion" as
    a required schema field but defines no value set. Standard anatomical
    planes are used here as the engineering default taxonomy.
    """
    SAGITTAL = "sagittal"
    FRONTAL = "frontal"
    TRANSVERSE = "transverse"
    MULTI_PLANAR = "multi_planar"


class ForceVector(str, Enum):
    """
    Source: movement_schema.md field "Force vector" -- name only, no
    defined value set in the KB. Engineering default taxonomy below.
    """
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    LATERAL = "lateral"
    ROTATIONAL = "rotational"
    MULTI_DIRECTIONAL = "multi_directional"


class ChainType(str, Enum):
    """Source: movement_schema.md field "Open/Closed chain"."""
    OPEN = "open"
    CLOSED = "closed"


class Bilaterality(str, Enum):
    """Source: movement_schema.md field "Bilateral/Unilateral"."""
    BILATERAL = "bilateral"
    UNILATERAL = "unilateral"
    ALTERNATING = "alternating"


class FunctionalCategory(str, Enum):
    """
    Source: movement_schema.md field "Functional category" -- name only,
    no defined value set in the KB. Engineering default taxonomy grouping
    patterns by primary function; see lookup_tables.PATTERN_DEFAULTS for
    the pattern -> category mapping.
    """
    PUSH = "push"
    PULL = "pull"
    HIP_DOMINANT = "hip_dominant"
    KNEE_DOMINANT = "knee_dominant"
    LOADED_CARRY = "loaded_carry"
    ROTATIONAL_CONTROL = "rotational_control"


class ComplexityTier(int, Enum):
    """
    Source: movement_schema.md field "Complexity" -- name only, no defined
    scale in the KB. A 1-3 engineering-default tier is used (rather than
    inventing a false-precision numeric score) so the field exists without
    overclaiming KB-sourced precision.
    """
    LOW = 1
    MODERATE = 2
    HIGH = 3


@dataclass(frozen=True)
class MovementRecord:
    """
    Per-exercise biomechanical schema, exactly the field list from
    movement_schema.md's "For each exercise store" section. This class
    holds no exercise data itself -- exercise_database instantiates one
    of these per exercise and stores it alongside that exercise's other
    metadata.

    Every field below traces 1:1 to a bullet in movement_schema.md:
      Primary movement, Secondary movement, Prime movers, Synergists,
      Stabilizers, Plane of motion, Force vector, Bilateral/Unilateral,
      Open/Closed chain, Complexity, ROM, Functional category.
    """
    exercise_id: str
    movement_pattern: MovementPattern

    primary_movement: str = ""
    secondary_movement: Optional[str] = None
    prime_movers: tuple[str, ...] = field(default_factory=tuple)
    synergists: tuple[str, ...] = field(default_factory=tuple)
    stabilizers: tuple[str, ...] = field(default_factory=tuple)

    plane_of_motion: Optional[Plane] = None
    force_vector: Optional[ForceVector] = None
    bilaterality: Optional[Bilaterality] = None
    chain_type: Optional[ChainType] = None
    complexity: Optional[ComplexityTier] = None
    rom: str = ""
    functional_category: Optional[FunctionalCategory] = None

    def is_complete(self) -> bool:
        """True if every schema field has been curated (not just the
        required primary_movement/movement_pattern). Engines consuming
        this record for similarity scoring should check this first --
        see rules.is_ready_for_classification."""
        return all(
            [
                self.primary_movement,
                self.plane_of_motion is not None,
                self.force_vector is not None,
                self.bilaterality is not None,
                self.chain_type is not None,
                self.complexity is not None,
                self.rom,
                self.functional_category is not None,
            ]
        )
