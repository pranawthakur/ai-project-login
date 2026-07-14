import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.nutrition import (
    SupplementDecision, GateResult, ClientSupplementContext,
    check_interactions, evaluate_supplement, gi_distress_triage, tested_athlete_overlay,
    handle_steroid_protocol_request, handle_midcycle_programming_request, creatine_needs_loading_phase,
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

# --- Tier 1 default recommendable ---
r = evaluate_supplement("electrolytes", ClientSupplementContext())
check("electrolytes default recommend, no flags", r.result == GateResult.RECOMMEND)

# --- protein + lactose intolerance ---
r = evaluate_supplement("protein_powder", ClientSupplementContext(lactose_intolerant=True))
check("lactose intolerant flagged before recommending whey", r.result == GateResult.CONDITIONAL)
check("lactose flag action correct", "isolate_or_plant" in r.action)

r_no_flag = evaluate_supplement("protein_powder", ClientSupplementContext(lactose_intolerant=False))
check("no lactose issue -> straight recommend", r_no_flag.result == GateResult.RECOMMEND)

# --- creatine + kidney disease ---
r = evaluate_supplement("creatine_monohydrate", ClientSupplementContext(disclosed_conditions=["kidney_disease"]))
check("creatine + kidney disease -> refuse, requires medical clearance", r.result == GateResult.REFUSE)
check("creatine kidney refusal names medical_clearance_required", "medical_clearance_required" in r.action)

# --- caffeine + hypertension ---
r = evaluate_supplement("caffeine", ClientSupplementContext(disclosed_conditions=["hypertension"]))
check("caffeine + hypertension -> caution", r.result == GateResult.CAUTION)

r_clean = evaluate_supplement("caffeine", ClientSupplementContext())
check("caffeine with no flags -> recommend", r_clean.result == GateResult.RECOMMEND)

# --- Tier 2 conditional ---
r = evaluate_supplement("beta_alanine", ClientSupplementContext())
check("beta-alanine is conditional, not blanket recommend", r.result == GateResult.CONDITIONAL)

r = evaluate_supplement("omega_3", ClientSupplementContext(medications=["blood_thinners"]))
check("omega-3 + blood thinners -> caution (bleeding risk)", r.result == GateResult.CAUTION)

r = evaluate_supplement("multi_ingredient_preworkout", ClientSupplementContext(anxiety_disorder_disclosed=True))
check("preworkout + disclosed anxiety -> caution", r.result == GateResult.CAUTION)

# --- Tier 3 -- ALWAYS REFUSE, regardless of framing ---
r = evaluate_supplement("anabolic_androgenic_steroids", ClientSupplementContext())
check("steroids always refused, no dosing under any framing", r.result == GateResult.REFUSE)
check("steroid refusal includes non-judgmental disclosed-use protocol", "if_disclosed" in r.data)

r = evaluate_supplement("sarms_prohormones_research_chemicals", ClientSupplementContext())
check("SARMs/research chemicals refused unconditionally", r.result == GateResult.REFUSE)

r = evaluate_supplement("injectable_peptides", ClientSupplementContext())
check("injectable peptides refused, same treatment as steroids", r.result == GateResult.REFUSE)

# even with sympathetic/harm-reduction-sounding context, still refuses (context fields don't unlock tier3)
r = evaluate_supplement("anabolic_androgenic_steroids",
                          ClientSupplementContext(disclosed_conditions=[], age=30))
check("steroids refused even for adult with no other flags -- tier alone gates it", r.result == GateResult.REFUSE)

# --- pregnancy routing ---
r = evaluate_supplement("caffeine", ClientSupplementContext(pregnant=True))
check("pregnancy routes non-electrolyte/vitaminD supplements through file 12, refuses direct rec",
      r.result == GateResult.REFUSE)
r_ok = evaluate_supplement("electrolytes", ClientSupplementContext(pregnant=True))
check("pregnancy still allows electrolytes through (tier1 exception)", r_ok.result != GateResult.REFUSE)

# --- under 18 ---
r = evaluate_supplement("beta_alanine", ClientSupplementContext(age=16))
check("under 18 blocked from tier2 supplement", r.result == GateResult.REFUSE)
r_ok = evaluate_supplement("creatine_monohydrate", ClientSupplementContext(age=16))
check("under 18 allowed tier1 supplement (no other flags)", r_ok.result != GateResult.REFUSE)

# --- interaction matrix direct check ---
flags = check_interactions("caffeine", ClientSupplementContext(medications=["beta_blockers"]))
check("beta blockers + caffeine flagged via interaction matrix", len(flags) == 1)

# --- GI distress triage ---
check("nausea after preworkout gets dose-reduction guidance",
      "reduce_dose" in gi_distress_triage("nausea_after_preworkout"))
check("bloating after protein shake suggests lactose test",
      "lactose" in gi_distress_triage("bloating_after_protein_shake"))
check("GI upset after creatine suggests split dosing",
      "split_5g" in gi_distress_triage("GI_upset_after_creatine"))
check("multiple supplements started same week overrides specific symptom logic",
      gi_distress_triage("nausea_after_preworkout", multiple_supplements_started_same_week=True)
      == "reintroduce_one_at_a_time_3_5_days_apart_to_isolate_cause")
check("unknown symptom -> gather more info, not a guess", gi_distress_triage("random_symptom") == "insufficient_information_gather_more_detail_before_advising")

# --- tested athlete overlay ---
overlay = tested_athlete_overlay(True)
check("tested athlete gets banned substance screening flag", overlay["flag"] == "banned_substance_screening_required")
check("tested athlete overlay: tier1 not automatically safe (contamination risk)",
      overlay["tier1_not_automatically_safe"] is True)
check("non-tested athlete gets no overlay", tested_athlete_overlay(False)["applies"] is False)

# --- steroid protocol request edge case ---
first = handle_steroid_protocol_request(already_asked_once=False)
check("first steroid request gets referral response", "action" in first)
second = handle_steroid_protocol_request(already_asked_once=True)
check("repeated request redirects instead of re-lecturing", second["repeat_lecture"] is False)

# --- mid-cycle programming request ---
mc = handle_midcycle_programming_request()
check("mid-cycle request does not adjust programming for assumed enhanced recovery",
      mc["do_not_adjust_volume_intensity_for_assumed_enhanced_recovery"] is True)
check("mid-cycle request logs anabolic_use_disclosed flag", mc["log_flag"] == "anabolic_use_disclosed")

# --- creatine loading FAQ ---
check("creatine does not require a loading phase per FAQ", creatine_needs_loading_phase() is False)

print(f"\n{passed} passed, {failed} failed")
if failed:
    raise SystemExit(1)
