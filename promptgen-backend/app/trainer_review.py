"""
trainer_review.py
──────────────────────────────────────────────────────────────────────────────
The Trainer Review stage: Gemini reviews the already-final, deterministic
workout for safety and quality, and may propose substitutions — it never
generates a workout from scratch, and it is structurally prevented (not
just prompted) from inventing an exercise that isn't in the production
pool.

HOW "GEMINI MUST NOT INVENT EXERCISES" IS ENFORCED
    For every exercise in the workout, build_candidates() below computes a
    deterministic whitelist of legal substitutes (same muscle/slot,
    equipment- and injury-safe, not already used elsewhere that day) using
    exactly the same app/exercise_selector.py machinery
    build_deterministic_workout_days() already uses. Gemini is given only
    those candidate names to choose from per exercise — it cannot name
    anything outside that list, because the prompt frames substitution as
    "pick one of these options, or 'keep'". review_validation.py then
    re-checks every proposed substitution against that same whitelist
    server-side, so a model that ignores the instruction and answers with
    an arbitrary string is still caught, not just discouraged.

WHAT GEMINI RECEIVES
    generated workout (day/exercise/muscle/pattern only — not the full
    exercise pool), structured KB context from knowledge_retriever.py
    (enrichment for the few exercises that have a full V7 record, pattern
    facts, condition avoid-tags/RPE cap), and the client's goal/
    experience/equipment/injuries. It does NOT receive the raw KB package,
    the full 71-exercise pool, or any other client's data.

WHAT GEMINI MAY DO: review safety, recommend a substitution (from the
    whitelist), explain a substitution, flag an injury-compatibility
    concern, flag an obvious sequencing issue.
WHAT GEMINI MAY NOT DO (enforced by review_validation.py, not just this
    prompt): regenerate the workout, change progression/sets/reps,
    override the deterministic engines, or substitute to an exercise
    outside the provided whitelist.
"""

from __future__ import annotations

import json
import random
import re

from app.equipment import normalize_equipment, requirement_met
from app.exercise_database import (
    EXERCISE_DB,
    _parse_injury_keywords,
    _blocked_by_injury,
    _filter_pool,
)
from app.exercise_selector import get_pattern, PROTECTED_COMPOUND_PATTERN
from app import knowledge_retriever as kb

__all__ = ["build_candidates", "build_review_prompt", "review_workout"]


MAX_CANDIDATES_PER_EXERCISE = 3


def _slot_for(muscle_lower: str, name: str) -> str:
    """Infer compound/isolation for an already-selected exercise by
    checking which pool it came from in EXERCISE_DB. Defaults to
    "isolation" if not found in either pool (shouldn't happen for a
    genuinely pool-sourced exercise; fails toward the less-consequential
    slot rather than raising)."""
    muscle_entry = EXERCISE_DB.get(muscle_lower, {})
    if any(ex["name"] == name for ex in muscle_entry.get("compound", [])):
        return "compound"
    return "isolation"


def build_candidates(
    day: dict,
    equipment_raw: str,
    notes_raw: str,
    rng: random.Random,
) -> dict:
    """
    Deterministic substitution whitelist for every exercise in one
    non-rest day. Returns {exercise_name: [candidate_name, ...]}. An
    exercise with an empty candidate list means "no safe alternative
    exists" — Trainer Review can still flag it, just not substitute it.
    """
    available_lower = normalize_equipment(equipment_raw)
    injury_keywords = _parse_injury_keywords(notes_raw)
    exercise_names = {ex["name"] for ex in day.get("exercises", [])}

    candidates: dict = {}
    for ex in day.get("exercises", []):
        muscle_lower = ex["muscle"].lower()
        slot = _slot_for(muscle_lower, ex["name"])
        pool = EXERCISE_DB.get(muscle_lower, {}).get(slot, [])
        filtered, _ = _filter_pool(pool, available_lower, injury_keywords)
        options = [
            e["name"] for e in filtered
            if e["name"] not in exercise_names and e["name"] != ex["name"]
        ]
        rng.shuffle(options)
        candidates[ex["name"]] = options[:MAX_CANDIDATES_PER_EXERCISE]

    return candidates


def build_review_prompt(
    *,
    days: list,
    profile: dict,
    condition_flags: dict,
    candidates_by_day: list,
) -> tuple[str, str]:
    """Builds (system_prompt, user_prompt) for the Gemini review call."""
    exercise_names: set = set()
    patterns: set = set()
    review_payload = []

    for day_index, day in enumerate(days):
        if day.get("is_rest") or not day.get("exercises"):
            continue
        day_candidates = candidates_by_day[day_index]
        day_items = []
        for ex in day["exercises"]:
            pattern = get_pattern(ex["name"])
            exercise_names.add(ex["name"])
            patterns.add(pattern)
            day_items.append({
                "name": ex["name"],
                "muscle": ex["muscle"],
                "pattern": pattern,
                "sets": ex.get("sets"),
                "reps": ex.get("reps"),
                "substitution_candidates": day_candidates.get(ex["name"], []),
            })
        review_payload.append({"day_index": day_index, "exercises": day_items})

    kb_context = kb.build_review_context(
        exercise_names=exercise_names,
        patterns=patterns,
        condition_flags=condition_flags,
        goal=str(profile.get("goal", "")),
        experience=str(profile.get("experience", "")),
        equipment=str(profile.get("equipment", "")),
    )

    system = (
        "You are a certified trainer performing a SAFETY REVIEW of an "
        "already-finalized workout. You are not the workout's author and "
        "must not redesign it. For every exercise you may choose exactly "
        "one action: \"keep\" (no issue), \"substitute\" (only to a name "
        "listed in that exercise's substitution_candidates array — never "
        "any other name), or \"flag\" (safety/sequencing concern worth a "
        "human's attention, no exercise change). Never invent an exercise "
        "name. Never change sets, reps, or exercise order. Respond with "
        "ONLY a JSON object of this exact shape, no prose, no markdown "
        "fences:\n"
        '{"reviews": [{"day_index": int, "name": str, "action": '
        '"keep"|"substitute"|"flag", "substitute_to": str|null, '
        '"reason": str}]}'
    )

    user = json.dumps({
        "workout": review_payload,
        "knowledge_base_context": kb_context,
        "client": {
            "goal": profile.get("goal", ""),
            "experience": profile.get("experience", ""),
            "equipment": profile.get("equipment", ""),
            "medical_notes": profile.get("medical_notes") or profile.get("notes") or "",
        },
    })

    return system, user


def _extract_first_json_object(text: str) -> str:
    """Brace-balanced extraction of the first {...} object, mirroring
    fitness_generator._extract_first_json_object's approach — a plain
    regex can over/under-match if the model adds trailing prose."""
    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object found in Trainer Review response")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("unbalanced JSON object in Trainer Review response")


async def review_workout(
    *,
    days: list,
    profile: dict,
    condition_flags: dict,
    llm_caller,
    seed: int | None = None,
) -> dict:
    """
    Runs the Trainer Review stage. `llm_caller` matches
    app.ollama_client.generate_with_ollama's signature:
    `async def llm_caller(prompt: str, system: str | None = None) -> str`.

    Returns:
        {
          "items": [{"day_index", "name", "action", "substitute_to", "reason"}, ...],
          "candidates_by_day": [dict, ...]  # index-aligned with `days`,
                                             # the deterministic whitelist
                                             # review_validation.py re-checks against
          "raw_response": str,
          "parse_error": str | None,        # set, with items=[], if Gemini's
                                             # response couldn't be parsed —
                                             # fail-safe: caller keeps the
                                             # workout unchanged, never blocks
                                             # plan delivery on a review-layer error
        }
    """
    equipment_raw = profile.get("equipment", "full gym")
    notes_raw = profile.get("medical_notes") or profile.get("notes") or ""
    rng = random.Random(seed)

    candidates_by_day = [
        {} if day.get("is_rest") or not day.get("exercises")
        else build_candidates(day, equipment_raw, notes_raw, rng)
        for day in days
    ]

    system, user = build_review_prompt(
        days=days, profile=profile, condition_flags=condition_flags,
        candidates_by_day=candidates_by_day,
    )

    raw = await llm_caller(user, system=system)

    try:
        obj = json.loads(_extract_first_json_object(raw))
        items = obj.get("reviews", [])
        if not isinstance(items, list):
            raise ValueError("'reviews' was not a list")
        parse_error = None
    except Exception as e:  # noqa: BLE001 — deliberately broad: any parse
        # failure here must fail SAFE (no changes applied), not crash plan
        # generation. See review_validation.py: an empty items list means
        # every exercise is implicitly "kept".
        items = []
        parse_error = str(e)

    return {
        "items": items,
        "candidates_by_day": candidates_by_day,
        "raw_response": raw,
        "parse_error": parse_error,
    }
