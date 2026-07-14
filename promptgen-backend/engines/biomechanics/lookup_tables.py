"""
lookup_tables.py -- Biomechanics Engine
=========================================
Pure data. Pattern-level defaults for the schema fields that the KB names
but never assigns values to (see models.py docstrings for provenance of
each enum). These are engineering defaults, applied at the MovementPattern
level -- a specific exercise in exercise_database can and should override
any of these on its own MovementRecord where the general pattern default
doesn't hold (e.g. a single-arm row is UNILATERAL even though
HORIZONTAL_PULL defaults to BILATERAL).
"""

from __future__ import annotations

from .models import (
    Bilaterality,
    ChainType,
    ForceVector,
    FunctionalCategory,
    MovementPattern,
    Plane,
)

# Antagonist/complementary pattern pairing, used for weekly balance checks
# (e.g. "did this program pair horizontal push with horizontal pull?").
# Rotation <-> Anti-Rotation and Squat <-> Hip Hinge are grouped as
# complementary because they load the same joints/region through opposing
# or reciprocal roles. Carry and Lunge have no natural pair in this
# 10-pattern taxonomy and map to None.
OPPOSING_PATTERN: dict[MovementPattern, MovementPattern | None] = {
    MovementPattern.HORIZONTAL_PUSH: MovementPattern.HORIZONTAL_PULL,
    MovementPattern.HORIZONTAL_PULL: MovementPattern.HORIZONTAL_PUSH,
    MovementPattern.VERTICAL_PUSH: MovementPattern.VERTICAL_PULL,
    MovementPattern.VERTICAL_PULL: MovementPattern.VERTICAL_PUSH,
    MovementPattern.SQUAT: MovementPattern.HIP_HINGE,
    MovementPattern.HIP_HINGE: MovementPattern.SQUAT,
    MovementPattern.ROTATION: MovementPattern.ANTI_ROTATION,
    MovementPattern.ANTI_ROTATION: MovementPattern.ROTATION,
    MovementPattern.LUNGE: None,
    MovementPattern.CARRY: None,
}

# Pattern -> default schema field values. Every value here is an
# engineering default, not a KB-sourced fact (see models.py docstrings).
# exercise_database should treat these as a starting point, not ground
# truth, and override per-exercise when the specific variation differs
# (e.g. a landmine press is force_vector=MULTI_DIRECTIONAL even though
# VERTICAL_PUSH defaults to VERTICAL).
PATTERN_DEFAULTS: dict[MovementPattern, dict] = {
    MovementPattern.SQUAT: {
        "plane_of_motion": Plane.SAGITTAL,
        "force_vector": ForceVector.VERTICAL,
        "bilaterality": Bilaterality.BILATERAL,
        "chain_type": ChainType.CLOSED,
        "functional_category": FunctionalCategory.KNEE_DOMINANT,
    },
    MovementPattern.HIP_HINGE: {
        "plane_of_motion": Plane.SAGITTAL,
        "force_vector": ForceVector.VERTICAL,
        "bilaterality": Bilaterality.BILATERAL,
        "chain_type": ChainType.CLOSED,
        "functional_category": FunctionalCategory.HIP_DOMINANT,
    },
    MovementPattern.HORIZONTAL_PUSH: {
        "plane_of_motion": Plane.SAGITTAL,
        "force_vector": ForceVector.HORIZONTAL,
        "bilaterality": Bilaterality.BILATERAL,
        "chain_type": ChainType.OPEN,
        "functional_category": FunctionalCategory.PUSH,
    },
    MovementPattern.HORIZONTAL_PULL: {
        "plane_of_motion": Plane.SAGITTAL,
        "force_vector": ForceVector.HORIZONTAL,
        "bilaterality": Bilaterality.BILATERAL,
        "chain_type": ChainType.OPEN,
        "functional_category": FunctionalCategory.PULL,
    },
    MovementPattern.VERTICAL_PUSH: {
        "plane_of_motion": Plane.SAGITTAL,
        "force_vector": ForceVector.VERTICAL,
        "bilaterality": Bilaterality.BILATERAL,
        "chain_type": ChainType.OPEN,
        "functional_category": FunctionalCategory.PUSH,
    },
    MovementPattern.VERTICAL_PULL: {
        "plane_of_motion": Plane.SAGITTAL,
        "force_vector": ForceVector.VERTICAL,
        "bilaterality": Bilaterality.BILATERAL,
        "chain_type": ChainType.OPEN,
        "functional_category": FunctionalCategory.PULL,
    },
    MovementPattern.LUNGE: {
        "plane_of_motion": Plane.SAGITTAL,
        "force_vector": ForceVector.VERTICAL,
        "bilaterality": Bilaterality.UNILATERAL,
        "chain_type": ChainType.CLOSED,
        "functional_category": FunctionalCategory.KNEE_DOMINANT,
    },
    MovementPattern.CARRY: {
        "plane_of_motion": Plane.MULTI_PLANAR,
        "force_vector": ForceVector.VERTICAL,
        "bilaterality": Bilaterality.BILATERAL,
        "chain_type": ChainType.CLOSED,
        "functional_category": FunctionalCategory.LOADED_CARRY,
    },
    MovementPattern.ROTATION: {
        "plane_of_motion": Plane.TRANSVERSE,
        "force_vector": ForceVector.ROTATIONAL,
        "bilaterality": Bilaterality.BILATERAL,
        "chain_type": ChainType.CLOSED,
        "functional_category": FunctionalCategory.ROTATIONAL_CONTROL,
    },
    MovementPattern.ANTI_ROTATION: {
        "plane_of_motion": Plane.TRANSVERSE,
        "force_vector": ForceVector.ROTATIONAL,
        "bilaterality": Bilaterality.BILATERAL,
        "chain_type": ChainType.CLOSED,
        "functional_category": FunctionalCategory.ROTATIONAL_CONTROL,
    },
}
