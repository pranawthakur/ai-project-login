"""
Configuration Management (Engine 33) — scoped to what this app actually
is: a single FastAPI process + Supabase, not a multi-service deployment
with a config-management system to orchestrate. What that means here:
one place that KNOWS about every hardcoded tunable that used to be
scattered inline across main.py, with each one's source, rationale, and
whether it's a deliberate test override — instead of a future session
finding `REASSESSMENT_INTERVAL_MINUTES_TEST = 5` inline and "fixing" it
without knowing it was intentional (see HANDOFF.md session 24).

This does NOT wrap secrets (SUPABASE_URL etc.) — those stay exactly where
they've always been, in app/config.py's pydantic Settings, loaded from
.env. Duplicating that here would be a second source of truth for
security-relevant values, which is the opposite of what a real
configuration-management engine should do. This only covers behavioral
tunables: cycle length, plan validity, rest defaults — values that change
what the app DOES, not values that authenticate it.
"""

from __future__ import annotations

# Each entry: (value, is_test_override, rationale). Reading FROM here
# (not redefining inline) is what makes this a real single source of
# truth rather than documentation that can silently drift from the code.
_REGISTRY = {
    "reassessment_interval_minutes": {
        "value": 14 * 24 * 60,  # 20160 — real 14-day cycle length, in minutes
        "is_test_override": False,
        "rationale": (
            "Real 14-day cycle length. Was deliberately 5 minutes during "
            "dev testing (session 24) so the check-in -> plan-expiry -> "
            "regenerate flow could be exercised without a 2-week wait. "
            "Reverted to production value ahead of final submission."
        ),
    },
    "plan_validity_days": {
        "value": 14,
        "is_test_override": False,
        "rationale": "Real cycle length — a generated plan/diet stays active for 14 days.",
    },
    "intra_cycle_adaptation_enabled": {
        "value": True,
        "is_test_override": False,
        "rationale": "Session 17's same-week hold/substitute feature. On by default.",
    },
}


def get_config(key: str):
    """Real value for one tunable. Raises KeyError if unregistered — fail
    loud rather than silently returning None for a typo'd key name."""
    return _REGISTRY[key]["value"]


def get_full_config() -> dict:
    """Everything in the registry, INCLUDING the is_test_override flags
    and rationale — the whole point of this engine over a bare constant
    is that a caller (an admin endpoint, a future session) can see WHICH
    values are deliberately non-production and why, not just what the
    current number is."""
    return {k: dict(v) for k, v in _REGISTRY.items()}


def get_test_overrides() -> dict:
    """Just the subset flagged is_test_override — the specific list a
    pre-launch checklist should review before going to real users."""
    return {k: v for k, v in _REGISTRY.items() if v["is_test_override"]}
