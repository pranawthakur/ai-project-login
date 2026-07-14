from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ClientState:
    days_available: int = 3
    recovery_score: str = "moderate"  # "poor" | "moderate" | "good"
    trailing_2wk_recovery_scores: Optional[List[str]] = None
    goal: str = "hypertrophy"
    confidence_tier: str = "green"  # "orange" | "yellow" | "green"
    training_age_months: int = 12
    training_history_complexity_tolerance: str = "moderate"  # "low" | "moderate" | "high"
    equipment_available: Optional[List[str]] = None
    target_date_set: bool = False
    unresolved_lower_limb_injury_flag: bool = False
    stated_split_preference: Optional[str] = None
    reported_staleness_plateau: bool = False

    def __post_init__(self):
        if self.trailing_2wk_recovery_scores is None:
            self.trailing_2wk_recovery_scores = []
        if self.equipment_available is None:
            self.equipment_available = []


@dataclass
class SplitRecommendation:
    split: str
    confidence: int
    reason: str = ""
    alternative: Optional[str] = None
    alternative_confidence: Optional[int] = None


@dataclass
class ConfidenceFactors:
    evidence_strength: str = "moderate"  # "high" | "moderate" | "low_theoretical"
    client_data_completeness_pct: float = 75.0
    conflicting_flags_present: bool = False
    unresolved_safety_flag_overlap: bool = False
    confidence_tier: str = "green"
