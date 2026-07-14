"""
equipment.py
──────────────────────────────────────────────────────────────────────────────
Centralized equipment logic for the deterministic workout engine.

WHY THIS EXISTS
    Equipment handling (the fixed vocabulary of chip labels, parsing the
    intake form's comma-joined equipment string, and deciding whether a
    given exercise's requirement is satisfied) previously lived inside
    exercise_database.py, coupled to the exercise pool itself. As the
    engine grows new modules (exercise_selector.py, validator.py) that
    also need to reason about equipment — without needing to know
    anything about the exercise pool's shape — that logic is centralized
    here as the single source of truth.

    exercise_database.py now imports from this module instead of defining
    its own copy. No behavioural change: the exact chip vocabulary, the
    "full gym" / "bodyweight only" shortcuts, and the equipment-relaxation
    fallback semantics are preserved byte-for-byte from the original
    implementation.

EQUIPMENT MODEL
    Every exercise in the pool carries a `requires` value:
        None              -> bodyweight, always available
        "<chip label>"     -> exactly one required item
        ("<chip>", "<chip>", ...) -> any ONE of these satisfies it
          (interchangeable equipment for the same movement)

    A client's `equipment` profile field is a comma-joined string of
    whichever chip labels the intake form left ticked (all ticked by
    default -> "full gym" client sends the full list, not a keyword).

ALIASES
    The form always sends exact chip labels, so alias resolution never
    fires for normal traffic. It exists as a safety net for non-form
    callers (tests, scripts, future integrations, manual API use) that
    might reasonably send a loose synonym instead of the exact chip
    string. Resolution is strictly additive: if a token already matches
    the canonical vocabulary (case-insensitively) it is used as-is;
    aliases are only consulted for tokens that don't.
"""

from __future__ import annotations

# ── EQUIPMENT VOCABULARY ──────────────────────────────────────────────────────
# Matches the exact chip labels from dashbord.html's EQUIPMENT array (the form
# posts a comma-joined string of whichever chips the user left ticked; all are
# ticked by default, so "full gym" clients send the full list, not a keyword).
FULL_EQUIPMENT_LIST = [
    "Barbell", "Dumbbells", "EZ curl bar", "Flat bench", "Incline/decline bench",
    "Squat rack", "Power rack / cage", "Smith machine", "Cable machine (dual stack)",
    "Lat pulldown", "Seated row machine", "Leg press", "Hack squat machine",
    "Leg extension machine", "Leg curl machine", "Chest press machine",
    "Shoulder press machine", "Pec deck / chest fly machine",
    "Assisted pull-up/dip machine", "Pull-up bar", "Dip station",
    "Preacher curl bench", "Hyperextension bench", "Calf raise machine",
    "Hip thrust machine / Smith setup", "Cable crossover", "Functional trainer",
    "Kettlebells", "Resistance bands", "Battle ropes", "Medicine balls",
    "TRX / suspension trainer", "Treadmill", "Stationary bike / spin bike",
    "Elliptical / cross-trainer", "Rowing machine", "Stair climber", "Foam roller",
]

_FULL_EQUIPMENT_LOWER = frozenset(e.lower() for e in FULL_EQUIPMENT_LIST)

# Loose synonyms a non-form caller might send instead of the exact chip
# label. Keys and values are already lowercased. Only consulted as a
# fallback (see normalize_equipment) — never overrides an exact match.
EQUIPMENT_ALIASES: dict[str, str] = {
    "dumbbell": "dumbbells",
    "db": "dumbbells",
    "barbells": "barbell",
    "bb": "barbell",
    "bench": "flat bench",
    "incline bench": "incline/decline bench",
    "decline bench": "incline/decline bench",
    "cable machine": "cable machine (dual stack)",
    "cable": "cable machine (dual stack)",
    "cables": "cable machine (dual stack)",
    "pulldown": "lat pulldown",
    "row machine": "seated row machine",
    "leg extension": "leg extension machine",
    "leg curl": "leg curl machine",
    "chest press": "chest press machine",
    "shoulder press machine ": "shoulder press machine",
    "pec deck": "pec deck / chest fly machine",
    "chest fly machine": "pec deck / chest fly machine",
    "assisted pull-up machine": "assisted pull-up/dip machine",
    "assisted dip machine": "assisted pull-up/dip machine",
    "pullup bar": "pull-up bar",
    "pull up bar": "pull-up bar",
    "dip bars": "dip station",
    "calf raise": "calf raise machine",
    "hip thrust machine": "hip thrust machine / smith setup",
    "cable crossover machine": "cable crossover",
    "kettlebell": "kettlebells",
    "kb": "kettlebells",
    "resistance band": "resistance bands",
    "bands": "resistance bands",
    "band": "resistance bands",
    "medicine ball": "medicine balls",
    "trx": "trx / suspension trainer",
    "suspension trainer": "trx / suspension trainer",
    "treadmills": "treadmill",
    "spin bike": "stationary bike / spin bike",
    "stationary bike": "stationary bike / spin bike",
    "elliptical": "elliptical / cross-trainer",
    "cross trainer": "elliptical / cross-trainer",
    "rowing machine (cardio)": "rowing machine",
    "stairmaster": "stair climber",
    "foam rolling": "foam roller",
}

# Loose phrases the intake form itself (or manual/legacy callers) may send
# in place of a comma-joined chip list.
_FULL_GYM_PHRASES = {"full gym", ""}
_NO_EQUIPMENT_PHRASES = {"bodyweight only", "no equipment", "none"}


def _resolve_token(token: str) -> str | None:
    """Resolve a single lowercased, stripped token to a canonical chip
    label (also lowercased), or None if it doesn't resolve to anything
    in the fixed vocabulary. Exact matches win; aliases are the fallback."""
    if not token:
        return None
    if token in _FULL_EQUIPMENT_LOWER:
        return token
    alias = EQUIPMENT_ALIASES.get(token)
    if alias in _FULL_EQUIPMENT_LOWER:
        return alias
    # Unknown token: not silently dropped from availability, since a client
    # could plausibly own something outside the fixed vocabulary that isn't
    # required by any exercise here. Passed through as-is so a `requires`
    # value that happens to match it (case-insensitively) still resolves.
    return token


def normalize_equipment(equipment_raw: str) -> frozenset[str]:
    """
    Parse the intake form's `equipment` field (or a legacy/manual caller's
    loose phrase) into a lowercased, alias-resolved set of available
    equipment item names.

    Behaviourally identical to the original
    exercise_database._parse_available_equipment for every input the form
    actually sends (exact chip labels, comma-joined, or the empty/"full
    gym" shortcut); alias resolution only changes results for inputs that
    were never part of the original vocabulary handling to begin with.
    """
    raw = str(equipment_raw or "").strip()
    low = raw.lower()

    if low in _FULL_GYM_PHRASES:
        return frozenset(_FULL_EQUIPMENT_LOWER)
    if low in _NO_EQUIPMENT_PHRASES:
        return frozenset()  # exercises with requires=None still work

    tokens = (t.strip().lower() for t in raw.split(","))
    resolved = (_resolve_token(t) for t in tokens if t.strip())
    return frozenset(t for t in resolved if t)


def is_full_gym(equipment_raw: str) -> bool:
    """True if the client's equipment normalizes to the entire vocabulary."""
    return normalize_equipment(equipment_raw) >= _FULL_EQUIPMENT_LOWER


def is_bodyweight_only(equipment_raw: str) -> bool:
    """True if the client has no tagged equipment at all (bodyweight-only
    exercises, `requires=None`, remain available regardless)."""
    return len(normalize_equipment(equipment_raw)) == 0


def substitution_hierarchy(requires) -> tuple:
    """
    Normalize an exercise's `requires` value into a tuple of interchangeable
    equipment options, for callers (e.g. exercise_selector.py) that need to
    enumerate alternatives rather than just check availability.

        None            -> ()      (bodyweight; no equipment options to list)
        "Barbell"       -> ("Barbell",)
        ("A", "B")      -> ("A", "B")   (already a hierarchy; returned as-is)
    """
    if requires is None:
        return ()
    if isinstance(requires, tuple):
        return requires
    return (requires,)


def requirement_met(requires, available_lower: frozenset | set) -> bool:
    """
    True if `requires` (None, a single chip label, or a tuple of
    interchangeable chip labels) is satisfied by the client's available
    equipment set (already lowercased, e.g. from normalize_equipment()).
    """
    if requires is None:
        return True
    if isinstance(requires, tuple):
        return any(r.lower() in available_lower for r in requires)
    return requires.lower() in available_lower


def any_requirement_available(requires, available_lower: frozenset | set) -> bool:
    """Alias of requirement_met, named for readability at call sites that
    are specifically checking substitution alternatives rather than a
    single exercise's own requirement."""
    return requirement_met(requires, available_lower)


def filter_by_equipment(pool: list, available_lower: frozenset | set, key: str = "requires") -> list:
    """
    Filter a list of exercise-like dicts down to those whose `key` field
    (default "requires") is satisfied by the available equipment set.
    Order is preserved; this does no injury filtering or fallback —
    callers needing the "relax equipment before ever relaxing injury
    safety" fallback behaviour should use exercise_selector.py's pool
    filter, which composes this with injury filtering explicitly.
    """
    return [item for item in pool if requirement_met(item.get(key), available_lower)]


def describe_missing(requires, available_lower: frozenset | set) -> str | None:
    """
    Human-readable description of what's missing for an unmet requirement,
    or None if it's already met (or requires nothing). Useful for surfacing
    "why was this swapped" context to the client or to Trainer Review.
    """
    if requirement_met(requires, available_lower):
        return None
    options = substitution_hierarchy(requires)
    if len(options) == 1:
        return f"requires {options[0]}"
    return f"requires one of: {', '.join(options)}"
