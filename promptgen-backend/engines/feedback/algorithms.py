"""
app/engines/feedback/algorithms.py

explain_decision() turns another engine's structured output into a
readable sentence. Input shapes are duck-typed (any object with the
listed attributes) so this doesn't force a hard dependency on every
other engine's exact class — it just reads whatever's there.
"""

from __future__ import annotations
from .models import Explanation
from . import constants as C

# Human-readable templates per known reason_code family. Extend this as
# other engines add reason_code values — anything unmapped falls through
# to a generic template rather than raising, so this never blocks on an
# unrecognized code.
_REASON_TEMPLATES = {
    "RIR_BELOW_TARGET_3_WEEKS": "Your last 3 weeks were consistently harder than the target effort, so weight was reduced to bring difficulty back in range.",
    "RIR_ABOVE_TARGET_3_WEEKS": "Your last 3 weeks were consistently easier than the target effort, so weight was increased.",
    "SCHEDULED_DELOAD_DUE": "This is a planned lighter week to let you recover before the next training block.",
}


def explain_decision(decision) -> Explanation:
    reason_code = getattr(decision, "reason_code", None) or getattr(decision, "reason", None)
    action = getattr(decision, "action", None)
    magnitude = getattr(decision, "magnitude", None)

    if reason_code in _REASON_TEMPLATES:
        detail = _REASON_TEMPLATES[reason_code]
    elif reason_code:
        detail = f"Reason: {reason_code.replace('_', ' ').lower()}."
    else:
        detail = "No specific reason was recorded for this decision."

    if action and magnitude is not None:
        summary = f"{action.replace('_', ' ').title()} ({magnitude:+g})"
    elif action:
        summary = action.replace("_", " ").title()
    else:
        summary = detail[:60] + ("…" if len(detail) > 60 else "")

    return Explanation(summary=summary, detail=detail, source_reason_code=reason_code)
