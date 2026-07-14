"""Confidence/risk scoring used by the triage dispatcher (file 20 Section 5)."""

CONFIDENCE_TABLE = [
    {"signal": "no_symptom_reported", "confidence": 0.99, "action": "proceed_normally"},
    {"signal": "vague_incomplete_low_severity", "confidence": 0.0, "action": "always_request_follow_up"},
    {"signal": "clear_mild_benign_pattern", "confidence": 0.75, "action": "proceed_with_monitoring"},
    {"signal": "matches_known_injury_or_condition_table", "confidence": None, "action": "follow_that_protocol_exactly"},
    {"signal": "ambiguous_emergency_adjacent", "confidence": 0.0, "action": "route_through_emergency_list_check_first"},
]


def confidence_for(signal: str) -> dict:
    for row in CONFIDENCE_TABLE:
        if row["signal"] == signal:
            return row
    # unlisted signal -- fail conservative per file 20's overriding rule
    return {"signal": signal, "confidence": 0.0, "action": "treat_as_needing_escalation_check"}


def resolve_ambiguous(option_a_confidence: float, option_b_confidence: float,
                       option_a_is_more_conservative: bool) -> str:
    """When genuinely uncertain between two branches, always take the more
    conservative one -- never the one permitting a 'better' workout."""
    return "option_a" if option_a_is_more_conservative else "option_b"
