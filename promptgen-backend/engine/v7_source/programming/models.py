from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class ConfidenceTier(str, Enum):
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"


@dataclass
class ExerciseSlot:
    pattern: str
    exercise: str
    regression: Optional[str] = None
    sets: int = 2
    reps: str = "10-15"
    rpe_cap: int = 6


@dataclass
class SafeTemplate:
    days_per_week: str = "2-3"
    session_length_min: str = "30-40"
    split_type: str = "full_body_same_routine"
    exercise_count: str = "5-6"
    sets_per_exercise: int = 2
    rep_range: str = "10-15"
    load: str = "bodyweight_or_light_moderate"
    rpe_cap: int = 6
    rest_seconds: int = 90
    progression_model: Optional[str] = None
    intensity_techniques_permitted: bool = False
    hiit_permitted: bool = False
    cardio_note: str = "zone_1_2_walking_only_15_20min_optional"
    exercises: List[ExerciseSlot] = field(default_factory=list)
    warmup_protocol: List[str] = field(default_factory=list)
    never_includes: List[str] = field(default_factory=list)


@dataclass
class OverrideRequest:
    override_id: str
    coach_id: str
    coach_certification_verified: bool
    client_id: str
    timestamp: str
    field_overridden: str
    system_recommendation: str
    coach_decision: str
    justification_note: str
    expires_at: Optional[str] = None
    in_person_supervision_confirmed: bool = False


@dataclass
class OverrideResult:
    allowed: bool
    reason: str
    audit_entry: Dict[str, Any] = field(default_factory=dict)
    review_flag: bool = False


@dataclass
class ClientProgrammingState:
    confidence_tier: ConfidenceTier = ConfidenceTier.GREEN
    flags: List[str] = field(default_factory=list)
    medical_clearance_resolved: bool = True
    movement_screen_completed: bool = False
    consecutive_checkins_submitted: int = 0
    pain_flag_resolved: bool = False
    reintroduce_pattern_completed: bool = False
    weeks_consistent_checkins: int = 0
    intake_completeness_pct: float = 0.0
    thoracic_mobility_limited: bool = False
    ed_flag_present: bool = False
    pain_provoking_movements: List[str] = field(default_factory=list)
