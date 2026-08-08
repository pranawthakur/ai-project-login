import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.constraints import (
    Decision, GateResult, ClientState, SessionInput, HealthReport, ConfidenceTier,
    safety_gate, pain_triage, condition_constraints, medication_flags, ed_safety_route,
    reintroduce_pattern, age_overlay, environmental_flags, check_recurring_pattern_pain,
    route_injury, detect_recurring_injury_pattern, route_chronic_condition,
    resolve_multi_condition_conflict, classify_health_report, todays_session_decision,
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

# --- safety_gate ---
check("red tier blocks", safety_gate(ClientState(confidence_tier=ConfidenceTier.RED), SessionInput()).blocked())
check("pain>=7 blocks", safety_gate(ClientState(), SessionInput(reported_pain_scale=8)).blocked())
check("emergency symptom blocks", safety_gate(ClientState(), SessionInput(contains_emergency_symptom=True)).blocked())
check("unresolved clearance restricts",
      safety_gate(ClientState(flags=["medical_clearance_required"], medical_clearance_resolved=False),
                  SessionInput()).result == GateResult.RESTRICT)
check("clean state proceeds", safety_gate(ClientState(), SessionInput()).result == GateResult.PROCEED)

# --- pain_triage ---
check("sharp sudden joint pain -> remove pattern",
      pain_triage(SessionInput(pain_type="sharp_localized_joint", pain_onset="sudden")).action
      == "stop_pattern_refer_to_professional")
check("mild doms proceeds",
      pain_triage(SessionInput(pain_type="dull_muscular", reported_pain_scale=2, pain_improves_with_warmup=True)).result
      == GateResult.PROCEED)
check("persists beyond 72h escalates",
      pain_triage(SessionInput(pain_persists_beyond_72h=True)).blocked())

# --- condition_constraints ---
check("uncontrolled hypertension blocks", condition_constraints("hypertension_uncontrolled").blocked())
check("controlled hypertension restricts rpe cap",
      condition_constraints("hypertension_controlled").data.get("rpe_cap") == 8)
check("cardiac history blocks", condition_constraints("cardiac_history_any").blocked())

# --- medication_flags ---
mf = medication_flags(["beta_blockers", "blood_thinners", "unknown_med"])
check("medication flags found for known meds", len(mf) == 2)
check("beta blocker flag correct", any(m["flag"] == "heart_rate_response_blunted" for m in mf))

# --- ed_safety_route ---
check("diagnosed ed restricts", ed_safety_route(True, []).result == GateResult.RESTRICT)
check("single behavioral flag insufficient (threshold=2)",
      ed_safety_route(False, ["extreme_restriction_language"]).result == GateResult.PROCEED)
check("two behavioral flags trigger restriction",
      ed_safety_route(False, ["extreme_restriction_language", "compulsive_exercise_language"]).result
      == GateResult.RESTRICT)

# --- reintroduce_pattern ---
check("too early (<2wk) restricts", reintroduce_pattern(1).action == "too_early_continue_substitution")
check("pain-free 2 sessions -> increase load",
      reintroduce_pattern(3, pain_free_sessions_at_current_step=2).action == "increase_load_10_20_percent")
check("2nd recurrence -> professional eval",
      reintroduce_pattern(3, pain_recurred=True, recurrence_count=2).action
      == "reset_to_substitution_recommend_professional_eval")

# --- age_overlay ---
check("teen overlay requires guardian consent", age_overlay(15)["guardian_consent_required"] is True)
check("senior overlay caps rpe", age_overlay(70)["rpe_cap"] == 7)
check("adult standard rules", age_overlay(30) == {"standard_rules": True})

# --- environmental_flags ---
ef = environmental_flags(["extreme_heat_humidity_no_acclimation", "nonexistent_signal"])
check("environmental flag matched", len(ef) == 1 and ef[0]["flag"] == "heat_illness_risk")

# --- recurring pattern pain (file 12 edge case) ---
check("3 distinct pattern flags escalates",
      check_recurring_pattern_pain(ClientState(distinct_pattern_pain_flags_this_mesocycle=3)) is not None)
check("2 flags does not escalate (file 12 threshold)",
      check_recurring_pattern_pain(ClientState(distinct_pattern_pain_flags_this_mesocycle=2)) is None)

# --- route_injury (file 18) ---
check("emergency severity blocks", route_injury(None, "emergency_symptom", ClientState()).blocked())
check("known injury type routes to its protocol",
      route_injury("low_back_strain_nonspecific", None, ClientState()).result in (GateResult.RESTRICT, GateResult.PROCEED, GateResult.BLOCK))
check("unknown injury type -> generic protocol handles gracefully",
      route_injury("some_unlisted_injury", None, ClientState()).action in
      ("professional_eval_required", "remove_affected_region_exercise", "reduce_load_30_50pct_monitor_1_week", "log_for_monitoring_only"))
check("no injury type -> insufficient information",
      route_injury(None, None, ClientState()).action == "insufficient_information")

# --- detect_recurring_injury_pattern ---
check("3x same region -> full reeval flag",
      detect_recurring_injury_pattern(3, 0).action == "flag_recurring_injury_pattern")
check("4 distinct regions -> systemic flag",
      detect_recurring_injury_pattern(0, 4).action == "flag_possible_systemic_or_programming_error_pattern")
check("no pattern -> no action", detect_recurring_injury_pattern(0, 0).action == "no_special_action")

# --- route_chronic_condition (file 19) ---
check("high risk condition without clearance blocks",
      route_chronic_condition("hypertension_uncontrolled", ClientState(medical_clearance_resolved=False)).blocked()
      or route_chronic_condition("cardiac_history_any", ClientState(medical_clearance_resolved=False)).blocked())
check("known condition routes to specific protocol",
      route_chronic_condition("pcos", ClientState()).result == GateResult.PROCEED)
check("unknown condition -> generic protocol, safe default",
      route_chronic_condition("unlisted_condition_xyz", ClientState()).result == GateResult.RESTRICT)

# --- resolve_multi_condition_conflict ---
check("clearance trigger overrides everything",
      resolve_multi_condition_conflict(["a", "b"], True).blocked())
check("3+ conditions flags complexity",
      resolve_multi_condition_conflict(["a", "b", "c"], False).action == "flag_complex_multi_condition_case")

# --- file 20 dispatcher ---
check("emergency match handoff",
      classify_health_report(HealthReport(matches_emergency_list=True)).action == "handoff_emergency_gate")
check("vague report requests follow-up",
      classify_health_report(HealthReport(is_vague_or_incomplete=True)).action == "request_structured_follow_up")
check("nothing matches -> log for monitoring (defined fallback, never undefined)",
      classify_health_report(HealthReport()).action == "log_for_monitoring")

# --- todays_session_decision fail-conservative default ---
fake_decision = Decision(GateResult.PROCEED, "some_unmapped_action_key")
d = todays_session_decision(fake_decision)
check("unmapped action fails conservative (never full unmodified session)",
      d.result == GateResult.RESTRICT)

# --- cross-engine wiring: safety_gate now returns a REAL template, not a string key ---
gated = safety_gate(ClientState(flags=["medical_clearance_required"], medical_clearance_resolved=False), SessionInput())
check("restricted client gets real SafeTemplate object, not a string placeholder",
      "template" in gated.data and len(gated.data["template"].exercises) == 6)
check("real safe template has no HIIT/intensity techniques permitted",
      gated.data["template"].hiit_permitted is False and gated.data["template"].intensity_techniques_permitted is False)

print(f"\n{passed} passed, {failed} failed")
if failed:
    raise SystemExit(1)
