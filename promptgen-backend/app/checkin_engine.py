"""
checkin_engine.py
────────────────────────────────────────────────────────────────────────────
Phase 6 — Biweekly Reassessment & Adaptive Progression.

This module owns the SUBJECTIVE half of a reassessment: validating and
storing the ~3-minute check-in form (recovery / difficulty / soreness /
pain / optional measurements), and pulling the OBJECTIVE workout history
the member already logged this cycle.

IMPORTANT — real data source: the feedback UI in Templates/result.html
writes directly from the browser to Supabase (`workout_set_feedback` for
per-set weight/reps, `workout_exercise_feedback` for the one difficulty
rating + notes per exercise), NOT through any FastAPI route. Those two
tables — not `plan_feedback` — are this module's read source. Requires
sql/patch_real_feedback_tables.sql to have been run (adds cycle_number
to both, without which every cycle's feedback overwrites the last).

This module does NOT decide progression. It only assembles the inputs.
progression_engine.py is the sole authority for the actual decision.

100% Python. No LLM calls anywhere in this file.
"""
from __future__ import annotations
import re
from app.db import supabase

VALID_RECOVERY   = {"excellent", "good", "average", "poor"}
VALID_DIFFICULTY = {"too_easy", "easy", "just_right", "hard", "too_hard"}
VALID_SORENESS   = {"none", "mild", "moderate", "severe"}
VALID_PAIN_AREAS = {
    "none", "shoulder", "elbow", "wrist", "lower_back",
    "hip", "knee", "ankle", "other",
}

_INT_RE = re.compile(r"\d+")


def _parse_reps(raw) -> int | None:
    """reps_used is stored as free text from an <input> the member typed
    into (e.g. '8', '10 reps', maybe '8-10'). Pull the first integer out
    of it; anything unparseable becomes None rather than raising, since
    this is member-typed data and will occasionally be messy."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return int(raw)
    m = _INT_RE.search(str(raw))
    return int(m.group()) if m else None


def validate_checkin(payload: dict) -> list[str]:
    """Returns a list of validation error strings (empty list = valid)."""
    errors = []
    if payload.get("recovery") not in VALID_RECOVERY:
        errors.append(f"recovery must be one of {sorted(VALID_RECOVERY)}")
    if payload.get("difficulty") not in VALID_DIFFICULTY:
        errors.append(f"difficulty must be one of {sorted(VALID_DIFFICULTY)}")
    if payload.get("soreness") not in VALID_SORENESS:
        errors.append(f"soreness must be one of {sorted(VALID_SORENESS)}")
    for area in payload.get("pain_areas", []):
        if area not in VALID_PAIN_AREAS:
            errors.append(f"unknown pain_area '{area}'")
    return errors


def get_current_cycle_number(member_id: str) -> int:
    """The cycle a check-in belongs to = the member's current ACTIVE plan's
    cycle_number. Falls back to 1 if no active plan is found."""
    res = (
        supabase.table("plans")
        .select("cycle_number")
        .eq("member_id", member_id)
        .eq("status", "active")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]["cycle_number"]
    return 1


def store_checkin(member_id: str, cycle_number: int, payload: dict) -> dict:
    """Persists the check-in row. Body measurements are optional — missing
    keys just get stored as null, nothing blocks on them."""
    row = {
        "member_id":      member_id,
        "cycle_number":   cycle_number,
        "recovery":       payload["recovery"],
        "difficulty":     payload["difficulty"],
        "soreness":       payload["soreness"],
        "pain_areas":     payload.get("pain_areas", []),
        "pain_notes":     payload.get("pain_notes"),
        "food_feedback":  payload.get("food_feedback"),
        "body_weight_kg": payload.get("body_weight_kg"),
        "waist_cm":       payload.get("waist_cm"),
        "chest_cm":       payload.get("chest_cm"),
        "arms_cm":        payload.get("arms_cm"),
        "thighs_cm":      payload.get("thighs_cm"),
        "hips_cm":        payload.get("hips_cm"),
        "body_fat_pct":   payload.get("body_fat_pct"),
    }
    res = supabase.table("checkins").insert(row).execute()
    return res.data[0]


def get_previous_checkin(member_id: str, before_cycle: int) -> dict | None:
    """Most recent check-in strictly before this cycle — used for body
    measurement deltas."""
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


def get_plan_exercise_names(member_id: str, cycle_number: int) -> list[str]:
    """The full set of exercise names the member was PRESCRIBED this
    cycle, read from plans.plan_json. Needed because 'missed' can only be
    computed by diffing prescribed vs logged — a set with no row could
    mean skipped, or could mean the member just hasn't logged yet, but
    against the full prescribed list this is the best available signal
    without asking the user directly (spec's whole point)."""
    res = (
        supabase.table("plans")
        .select("plan_json")
        .eq("member_id", member_id)
        .eq("cycle_number", cycle_number)
        .limit(1)
        .execute()
    )
    if not res.data:
        return []
    plan_json = res.data[0].get("plan_json") or {}
    names = []
    for day in plan_json.get("workout", {}).get("days", []):
        for ex in day.get("exercises", []):
            if ex.get("name"):
                names.append(ex["name"])
    return names


def get_cycle_workout_logs(member_id: str, cycle_number: int) -> list[dict]:
    """Every logged set for this member's cycle, joined with that
    exercise's difficulty rating (if given). This is the objective
    performance data the spec requires — never asked of the user
    directly. Returns rows already normalized to the shape
    progression_engine.py expects (weight_kg, reps_completed as int,
    completed=True for every returned row — a row only exists here if the
    member actually logged something)."""
    set_res = (
        supabase.table("workout_set_feedback")
        .select("day_index, day_name, exercise, set_number, weight_kg, reps_used")
        .eq("member_id", member_id)
        .eq("cycle_number", cycle_number)
        .execute()
    )
    ex_res = (
        supabase.table("workout_exercise_feedback")
        .select("day_index, exercise, difficulty, notes")
        .eq("member_id", member_id)
        .eq("cycle_number", cycle_number)
        .execute()
    )
    difficulty_by_key = {
        (r["day_index"], r["exercise"]): r.get("difficulty")
        for r in (ex_res.data or [])
    }

    logs = []
    for r in (set_res.data or []):
        logs.append({
            "day_index":         r["day_index"],
            "day_name":          r.get("day_name"),
            "exercise":          r["exercise"],
            "set_number":        r["set_number"],
            "weight_kg":         r.get("weight_kg"),
            "reps_completed":    _parse_reps(r.get("reps_used")),
            "difficulty_rating": difficulty_by_key.get((r["day_index"], r["exercise"])),
            "completed":         True,  # a logged row = an attempted/completed set
        })
    return logs


def get_reassessment_history(member_id: str, limit: int = 6) -> list[dict]:
    """Last N reassessments, most recent first — used for plateau counting
    and deload-interval checks."""
    res = (
        supabase.table("reassessments")
        .select("*")
        .eq("member_id", member_id)
        .order("cycle_number", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def assemble_reassessment_inputs(member_id: str, payload: dict) -> dict:
    """Single entry point main.py calls: validates the check-in, stores it,
    and gathers everything progression_engine.compute() needs into one
    dict. Raises ValueError with a joined message on validation failure —
    caller maps that to a 400."""
    errors = validate_checkin(payload)
    if errors:
        raise ValueError("; ".join(errors))

    cycle_number = get_current_cycle_number(member_id)
    checkin_row = store_checkin(member_id, cycle_number, payload)
    prev_checkin = get_previous_checkin(member_id, cycle_number)

    logs = get_cycle_workout_logs(member_id, cycle_number)
    prev_logs = get_cycle_workout_logs(member_id, cycle_number - 1) if cycle_number > 1 else []
    prescribed_exercises = get_plan_exercise_names(member_id, cycle_number)
    history = get_reassessment_history(member_id)

    return {
        "member_id":            member_id,
        "cycle_number":         cycle_number,
        "checkin":              checkin_row,
        "prev_checkin":         prev_checkin,
        "workout_logs":         logs,
        "prev_workout_logs":    prev_logs,
        "prescribed_exercises": prescribed_exercises,
        "reassessment_history": history,
    }
