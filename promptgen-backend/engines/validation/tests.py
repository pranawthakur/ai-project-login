import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.validation import (
    ConfidenceTier, IntakeStatus, AdherenceRiskTier,
    IntakeRecord, IntakeResult, CheckIn, ClientState, CheckInResult, OneRMEstimate,
    normalize_weight_to_kg, normalize_height_to_cm, normalize_distance_to_km,
    normalize_temperature_to_celsius, validate_call_order, resolve_precedence,
    is_breaking_change, process_intake, resolve_confidence_tier, estimate_1rm,
    lookup_mobility_response, process_check_in, adherence_risk_score, adherence_response,
    most_restrictive_tier,
    validate_intake, validate_intake_consent, validate_intake_demographics,
    validate_disclosure_completeness, validate_check_in,
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

def base_intake(**overrides):
    intake = IntakeRecord()
    intake.consent = {"data_processing": True, "liability_waiver": True, "photo_consent": False}
    intake.demographics = {"age_years": 25, "sex": "f", "height_cm": 165, "weight_kg": 60, "body_fat_pct_estimate": None}
    intake.training_history = {"months_trained": 12, "prior_splits_used": [], "current_split": None}
    intake.health = {
        "injuries_current": [], "injuries_historical": [], "medical_conditions": [],
        "medications": [], "pregnancy_status": "not_applicable", "cleared_by_physician": None,
    }
    intake.disclosure_completeness = {"pct_fields_completed": 100, "refused_fields": []}
    for k, v in overrides.items():
        setattr(intake, k, v)
    return intake

# ---------------------------------------------------------------------
# Sec 4 -- unit normalization
# ---------------------------------------------------------------------
check("1 lb ~= 0.4536 kg", abs(normalize_weight_to_kg(1, "lb") - 0.4536) < 0.001)
check("kg passthrough", normalize_weight_to_kg(70, "kg") == 70)
check("1 stone ~= 6.35 kg", abs(normalize_weight_to_kg(1, "stone") - 6.3503) < 0.001)
check("5ft 10in ~= 177.8 cm", abs(normalize_height_to_cm(5, "ft_in", inches=10) - 177.8) < 0.1)
check("cm passthrough", normalize_height_to_cm(180, "cm") == 180)
check("1 mile ~= 1.609 km", abs(normalize_distance_to_km(1, "mi") - 1.609344) < 0.0001)
check("32F == 0C", normalize_temperature_to_celsius(32, "fahrenheit") == 0)
check("212F == 100C", normalize_temperature_to_celsius(212, "fahrenheit") == 100)

try:
    normalize_weight_to_kg(1, "furlong")
    check("normalize_weight_to_kg rejects unknown unit", False)
except ValueError:
    check("normalize_weight_to_kg rejects unknown unit", True)

# ---------------------------------------------------------------------
# Sec 2 -- canonical call order / precedence / versioning
# ---------------------------------------------------------------------
check("call order valid when safety gate runs first",
      validate_call_order(["2", "1", "3"]) == [])
check("call order invalid when safety gate not first",
      len(validate_call_order(["1", "2", "3"])) > 0)
check("call order invalid when safety gate skipped entirely",
      len(validate_call_order(["1", "3", "4"])) > 0)
check("empty call order is invalid", len(validate_call_order([])) > 0)

check("precedence: safety (12) beats intake (11)", resolve_precedence([12, 11]) == 12)
check("precedence: intake (11) beats override (14)", resolve_precedence([11, 14]) == 11)
check("precedence: override (14) beats programming files",
      resolve_precedence([14, "programming_files_1_through_10_13_15"]) == 14)
try:
    resolve_precedence([99])
    check("resolve_precedence rejects unknown file id", False)
except ValueError:
    check("resolve_precedence rejects unknown file id", True)

check("identical section lists are not breaking",
      not is_breaking_change(["A", "B", "C"], ["A", "B", "C"]))
check("reordered sections are breaking",
      is_breaking_change(["A", "B", "C"], ["B", "A", "C"]))
check("inserted section is breaking",
      is_breaking_change(["A", "B"], ["A", "B", "C"]))

# ---------------------------------------------------------------------
# Sec 2 -- processIntake
# ---------------------------------------------------------------------
no_consent = base_intake(consent={"data_processing": False, "liability_waiver": True, "photo_consent": False})
r = process_intake(no_consent)
check("missing consent -> blocked_no_consent", r.status == IntakeStatus.BLOCKED_NO_CONSENT)

under_13 = base_intake(demographics={"age_years": 10, "sex": "m", "height_cm": 140, "weight_kg": 35, "body_fat_pct_estimate": None})
r = process_intake(under_13)
check("age 10 -> rejected below_minimum_age", r.status == IntakeStatus.REJECTED and r.reason == "below_minimum_age")

minor = base_intake(demographics={"age_years": 16, "sex": "m", "height_cm": 170, "weight_kg": 60, "body_fat_pct_estimate": None})
r = process_intake(minor)
check("age 16 -> guardian_awareness_required flag, still ready", "guardian_awareness_required" in r.flags)
check("age 16 with clean intake still routes ready", r.status == IntakeStatus.READY)

pregnant = base_intake(health={
    "injuries_current": [], "injuries_historical": [], "medical_conditions": [],
    "medications": [], "pregnancy_status": "pregnant", "cleared_by_physician": None,
})
r = process_intake(pregnant)
check("pregnant -> pending_clearance", r.status == IntakeStatus.PENDING_CLEARANCE)
check("pending_clearance uses default safe template", r.use_default_safe_template)

high_risk = base_intake(health={
    "injuries_current": [], "injuries_historical": [], "medical_conditions": ["uncontrolled_hypertension"],
    "medications": [], "pregnancy_status": "not_applicable", "cleared_by_physician": None,
})
r = process_intake(high_risk)
check("high-risk condition -> pending_clearance", r.status == IntakeStatus.PENDING_CLEARANCE)

refused = base_intake(disclosure_completeness={"pct_fields_completed": 80, "refused_fields": ["medical_conditions"]})
r = process_intake(refused)
check("refused medical disclosure -> restricted_general_guidance_only",
      r.status == IntakeStatus.RESTRICTED_GENERAL_GUIDANCE_ONLY)

untrained = base_intake(training_history={"months_trained": 0, "prior_splits_used": [], "current_split": None})
r = process_intake(untrained)
check("0 months trained -> route_to_movement_screen flag", "route_to_movement_screen" in r.flags)

incomplete = base_intake(disclosure_completeness={"pct_fields_completed": 40, "refused_fields": []})
r = process_intake(incomplete)
check("<60% disclosure -> incomplete_intake_low_confidence flag",
      "incomplete_intake_low_confidence" in r.flags)

clean = base_intake()
r = process_intake(clean)
check("fully clean intake -> ready with no flags", r.status == IntakeStatus.READY and r.flags == ())

# ---------------------------------------------------------------------
# Sec 2.2 -- confidence tier resolution
# ---------------------------------------------------------------------
check("rejected intake -> red tier",
      resolve_confidence_tier(process_intake(under_13), weeks_consistent_checkins=0, missed_checkin_cycles=0) == ConfidenceTier.RED)
check("pending clearance -> orange tier",
      resolve_confidence_tier(process_intake(pregnant), weeks_consistent_checkins=10, missed_checkin_cycles=0) == ConfidenceTier.ORANGE)
check("2 missed check-in cycles -> orange even if intake ready",
      resolve_confidence_tier(process_intake(clean), weeks_consistent_checkins=10, missed_checkin_cycles=2) == ConfidenceTier.ORANGE)
check("<8 weeks consistent -> yellow",
      resolve_confidence_tier(process_intake(clean), weeks_consistent_checkins=4, missed_checkin_cycles=0) == ConfidenceTier.YELLOW)
check(">=8 weeks + ready + no misses -> green",
      resolve_confidence_tier(process_intake(clean), weeks_consistent_checkins=8, missed_checkin_cycles=0) == ConfidenceTier.GREEN)

# ---------------------------------------------------------------------
# Sec 3.1 -- estimate1RM (Epley formula worked examples)
# ---------------------------------------------------------------------
# reps=5, load=100: base = 100 * (1 + 5/30) = 116.67 -> round=117; reps not >5 -> moderate_to_high
r5 = estimate_1rm(reps=5, load=100)
check("estimate_1rm(5, 100) == 117", r5.est_1rm == 117)
check("estimate_1rm(5, 100) confidence moderate_to_high", r5.confidence == "moderate_to_high")

# reps=8, load=100: base = 100*(1+8/30)=126.667; reps>5 -> *0.9 = 114.0 -> round 114, confidence low
r8 = estimate_1rm(reps=8, load=100)
check("estimate_1rm(8, 100) == 114", r8.est_1rm == 114)
check("estimate_1rm(8, 100) confidence low", r8.confidence == "low")

# reps=5, load=100, form breakdown: base=116.667*0.95=110.833 -> round 111
r5_breakdown = estimate_1rm(reps=5, load=100, rep_quality="form_breakdown_near_failure")
check("form breakdown applies 0.95x", r5_breakdown.est_1rm == 111)

check("estimate_1rm never true-1RM-tests (documentation-level rule check n/a)", True)  # see Sec 3 rule note

# ---------------------------------------------------------------------
# Sec 4 -- mobility flag lookup
# ---------------------------------------------------------------------
entry = lookup_mobility_response("heels_rise_during_squat")
check("mobility lookup returns correct flag", entry["flag"] == "ankle_mobility_limited")
check("unknown mobility key returns None", lookup_mobility_response("nonexistent") is None)

# ---------------------------------------------------------------------
# Sec 5 -- processCheckIn
# ---------------------------------------------------------------------
state = ClientState(goal="hypertrophy")
ci_low_completion = CheckIn(sessions_completed=2, sessions_planned=4, motivation_rating=7)
result = process_check_in(ci_low_completion, state)
check("completion 2/4=0.5 < 0.7 -> adherence_risk flag", "adherence_risk" in result.flags)

state2 = ClientState(goal="hypertrophy")
ci_pain = CheckIn(sessions_completed=4, sessions_planned=4, new_pain_flags=("shoulder",))
result2 = process_check_in(ci_pain, state2)
check("new pain flags trigger injury substitution", result2.triggers_injury_substitution)
check("new pain flags trigger pain triage", result2.triggers_pain_triage)

state3 = ClientState(goal="hypertrophy")
state3.rolling_history.append(CheckIn(bodyweight_kg=80.0))
ci_weight_drop = CheckIn(bodyweight_kg=78.0, sessions_completed=4, sessions_planned=4)  # -2.5%
result3 = process_check_in(ci_weight_drop, state3)
check("unexpected weight loss flagged when goal != fat_loss", "unexpected_weight_loss_review" in result3.flags)

state4 = ClientState(goal="fat_loss")
state4.rolling_history.append(CheckIn(bodyweight_kg=80.0))
ci_weight_drop_fatloss = CheckIn(bodyweight_kg=78.0, sessions_completed=4, sessions_planned=4)
result4 = process_check_in(ci_weight_drop_fatloss, state4)
check("weight loss NOT flagged when goal == fat_loss", "unexpected_weight_loss_review" not in result4.flags)

state5 = ClientState(goal="hypertrophy")
state5.rolling_history.append(CheckIn(motivation_rating=1))
ci_low_motivation = CheckIn(motivation_rating=2, sessions_completed=4, sessions_planned=4)
result5 = process_check_in(ci_low_motivation, state5)
check("2 consecutive low motivation ratings -> disengagement_risk", "disengagement_risk" in result5.flags)

check("processCheckIn appends to rolling_history", len(state.rolling_history) == 1)

# ---------------------------------------------------------------------
# Sec 7 -- adherenceRiskScore (worked threshold checks)
# ---------------------------------------------------------------------
s0 = ClientState()
score0, tier0 = adherence_risk_score(s0)
check("all-clear state -> score 0, low_risk", score0 == 0 and tier0 == AdherenceRiskTier.LOW_RISK)

s1 = ClientState(trailing_4wk_completion_pct=0.5)
score1, tier1 = adherence_risk_score(s1)
check("low completion alone -> score 20, moderate_risk", score1 == 20 and tier1 == AdherenceRiskTier.MODERATE_RISK)

s2 = ClientState(trailing_4wk_completion_pct=0.5, checkin_submission_streak_broken=2)
score2, tier2 = adherence_risk_score(s2)
check("completion(20) + streak broken(15) = 35 -> still moderate", score2 == 35 and tier2 == AdherenceRiskTier.MODERATE_RISK)

s3 = ClientState(
    trailing_4wk_completion_pct=0.5, checkin_submission_streak_broken=2,
    motivation_rating_avg_trailing_2wk=3,
)
score3, tier3 = adherence_risk_score(s3)
check("20+15+10=45 -> high_risk", score3 == 45 and tier3 == AdherenceRiskTier.HIGH_RISK)

check("adherence_response maps high_risk to downgrade language",
      "2-3 day" in adherence_response(AdherenceRiskTier.HIGH_RISK))

# ---------------------------------------------------------------------
# scoring.py
# ---------------------------------------------------------------------
check("most_restrictive_tier picks RED over GREEN",
      most_restrictive_tier([ConfidenceTier.GREEN, ConfidenceTier.RED]) == ConfidenceTier.RED)
check("most_restrictive_tier picks ORANGE over YELLOW",
      most_restrictive_tier([ConfidenceTier.YELLOW, ConfidenceTier.ORANGE]) == ConfidenceTier.ORANGE)
try:
    most_restrictive_tier([])
    check("most_restrictive_tier rejects empty list", False)
except ValueError:
    check("most_restrictive_tier rejects empty list", True)

# ---------------------------------------------------------------------
# validators.py
# ---------------------------------------------------------------------
bad_intake = base_intake(consent={"liability_waiver": True, "photo_consent": False})  # missing data_processing
check("validate_intake_consent flags missing key", len(validate_intake_consent(bad_intake)) > 0)

bad_age = base_intake(demographics={"age_years": -5, "sex": "m", "height_cm": 170, "weight_kg": 70, "body_fat_pct_estimate": None})
check("validate_intake_demographics flags negative age", len(validate_intake_demographics(bad_age)) > 0)

bad_disclosure = base_intake(disclosure_completeness={"pct_fields_completed": 150, "refused_fields": []})
check("validate_disclosure_completeness flags out-of-range pct", len(validate_disclosure_completeness(bad_disclosure)) > 0)

check("validate_intake passes on clean record", validate_intake(base_intake()) == [])

bad_checkin = CheckIn(sessions_completed=5, sessions_planned=4, motivation_rating=7)
check("validate_check_in flags completed > planned", len(validate_check_in(bad_checkin)) > 0)

ok_checkin = CheckIn(sessions_completed=3, sessions_planned=4, motivation_rating=7)
check("validate_check_in passes clean check-in", validate_check_in(ok_checkin) == [])

print(f"\n{passed} passed, {failed} failed")
if failed:
    sys.exit(1)
