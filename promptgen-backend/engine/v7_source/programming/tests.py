import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.programming import (
    ConfidenceTier, OverrideRequest, ClientProgrammingState,
    build_default_safe_template, can_exit_safe_template,
    check_override_permission, apply_override, escalated_override_check,
    resolve_conflicting_overrides, evaluate_tier_transition, determine_tier_from_state,
)

passed = 0
failed = 0

def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {name}")

# --- build_default_safe_template ---
tmpl = build_default_safe_template()
check("template has 6 exercise patterns", len(tmpl.exercises) == 6)
check("no intensity techniques permitted", tmpl.intensity_techniques_permitted is False)
check("no HIIT permitted", tmpl.hiit_permitted is False)
check("never_includes has 5 rules", len(tmpl.never_includes) == 5)

tmpl2 = build_default_safe_template(pain_provoking_movements=["glute_bridge"])
squat_pattern = [e for e in tmpl2.exercises if e.pattern == "hinge"][0]
check("pain-flagged exercise gets regressed", squat_pattern.exercise == "supported_glute_bridge_feet_elevated_less")

# --- can_exit_safe_template (fail-closed logic) ---
check("unresolved medical clearance blocks exit",
      can_exit_safe_template(ClientProgrammingState(
          flags=["medical_clearance_required"], medical_clearance_resolved=False)) is False)
check("below_minimum_age_reject is permanent block",
      can_exit_safe_template(ClientProgrammingState(flags=["below_minimum_age_reject"])) is False)
check("orange due to missed checkins, 2 consecutive submitted -> exit allowed",
      can_exit_safe_template(ClientProgrammingState(
          confidence_tier=ConfidenceTier.ORANGE, consecutive_checkins_submitted=2, flags=[])) is True)
check("orange due to missed checkins, only 1 submitted -> still blocked (fail closed)",
      can_exit_safe_template(ClientProgrammingState(
          confidence_tier=ConfidenceTier.ORANGE, consecutive_checkins_submitted=1, flags=[])) is False)
check("orange due to pain flag resolved + reintro completed -> exit allowed",
      can_exit_safe_template(ClientProgrammingState(
          confidence_tier=ConfidenceTier.ORANGE, pain_flag_resolved=True,
          reintroduce_pattern_completed=True)) is True)
check("movement screen never run -> blocked",
      can_exit_safe_template(ClientProgrammingState(movement_screen_completed=False,
                                                      confidence_tier=ConfidenceTier.GREEN)) is False)
check("ambiguous/no criteria met -> fail closed default False",
      can_exit_safe_template(ClientProgrammingState(movement_screen_completed=True,
                                                      confidence_tier=ConfidenceTier.GREEN)) is False)

# --- override permissions (Section 2.1) ---
check("exercise substitution overridable", check_override_permission("exercise_selection_substitution") is True)
check("emergency symptom stop NEVER overridable", check_override_permission("emergency_symptom_stop") is False)
check("below_minimum_age_reject NEVER overridable", check_override_permission("below_minimum_age_reject") is False)
check("unknown field fails closed (not overridable)", check_override_permission("some_made_up_field") is False)

# --- apply_override ---
uncert_req = OverrideRequest("o1", "c1", False, "cl1", "t1", "exercise_selection_substitution", "rec", "dec", "note")
check("uncertified coach blocked", apply_override(uncert_req).allowed is False)

emergency_req = OverrideRequest("o2", "c1", True, "cl1", "t1", "emergency_symptom_stop", "rec", "dec", "note")
check("emergency stop cannot be overridden even by certified coach", apply_override(emergency_req).allowed is False)

good_req = OverrideRequest("o3", "c1", True, "cl1", "t1", "exercise_selection_substitution", "rec", "dec", "swap for knee pain")
res = apply_override(good_req)
check("valid override allowed", res.allowed is True)
check("audit entry marked immutable", res.audit_entry.get("immutable") is True)

# --- escalated override (Section 2.3) ---
esc_req_short_note = OverrideRequest("o4", "c1", True, "cl1", "t1", "volume_intensity_within_same_tier",
                                       "rec", "dec", "too short", in_person_supervision_confirmed=True)
check("escalated override rejects short justification", escalated_override_check(esc_req_short_note, "volume_intensity_within_same_tier").allowed is False)

esc_req_no_supervision = OverrideRequest("o5", "c1", True, "cl1", "t1", "volume_intensity_within_same_tier",
                                           "rec", "dec", "a sufficiently long justification note here",
                                           in_person_supervision_confirmed=False)
check("escalated override requires in-person supervision", escalated_override_check(esc_req_no_supervision, "volume_intensity_within_same_tier").allowed is False)

esc_req_good = OverrideRequest("o6", "c1", True, "cl1", "t1", "volume_intensity_within_same_tier",
                                 "rec", "dec", "a sufficiently long justification note here",
                                 in_person_supervision_confirmed=True)
esc_res = escalated_override_check(esc_req_good, "volume_intensity_within_same_tier")
check("valid escalated override allowed and flagged for review", esc_res.allowed is True and esc_res.review_flag is True)

esc_req_noverride_field = OverrideRequest("o7", "c1", True, "cl1", "t1", "emergency_symptom_stop",
                                            "rec", "dec", "a sufficiently long justification note here",
                                            in_person_supervision_confirmed=True)
check("escalated override still can't touch Section 2.1 No-rows", escalated_override_check(esc_req_noverride_field, "emergency_symptom_stop").allowed is False)

# --- conflicting overrides ---
overrides = [
    {"override_id": "a", "timestamp": "2026-07-01T10:00:00"},
    {"override_id": "b", "timestamp": "2026-07-01T14:00:00"},
]
result = resolve_conflicting_overrides(overrides)
check("most recent override is active", result["active"]["override_id"] == "b")
check("both remain in audit trail", len(result["audit_trail"]) == 2)

# --- tier transitions ---
check("known transition trigger resolves",
      evaluate_tier_transition(ClientProgrammingState(), "exit_criteria_met_section_1_5") is not None)
check("unknown trigger returns None", evaluate_tier_transition(ClientProgrammingState(), "made_up_trigger") is None)

check("determine tier: below age flag -> red",
      determine_tier_from_state(ClientProgrammingState(flags=["below_minimum_age_reject"])) == ConfidenceTier.RED)
check("determine tier: unresolved clearance -> orange",
      determine_tier_from_state(ClientProgrammingState(flags=["medical_clearance_required"],
                                                         medical_clearance_resolved=False)) == ConfidenceTier.ORANGE)
check("determine tier: 8wk consistent + full intake + no flags -> green",
      determine_tier_from_state(ClientProgrammingState(weeks_consistent_checkins=8, intake_completeness_pct=95.0,
                                                         flags=[])) == ConfidenceTier.GREEN)

print(f"\n{passed} passed, {failed} failed")
if failed:
    raise SystemExit(1)
