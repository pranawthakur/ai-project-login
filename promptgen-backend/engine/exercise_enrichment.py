"""
engine/exercise_enrichment.py
────────────────────────────────────────────────────────────────────────────
WHAT THIS IS (and isn't)

This is deliberately NOT a drop-in replacement for app/exercise_database.py.

Why: the V7 exercise_database engine (engine/v7_source/exercise_database)
only has a full ~30-field record for 5 exercises total — one worked example
per movement pattern (squat, hinge, horizontal push, vertical push,
horizontal pull). Every other named exercise in that engine is a much
lighter "AlternativeEntry" (name/skill/fatigue/sfr_score/use_case only) with
NO equipment tag and NO contraindication data. See
engine/v7_source/exercise_database/GAPS.md for the authoritative list of
what's missing.

The current production pool (app/exercise_database.py) has 71 exercises,
each hand-tagged with the exact equipment chip names the frontend sends and
contraindication flags the injury filter depends on. Swapping it for V7's
data, as originally proposed ("same API, better data, zero behavioural
change"), would silently drop the equipment/injury filtering that
select_day_exercises() depends on for ~66 of those 71 exercises, and would
shrink the pool by ~93%. That is a regression, not a safe upgrade.

WHAT THIS ADAPTER DOES INSTEAD

It's a lookup: given the name of an exercise the CURRENT pool already
selected, return the richer V7 record if one exists for that exact
exercise (by name, with a small alias table for near-matches), else None.
Callers use this to *enrich* an already-selected exercise with joint-stress
detail, coaching cues, and pain-free substitutions — useful context for the
Gemini trainer-review layer (Phase 5) and the explanation layer (Phase 6) —
without touching selection logic at all.

Coverage today is intentionally small (see MATCHED_COUNT below). This will
grow only if a future KB source gives full records for more exercises;
don't backfill missing exercises with guessed values here — that defeats
the point of keeping this separate from the production pool.
"""
from __future__ import annotations
from dataclasses import asdict
from typing import Optional

from .v7_source.exercise_database.lookup_tables import SQ_001, HG_001, HP_001, VP_001, HPL_001

_ALL_FULL_RECORDS = [SQ_001, HG_001, HP_001, VP_001, HPL_001]

# Exact production-pool name -> V7 record. Verified by hand against
# app/exercise_database.py's EXERCISE_DB; do not assume a match, add one
# only after confirming the underlying exercise is actually the same
# movement (grip, stance, ROM) as the V7 source describes.
_NAME_ALIASES = {
    "Barbell Back Squat": SQ_001,
    "Barbell Bench Press": HP_001,
    "Barbell Overhead Press": VP_001,  # V7 name: "Standing Barbell Overhead Press"
    # No match in the current pool for HG_001 (Conventional Deadlift) or
    # HPL_001 (Barbell Bent-Over Row) — neither appears in
    # app/exercise_database.py today.
}

MATCHED_COUNT = len(_NAME_ALIASES)
TOTAL_FULL_RECORDS = len(_ALL_FULL_RECORDS)


def enrich(exercise_name: str) -> Optional[dict]:
    """
    Look up V7 metadata for an exercise already selected by the production
    pool. Returns None if no full V7 record exists for this exercise —
    which, today, is the expected result for the large majority of names.

    Return shape (when found) is a plain dict via dataclasses.asdict(),
    trimmed to the fields actually useful for LLM review context —
    everything else in the record is either identity fields already known
    (name, id) or fields covered elsewhere in the pipeline (e.g.
    equipment_required, since the production pool already has that).
    """
    record = _NAME_ALIASES.get(exercise_name)
    if record is None:
        return None

    full = asdict(record)
    return {
        "joint_stress": full.get("joint_stress"),
        "execution_cues": full.get("execution_cues"),
        "common_mistakes": full.get("common_mistakes"),
        "substitutions_pain_free": full.get("substitutions_pain_free"),
        "who_should_avoid": full.get("who_should_avoid"),
        "coaching_tips": full.get("coaching_tips"),
        "evidence_strength": str(full.get("evidence_strength")),
    }


if __name__ == "__main__":
    # Quick manual sanity check.
    for name in ["Barbell Back Squat", "Leg Press", "Barbell Overhead Press"]:
        print(name, "->", enrich(name))
