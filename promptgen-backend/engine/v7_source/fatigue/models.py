from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class RecoveryInputs:
    sleep_hours: float = 8.0
    sleep_sudden_increase_from_baseline: bool = False
    stress_level: str = "low"  # "low" | "moderate" | "high"
    protein_g_per_kg: Optional[float] = None
    in_fat_loss_phase: bool = False
    alcohol_use: str = "none"  # "none" | "occasional_moderate" | "frequent_heavy"


@dataclass
class FatigueIndicatorReport:
    session_rpe_higher_than_expected: bool = False
    bar_speed_slower_than_expected: bool = False
    resting_hr_elevated_bpm: float = 0.0
    sleep_restless_or_needing_more: bool = False
    motivation_persistent_dread: bool = False
    soreness_days: int = 0
    soreness_worsening_across_week: bool = False
    joint_tendon_new_or_worsening_pain: bool = False
    appetite_significant_change: bool = False


@dataclass
class DeloadDecision:
    deload_needed: bool
    reason: str
    method: Optional[str] = None
    duration_days: Optional[tuple] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClientRecoveryState:
    training_age_years: float = 1.0
    weeks_since_last_deload: int = 0
    recovery_quality: str = "average"  # "poor" | "average" | "excellent"
    age_group: str = "18_30"
