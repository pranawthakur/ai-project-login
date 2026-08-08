"""
app/engines/analytics/models.py

NOT KB-SOURCED. The KB's only material for this engine is two 2-line
stubs (20_adherence_engine, 25_metadata_engine — both just "Scaffold for
V7."). Everything here is an engineering design covering the two things
those folder names imply:

  1. Adherence — how consistently a member is actually logging/completing
     what was prescribed, computed from SetLog history already flowing
     through your app (shared_models.TrainingState.set_logs).
  2. Metadata — a version-stamp record for a generated plan, so you can
     always answer "which engine versions / KB version produced this
     specific plan" later, which matters once these engines start
     changing over time and you need to explain why an old plan looks
     different from a new one.

Every threshold below is a stated engineering choice, not a KB fact.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class AdherenceTier(str, Enum):
    HIGH = "high"           # >= HIGH_THRESHOLD
    MODERATE = "moderate"   # >= MODERATE_THRESHOLD, < HIGH_THRESHOLD
    LOW = "low"              # < MODERATE_THRESHOLD


@dataclass(frozen=True)
class AdherenceReport:
    member_id: str
    week_number: int
    sets_prescribed: int
    sets_logged: int
    adherence_pct: float          # sets_logged / sets_prescribed, 0-100+ (can exceed 100 if extra sets logged)
    tier: AdherenceTier
    streak_weeks: int              # consecutive prior weeks at HIGH tier, including this one


@dataclass(frozen=True)
class PlanMetadata:
    """Version-stamp for a single generated plan. Not a fitness decision
    at all — pure software bookkeeping, so there's no fabrication risk
    here the way there is for anything claiming to be exercise science."""
    plan_id: str
    member_id: str
    generated_at: date
    kb_version: str                       # e.g. "V7_Part7"
    engine_versions: dict[str, str] = field(default_factory=dict)   # engine_name -> version tag
    goal: str = ""
    training_age: str = ""
