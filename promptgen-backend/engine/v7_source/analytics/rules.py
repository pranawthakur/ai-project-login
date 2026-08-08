"""app/engines/analytics/rules.py — metadata stamping, pure bookkeeping."""

from __future__ import annotations
from datetime import date
from .models import PlanMetadata
from . import constants as C


def stamp_plan_metadata(plan_id: str, member_id: str, goal: str, training_age: str,
                         engine_versions: dict[str, str] | None = None,
                         generated_at: date | None = None) -> PlanMetadata:
    return PlanMetadata(
        plan_id=plan_id, member_id=member_id,
        generated_at=generated_at or date.today(),
        kb_version=C.CURRENT_KB_VERSION,
        engine_versions=engine_versions or {},
        goal=goal, training_age=training_age,
    )
