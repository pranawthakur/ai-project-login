"""
cardio_engine.py
──────────────────────────────────────────────────────────────────────────────
Deterministic cardio prescription — sessions/week, minutes/session, modality
(LISS/HIIT), and where in the week it lands — as a standalone rule engine
alongside split_engine.py (which split) and programming_rules.py (sets/reps/
volume). Nothing in this file picks lifting exercises or split day-names;
it only decides the cardio component and how it attaches to whatever split
split_engine.py already chose.

DESIGN, AGREED WITH CLIENT (see HANDOFF.md / chat log for full discussion):

1. Weekly volume is table-driven by (goal, training_age tier), with a
   weight-gap modifier for fat_loss only, capped at a hard ceiling
   (4 sessions x 30 min/week) regardless of how large the gap is — a bigger
   gap gets a longer PROGRAM duration, never more weekly cardio. Recovery
   capacity outranks urgency.

2. Modality gating: beginners are LISS-only, no exceptions. HIIT is only
   ever unlocked for intermediate/advanced clients whose goal is fat_loss
   or athletic, capped at 1 HIIT session/week (rest stays LISS). muscle_gain,
   strength, and recovery goals are LISS-only regardless of training age.
   A disclosed lower-body/joint-impact injury also disables HIIT and forces
   low-impact LISS modalities, using the SAME injury-keyword vocabulary
   exercise_database.py already parses (no second copy of that list).

3. Recovery-capacity override: lifting days/week >= 6 caps cardio at
   2 sessions/week; == 5 caps at 3 sessions/week; <= 4 has no extra cap
   beyond the base table/ceiling. This can only ever REDUCE the table
   value, never increase it.

4. Placement: standalone on rest days first (up to however many rest days
   exist), remaining sessions attached as a post-lifting finisher —
   push/upper days first, leg day last (avoid stacking fatigue on the
   already-highest-fatigue day) UNLESS the top weight-gap fat_loss tier is
   active, in which case leg day is eligible too. Cardio never displaces a
   lifting day — always additive (rest day) or attached (finisher).
   split_engine.py's "cardio_core"/NO_LIFTING_TOKENS day tokens (e.g. the
   Machine-Based split) are recognized and filled directly instead of
   adding a second, separate finisher on top.

5. Duration-budget interaction: finisher minutes count AGAINST the day's
   session_duration_cap() time budget (the caller is responsible for
   passing a reduced effective session_minutes into _compute_day_plan for
   any day this engine marks as a finisher day — see
   effective_session_minutes() below). Standalone cardio days are NOT
   subject to session_duration_cap() (that function caps lifting-exercise
   count specifically); they just use this engine's minutes directly.

This module has no dependency on the LLM prompt/schema code and can be
unit tested in isolation, same philosophy as split_engine.py.
"""

from __future__ import annotations

from app.exercise_database import INJURY_KEYWORDS
from app.text_matching import text_has_unnegated_keyword as _text_has_unnegated_keyword

__all__ = [
    "build_cardio_plan",
    "effective_session_minutes",
    "estimate_session_count",
]

# ── 1. WEEKLY VOLUME TABLE (sessions, minutes) by goal x training age ──────
# minutes is the LISS/steady-state figure. HIIT sessions (when unlocked)
# override minutes per-session — see _apply_modality() below.
_BASE_CARDIO_TABLE = {
    "fat_loss": {
        "beginner":     (3, 20),
        "intermediate": (3, 25),
        "advanced":     (4, 25),
    },
    "muscle_gain": {
        "beginner":     (2, 15),
        "intermediate": (2, 15),
        "advanced":     (1, 15),
    },
    "strength": {
        "beginner":     (1, 15),
        "intermediate": (1, 15),
        "advanced":     (1, 15),
    },
    "general_fitness": {
        "beginner":     (2, 20),
        "intermediate": (3, 20),
        "advanced":     (3, 25),
    },
    "athletic": {
        "beginner":     (3, 20),
        "intermediate": (3, 25),
        "advanced":     (4, 25),
    },
    "recovery": {
        "beginner":     (2, 15),
        "intermediate": (2, 15),
        "advanced":     (2, 15),
    },
}

# "bodybuilding" is a goal-flag alias of muscle_gain for cardio purposes —
# both mean "protect recovery/surplus, cardio is maintenance-only here".
_GOAL_ALIASES = {
    "bodybuilding": "muscle_gain",
}

_HARD_CEILING_SESSIONS = 4
_HARD_CEILING_MINUTES = 30

# Weight-gap modifier only ever applies to fat_loss, and only ever bumps
# UP toward the ceiling — never down, never for other goals.
_WEIGHT_GAP_PCT_THRESHOLD = 0.10  # >= 10% of current bodyweight

# HIIT is a short, interval-work session — its minutes figure is
# deliberately independent of the LISS table value for that goal/tier.
_HIIT_SESSION_MINUTES = 15
_HIIT_MAX_SESSIONS_PER_WEEK = 1
_HIIT_ELIGIBLE_GOALS = {"fat_loss", "athletic"}
_HIIT_ELIGIBLE_TIERS = {"intermediate", "advanced"}

# Injury keywords relevant to impact-loading cardio specifically (subset
# of exercise_database.INJURY_KEYWORDS — reusing that list/parser exactly,
# not inventing a parallel one).
_IMPACT_RELEVANT_INJURY_KEYWORDS = {"knee", "hip", "ankle"}


def _goal_key(raw_goal: str) -> str:
    """Same substring-match style as programming_rules._goal_key /
    split_engine._goal_flags, kept local and simple since cardio's goal
    buckets (fat_loss/muscle_gain/strength/general_fitness/athletic/
    recovery) don't need the full flag set those modules build."""
    g = (raw_goal or "").lower()
    if any(t in g for t in ("recovery", "recover", "deload", "injury", "rehab", "rehabilitation")):
        return "recovery"
    if any(t in g for t in ("recomp", "recomposition", "body recomp")):
        return "general_fitness"
    if any(t in g for t in ("fat loss", "weight loss", "cut", "lean")):
        return "fat_loss"
    if any(t in g for t in ("strength", "powerlift", "power lift")):
        return "strength"
    if any(t in g for t in ("bodybuilding", "aesthetic", "stage prep", "physique")):
        return "bodybuilding"
    if any(t in g for t in ("athletic", "performance", "sport")):
        return "athletic"
    if any(t in g for t in ("general fitness", "general health", "wellness")):
        return "general_fitness"
    if any(t in g for t in ("muscle", "bulk", "gain", "mass", "hypertrophy")):
        return "muscle_gain"
    return "general_fitness"


def _training_age_tier(experience_raw: str) -> str:
    tier = str(experience_raw or "intermediate").strip().lower()
    if tier.startswith("beg"):
        return "beginner"
    if tier.startswith("adv"):
        return "advanced"
    return "intermediate"


def _weight_gap_fraction(current_weight_kg, target_weight_kg) -> float:
    """abs(current - target) / current, as a fraction. Returns 0.0 if
    either value is missing/invalid — a missing/unset target weight should
    never accidentally trigger the aggressive modifier."""
    try:
        current = float(current_weight_kg)
        target = float(target_weight_kg)
    except (TypeError, ValueError):
        return 0.0
    if current <= 0:
        return 0.0
    return abs(current - target) / current


def _has_impact_relevant_injury(notes_raw: str) -> bool:
    """Reuses exercise_database's own negation-aware keyword matcher so
    'no knee issues' doesn't wrongly flag as an injury here either — same
    bugfix rationale as exercise_database._parse_injury_keywords."""
    text = str(notes_raw or "").lower()
    return any(
        _text_has_unnegated_keyword(text, (kw,))
        for kw in _IMPACT_RELEVANT_INJURY_KEYWORDS
        if kw in INJURY_KEYWORDS
    )


def _base_sessions_minutes(goal_key: str, tier: str) -> tuple[int, int]:
    goal_key = _GOAL_ALIASES.get(goal_key, goal_key)
    table = _BASE_CARDIO_TABLE.get(goal_key, _BASE_CARDIO_TABLE["general_fitness"])
    return table.get(tier, table["intermediate"])


def _apply_weight_gap_modifier(sessions: int, minutes: int, goal_key: str, gap_fraction: float) -> tuple[int, int, bool]:
    """fat_loss only: gap >= 10% of current bodyweight bumps +1 session
    and/or +5 min, still bounded by the hard ceiling below. Returns
    (sessions, minutes, modifier_applied)."""
    goal_key = _GOAL_ALIASES.get(goal_key, goal_key)
    if goal_key != "fat_loss" or gap_fraction < _WEIGHT_GAP_PCT_THRESHOLD:
        return sessions, minutes, False
    bumped_sessions = min(sessions + 1, _HARD_CEILING_SESSIONS)
    bumped_minutes = min(minutes + 5, _HARD_CEILING_MINUTES)
    return bumped_sessions, bumped_minutes, True


def _apply_ceiling(sessions: int, minutes: int) -> tuple[int, int]:
    return min(sessions, _HARD_CEILING_SESSIONS), min(minutes, _HARD_CEILING_MINUTES)


def _apply_recovery_capacity_cap(sessions: int, lifting_days_per_week: int) -> tuple[int, bool]:
    """Rule #3: can only reduce, never increase, the table/ceiling value."""
    if lifting_days_per_week >= 6:
        capped = min(sessions, 2)
    elif lifting_days_per_week == 5:
        capped = min(sessions, 3)
    else:
        capped = sessions
    return capped, capped < sessions


def _resolve_modality(goal_key: str, tier: str, impact_relevant_injury: bool) -> tuple[str, int]:
    """
    Returns (modality, hiit_sessions).
      modality: "LISS" or "HIIT_mixed"
      hiit_sessions: 0 unless HIIT is actually unlocked for this profile.
    """
    goal_key = _GOAL_ALIASES.get(goal_key, goal_key)
    if impact_relevant_injury:
        return "LISS", 0
    if tier not in _HIIT_ELIGIBLE_TIERS:
        return "LISS", 0
    if goal_key not in _HIIT_ELIGIBLE_GOALS:
        return "LISS", 0
    return "HIIT_mixed", _HIIT_MAX_SESSIONS_PER_WEEK


def estimate_session_count(
    goal_raw: str,
    experience_raw: str,
    lifting_days_per_week: int,
    current_weight_kg=None,
    target_weight_kg=None,
) -> int:
    """
    Sessions/week only (no minutes/modality/placement) — same table +
    weight-gap modifier + hard ceiling + recovery-capacity cap as
    build_cardio_plan(), factored out so callers that need to know cardio
    DEMAND before a weekly_template exists (e.g. split_engine.py deciding
    whether to reserve a dedicated cardio day) don't duplicate the rules.
    lifting_days_per_week here is the CANDIDATE lifting day count being
    considered, not necessarily the final one — recovery-cap is applied
    against whatever is passed in.
    """
    goal_key = _goal_key(goal_raw)
    tier = _training_age_tier(experience_raw)
    sessions, minutes = _base_sessions_minutes(goal_key, tier)
    gap_fraction = _weight_gap_fraction(current_weight_kg, target_weight_kg)
    sessions, minutes, _ = _apply_weight_gap_modifier(sessions, minutes, goal_key, gap_fraction)
    sessions, minutes = _apply_ceiling(sessions, minutes)
    sessions, _ = _apply_recovery_capacity_cap(sessions, lifting_days_per_week)
    return sessions


def _plan_placement(
    sessions: int,
    minutes: int,
    weekly_template: list[str],
    hiit_sessions: int,
    aggressive_fat_loss: bool,
) -> list[dict]:
    """
    weekly_template: the full 7-token week (e.g. from
    fitness_generator._build_weekly_template) — "rest", lifting-day tokens,
    or a NO_LIFTING_TOKENS-style token like "cardio"/"cardio_core".

    Placement priority:
      1. Existing rest-day slots, filled first (standalone).
      2. An existing cardio-designated day token (e.g. "cardio_core" from
         the Machine-Based split) — filled directly, never double-stacked
         with a separate finisher on the same day.
      3. Remaining sessions -> post-lifting finisher, push/upper-style days
         first, leg day last, unless aggressive_fat_loss is True (then leg
         day is eligible too).

    Cardio never displaces a lifting day — sessions that can't be placed
    (more sessions than available rest+cardio-day+lifting-day slots) are
    simply not placed; build_cardio_plan() reports this via
    "unplaced_sessions" so a caller can decide what, if anything, to do
    (e.g. surface a note to the coach) rather than this module silently
    inventing an 8th day.
    """
    placements: list[dict] = []
    remaining = sessions
    hiit_remaining = hiit_sessions

    def _next_minutes() -> tuple[int, bool]:
        nonlocal hiit_remaining
        if hiit_remaining > 0:
            hiit_remaining -= 1
            return _HIIT_SESSION_MINUTES, True
        return minutes, False

    # Pass 1: rest days (standalone)
    for idx, token in enumerate(weekly_template):
        if remaining <= 0:
            break
        if token == "rest":
            m, is_hiit = _next_minutes()
            placements.append({
                "day_index": idx, "day_token": "rest", "mode": "standalone",
                "minutes": m, "is_hiit": is_hiit,
            })
            remaining -= 1

    # Pass 2: existing cardio-designated day tokens (e.g. cardio_core) —
    # fill directly rather than adding a finisher on the same day.
    _CARDIO_DAY_TOKENS = {"cardio", "cardio_core", "conditioning", "athletic"}
    for idx, token in enumerate(weekly_template):
        if remaining <= 0:
            break
        if token in _CARDIO_DAY_TOKENS and not any(p["day_index"] == idx for p in placements):
            m, is_hiit = _next_minutes()
            placements.append({
                "day_index": idx, "day_token": token, "mode": "standalone",
                "minutes": m, "is_hiit": is_hiit,
            })
            remaining -= 1

    # Pass 3: post-lifting finisher on remaining lifting days, push/upper
    # first, legs last (unless aggressive_fat_loss).
    _LEG_TOKENS = {
        "legs", "lower", "lower_machines", "squat_focus", "legs_core",
        "heavy_legs", "hypertrophy_legs", "lower_strength", "legs_heavy",
        "legs_volume", "lower_power", "lower_hypertrophy",
    }
    already_used = {p["day_index"] for p in placements}
    lifting_indices = [
        idx for idx, token in enumerate(weekly_template)
        if idx not in already_used and token != "rest" and token not in _CARDIO_DAY_TOKENS
    ]
    if not aggressive_fat_loss:
        lifting_indices.sort(key=lambda i: weekly_template[i] in _LEG_TOKENS)
    for idx in lifting_indices:
        if remaining <= 0:
            break
        m, is_hiit = _next_minutes()
        placements.append({
            "day_index": idx, "day_token": weekly_template[idx], "mode": "finisher",
            "minutes": m, "is_hiit": is_hiit,
        })
        remaining -= 1

    placements.sort(key=lambda p: p["day_index"])
    return placements, remaining  # remaining = unplaced_sessions


def effective_session_minutes(session_minutes: int | None, placement_entry: dict | None) -> int | None:
    """
    Rule #5: a finisher's minutes count AGAINST the day's normal session
    budget. Callers building a specific day's exercise plan should pass
    the result of this function into _compute_day_plan/session_minutes
    instead of the raw profile session_duration for any day that has a
    "finisher" placement entry. Standalone cardio days don't call this at
    all (they're not subject to session_duration_cap()).
    """
    if session_minutes is None or not placement_entry:
        return session_minutes
    if placement_entry.get("mode") != "finisher":
        return session_minutes
    reduced = session_minutes - placement_entry.get("minutes", 0)
    return max(reduced, 1)


def build_cardio_plan(
    goal: str,
    experience: str,
    lifting_days_per_week: int,
    weekly_template: list[str],
    current_weight_kg=None,
    target_weight_kg=None,
    notes_raw: str = "",
) -> dict:
    """
    Main entry point. Returns:
        {
            "sessions_per_week": int,
            "session_minutes": int,          # LISS default, per session
            "modality": "LISS" | "HIIT_mixed",
            "hiit_sessions": int,
            "placement": [
                {"day_index": int, "day_token": str,
                 "mode": "standalone" | "finisher",
                 "minutes": int, "is_hiit": bool},
                ...
            ],
            "unplaced_sessions": int,
            "recovery_capacity_capped": bool,
            "weight_gap_modifier_applied": bool,
            "reason": str,
        }

    weekly_template: the full 7-slot week token list (see
    fitness_generator._build_weekly_template) so placement can see actual
    rest-day positions and actual day tokens, not just a day count.
    """
    goal_key = _goal_key(goal)
    tier = _training_age_tier(experience)
    gap_fraction = _weight_gap_fraction(current_weight_kg, target_weight_kg)
    impact_injury = _has_impact_relevant_injury(notes_raw)

    sessions, minutes = _base_sessions_minutes(goal_key, tier)
    sessions, minutes, gap_modifier_applied = _apply_weight_gap_modifier(
        sessions, minutes, goal_key, gap_fraction
    )
    sessions, minutes = _apply_ceiling(sessions, minutes)
    sessions, recovery_capped = _apply_recovery_capacity_cap(sessions, lifting_days_per_week)

    modality, hiit_sessions = _resolve_modality(goal_key, tier, impact_injury)
    hiit_sessions = min(hiit_sessions, sessions)

    aggressive_fat_loss = (
        _GOAL_ALIASES.get(goal_key, goal_key) == "fat_loss"
        and gap_modifier_applied
    )

    placement, unplaced = _plan_placement(
        sessions, minutes, weekly_template or ["rest"] * 7, hiit_sessions, aggressive_fat_loss
    )

    reason_bits = [f"{goal_key.replace('_', ' ')} goal, {tier} tier"]
    if gap_modifier_applied:
        reason_bits.append("weight-gap >=10% bumped volume toward the ceiling")
    if recovery_capped:
        reason_bits.append(f"capped by recovery capacity ({lifting_days_per_week} lifting days/week)")
    if hiit_sessions:
        reason_bits.append(f"{hiit_sessions} HIIT session/week unlocked")
    if impact_injury:
        reason_bits.append("impact-relevant injury disclosed — LISS/low-impact only")
    if unplaced:
        reason_bits.append(f"{unplaced} session(s) could not be placed without displacing a lifting day")

    return {
        "sessions_per_week": sessions,
        "session_minutes": minutes,
        "modality": modality,
        "hiit_sessions": hiit_sessions,
        "placement": placement,
        "unplaced_sessions": unplaced,
        "recovery_capacity_capped": recovery_capped,
        "weight_gap_modifier_applied": gap_modifier_applied,
        "reason": "; ".join(reason_bits) + ".",
    }
