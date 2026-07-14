"""
knowledge_retriever.py
──────────────────────────────────────────────────────────────────────────────
The single, centralized entry point for reading Knowledge Base V7
(engine/v7_source, wrapped by engine/exercise_enrichment.py and the
engines/ package). No other module should import from engine.* or
engines.* directly — exercise_selector.py, validator.py, trainer_review.py
and review_validation.py all go through this module instead, so there is
exactly one place that knows how V7 is structured and exactly one place
that would need to change if V7's shape changes.

WHAT THIS MODULE INTENTIONALLY DOES NOT PROMISE
    Per the audit already recorded in v7pkg/README.md and the module
    docstrings of validator.py / exercise_selector.py, several V7 engines
    are placeholders or narrower than their names suggest:
      * engines/exercise_database only has 5 fully-populated records
        (one per movement pattern) — enrichment coverage is real but
        small, and get_exercise_context() returns None rather than a
        guessed value for anything outside that set.
      * engines/substitution, engines/feedback, engines/analytics are
        undocumented-source placeholders (their own GAPS.md files say so)
        and are deliberately NOT wrapped here. Don't add a call into them
        without first checking whether that's changed.
      * engines/biomechanics' MovementPattern enum (10 top-level patterns)
        is coarser than this app's own movement-pattern taxonomy
        (app/exercise_selector.py's EXERCISE_MOVEMENT_PATTERN, ~20 tags,
        e.g. "lateral_raise", "elbow_flexion", "calf_raise" have no V7
        equivalent). _PATTERN_TO_V7 below is an explicit, partial mapping
        — patterns with no honest V7 analog map to None, not a guess.
      * engines/validation is a KB-file-dependency cross-reference engine,
        not a generated-workout validator — never call it expecting a
        rep-count or set-count check.
      * engines/constraints is genuinely well-grounded (condition-specific
        avoid-lists, RPE caps, pain triage) and is the main thing this
        module wraps for validator.py.

CACHING
    Every wrapper here is backed by functools.lru_cache — V7's source data
    is static for the process lifetime (loaded once from Python modules,
    not a database), so repeated queries for the same exercise/condition
    are free after the first call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

from engine import exercise_enrichment as _enrichment
from engines.constraints import rules as _constraints_rules
from engines.constraints.models import Decision
from engines.biomechanics import rules as _biomechanics_rules
from engines.biomechanics.models import MovementPattern

__all__ = [
    "KnowledgeQuery",
    "KnowledgeContext",
    "get_exercise_context",
    "get_exercise_context_bulk",
    "condition_constraints",
    "pattern_facts",
    "retrieve",
    "build_review_context",
]


# ── LOCAL PATTERN -> V7 MOVEMENTPATTERN MAPPING ───────────────────────────────
# See module docstring. None = no honest V7 analog; don't invent one.
_PATTERN_TO_V7: dict[str, MovementPattern] = {
    "squat": MovementPattern.SQUAT,
    "squat_accessory": MovementPattern.SQUAT,
    "lunge": MovementPattern.LUNGE,
    "hip_extension": MovementPattern.HIP_HINGE,
    "horizontal_push": MovementPattern.HORIZONTAL_PUSH,
    "horizontal_push_isolation": MovementPattern.HORIZONTAL_PUSH,
    "vertical_push": MovementPattern.VERTICAL_PUSH,
    "horizontal_pull": MovementPattern.HORIZONTAL_PULL,
    "horizontal_pull_isolation": MovementPattern.HORIZONTAL_PULL,
    "vertical_pull": MovementPattern.VERTICAL_PULL,
    "vertical_pull_isolation": MovementPattern.VERTICAL_PULL,
}


# ── STRUCTURED QUERY / CONTEXT OBJECTS ────────────────────────────────────────

@dataclass(frozen=True)
class KnowledgeQuery:
    """What a caller wants metadata for. Every field is optional — pass
    only the axes relevant to your call, per the retrieval task's required
    query axes (exercises, movement patterns, goal, experience level,
    equipment, injuries, medical limitations)."""
    exercise_names: tuple[str, ...] = ()
    movement_patterns: tuple[str, ...] = ()
    goal: str = ""
    experience: str = ""
    equipment: tuple[str, ...] = ()
    injuries: tuple[str, ...] = ()
    medical_notes: str = ""


@dataclass(frozen=True)
class KnowledgeContext:
    """Structured result of a KnowledgeQuery. Only ever contains the
    metadata actually relevant to downstream decisions — never the raw KB
    package (see module docstring)."""
    exercise_enrichment: dict = field(default_factory=dict)   # name -> enrichment dict|None
    pattern_facts: dict = field(default_factory=dict)         # pattern -> facts dict
    condition_flags: dict = field(default_factory=dict)       # {"avoid": set, "rpe_cap": int|None, "matched_conditions": [...]}


# ── EXERCISE METADATA ─────────────────────────────────────────────────────────

@lru_cache(maxsize=256)
def get_exercise_context(exercise_name: str) -> Optional[dict]:
    """
    Structured V7 metadata for one exercise already selected by the
    deterministic pool (app/exercise_database.py). Returns None if V7 has
    no full record for this exact exercise — expected for most names (see
    module docstring); callers must treat None as "no enrichment
    available", not an error.

    Return shape (when found): joint_stress, execution_cues,
    common_mistakes, substitutions_pain_free, who_should_avoid,
    coaching_tips, evidence_strength.
    """
    return _enrichment.enrich(exercise_name)


def get_exercise_context_bulk(exercise_names) -> dict:
    """Same as get_exercise_context(), for many exercises at once. Only
    includes entries that actually resolved to a V7 record — exercises
    with no match are simply absent from the returned dict, so callers
    can do `ctx.get(name)` without a None-check dance for every miss."""
    out = {}
    for name in exercise_names:
        record = get_exercise_context(name)
        if record is not None:
            out[name] = record
    return out


# ── MOVEMENT-PATTERN FACTS ────────────────────────────────────────────────────

@lru_cache(maxsize=64)
def pattern_facts(local_pattern: str) -> dict:
    """
    Biomechanical facts for one of this app's local movement-pattern tags
    (app/exercise_selector.EXERCISE_MOVEMENT_PATTERN values), via V7's
    biomechanics engine where a mapping exists.

    Returns:
        {"v7_pattern": str|None, "is_push": bool|None, "is_pull": bool|None,
         "is_lower_body": bool|None, "opposing_pattern": str|None}
    All fields are None (not False/guessed) when this local pattern has no
    V7 analog — see _PATTERN_TO_V7.
    """
    v7_pattern = _PATTERN_TO_V7.get(local_pattern)
    if v7_pattern is None:
        return {
            "v7_pattern": None, "is_push": None, "is_pull": None,
            "is_lower_body": None, "opposing_pattern": None,
        }

    opposing = _biomechanics_rules.opposing_pattern(v7_pattern)
    return {
        "v7_pattern": v7_pattern.value,
        "is_push": _biomechanics_rules.is_push_pattern(v7_pattern),
        "is_pull": _biomechanics_rules.is_pull_pattern(v7_pattern),
        "is_lower_body": _biomechanics_rules.is_lower_body_pattern(v7_pattern),
        "opposing_pattern": opposing.value if opposing else None,
    }


# ── CONSTRAINTS (CONDITION-SPECIFIC SAFETY DATA) ──────────────────────────────

@lru_cache(maxsize=64)
def condition_constraints(condition_key: str) -> Decision:
    """
    Thin cached wrapper around engines.constraints.rules.condition_constraints().
    This is the ONLY place in the app that should import engines.constraints
    directly — validator.py calls this function instead of the engine module.
    """
    return _constraints_rules.condition_constraints(condition_key)


# ── GENERIC MULTI-AXIS RETRIEVAL ──────────────────────────────────────────────

def retrieve(query: KnowledgeQuery) -> KnowledgeContext:
    """
    General-purpose retrieval across every supported query axis. Returns
    only what was asked for — an empty KnowledgeQuery returns an empty
    KnowledgeContext, not the whole KB. This is the primary entry point
    for new callers; the narrower helpers above exist for call sites that
    only need one axis and would rather not build a KnowledgeQuery.
    """
    exercise_enrichment = get_exercise_context_bulk(query.exercise_names)

    patterns = {}
    for p in query.movement_patterns:
        patterns[p] = pattern_facts(p)

    condition_flags: dict = {}
    if query.medical_notes or query.injuries:
        # Deliberately delegate condition-keyword matching to validator.py's
        # get_condition_intensity_flags() rather than duplicating that
        # keyword table here — see validator.py's
        # _KEYWORD_TO_CONDITION_KEY. Callers that already have condition
        # flags computed should pass them straight into
        # build_review_context() instead of round-tripping through here.
        condition_flags = {}

    return KnowledgeContext(
        exercise_enrichment=exercise_enrichment,
        pattern_facts=patterns,
        condition_flags=condition_flags,
    )


# ── TRAINER REVIEW CONTEXT BUILDER ────────────────────────────────────────────

def build_review_context(
    *,
    exercise_names,
    patterns,
    condition_flags: dict,
    goal: str = "",
    experience: str = "",
    equipment: str = "",
) -> dict:
    """
    Assembles the bounded, structured KB context passed to trainer_review.py
    for the Gemini review call. Only includes:
      * enrichment for exercises that actually have a full V7 record
        (most won't — omitted, not padded with nulls)
      * pattern facts for the distinct patterns actually present in the
        workout being reviewed
      * the already-computed condition avoid-tags / RPE cap (from
        validator.get_condition_intensity_flags) — not re-derived here
      * the client's goal/experience/equipment as plain strings, for the
        reviewer's context, never the exercise pool or the KB source files
        themselves.
    """
    enrichment = get_exercise_context_bulk(exercise_names)
    pattern_ctx = {p: pattern_facts(p) for p in set(patterns) if p and p != "unclassified"}

    return {
        "exercise_enrichment": enrichment,
        "movement_pattern_facts": pattern_ctx,
        "condition_flags": {
            "avoid": sorted(condition_flags.get("avoid", set())),
            "rpe_cap": condition_flags.get("rpe_cap"),
            "matched_conditions": condition_flags.get("matched_conditions", []),
        },
        "client_profile": {
            "goal": goal,
            "experience": experience,
            "equipment": equipment,
        },
    }
