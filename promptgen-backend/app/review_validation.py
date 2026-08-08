"""
review_validation.py
──────────────────────────────────────────────────────────────────────────────
Final authority over Trainer Review's (Gemini's) proposed changes. Every
"substitute" action from trainer_review.py is re-checked here against the
same deterministic constraints the rest of the pipeline already enforces —
equipment availability, injury contraindication, the protected-compound-
pattern rule (leg day's compound must stay a squat variant), and same-day
duplicate prevention. A proposed change is applied only if it passes every
check; otherwise it's rejected and the original exercise is kept
unchanged. Python never trusts Gemini's substitute_to string without
re-deriving safety for it from scratch — the whitelist trainer_review.py
handed Gemini is itself untrusted here on purpose (defense-in-depth: even
if that whitelist were ever built wrong, this function still can't ship
an unsafe or duplicate exercise).

"flag" actions never change the workout — they're surfaced to the client/
coach as a note. "keep" and anything trainer_review.py couldn't parse are
no-ops.
"""

from __future__ import annotations

from app.equipment import normalize_equipment, requirement_met
from app.exercise_database import EXERCISE_DB, _parse_injury_keywords, _blocked_by_injury
from app.exercise_selector import get_pattern, PROTECTED_COMPOUND_PATTERN

__all__ = ["apply_review"]


def _find_exercise_record(muscle_lower: str, name: str) -> dict | None:
    """Look up the full pool record (requires/cue) for a named exercise,
    across both compound and isolation pools for that muscle."""
    entry = EXERCISE_DB.get(muscle_lower, {})
    for slot in ("compound", "isolation"):
        for ex in entry.get(slot, []):
            if ex["name"] == name:
                return ex
    return None


def _validate_substitution(
    *,
    day: dict,
    original_name: str,
    substitute_to: str,
    candidates: dict,
    equipment_raw: str,
    notes_raw: str,
) -> tuple[bool, str]:
    """Returns (is_valid, reason). reason explains a rejection, or is
    "ok" on success."""
    # 1. Must be in the deterministic whitelist trainer_review.py actually
    #    offered for THIS exercise — not just any name that happens to be
    #    safe elsewhere in the workout.
    allowed = candidates.get(original_name, [])
    if substitute_to not in allowed:
        return False, "trainer_suggested_exercise_outside_deterministic_candidates"

    exercise_lookup = {ex["name"]: ex for ex in day.get("exercises", [])}
    original = exercise_lookup.get(original_name)
    if original is None:
        return False, "original_exercise_not_found_in_day"
    muscle_lower = original["muscle"].lower()

    # 2. Re-derive equipment/injury safety from scratch — never trust that
    #    build_candidates() was correct, re-check independently.
    record = _find_exercise_record(muscle_lower, substitute_to)
    if record is None:
        return False, "substitute_not_found_in_exercise_database"

    available_lower = normalize_equipment(equipment_raw)
    injury_keywords = _parse_injury_keywords(notes_raw)
    if not requirement_met(record["requires"], available_lower):
        return False, "substitute_equipment_unavailable"
    if _blocked_by_injury(record, injury_keywords):
        return False, "substitute_injury_contraindication"

    # 3. Movement-pattern rules: a protected compound slot (currently only
    #    leg day's compound, which must stay squat-pattern) can't be
    #    substituted into a different pattern by Trainer Review.
    is_original_compound = any(
        e["name"] == original_name for e in EXERCISE_DB.get(muscle_lower, {}).get("compound", [])
    )
    protected_pattern = PROTECTED_COMPOUND_PATTERN.get(muscle_lower)
    if is_original_compound and protected_pattern:
        if get_pattern(substitute_to) != protected_pattern:
            return False, f"substitute_breaks_protected_{protected_pattern}_pattern"

    # 4. Same-day duplicate prevention: the substitute can't already be
    #    used elsewhere in this day (would create an exact-duplicate
    #    exercise, which validator.py's own rules forbid).
    other_names = {ex["name"] for ex in day.get("exercises", []) if ex["name"] != original_name}
    if substitute_to in other_names:
        return False, "substitute_would_duplicate_another_exercise_in_day"

    return True, "ok"


def apply_review(
    *,
    days: list,
    review: dict,
    profile: dict,
) -> dict:
    """
    Applies trainer_review.review_workout()'s output to `days`, subject to
    full re-validation. Returns a NEW days list (input is not mutated) plus
    an audit trail.

    Returns:
        {
          "days": list,        # final workout, ready to ship
          "accepted": [{"day_index","from","to","reason"}, ...],
          "rejected": [{"day_index","name","attempted_to","reason"}, ...],
          "flags": [{"day_index","name","reason"}, ...],  # from action="flag"
        }
    """
    equipment_raw = profile.get("equipment", "full gym")
    notes_raw = profile.get("medical_notes") or profile.get("notes") or ""

    new_days = [dict(day) for day in days]
    for day in new_days:
        if "exercises" in day:
            day["exercises"] = [dict(ex) for ex in day["exercises"]]

    candidates_by_day = review.get("candidates_by_day", [])
    accepted, rejected, flags = [], [], []

    for item in review.get("items", []):
        try:
            day_index = int(item["day_index"])
            name = str(item["name"])
            action = str(item.get("action", "keep"))
        except (KeyError, TypeError, ValueError):
            continue  # malformed item — ignore rather than crash the pipeline

        if day_index < 0 or day_index >= len(new_days):
            rejected.append({"day_index": day_index, "name": name, "attempted_to": None,
                              "reason": "day_index_out_of_range"})
            continue

        day = new_days[day_index]
        candidates = candidates_by_day[day_index] if day_index < len(candidates_by_day) else {}

        if action == "flag":
            flags.append({"day_index": day_index, "name": name, "reason": item.get("reason", "")})
            continue

        if action != "substitute":
            continue  # "keep" or anything else — no-op

        substitute_to = item.get("substitute_to")
        if not substitute_to:
            rejected.append({"day_index": day_index, "name": name, "attempted_to": substitute_to,
                              "reason": "substitute_action_missing_substitute_to"})
            continue

        is_valid, reason = _validate_substitution(
            day=day, original_name=name, substitute_to=substitute_to,
            candidates=candidates, equipment_raw=equipment_raw, notes_raw=notes_raw,
        )
        if not is_valid:
            rejected.append({"day_index": day_index, "name": name, "attempted_to": substitute_to,
                              "reason": reason})
            continue

        muscle_lower = None
        for ex in day["exercises"]:
            if ex["name"] == name:
                muscle_lower = ex["muscle"].lower()
                break
        record = _find_exercise_record(muscle_lower, substitute_to)

        for ex in day["exercises"]:
            if ex["name"] == name:
                ex["name"] = substitute_to
                if record:
                    ex["tempo_or_cue"] = record.get("cue", ex.get("tempo_or_cue"))
                ex["_trainer_review_substitution"] = {
                    "from": name, "reason": item.get("reason", ""),
                }
                break

        accepted.append({"day_index": day_index, "from": name, "to": substitute_to,
                          "reason": item.get("reason", "")})

    return {"days": new_days, "accepted": accepted, "rejected": rejected, "flags": flags}
