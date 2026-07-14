"""Deterministic logic ported from KB V7 file 15 (Supplement Safety &
Interaction Engine). Scope: OTC evidence-supported sports supplements
only. Never provides dosing for prescription substances; never overrides
file 12 medical constraints."""
from typing import Optional, Dict, Any, List
from .models import SupplementDecision, GateResult, ClientSupplementContext
from . import lookup_tables as T


def _find_supplement(name: str) -> Optional[tuple]:
    if name in T.TIER_1_SUPPLEMENTS:
        return ("tier1", T.TIER_1_SUPPLEMENTS[name])
    if name in T.TIER_2_SUPPLEMENTS:
        return ("tier2", T.TIER_2_SUPPLEMENTS[name])
    if name in T.TIER_3_SUBSTANCES:
        return ("tier3", T.TIER_3_SUBSTANCES[name])
    return None


# =====================================================================
# SECTION 4 -- INTERACTION CHECK (must run before any recommendation)
# =====================================================================

def check_interactions(supplement: str, context: ClientSupplementContext) -> List[Dict[str, str]]:
    """Section 9 troubleshooting rule made explicit: this must be called
    and its results applied BEFORE any Tier 1/2 recommendation is issued."""
    flags = []
    matrix_entry = T.INTERACTION_MATRIX.get(supplement, {})
    for condition in context.disclosed_conditions:
        if condition in matrix_entry:
            flags.append({"condition": condition, "flag": matrix_entry[condition]})
    for med in context.medications:
        if med in matrix_entry:
            flags.append({"medication": med, "flag": matrix_entry[med]})
    if context.pregnant:
        preg_flag = T.INTERACTION_MATRIX.get("any_stimulant_containing_product", {}).get("pregnancy")
        if preg_flag and supplement in ("caffeine", "multi_ingredient_preworkout"):
            flags.append({"condition": "pregnancy", "flag": preg_flag})
    return flags


# =====================================================================
# MAIN GATE
# =====================================================================

def evaluate_supplement(supplement: str, context: ClientSupplementContext) -> SupplementDecision:
    lookup = _find_supplement(supplement)
    if lookup is None:
        return SupplementDecision(GateResult.CAUTION, "unknown_supplement_default_conservative",
                                    message="Not in the known supplement set; recommend physician/label review.")

    tier, entry = lookup

    # Section 8 edge case: pregnancy routes through file 12 pregnancy constraints first,
    # only Tier 1 electrolytes/vitamin D (with physician guidance) ever considered.
    if context.pregnant and not (tier == "tier1" and supplement in ("electrolytes", "vitamin_d")):
        return SupplementDecision(GateResult.REFUSE, "route_through_pregnancy_constraints_file_12_sec_4",
                                    message="Deferred to physician per pregnancy protocol.")

    # Section 8 edge case: under-18 -> Tier 1 only
    if context.age is not None and context.age < 18 and tier != "tier1":
        return SupplementDecision(GateResult.REFUSE, "under_18_tier1_only_requires_guardian_coach_involvement")

    if tier == "tier3":
        return SupplementDecision(GateResult.REFUSE, entry["behavior"],
                                    data={"tier": "tier3", **({"if_disclosed": entry["if_disclosed"]} if "if_disclosed" in entry else {})})

    interactions = check_interactions(supplement, context)

    if tier == "tier1":
        if supplement == "protein_powder" and context.lactose_intolerant:
            return SupplementDecision(GateResult.CONDITIONAL, "flag_lactose_intolerance_recommend_isolate_or_plant",
                                        data={"interactions": interactions})
        if supplement == "creatine_monohydrate" and "kidney_disease" in context.disclosed_conditions:
            return SupplementDecision(GateResult.REFUSE, entry["contraindication"], data={"interactions": interactions})
        if supplement == "caffeine" and interactions:
            return SupplementDecision(GateResult.CAUTION, "stimulant_caution_reduce_or_avoid", data={"interactions": interactions})
        if interactions:
            return SupplementDecision(GateResult.CAUTION, "interaction_flagged_review_before_recommending",
                                        data={"interactions": interactions})
        return SupplementDecision(GateResult.RECOMMEND, "tier1_default_recommendable", data={"details": entry})

    if tier == "tier2":
        if interactions:
            return SupplementDecision(GateResult.CAUTION, "interaction_flagged_review_before_recommending",
                                        data={"interactions": interactions})
        if supplement == "multi_ingredient_preworkout" and context.anxiety_disorder_disclosed:
            return SupplementDecision(GateResult.CAUTION, "anxiety_disclosed_avoid_stacked_stimulants")
        return SupplementDecision(GateResult.CONDITIONAL, "tier2_conditional_on_stated_condition_met",
                                    data={"condition_required": entry["condition"], "flag": entry["flag"]})

    return SupplementDecision(GateResult.CAUTION, "unclassified_fallback")


# =====================================================================
# SECTION 5 -- GI DISTRESS TRIAGE
# =====================================================================

def gi_distress_triage(reported_symptom: str, multiple_supplements_started_same_week: bool = False) -> str:
    if multiple_supplements_started_same_week:
        return T.GI_MULTIPLE_SUPPLEMENTS_RESPONSE
    response = T.GI_DISTRESS_RESPONSES.get(reported_symptom)
    if response is None:
        return "insufficient_information_gather_more_detail_before_advising"
    return response


# =====================================================================
# SECTION 6 -- TESTED ATHLETE OVERLAY
# =====================================================================

def tested_athlete_overlay(competes_in_tested_federation: bool) -> Dict[str, Any]:
    if not competes_in_tested_federation:
        return {"applies": False}
    return {
        "applies": True,
        "flag": "banned_substance_screening_required",
        "recommendation": "check_against_batch_tested_certified_list_before_use",
        "note": "system_does_not_maintain_live_banned_substance_database_must_say_so",
        "tier1_not_automatically_safe": True,  # contamination risk exists even for basic products
    }


# =====================================================================
# SECTION 8 -- EDGE CASES
# =====================================================================

def handle_steroid_protocol_request(already_asked_once: bool = False) -> Dict[str, Any]:
    """Decline to provide protocol; restate once if client persists, then
    redirect rather than repeatedly lecturing."""
    if already_asked_once:
        return {"action": "redirect_to_what_system_can_help_with", "repeat_lecture": False}
    return {"action": T.EDGE_CASE_STEROID_REQUEST_RESPONSE}


def handle_midcycle_programming_request() -> Dict[str, Any]:
    return dict(T.EDGE_CASE_MIDCYCLE_RESPONSE)


def creatine_needs_loading_phase() -> bool:
    return T.CREATINE_LOADING_PHASE_REQUIRED
