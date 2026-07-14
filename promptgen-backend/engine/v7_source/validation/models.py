"""
models.py -- Validation Engine (Intake, Routing, Versioning & Localization)
==============================================================================
Scope note (per engines/manifest.json / section_index.json): this engine's
sources are

    0_Master_Index_Versioning_and_Localization.md
    11_Assessment_and_Intake_Engine.md

Unlike feedback/analytics, both are substantial, fully-specified documents
(112 + 252 lines): file 0 defines the system's pipeline call order,
cross-file dependency map, versioning rules, and unit/locale
normalization; file 11 defines the client intake schema, intake
validation/routing algorithm, confidence tiering, movement assessment
protocol (incl. an exact 1RM estimation formula), check-in processing,
adherence-risk scoring, and the intake-to-downstream data contract.

This is not domain sports-science content the way biomechanics/nutrition
are -- it's system plumbing (what runs when, what gates what, how raw
client input becomes validated state). Every function/table below traces
to a specific numbered section in one of the two source files, cited in
its docstring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------
# file 11 Section 2.2 -- System-Wide Confidence Tiering
# ---------------------------------------------------------------------
class ConfidenceTier(str, Enum):
    """Source: 11_Assessment_and_Intake_Engine.md Sec 2.2."""
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


# ---------------------------------------------------------------------
# file 11 Section 2 -- processIntake() return statuses
# ---------------------------------------------------------------------
class IntakeStatus(str, Enum):
    """Source: 11_Assessment_and_Intake_Engine.md Sec 2 (processIntake)."""
    BLOCKED_NO_CONSENT = "blocked_no_consent"
    REJECTED = "rejected"
    RESTRICTED_GENERAL_GUIDANCE_ONLY = "restricted_general_guidance_only"
    PENDING_CLEARANCE = "pending_clearance"
    READY = "ready"


# ---------------------------------------------------------------------
# file 11 Section 7 -- Adherence risk tiers
# ---------------------------------------------------------------------
class AdherenceRiskTier(str, Enum):
    """Source: 11_Assessment_and_Intake_Engine.md Sec 7 (adherenceRiskScore)."""
    LOW_RISK = "low_risk"
    MODERATE_RISK = "moderate_risk"
    HIGH_RISK = "high_risk"


# ---------------------------------------------------------------------
# file 11 Section 1 -- Full intake schema, ported to a dataclass.
# Structure and field names match the JSON schema verbatim; nested dicts
# kept as plain dict fields (rather than sub-dataclasses) to mirror the
# source JSON shape 1:1 and stay trivially (de)serializable.
# ---------------------------------------------------------------------
@dataclass
class IntakeRecord:
    """Source: 11_Assessment_and_Intake_Engine.md Sec 1 (FULL INTAKE SCHEMA)."""
    demographics: dict = field(default_factory=lambda: {
        "age_years": 0, "sex": "", "height_cm": 0, "weight_kg": 0,
        "body_fat_pct_estimate": None,
    })
    training_history: dict = field(default_factory=lambda: {
        "months_trained": 0, "prior_splits_used": [], "current_split": None,
    })
    goals: dict = field(default_factory=lambda: {
        "primary": "", "secondary": None, "target_date": None,
    })
    equipment: dict = field(default_factory=lambda: {
        "location": "", "available": [],
    })
    schedule: dict = field(default_factory=lambda: {
        "days_available": 0, "session_minutes": 0, "consistency_confidence": "",
    })
    health: dict = field(default_factory=lambda: {
        "injuries_current": [], "injuries_historical": [], "medical_conditions": [],
        "medications": [], "pregnancy_status": "not_applicable",
        "cleared_by_physician": None,
    })
    lifestyle: dict = field(default_factory=lambda: {
        "sleep_hours_avg": 0, "stress_level": "", "occupation_activity": "",
    })
    preferences: dict = field(default_factory=lambda: {
        "disliked_exercises": [], "preferred_training_style": "", "enjoys_cardio": None,
    })
    baseline_performance: dict = field(default_factory=lambda: {
        "squat_1rm_est": None, "bench_1rm_est": None, "deadlift_1rm_est": None,
    })
    consent: dict = field(default_factory=lambda: {
        "data_processing": False, "liability_waiver": False, "photo_consent": False,
    })
    disclosure_completeness: dict = field(default_factory=lambda: {
        "pct_fields_completed": 0, "refused_fields": [],
    })


@dataclass(frozen=True)
class IntakeResult:
    """Return value of rules.process_intake(). Mirrors the dict literal
    shapes returned by processIntake() in file 11 Sec 2."""
    status: IntakeStatus
    flags: tuple[str, ...] = field(default_factory=tuple)
    reason: Optional[str] = None
    use_default_safe_template: bool = False


# ---------------------------------------------------------------------
# file 11 Section 5 -- Ongoing check-in schema
# ---------------------------------------------------------------------
@dataclass
class CheckIn:
    """Source: 11_Assessment_and_Intake_Engine.md Sec 5 (ONGOING CHECK-IN SCHEMA)."""
    date: str = ""
    bodyweight_kg: float = 0.0
    sleep_hours_avg_7d: float = 0.0
    stress_level: str = ""
    soreness_rating_avg: float = 0.0
    motivation_rating: float = 0.0
    sessions_completed: int = 0
    sessions_planned: int = 0
    new_pain_flags: tuple[str, ...] = field(default_factory=tuple)
    adherence_nutrition_pct: float = 0.0
    subjective_notes: str = ""


@dataclass
class ClientState:
    """
    Minimal running state needed by rules.process_check_in /
    adherence_risk_score -- a subset of the full client_state object file
    11 references (the complete object spans every engine's outputs;
    this dataclass only holds what this engine's own functions read/write).
    """
    confidence_tier: ConfidenceTier = ConfidenceTier.YELLOW
    trailing_4wk_completion_pct: float = 1.0
    checkin_submission_streak_broken: int = 0
    motivation_rating_avg_trailing_2wk: float = 10.0
    goal_target_date_passed_unmet: bool = False
    life_event_disclosed_last_2wk: bool = False
    goal: str = ""
    rolling_history: list = field(default_factory=list)


@dataclass(frozen=True)
class CheckInResult:
    """Flags raised by rules.process_check_in(), source: file 11 Sec 5
    (processCheckIn)."""
    flags: tuple[str, ...] = field(default_factory=tuple)
    triggers_injury_substitution: bool = False
    triggers_pain_triage: bool = False


@dataclass(frozen=True)
class OneRMEstimate:
    """Source: 11_Assessment_and_Intake_Engine.md Sec 3.1 (estimate1RM)."""
    est_1rm: int
    confidence: str  # "low" | "moderate_to_high"
