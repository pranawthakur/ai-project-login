"""
scoring.py -- Substitution (Exercise Conflict) Engine
========================================================
Aggregate numeric scoring over a list of ConflictFlag, so callers (e.g.
programming, when comparing two candidate session layouts) can rank
options without inspecting individual flags.
"""

from __future__ import annotations

from .models import ConflictFlag, ConflictSeverity

_SEVERITY_WEIGHT = {
    ConflictSeverity.LOW: 1,
    ConflictSeverity.MODERATE: 3,
    ConflictSeverity.HIGH: 9,
}


def conflict_score(flags: list[ConflictFlag]) -> int:
    """Sum of severity weights across all flags. 0 = no conflicts.
    HIGH-severity flags are weighted disproportionately (9x LOW) so a
    single blocking conflict dominates the score over several minor ones."""
    return sum(_SEVERITY_WEIGHT[f.severity] for f in flags)


def worst_severity(flags: list[ConflictFlag]) -> ConflictSeverity | None:
    """Highest severity present, or None if flags is empty."""
    if not flags:
        return None
    return max(flags, key=lambda f: _SEVERITY_WEIGHT[f.severity]).severity


def rank_sessions_by_conflict(
    sessions: dict[str, list[ConflictFlag]],
) -> list[tuple[str, int]]:
    """
    Given {session_label: flags_for_that_session}, returns
    (label, conflict_score) pairs sorted ascending (least-conflicted
    first) -- the natural ordering for "which candidate layout should we
    prefer".
    """
    scored = [(label, conflict_score(flags)) for label, flags in sessions.items()]
    return sorted(scored, key=lambda pair: pair[1])
