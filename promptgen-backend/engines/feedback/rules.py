"""app/engines/feedback/rules.py — see models.py for why this isn't KB-sourced."""

from __future__ import annotations
from .models import FeedbackCategory, FeedbackClassification
from . import constants as C


def classify_feedback(rating: int | None, notes: str | None) -> FeedbackClassification:
    """Deterministic, rule-order matters: a pain keyword always wins over
    a numeric rating, even if the rating alone would read as 'appropriate'
    or 'too_easy' — a user who rates something 3/5 but mentions a sharp
    pain twinge should never be silently classified as fine."""
    triggered = []

    if notes:
        lowered = notes.lower()
        hits = [kw for kw in C.PAIN_KEYWORDS if kw in lowered]
        if hits:
            triggered.extend(f"keyword:{h}" for h in hits)
            return FeedbackClassification(FeedbackCategory.POSSIBLE_PAIN_FLAG, confidence=0.9, triggered_by=triggered)

    if rating is None:
        return FeedbackClassification(FeedbackCategory.INSUFFICIENT_DATA, confidence=1.0, triggered_by=["no_rating"])

    if rating <= C.RATING_TOO_EASY_MAX:
        return FeedbackClassification(FeedbackCategory.TOO_EASY, confidence=0.7, triggered_by=[f"rating<={C.RATING_TOO_EASY_MAX}"])
    if rating >= C.RATING_TOO_HARD_MIN:
        return FeedbackClassification(FeedbackCategory.TOO_HARD, confidence=0.7, triggered_by=[f"rating>={C.RATING_TOO_HARD_MIN}"])
    return FeedbackClassification(FeedbackCategory.APPROPRIATE, confidence=0.6, triggered_by=["rating==3"])
