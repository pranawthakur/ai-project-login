"""
app/engines/feedback/models.py

NOT KB-SOURCED. The KB's only material for this engine is a 2-line stub
(26_explanation_engine/README.md: "Foundation module."). Everything here
is an engineering design built to serve two purposes implied by the
engine's name/folder pairing ("feedback" + "explanation_engine"):

  1. Turn other engines' machine-shaped decisions (ProgressionDecision,
     SelectionResult, etc. from shared_models) into a plain-English
     explanation a user could actually read.
  2. Classify the subjective feedback your app already collects
     (ExerciseFeedback.difficulty_rating + notes) into an actionable
     category, deterministically.

Every threshold below is a stated engineering choice, not a KB fact.
Tune freely — nothing here is "correct" in the sense that KB-sourced
values are.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class FeedbackCategory(str, Enum):
    TOO_EASY = "too_easy"
    APPROPRIATE = "appropriate"
    TOO_HARD = "too_hard"
    POSSIBLE_PAIN_FLAG = "possible_pain_flag"       # notes mention pain-adjacent language
    INSUFFICIENT_DATA = "insufficient_data"          # no rating/notes given


@dataclass(frozen=True)
class FeedbackClassification:
    category: FeedbackCategory
    confidence: float           # 0-1, engineering heuristic, not a KB-derived probability
    triggered_by: list[str]     # which signals fired (e.g. ["rating<=2", "keyword:sharp"])


@dataclass(frozen=True)
class Explanation:
    """Output of explain_decision(). `summary` is the one-line version for
    UI display; `detail` is the fuller explanation with the reason trail."""
    summary: str
    detail: str
    source_reason_code: str | None    # carries through ProgressionDecision.reason_code etc. if present
