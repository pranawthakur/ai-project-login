"""
validator.py
──────────────────────────────────────────────────────────────────────────────
Validates every generated workout before Trainer Review: duplicate
exercises, duplicate movement patterns, push/pull balance, exercise
ordering, equipment/experience compatibility, muscle distribution, weekly
volume sanity, and split consistency. Automatically repairs recoverable
issues (via exercise_selector.find_substitute); rejects (drops the slot)
only when no safe repair exists — never forces an unsafe or duplicate
pick, matching the fail-conservative principle used everywhere else in
this engine.

IMPORTANT SCOPE NOTE — READ BEFORE EXTENDING THIS FILE
    The task that asked for this module assumed V7's "validation" and
    "constraints" engines were generic post-generation workout QA (the
    duplicate/balance/ordering checks below). They are not:

      * engines/validation is a KB file-dependency cross-reference
        engine (which KB doc depends on which) — useful for checking the
        KB's own internal consistency, not for validating a generated
        workout. Its own GAPS.md says so explicitly: "not a numeric-range
        validator... don't expect it to catch a bad rep count."
      * engines/constraints is a real, well-grounded medical
        safety-gate engine (condition-specific intensity caps, pain
        triage, emergency routing) — but that's PRE-generation client
        screening, the same job app/safety_engine.py already does earlier
        in the pipeline (before build_deterministic_workout_days() ever
        runs). It has no concept of "this generated day has two lateral
        raises" either.

    So: every structural check below (duplicates, patterns, ordering,
    equipment/experience compatibility, volume sanity, split consistency)
    is NEW deterministic logic — there's no KB engine that already does
    this to wrap instead. What genuinely IS reused from
    engines/constraints is condition_constraints() as a
    defense-in-depth cross-check (see get_condition_intensity_flags /
    check_condition_pattern_conflicts near the bottom) — real KB data,
    applied here in a way its own module never does (per-exercise-pattern
    conflict checking). The keyword->canonical-condition-key mapping and
    the avoid-tag->movement-pattern mapping used to do that are both new
    engineering judgment bridging two independently-built vocabularies,
    and are called out as such, not silently presented as KB-sourced.

    This file no longer imports engines.constraints directly — it goes
    through app/knowledge_retriever.py's condition_constraints(), which is
    now the only module in the app allowed to import engines.* / engine.*.
    Behavior is unchanged; this is purely a routing change so there's one
    place, not several, that knows how V7 is structured.
"""

from __future__ import annotations
import random

from app.equipment import normalize_equipment, requirement_met
from app.exercise_selector import get_pattern, find_substitute
from app.exercise_database import (
    _parse_injury_keywords,
    _blocked_by_injury,
    _experience_rank,
    BEGINNER_CAP_LEG_DAY,
    BEGINNER_CAP_OTHER_DAY,
    BEGINNER_CAP_UPPER_DAY,
)
from app.programming_rules import MUSCLE_VOLUME_MEV_MAV
from app import knowledge_retriever as kb

__all__ = [
    "validate_and_repair_day",
    "validate_week",
    "get_condition_intensity_flags",
    "check_condition_pattern_conflicts",
]


# ── PATTERN GROUPS FOR BALANCE CHECKS ──────────────────────────────────────────
PUSH_PATTERNS = frozenset({"horizontal_push", "horizontal_push_isolation", "vertical_push", "lateral_raise"})
PULL_PATTERNS = frozenset({"horizontal_pull", "horizontal_pull_isolation", "vertical_pull", "vertical_pull_isolation"})
SQUAT_PATTERNS = frozenset({"squat", "squat_accessory", "lunge"})
HIP_DOMINANT_PATTERNS = frozenset({"hip_extension"})


# ═══════════════════════════════════════════════════════════════════════════
# PER-DAY CHECKS
# ═══════════════════════════════════════════════════════════════════════════

def _dedupe_exact_names(exercises: list) -> tuple[list, list]:
    """Drop any exercise whose exact name already appeared earlier in the
    list. Safety net, not the primary defense — exercise_selector.py
    already prevents this at selection time; this exists for any code path
    that builds an exercise list without going through the selector."""
    seen = set()
    kept, dropped = [], []
    for ex in exercises:
        if ex["name"] in seen:
            dropped.append(ex)
            continue
        seen.add(ex["name"])
        kept.append(ex)
    return kept, dropped


def _repair_equipment_and_injury(exercises: list, available_lower, injury_keywords, rng: random.Random) -> tuple[list, list, list]:
    """Re-verify every exercise's equipment requirement and injury safety
    (defense-in-depth — exercise_selector.py already filtered on both at
    selection time). Attempt a same-muscle/same-slot substitute; if none is
    safe and unused, drop the slot entirely rather than keep an unsafe or
    unavailable exercise."""
    kept, repairs, rejected = [], [], []
    exclude_names = {ex["name"] for ex in exercises}

    for ex in exercises:
        equipment_ok = requirement_met(ex["requires"], available_lower)
        injury_ok = not _blocked_by_injury(ex, injury_keywords)
        if equipment_ok and injury_ok:
            kept.append(ex)
            continue

        reason = "equipment_unavailable" if not equipment_ok else "injury_contraindication"
        substitute = find_substitute(
            ex["muscle"], ex["slot"], exclude_names, available_lower, injury_keywords, rng,
            from_exercise_name=ex["name"],
        )
        if substitute:
            repairs.append({"from": ex["name"], "to": substitute["name"], "muscle": ex["muscle"], "reason": reason})
            exclude_names.discard(ex["name"])
            exclude_names.add(substitute["name"])
            kept.append({**ex, "name": substitute["name"], "requires": substitute["requires"], "cue": substitute["cue"]})
        else:
            rejected.append({"name": ex["name"], "muscle": ex["muscle"], "reason": reason})

    return kept, repairs, rejected


def _repair_duplicate_patterns(exercises: list, available_lower, injury_keywords, rng: random.Random) -> tuple[list, list, list]:
    """
    Within each muscle, if the same movement pattern was chosen more than
    once, try to swap every occurrence past the first for a same-muscle
    exercise with a different, not-yet-used pattern via find_substitute().
    If no alternative pattern is available in the pool, the duplicate is
    left in place and reported as an unresolved warning rather than
    dropped — a repeated pattern is a quality issue, not a safety one, so
    it doesn't warrant losing an exercise the way an equipment/injury
    violation would.
    """
    by_muscle_pattern: dict[tuple, list] = {}
    for ex in exercises:
        key = (ex["muscle"], get_pattern(ex["name"]))
        by_muscle_pattern.setdefault(key, []).append(ex)

    repairs: list = []
    unresolved: list = []
    exclude_names = {ex["name"] for ex in exercises}

    for (muscle, pattern), group in by_muscle_pattern.items():
        if len(group) <= 1:
            continue
        for extra in group[1:]:
            substitute = find_substitute(
                muscle, extra["slot"], exclude_names, available_lower, injury_keywords, rng,
                avoid_pattern=pattern,
            )
            if substitute and get_pattern(substitute["name"]) != pattern:
                repairs.append({"from": extra["name"], "to": substitute["name"], "muscle": muscle, "reason": "duplicate_movement_pattern"})
                exclude_names.discard(extra["name"])
                exclude_names.add(substitute["name"])
                extra["name"] = substitute["name"]
                extra["requires"] = substitute["requires"]
                extra["cue"] = substitute["cue"]
            else:
                unresolved.append(
                    f"{muscle}: duplicate '{pattern}' pattern on {extra['name']} — no alternative pattern available in pool, kept as-is"
                )

    return exercises, repairs, unresolved


def _reorder_compound_before_isolation(exercises: list) -> tuple[list, bool]:
    """Stable-sort so every 'compound' slot exercise precedes every
    'isolation' slot exercise, preserving relative order within each group.
    exercise_selector.py already returns them in this order; this is a
    defense-in-depth re-check for any path that reorders the list
    afterward (e.g. a future manual-edit feature)."""
    order = {"compound": 0, "isolation": 1}
    correctly_ordered = all(
        order.get(a["slot"], 1) <= order.get(b["slot"], 1)
        for a, b in zip(exercises, exercises[1:])
    )
    if correctly_ordered:
        return exercises, False
    return sorted(exercises, key=lambda ex: order.get(ex["slot"], 1)), True


def _enforce_experience_cap(exercises: list, plan: dict, experience_raw: str) -> tuple[list, list]:
    """Re-verify the beginner exercise-count cap exercise_selector.py
    already applies. Defense-in-depth re-check; trims lowest-priority
    exercises from the end if a caller's list came in over cap (the same
    trim convention exercise_selector.py uses).

    Day types built from an explicit fixed distribution (plan["no_trim"]
    — beginner Push/Pull/Legs and the combined "upper" day, see
    fitness_generator.BEGINNER_FIXED_DAY_PLANS / UPPER_FIXED_DAY_PLAN) are
    exact by design and must never be trimmed, matching both
    _compute_day_plan()'s own docstring and the bypass
    exercise_selector.select_day_exercises_detailed() already applies at
    selection time. An earlier version of this function didn't check
    plan.get("no_trim") here, so this defense-in-depth re-check could
    silently drop a real exercise from an exact-by-design day — caught via
    the regression harness (a beginner push day went from 6 exercises to
    5), fixed here rather than left in.
    """
    if _experience_rank(experience_raw) != 0 or plan.get("no_trim"):
        return exercises, []

    is_leg_day = "legs" in plan.get("muscles", [])
    is_upper_day = set(plan.get("muscles", [])) == {"back", "chest", "shoulders", "biceps", "triceps"}
    cap = BEGINNER_CAP_LEG_DAY if is_leg_day else (BEGINNER_CAP_UPPER_DAY if is_upper_day else BEGINNER_CAP_OTHER_DAY)

    if len(exercises) <= cap:
        return exercises, []

    dropped = [{"name": ex["name"], "muscle": ex["muscle"], "reason": "beginner_cap_exceeded"} for ex in exercises[cap:]]
    return exercises[:cap], dropped


def validate_and_repair_day(
    exercises: list,
    plan: dict,
    equipment_raw: str,
    notes_raw: str,
    experience_raw: str,
    rng: random.Random,
) -> dict:
    """
    Full validation + auto-repair pass for one day's exercise list (the
    output of exercise_selector.select_day_exercises or equivalent).

    Returns:
        exercises   -> final (possibly repaired/trimmed) list
        repairs     -> [{"from","to","muscle","reason"}] substitutions made
        rejected    -> [{"name","muscle","reason"}] slots dropped entirely
        warnings    -> [str] non-blocking issues (e.g. unresolved duplicate
                       pattern, kept because no safe alternative existed;
                       ordering that had to be corrected)
    """
    available_lower = normalize_equipment(equipment_raw)
    injury_keywords = _parse_injury_keywords(notes_raw)
    warnings: list = []
    all_repairs: list = []
    all_rejected: list = []

    exercises, exact_dupes_dropped = _dedupe_exact_names(exercises)
    for d in exact_dupes_dropped:
        all_rejected.append({"name": d["name"], "muscle": d["muscle"], "reason": "exact_duplicate_exercise"})

    exercises, equip_injury_repairs, equip_injury_rejected = _repair_equipment_and_injury(
        exercises, available_lower, injury_keywords, rng,
    )
    all_repairs.extend(equip_injury_repairs)
    all_rejected.extend(equip_injury_rejected)

    exercises, pattern_repairs, pattern_warnings = _repair_duplicate_patterns(
        exercises, available_lower, injury_keywords, rng,
    )
    all_repairs.extend(pattern_repairs)
    warnings.extend(pattern_warnings)

    exercises, reordered = _reorder_compound_before_isolation(exercises)
    if reordered:
        warnings.append("exercise order was compound-after-isolation; reordered to compound-before-isolation")

    exercises, cap_dropped = _enforce_experience_cap(exercises, plan, experience_raw)
    all_rejected.extend(cap_dropped)

    return {
        "exercises": exercises,
        "repairs": all_repairs,
        "rejected": all_rejected,
        "warnings": warnings,
    }


# ═══════════════════════════════════════════════════════════════════════════
# WEEKLY CHECKS
# ═══════════════════════════════════════════════════════════════════════════
# Operate across all 7 days' (already-validated) exercise lists. These are
# informational (warnings), not auto-repaired — fixing a weekly imbalance
# means changing a different day's selection, which isn't this function's
# job to reach into.

def check_split_consistency(days_exercises: list, weekly_template: list, token_muscle_map: dict) -> list:
    """
    For every non-rest day, confirm every exercise's muscle actually
    belongs to that day's assigned token (e.g. a "push" day shouldn't
    contain a "back" exercise). This is an earlier, plan-to-selection
    check than fitness_generator.workout_matches_template() (which checks
    the final LLM-touched JSON's muscle text) — complementary, not a
    duplicate: this one runs on the deterministic selection itself, before
    anything else touches it.
    """
    warnings = []
    for i, token in enumerate(weekly_template):
        if token == "rest" or i >= len(days_exercises):
            continue
        expected_muscles = set(token_muscle_map.get(token, []))
        if not expected_muscles:
            continue
        for ex in days_exercises[i]:
            if ex["muscle"] not in expected_muscles:
                warnings.append(
                    f"day {i} (token={token!r}): {ex['name']} targets {ex['muscle']!r}, "
                    f"not in the day's expected muscles {sorted(expected_muscles)}"
                )
    return warnings


def check_push_pull_balance(days_exercises: list) -> list:
    """
    Weekly push-pattern vs pull-pattern exercise count. Flags if pull
    volume falls well below push volume — a general postural-balance /
    injury-prevention heuristic from S&C practice (favor pull >= push to
    counteract desk-posture-driven upper-crossed patterns), not a specific
    numeric rule transcribed from a KB doc. Informational only.
    """
    push_count = pull_count = 0
    for day in days_exercises:
        for ex in day:
            pattern = get_pattern(ex["name"])
            if pattern in PUSH_PATTERNS:
                push_count += 1
            elif pattern in PULL_PATTERNS:
                pull_count += 1

    warnings = []
    if push_count > 0 and pull_count / push_count < 0.7:
        warnings.append(
            f"push/pull balance: {push_count} push-pattern vs {pull_count} pull-pattern exercises this week "
            f"(pull:push ratio {pull_count / push_count:.2f}, below the 0.7 general-practice guideline)"
        )
    return warnings


def check_squat_hip_dominant_balance(days_exercises: list) -> list:
    """
    This app's exercise pool has no true hip-hinge movement (no deadlift
    variant is offered at all — see exercise_database.py's leg pool), so a
    literal squat:hinge ratio can't be checked. This checks the closest
    available proxy: across the week, is there at least one hip-dominant
    accessory (hip_extension pattern: Cable Kickback, Glute Bridge) to
    complement the mandatory squat-pattern compound, so leg day isn't
    100% knee-dominant. Informational only.
    """
    has_squat = has_hip_dominant = False
    for day in days_exercises:
        for ex in day:
            pattern = get_pattern(ex["name"])
            if pattern in SQUAT_PATTERNS:
                has_squat = True
            if pattern in HIP_DOMINANT_PATTERNS:
                has_hip_dominant = True

    warnings = []
    if has_squat and not has_hip_dominant:
        warnings.append(
            "leg training this week is squat/knee-dominant only, with no hip-dominant accessory "
            "(no hinge pattern exists in this pool at all; consider Cable Kickback or Glute Bridge for balance)"
        )
    return warnings


def check_weekly_muscle_volume(days_exercises: list, experience_raw: str) -> list:
    """
    Approximates weekly direct volume per muscle as exercise COUNT (not
    final set count — that's decided later by progression.py/programming_
    rules.py, not stored on the exercise dict at this pipeline stage) and
    flags a muscle whose weekly exercise count, at a typical ~3-4 sets per
    exercise, would land clearly outside its MEV-MAV band from
    programming_rules.MUSCLE_VOLUME_MEV_MAV. This is a sanity check
    against gross under/over-programming, not a precise volume audit —
    disclosed as an approximation since the pipeline doesn't have a
    finalized set count to check against at the point validation runs.
    """
    tier = "beginner"
    rank = _experience_rank(experience_raw)
    if rank == 1:
        tier = "intermediate"
    elif rank == 2:
        tier = "advanced"

    counts: dict = {}
    for day in days_exercises:
        for ex in day:
            counts[ex["muscle"]] = counts.get(ex["muscle"], 0) + 1

    warnings = []
    sets_per_exercise_estimate = 3.5
    for muscle, tiers in MUSCLE_VOLUME_MEV_MAV.items():
        band = tiers.get(tier)
        if not band:
            continue
        mev, mav = band
        est_sets = counts.get(muscle, 0) * sets_per_exercise_estimate
        if est_sets < mev * 0.5:
            warnings.append(
                f"{muscle}: ~{est_sets:.0f} estimated weekly sets, well below MEV ({mev}) for {tier} — "
                f"possible under-programming"
            )
        elif est_sets > mav * 1.5:
            warnings.append(
                f"{muscle}: ~{est_sets:.0f} estimated weekly sets, well above MAV ({mav}) for {tier} — "
                f"possible over-programming"
            )
    return warnings


def validate_week(days_exercises: list, weekly_template: list, token_muscle_map: dict, experience_raw: str) -> dict:
    """
    Weekly-level informational checks across all 7 days' (already
    per-day-validated) exercise lists. Returns {"warnings": [str, ...]} —
    nothing here is auto-repaired; a weekly imbalance is a signal for
    Trainer Review or a human, not something this function can fix by
    itself (fixing it means changing a different day's selection).
    """
    warnings = []
    warnings.extend(check_split_consistency(days_exercises, weekly_template, token_muscle_map))
    warnings.extend(check_push_pull_balance(days_exercises))
    warnings.extend(check_squat_hip_dominant_balance(days_exercises))
    warnings.extend(check_weekly_muscle_volume(days_exercises, experience_raw))
    return {"warnings": warnings}


# ═══════════════════════════════════════════════════════════════════════════
# CONDITION-BASED DEFENSE-IN-DEPTH (bonus reuse of engines/constraints)
# ═══════════════════════════════════════════════════════════════════════════
# safety_engine.py's HIGH_RISK_KEYWORDS is a substring match against free
# text, used only to set a confidence tier (green/yellow/orange/red) before
# generation. It doesn't know which specific movement categories a
# condition should avoid. engines/constraints.rules.
# condition_constraints() does have that (structured avoid-lists per
# canonical condition key) — this section bridges the two: a small,
# explicit subset of safety_engine's free-text keywords is mapped onto
# V7's canonical condition keys, then V7's "avoid" tags are mapped onto
# this app's movement patterns, so a generated exercise that conflicts can
# be flagged even if it wasn't already caught by the exercise pool's own
# (smaller) contraindicated_for tag set. Both mappings are new engineering
# judgment bridging two independently-built vocabularies — not a KB-stated
# equivalence — and are kept small and explicit for that reason, rather
# than guessed broadly.

_KEYWORD_TO_CONDITION_KEY = {
    "pregnant": "pregnancy_trimester_2_3",
    "pregnancy": "pregnancy_trimester_2_3",
    "osteoporosis": "osteoporosis_osteopenia",
    "heart condition": "cardiac_history_any",
    "heart disease": "cardiac_history_any",
    "cardiac": "cardiac_history_any",
    "pacemaker": "cardiac_history_any",
    "eating disorder": "active_eating_disorder_disclosure",
    "anorexia": "active_eating_disorder_disclosure",
    "bulimia": "active_eating_disorder_disclosure",
    "uncontrolled diabetes": "type_2_diabetes",
}

# V7's free-text "avoid" tags, mapped to the movement-pattern(s) they most
# directly correspond to in this app's taxonomy (app/exercise_selector.py).
_AVOID_TAG_TO_PATTERNS = {
    "loaded_spinal_flexion": frozenset({"core_flexion"}),
    "high_fall_risk": frozenset({"lunge"}),  # single-leg/balance-dependent movements
    "high_impact_jumping_without_clearance": frozenset(),  # no jumping/plyometric pattern exists in this pool
    "supine_after_20_weeks": frozenset({"horizontal_push", "horizontal_push_isolation"}),  # flat-bench-position work
}


def get_condition_intensity_flags(notes_raw: str) -> dict:
    """
    Parse disclosed medical notes for the small explicit keyword set above,
    look up each matched condition's structured constraints via V7's
    condition_constraints(), and merge them: aggregated avoid-tags (union),
    and the lowest rpe_cap across matches (most conservative wins). Returns
    {"avoid": set(), "rpe_cap": int|None, "matched_conditions": [...]}.
    """
    text = str(notes_raw or "").lower()
    matched = sorted({key for kw, key in _KEYWORD_TO_CONDITION_KEY.items() if kw in text})

    avoid: set = set()
    rpe_cap = None
    for key in matched:
        decision = kb.condition_constraints(key)
        entry = decision.data or {}
        tags = entry.get("avoid", [])
        if isinstance(tags, str):
            tags = [tags]
        avoid.update(tags)
        if "rpe_cap" in entry:
            rpe_cap = entry["rpe_cap"] if rpe_cap is None else min(rpe_cap, entry["rpe_cap"])

    return {"avoid": avoid, "rpe_cap": rpe_cap, "matched_conditions": matched}


def check_condition_pattern_conflicts(exercises: list, condition_flags: dict) -> list:
    """
    Cross-reference each generated exercise's movement pattern against the
    aggregated avoid-tags from get_condition_intensity_flags(). Flags a
    conflict as a warning (not an auto-repair — the injury-keyword filter
    in exercise_selector.py already handles most of these upstream via
    contraindicated_for tags; this is a second, differently-sourced pass
    that can catch what that smaller keyword set misses).
    """
    avoid_tags = condition_flags.get("avoid", set())
    if not avoid_tags:
        return []

    flagged_patterns: set = set()
    for tag in avoid_tags:
        flagged_patterns |= _AVOID_TAG_TO_PATTERNS.get(tag, frozenset())
    if not flagged_patterns:
        return []

    warnings = []
    for ex in exercises:
        pattern = get_pattern(ex["name"])
        if pattern in flagged_patterns:
            warnings.append(
                f"{ex['name']} ({ex['muscle']}, pattern={pattern}) may conflict with a disclosed condition's "
                f"avoid-list ({', '.join(sorted(condition_flags.get('matched_conditions', [])))})"
            )

        # Bonus cross-check, only possible for the small set of exercises
        # with a full V7 enrichment record (see knowledge_retriever.py) —
        # V7's own who_should_avoid text, when present, is a second,
        # differently-sourced signal beyond the avoid-tag/pattern mapping
        # above. Additive only: absence of a record changes nothing.
        enrichment = kb.get_exercise_context(ex["name"])
        if enrichment and enrichment.get("who_should_avoid"):
            matched_conditions = condition_flags.get("matched_conditions", [])
            for note in enrichment["who_should_avoid"]:
                note_lower = note.lower()
                if any(cond.split("_")[0] in note_lower for cond in matched_conditions):
                    warnings.append(
                        f"{ex['name']}: V7 enrichment notes '{note}', which may overlap a disclosed condition"
                    )
    return warnings
