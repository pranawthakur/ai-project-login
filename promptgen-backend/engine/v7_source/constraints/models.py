from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class ConfidenceTier(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class GateResult(str, Enum):
    PROCEED = "proceed"
    RESTRICT = "restrict"
    BLOCK = "block"


@dataclass
class Decision:
    """Uniform terminal output for every branch in this module."""
    result: GateResult
    action: str
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def blocked(self) -> bool:
        return self.result == GateResult.BLOCK


@dataclass
class SessionInput:
    reported_pain_scale: int = 0
    contains_emergency_symptom: bool = False
    pain_type: Optional[str] = None
    pain_onset: Optional[str] = None
    pain_improves_with_warmup: bool = False
    pain_persists_beyond_72h: bool = False
    pain_worsens_with_repeated_exposure: bool = False
    pain_at_end_range_only: bool = False
    pain_increases_session_over_session: bool = False


@dataclass
class ClientState:
    confidence_tier: ConfidenceTier = ConfidenceTier.GREEN
    flags: List[str] = field(default_factory=list)
    medical_clearance_resolved: bool = True
    age: Optional[int] = None
    guardian_consent: bool = False
    weeks_since_last_pain: Optional[int] = None
    distinct_pattern_pain_flags_this_mesocycle: int = 0
    medications: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)


@dataclass
class HealthReport:
    text: str = ""
    matches_emergency_list: bool = False
    is_new_and_related_to_recent_event: bool = False
    is_related_to_disclosed_chronic_condition: bool = False
    is_new_with_no_clear_mechanism: bool = False
    is_vague_or_incomplete: bool = False
    symptom_type: Optional[str] = None
    pain_scale: Optional[int] = None
    occurs_only_on_standing_quickly: bool = False
    occurs_during_exertion: bool = False
    occurs_at_rest_unrelated_to_training: bool = False
    duration_days: Optional[int] = None
    recent_life_stress_or_illness_disclosed: bool = False
