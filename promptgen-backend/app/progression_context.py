"""
progression_context.py
────────────────────────────────────────────────────────────────────────────
Final Backend Integration — connects the adaptive progression system
(checkin_engine.py + progression_engine.py) to workout generation
(fitness_generator.py).

This module decides NOTHING. progression_engine.py remains the sole
authority for what happened last cycle and what should change; this module
only:
  1. loads the most recent row progression_engine.py already computed and
     main.py already stored (the `reassessments` table, plus its linked
     `checkins` row for the subjective fields), and
  2. reshapes that into a small, clean, dedicated Python object — never
     raw DB rows — for the generator to consume.

100% Python, no LLM calls, no progression math. If anything about this
optional read is missing or fails, `load_latest_progression_context()`
returns None rather than raising — workout generation must never fail or
be blocked because reassessment data doesn't exist yet (e.g. a member's
very first cycle) or because of a transient DB hiccup. Callers should treat
None exactly like "no progression context yet" and generate as before.
"""
from __future__ import annotations
from app.db import supabase
from app import progression_engine

# checkins.pain_areas uses underscored tokens (see checkin_engine.py's
# VALID_PAIN_AREAS); exercise_database._parse_injury_keywords matches
# against space-separated phrases like "lower back". This is the only
# translation needed between the two vocabularies.
_PAIN_AREA_TEXT = {
    "lower_back": "lower back",
}


def _get_latest_reassessment(member_id: str) -> dict | None:
    res = (
        supabase.table("reassessments")
        .select("*")
        .eq("member_id", member_id)
        .order("cycle_number", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _get_checkin_by_id(checkin_id) -> dict | None:
    if not checkin_id:
        return None
    res = (
        supabase.table("checkins")
        .select("*")
        .eq("id", checkin_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _get_previous_checkin(member_id: str, before_cycle: int) -> dict | None:
    res = (
        supabase.table("checkins")
        .select("*")
        .eq("member_id", member_id)
        .lt("cycle_number", before_cycle)
        .order("cycle_number", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _fatigue_level(checkin: dict | None) -> str:
    if not checkin:
        return "unknown"
    if checkin.get("recovery") == "poor" or checkin.get("soreness") == "severe":
        return "high"
    if checkin.get("recovery") == "average" or checkin.get("soreness") == "moderate":
        return "moderate"
    return "low"


def _pain_flags(checkin: dict | None) -> list[str]:
    if not checkin:
        return []
    areas = checkin.get("pain_areas") or []
    return [_PAIN_AREA_TEXT.get(a, a) for a in areas if a and a != "none"]


def _body_weight_trend(checkin: dict | None, prev_checkin: dict | None) -> str | None:
    if not checkin or not prev_checkin:
        return None
    bw, prev_bw = checkin.get("body_weight_kg"), prev_checkin.get("body_weight_kg")
    if bw is None or prev_bw is None:
        return None
    delta = bw - prev_bw
    if delta > 0.25:
        return "gaining"
    if delta < -0.25:
        return "losing"
    return "stable"


def build_progression_context(reassessment: dict, checkin: dict | None,
                               prev_checkin: dict | None, goal: str = "") -> dict:
    """Pure — takes already-fetched rows in, returns the flat structured
    object fitness_generator.py consumes out. No Supabase calls here, so
    this half is trivially unit-testable like progression_engine.compute().
    """
    adaptations = reassessment.get("adaptations") or {}
    return {
        # ── Core fields the integration spec asks for ──────────────────
        "plateau_detected":       bool(adaptations.get("is_plateaued")),
        "deload_required":        bool(reassessment.get("is_deload")),
        "recovery_status":        (checkin or {}).get("recovery"),
        "compliance_score":       reassessment.get("compliance_pct"),
        "difficulty_trend":       (checkin or {}).get("difficulty"),
        "fatigue_level":          _fatigue_level(checkin),
        "pain_flags":             _pain_flags(checkin),
        "body_weight_trend":      _body_weight_trend(checkin, prev_checkin),
        "body_measurement_trend": progression_engine.analyze_measurements(
            checkin or {}, prev_checkin, goal,
        ),
        # ── Deterministic decisions the generator applies directly.
        # progression_engine.py already computed these; this module only
        # forwards them, never recomputes them (Progression Engine
        # Authority — see integration spec §5). ──────────────────────────
        "volume_multiplier":      adaptations.get("volume_multiplier", 1.0),
        "actions":                adaptations.get("actions", []),
        "plateau_counter":        reassessment.get("plateau_counter", 0),
        "cycle_number":           reassessment.get("cycle_number"),
    }


def load_latest_progression_context(member_id: str, goal: str = "") -> dict | None:
    """Single entry point main.py calls before generating a new workout.

    Returns None if no reassessment exists yet (member's first cycle) or if
    anything about this optional read fails — generation always falls back
    to "as before" behaviour in that case (see fitness_generator.py callers).
    """
    try:
        reassessment = _get_latest_reassessment(member_id)
        if not reassessment:
            return None
        checkin = _get_checkin_by_id(reassessment.get("checkin_id"))
        cycle_number = reassessment.get("cycle_number")
        prev_checkin = (
            _get_previous_checkin(member_id, cycle_number) if cycle_number else None
        )
        return build_progression_context(reassessment, checkin, prev_checkin, goal)
    except Exception as e:  # noqa: BLE001 — optional context, never fatal
        print(f"[progression_context] failed to load for member={member_id}: {e}")
        return None
