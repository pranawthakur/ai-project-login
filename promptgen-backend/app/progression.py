"""
progression.py
──────────────────────────────────────────────────────────────────────────────
Centralized deterministic programming: sets/rep/load/RIR progression,
goal-specific and experience-specific rules, deload timing, and
exercise-level progression decisions (linear vs. double progression).

THIS MODULE DOES NOT IMPLEMENT THE BIWEEKLY REASSESSMENT SYSTEM. That's a
separate, later task. What's here is the same "given today's inputs, what
should today's programming be" layer that already exists in
programming_rules.py — extended with real week-to-week progression logic
that file never had (it only ever answered "what sets/reps/rest for this
goal", never "what changes next session").

WHY THIS WRAPS V7's programming ENGINE INSTEAD OF EXTENDING
programming_rules.py DIRECTLY
    engines/programming is the best-sourced, most heavily tested
    part of the V7 delivery: 147/147 tests passing, independently re-run
    against this exact copy before writing this module (not just trusting
    the prior engineer's note). Its source documents (KB files 2, 3, 4, 5)
    are the same programming methodology docs programming_rules.py was
    hand-transcribed from — this module is a more complete transcription
    of the same source, not a competing one.

    programming_rules.py is left untouched here. It still owns weekly
    volume targets, the split decision tree, and session-duration caps —
    none of that is progression, and none of it is duplicated in this
    file. Where both files legitimately need the same underlying idea
    (goal -> sets/reps/rest), this module reads from V7's richer table
    rather than re-deriving numbers already centralized in
    programming_rules.py's SETS_REPS_BY_GOAL, to avoid two sources of
    truth for the same fact drifting apart. See GOAL_KEY_MAP below for the
    one translation step that requires.

WHAT V7's programming ENGINE DOES NOT PROVIDE, AND WHAT'S ADDED HERE
    V7's rules_programming.py names the progression MODEL a client should
    be on (linear / double_progression / undulating_dup / ...) but never
    provides the actual "given this session's performance, what's the next
    concrete step" decision — that function doesn't exist anywhere in the
    KB source. double_progression_next_step() and
    linear_progression_next_step() below are new deterministic logic built
    to actually execute the models V7 names, the same way exercise_selector
    .py's substitution logic was built new rather than borrowed from an
    unsourced placeholder. This is disclosed here for the same reason the
    codebase already discloses it elsewhere (equipment.py's alias table,
    exercise_selector.py's recovery-goal filter): so a future editor knows
    which parts are KB transcription and which are engineering judgment on
    top of it.
"""

from __future__ import annotations

from engines.programming import rules_programming as _rp
from engines.programming import rules_levels_cardio as _rlc
from engines.programming import lookup_tables_programming_rules as _rp_tables

from app.programming_rules import _goal_key, training_age_years as _profile_training_age_years

__all__ = [
    "goal_prescription",
    "rir_guidance",
    "tempo_for_goal",
    "rest_for_exercise_type",
    "training_age_years_for",
    "progression_model_for_experience",
    "failure_policy_for",
    "plateau_action",
    "recovery_adjustment",
    "beginner_load_increment_kg",
    "beginner_deload_due",
    "deload_due",
    "linear_progression_next_step",
    "double_progression_next_step",
    "next_progression_step",
    "age_programming_note",
]


# ── GOAL VOCABULARY TRANSLATION ───────────────────────────────────────────────
# programming_rules._goal_key() maps this app's freeform `goal` field to one
# of: fat_loss, strength, general_fitness, athletic, muscle_gain (the app's
# five-way vocabulary). V7's SETS_REPS_BY_GOAL table uses a six-way
# vocabulary from KB file 2 directly: strength, power, hypertrophy,
# muscular_endurance, fat_loss, general_fitness. Four of five map exactly;
# "muscle_gain" -> "hypertrophy" is the same concept under KB naming.
# "athletic" has no exact KB row (file 2 doesn't define an "athletic" goal
# as such) — mapped to "power" as the closest fit, since this app's
# "athletic/performance/sport" goal_key is about explosive, performance-first
# training, which is what KB's "power" row (1-5 reps, 30-95% 1RM, long rest)
# describes. This single mapping decision is called out because it's a
# judgment call, not a KB-stated equivalence — everything else in this table
# is a direct rename.
GOAL_KEY_MAP = {
    "fat_loss": "fat_loss",
    "strength": "strength",
    "general_fitness": "general_fitness",
    "athletic": "power",
    "muscle_gain": "hypertrophy",
}


def _v7_goal_key(goal_raw: str) -> str:
    app_key = _goal_key(goal_raw)
    return GOAL_KEY_MAP.get(app_key, "hypertrophy")


# ── GOAL / RIR / TEMPO / REST ─────────────────────────────────────────────────

def goal_prescription(goal_raw: str) -> dict:
    """
    Full KB-sourced prescription for a goal: rep range, set range, load as
    %1RM, and rest (compound/isolation split where the KB gives one).
    Richer than programming_rules.sets_reps_rest_for_goal() (which only
    returns a display-string reps/sets-per-exercise/rest triple) — this
    exposes the numeric ranges, for anything downstream that needs to
    reason about them rather than just print them.
    """
    return _rp.sets_reps_for_goal(_v7_goal_key(goal_raw))


def rir_guidance(training_age_years_value: float) -> dict:
    """Compound/isolation RIR ranges and failure frequency guidance for a
    training age (years). Uses V7's 5-band scale (beginner / novice_early /
    novice_late / intermediate / advanced), finer-grained than this app's
    3-tier experience label — training_age_years_for() below is how a
    caller gets from the app's tier to a concrete year value first."""
    return _rp.rir_guidelines(training_age_years_value)


def tempo_for_goal(goal_raw: str) -> str:
    """Tempo notation (eccentric-pause-concentric-pause) for a goal. Uses
    V7's tempo vocabulary directly (general_hypertrophy / strength_power /
    time_under_tension / tendon_joint_rehab / explosive_athletic_power)
    since that's a finer distinction than this app's 5-goal vocabulary
    maps onto 1:1 — callers pass the V7 tempo key directly rather than
    through GOAL_KEY_MAP, which is why this takes goal_raw as one of V7's
    own tempo keys, not the app's raw profile goal string."""
    return _rp.tempo_for_goal(goal_raw)


def rest_for_exercise_type(exercise_type: str) -> tuple:
    """Rest range (seconds) for a KB exercise_type key: heavy_compound_ge_85pct
    / moderate_compound_65_80pct / isolation_accessory / superset_circuit_density
    / antagonist_superset."""
    return _rp.rest_for_exercise_type(exercise_type)


# ── EXPERIENCE -> TRAINING AGE ─────────────────────────────────────────────────

def training_age_years_for(experience_raw: str) -> float:
    """
    Convert this app's 3-tier experience label to a training-age-years
    value, reusing programming_rules.training_age_years()'s existing
    beginner=0.5 / intermediate=3 / advanced=7 mapping rather than
    re-deriving it — that mapping is already centralized there and used by
    split_engine.py; progression.py needs the same conversion, not a
    second opinion on what "intermediate" means in years.
    """
    return _profile_training_age_years({"experience": experience_raw})


# ── PROGRESSION MODEL ─────────────────────────────────────────────────────────

def progression_model_for_experience(
    experience_raw: str,
    plateaued_on_current_model: bool = False,
    variety_needed: bool = False,
) -> str:
    """
    Which progression model (linear / double_progression / undulating_dup)
    a client should be on, given their experience tier and whether they've
    plateaued on their current model.

    BOUNDARY FIX: training_age_years_for("beginner") returns 0.5 — the
    midpoint programming_rules.py chose to represent doc 1's "<1yr"
    split-decision bracket. V7's progression_model_for() cuts linear vs.
    double_progression at a strict "<0.5" (doc 2/6's "0-0.5yr" bracket),
    so passing that shared 0.5 straight through would misclassify every
    beginner-tier client as double_progression instead of linear — the
    wrong model for someone who should unambiguously start on linear
    progression. Rather than change the shared 0.5 constant (used
    elsewhere for split decisions, where it's correctly inside the
    beginner bracket, not on its boundary), the app's explicit "beginner"
    experience label is special-cased here to guarantee "linear" — which
    is what both docs actually intend for a true beginner, boundary
    arithmetic aside.
    """
    if str(experience_raw or "").strip().lower().startswith("beg"):
        return "linear"
    years = training_age_years_for(experience_raw)
    return _rp.progression_model_for(years, plateaued_on_current_model, variety_needed)


def failure_policy_for(experience_raw: str, exercise_category: str, fatigue_or_illness_or_poor_sleep: bool = False) -> str:
    """exercise_category: 'compound' | 'isolation' | 'any'."""
    years = training_age_years_for(experience_raw)
    return _rp.failure_policy(years, exercise_category, fatigue_or_illness_or_poor_sleep)


def plateau_action(
    weeks_stalled: int,
    adherence_ok: bool,
    sleep_hours: float,
    stress_high: bool,
    weeks_since_last_deload: int,
    in_aggressive_deficit_while_seeking_gains: bool,
    current_volume_status: str,
    same_exercise_scheme_weeks: int,
) -> dict:
    """Thin pass-through to V7's plateau decision tree (KB file 2 §7) —
    exposed here rather than re-implemented, since progression.py is where
    a caller reasoning about "what should change" naturally looks."""
    return _rp.plateau_decision_tree(
        weeks_stalled, adherence_ok, sleep_hours, stress_high,
        weeks_since_last_deload, in_aggressive_deficit_while_seeking_gains,
        current_volume_status, same_exercise_scheme_weeks,
    )


def recovery_adjustment(recovery_quality: str, sleep_hours: float, stress_level: str) -> dict:
    """Combined recovery/sleep/stress adjustment note, merging all three of
    V7's independent lookup tables (KB file 2 §8-9) into one dict so a
    caller doesn't have to call three functions and merge them itself."""
    return {
        "recovery": _rp.recovery_quality_adjustment(recovery_quality),
        "sleep": _rp.sleep_adjustment(sleep_hours),
        "stress": _rp.stress_adjustment(stress_level),
    }


def age_programming_note(age_group: str) -> str:
    """age_group: 'teen' | '18_30' | '30_40' | '40_50' | '50_plus'."""
    return _rp.age_programming_note(age_group)


# ── DELOAD TIMING ──────────────────────────────────────────────────────────────

def beginner_load_increment_kg(lift_category: str) -> float:
    """lift_category: 'upper_body' | 'lower_body'. KB file 3's fixed
    per-session load increment for beginners on linear progression."""
    return _rlc.beginner_load_increment(lift_category)


def beginner_deload_due(weeks_since_last_deload: int, lifts_stalled_simultaneously: int = 0, fatigue_signs_present: bool = False) -> bool:
    """Direct pass-through to V7's beginner deload rule (KB file 3):
    due at 8-12 weeks regardless of other signals, or earlier if 3+ lifts
    have stalled simultaneously alongside visible fatigue signs."""
    return _rlc.beginner_deload_due(weeks_since_last_deload, lifts_stalled_simultaneously, fatigue_signs_present)


# Intermediate/advanced clients don't get their own explicit deload-frequency
# table in the KB source the way beginners do (see rules_levels_cardio.py's
# BEGINNER_DELOAD_FREQUENCY_WEEKS). The only concrete number tying deload
# timing to non-beginners is inside the plateau decision tree itself:
# weeks_since_last_deload > 8 is treated as a recovery issue requiring a
# deload before any other program change (KB file 2 §7). Rather than
# leaving intermediate/advanced clients with no due-date signal at all,
# this is used as an explicit standalone check too — disclosed as an
# inference from the plateau tree's own threshold, not a separately
# KB-stated deload-frequency table the way the beginner figure is.
_INTERMEDIATE_ADVANCED_DELOAD_DUE_WEEKS = 8


def deload_due(
    experience_raw: str,
    weeks_since_last_deload: int,
    lifts_stalled_simultaneously: int = 0,
    fatigue_signs_present: bool = False,
) -> bool:
    """
    Experience-aware deload check: beginners use the KB's explicit 8-12
    week beginner table; intermediate/advanced use the plateau tree's
    implicit >8-week recovery-issue threshold (see note above the module-
    level constant for why that's an inference, not a direct table).
    """
    years = training_age_years_for(experience_raw)
    if years < 1.0:
        return beginner_deload_due(weeks_since_last_deload, lifts_stalled_simultaneously, fatigue_signs_present)
    if weeks_since_last_deload > _INTERMEDIATE_ADVANCED_DELOAD_DUE_WEEKS:
        return True
    return lifts_stalled_simultaneously >= 3 and fatigue_signs_present


# ── EXERCISE-LEVEL PROGRESSION DECISIONS (new logic, see module docstring) ────
# V7 names these models (KB file 2 §6, lookup_tables_programming_rules.
# PROGRESSION_MODELS) but never supplies the session-to-session decision
# function that actually executes them — that function doesn't exist in
# the KB source. These two are built here to do that job, grounded in the
# models' own stated definitions (linear = add load every successful
# session until failure; double progression = fill the rep range first,
# then add load and drop back to the bottom of the range).

def linear_progression_next_step(
    lift_category: str,
    completed_all_prescribed_reps: bool,
    consecutive_failed_attempts: int,
) -> dict:
    """
    Next step for a client on the linear progression model (KB: 0-0.5
    years training age). Adds a fixed load increment every session the
    prescribed reps were completed; two consecutive failed attempts is the
    KB's own stated end condition for linear progression (KB file 2 §6 —
    see rules_programming.linear_progression_end_condition), at which
    point this recommends switching models rather than continuing to
    grind a model that's stopped working.
    """
    switch = _rp.linear_progression_end_condition(consecutive_failed_attempts)
    if switch:
        return {"action": "switch_progression_model", "to_model": "double_progression", "reason": switch}

    if completed_all_prescribed_reps:
        increment = beginner_load_increment_kg(lift_category)
        return {"action": "increase_load", "increment_kg": increment, "reason": "prescribed reps completed"}

    return {"action": "repeat_same_load", "reason": "prescribed reps not yet completed"}


def double_progression_next_step(
    current_top_set_reps: int,
    rep_range: tuple,
    rir_at_top_set: float,
    target_rir: float,
) -> dict:
    """
    Next step for a client on the double progression model (KB: primary
    hypertrophy model, 0.5-5 years training age). The model's own
    definition (fill the rep range at a given load before adding load,
    then drop back to the bottom of the range) is what's executed here:
    reached the top of the rep range at or below target RIR -> increase
    load and reset to the bottom of the range; otherwise -> stay at the
    current load and add reps toward the top.
    """
    lo, hi = rep_range
    at_top_of_range = current_top_set_reps >= hi
    within_rir_target = rir_at_top_set <= target_rir

    if at_top_of_range and within_rir_target:
        return {
            "action": "increase_load",
            "reset_reps_to": lo,
            "reason": f"reached top of {lo}-{hi} rep range at or below target RIR",
        }

    return {
        "action": "increase_reps",
        "target_reps": min(current_top_set_reps + 1, hi),
        "reason": f"stay at current load, add reps toward top of {lo}-{hi} range",
    }


def next_progression_step(
    experience_raw: str,
    lift_category: str,
    current_top_set_reps: int,
    rep_range: tuple,
    rir_at_top_set: float,
    target_rir: float,
    completed_all_prescribed_reps: bool,
    consecutive_failed_attempts: int,
    plateaued_on_current_model: bool = False,
    variety_needed: bool = False,
) -> dict:
    """
    Single entry point: picks the right model for this client's experience
    tier (progression_model_for_experience) and delegates to the matching
    step function. undulating_dup and other advanced models don't have a
    concrete step function here (yet) — returns an explicit "not
    implemented" action rather than silently falling back to a different
    model's logic, so a caller can tell the difference between "no change
    needed" and "this model isn't wired up yet".
    """
    model = progression_model_for_experience(experience_raw, plateaued_on_current_model, variety_needed)

    if model == "linear":
        return {"model": model, **linear_progression_next_step(
            lift_category, completed_all_prescribed_reps, consecutive_failed_attempts,
        )}

    if model == "double_progression":
        return {"model": model, **double_progression_next_step(
            current_top_set_reps, rep_range, rir_at_top_set, target_rir,
        )}

    return {"model": model, "action": "not_implemented", "reason": f"no step function wired for {model!r} yet"}
