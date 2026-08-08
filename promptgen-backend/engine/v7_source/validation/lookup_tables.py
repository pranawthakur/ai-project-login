"""
lookup_tables.py -- Validation Engine
========================================
Static tables transcribed from the two source documents. Every table here
is a direct port of a KB markdown table -- no engineering defaults, no
invented values (unlike biomechanics/substitution, this KB source is
fully populated).
"""

from __future__ import annotations

from .models import AdherenceRiskTier, ConfidenceTier

# ---------------------------------------------------------------------
# 0_Master_Index_Versioning_and_Localization.md Sec 1 -- FILE INDEX
# ---------------------------------------------------------------------
FILE_INDEX: dict[int, dict] = {
    1: {"name": "Master Workout Split Table", "role": "Split selection",
        "depends_on": [11, 8], "produces": ["active_split"]},
    2: {"name": "Programming Rules", "role": "Sets/reps/RIR/progression",
        "depends_on": [11, 10], "produces": ["prescription_variables"]},
    3: {"name": "Beginner Programming", "role": "Beginner-specific rules",
        "depends_on": [11], "produces": ["Beginner program overlay"]},
    4: {"name": "Intermediate Programming", "role": "Intermediate rules",
        "depends_on": [11, 2], "produces": ["Intermediate program overlay"]},
    5: {"name": "Advanced Programming", "role": "Advanced rules",
        "depends_on": [11, 2, 6], "produces": ["Advanced program overlay"]},
    6: {"name": "Intensity Techniques", "role": "Advanced techniques",
        "depends_on": [11], "produces": ["Technique injection into session"]},
    7: {"name": "Goal-Based Modifications", "role": "Nutrition/training goal skew",
        "depends_on": [11, 12], "produces": ["nutrition_targets", "goal-specific volume skew"]},
    8: {"name": "Weekly Muscle Volume", "role": "Volume landmarks",
        "depends_on": [11, 10], "produces": ["volume_targets"]},
    9: {"name": "Exercise Selection Rules", "role": "Exercise picking/substitution",
        "depends_on": [11, 12], "produces": ["exercise_list"]},
    10: {"name": "Recovery & Deload", "role": "Fatigue/deload logic",
         "depends_on": [11], "produces": ["recovery_score", "deload triggers"]},
    11: {"name": "Assessment & Intake Engine", "role": "Entry point, tiering",
         "depends_on": ["raw client input"],
         "produces": ["client_state root object", "confidence_tier", "flags[]"]},
    12: {"name": "Safety & Medical Red-Flag Engine", "role": "Cross-cutting safety gate",
         "depends_on": [11], "produces": ["safety_gate_result", "hard blocks/restrictions"]},
    13: {"name": "Cardio & Conditioning", "role": "Cardio prescription",
         "depends_on": [11, 12, 10], "produces": ["cardio_prescription"]},
    14: {"name": "Default Safe Template & Coach Override",
         "role": "Fallback program + human override", "depends_on": [11, 12],
         "produces": ["DEFAULT_SAFE_TEMPLATE object", "override_log[]"]},
    15: {"name": "Supplement Safety & Interaction Engine", "role": "Supplement guidance",
         "depends_on": [11, 12], "produces": ["supplement_guidance"]},
    16: {"name": "Exercise Intelligence Database",
         "role": "Per-exercise data model + selection engine",
         "depends_on": [11, 12], "produces": ["exercise_id objects", "selection confidence scores"]},
    17: {"name": "Periodization & AI Decision Engine",
         "role": "Split/periodization selection, advanced set-structure definitions, shared confidence formula",
         "depends_on": [1, 2, 8, 10, 11, 16],
         "produces": ["active_split (scored)", "periodization model", "confidence scores used across files"]},
    18: {"name": "Injury-Specific Rehabilitation and Return-to-Training",
         "role": "Per-injury (acute/soft-tissue) protocols and phased return-to-load",
         "depends_on": [11, 12], "produces": ["Injury phase", "session modifications", "reintroduction schedule"]},
    19: {"name": "Chronic Health Condition Management Engine",
         "role": "Per-condition (diabetes, hypertension, asthma, OA, PCOS, thyroid) ongoing programming rules",
         "depends_on": [11, 12, 13, 10],
         "produces": ["Condition-specific modifications", "stability monitoring flags"]},
    20: {"name": "Acute Symptom and First-Response Triage Engine",
         "role": "Front-door classification/dispatch for any newly reported health issue",
         "depends_on": [12, 18, 19],
         "produces": ["Classification + handoff target + today's-session decision"]},
}

# ---------------------------------------------------------------------
# 0_...md Sec 2 -- CANONICAL CALL ORDER (per session/program generation request)
# Ordered list of (step_id, description, source_file_or_None). Step "2"
# (safety gate) MUST run unconditionally before anything else -- see
# rules.SAFETY_GATE_STEP_ID and rules.validate_call_order.
# ---------------------------------------------------------------------
CANONICAL_CALL_ORDER: list[dict] = [
    {"step": "1", "description": "Load/update client_state via file 11 (intake or check-in processing)", "file": 11},
    {"step": "2", "description": "Run safetyGate() -- file 12 Section 1 -- UNCONDITIONALLY, before anything else", "file": 12},
    {"step": "2b", "description": "If any new health/symptom report is present, run file 20 classifyHealthReport()", "file": 20},
    {"step": "3", "description": "Determine confidence_tier transitions -- file 14 Section 3", "file": 14},
    {"step": "4", "description": "Pull recovery_score -- file 10", "file": 10},
    {"step": "5", "description": "Generate resistance program: split -> volume -> exercise selection -> prescription variables", "file": None},
    {"step": "6", "description": "Generate cardio prescription -- file 13, gated by file 12 flags", "file": 13},
    {"step": "7", "description": "Generate nutrition/goal skew -- file 7, gated by file 12 Section 6 ED rules", "file": 7},
    {"step": "8", "description": "Generate supplement guidance (if requested) -- file 15, gated by file 12 interaction flags", "file": 15},
    {"step": "9", "description": "Apply any active coach override -- file 14 Section 2 -- merge last, log to audit trail", "file": 14},
    {"step": "10", "description": "Return final program + surface any non-overridable flags/referral language to user", "file": None},
]

# ---------------------------------------------------------------------
# 0_...md Sec 4 -- UNIT & LOCALE NORMALIZATION LAYER
# ---------------------------------------------------------------------
CANONICAL_UNITS: dict[str, dict] = {
    "weight": {"canonical_unit": "kg", "display_adaptable": True, "display_alt": "lb"},
    "height": {"canonical_unit": "cm", "display_adaptable": True, "display_alt": "ft/in"},
    "distance_cardio": {"canonical_unit": "km", "display_adaptable": True, "display_alt": "mi"},
    "temperature_heat_risk": {"canonical_unit": "celsius", "display_adaptable": True, "display_alt": "fahrenheit"},
}

# ---------------------------------------------------------------------
# 0_...md Sec 7 -- FAQ: cross-file precedence order when files conflict
# ---------------------------------------------------------------------
FILE_PRECEDENCE_ORDER: list = [12, 11, 14, "programming_files_1_through_10_13_15"]

# ---------------------------------------------------------------------
# 11_...md Sec 2.1 -- High-Risk Condition List (Triggers Medical Clearance Flag)
# ---------------------------------------------------------------------
HIGH_RISK_CONDITIONS: dict[str, str] = {
    "uncontrolled_hypertension": "Risk with heavy/Valsalva lifting",
    "cardiovascular_disease_recent_cardiac_event": "Exercise intensity risk",
    "recent_surgery_under_12_weeks": "Tissue healing constraints",
    "uncontrolled_diabetes": "Blood sugar management during exercise",
    "joint_replacement_under_6_months": "Loading/ROM constraints",
    "diagnosed_eating_disorder_active": (
        "Deficit/volume prescriptions contraindicated -- route to supportive, "
        "non-diet-focused programming and professional referral"
    ),
    "pregnancy": "Trimester-specific contraindications apply",
    "uncontrolled_asthma_respiratory_condition": "Intensity/conditioning constraints",
    "osteoporosis_osteopenia_significant": "High-impact/spinal-flexion-under-load contraindications",
    "seizure_disorder_uncontrolled": "Risk with unsupervised free-weight/overhead loading",
    "untreated_cardiac_arrhythmia": "Risk with high-intensity/max-effort work",
    "current_dvt_blood_clot_history_unmanaged": "Risk with Valsalva and prolonged static positions",
}

# ---------------------------------------------------------------------
# 11_...md Sec 2.2 -- System-Wide Confidence Tiering
# ---------------------------------------------------------------------
CONFIDENCE_TIER_RULES: dict[ConfidenceTier, dict] = {
    ConfidenceTier.GREEN: {
        "trigger": "Full intake, cleared, >=8 weeks consistent check-ins",
        "behavior": "Full autoregulation, advanced techniques allowed (file 6) permitted",
    },
    ConfidenceTier.YELLOW: {
        "trigger": "Partial intake OR <8 weeks history OR 1 missed check-in cycle",
        "behavior": "Conservative progression, cap intensity techniques, re-request missing data",
    },
    ConfidenceTier.ORANGE: {
        "trigger": "pending_clearance, medical_disclosure_refused, or 2 missed check-in cycles",
        "behavior": (
            "DEFAULT_SAFE_TEMPLATE only, no advanced techniques, no aggressive "
            "deficits, repeat clearance/disclosure request each session"
        ),
    },
    ConfidenceTier.RED: {
        "trigger": "below_minimum_age_reject, active safety flag from file 12 unresolved",
        "behavior": "No program generation; human/professional referral message only",
    },
}

# ---------------------------------------------------------------------
# 11_...md Sec 3 -- Movement & Strength Assessment Protocol
# ---------------------------------------------------------------------
ASSESSMENT_PROTOCOL: dict[str, dict] = {
    "overhead_squat_assessment": {
        "protocol": "Bodyweight squat, arms overhead, observe from front/side",
        "output_use": "Feeds mobility flag table (Section 4)",
    },
    "single_leg_stance": {
        "protocol": "10s hold each leg, eyes open",
        "output_use": "Feeds unilateral/balance-work prioritization",
    },
    "push_pull_baseline": {
        "protocol": "Max unbroken push-ups; max unbroken rows (band or bodyweight)",
        "output_use": "Establishes starting point for beginners without load-based 1RM",
    },
    "submaximal_load_test_3_5rm": {
        "protocol": "For clients with some barbell experience only",
        "output_use": "Feeds estimated_1RM used in file 2 Section 18",
    },
    "grip_core_endurance": {
        "protocol": "Plank hold to failure (cap test at 120s)",
        "output_use": "Baseline for core programming, not a competitive metric",
    },
}

# ---------------------------------------------------------------------
# 11_...md Sec 4 -- Mobility/Movement Flag Table
# ---------------------------------------------------------------------
MOBILITY_FLAG_TABLE: dict[str, dict] = {
    "heels_rise_during_squat": {
        "flag": "ankle_mobility_limited",
        "response": "Elevate heels (wedge/plates) initially, add ankle dorsiflexion mobility work, prefer box squat/goblet squat",
    },
    "excessive_forward_lean_during_squat": {
        "flag": "hip_ankle_mobility_limited",
        "response": "Prefer front-loaded squat variants (goblet, front squat), add thoracic/hip mobility work",
    },
    "arms_cant_reach_overhead_without_lower_back_arching": {
        "flag": "thoracic_mobility_limited",
        "response": "Cap OHP range temporarily, use landmine press, add thoracic extension mobility work",
    },
    "rounded_shoulders_forward_head_at_rest": {
        "flag": "postural_imbalance",
        "response": "Increase horizontal pull:push ratio to 1.5:1, add face pulls/rear delt work",
    },
    "cant_maintain_neutral_spine_in_hinge": {
        "flag": "hinge_pattern_incompetent",
        "response": "Delay loaded hinge work, use hinge drills (dowel, wall-tap RDL) for 2-4 weeks first",
    },
    "knees_cave_inward_under_load_valgus": {
        "flag": "hip_stability_limited",
        "response": 'Add banded lateral walks/clamshells, cue "knees out," reduce load until pattern clean',
    },
    "asymmetric_single_leg_stance_hold_gt_3s_difference": {
        "flag": "unilateral_imbalance",
        "response": "Prioritize unilateral work at higher frequency on weaker side, screen for injury history",
    },
    "pain_not_just_limitation_during_any_screen": {
        "flag": "pain_provoking_movement",
        "response": "Do NOT program that pattern; route to file 12 Section on pain-vs-limitation triage",
    },
}

# ---------------------------------------------------------------------
# 11_...md Sec 5.1 -- Item Frequency Table
# ---------------------------------------------------------------------
ITEM_FREQUENCY_TABLE: dict[str, str] = {
    "bodyweight": "Weekly (same conditions: morning, post-bathroom, pre-food)",
    "circumference_measurements_or_photos": "Every 4 weeks",
}

# ---------------------------------------------------------------------
# 11_...md Sec 6 -- Re-assessment Cadence
# ---------------------------------------------------------------------
REASSESSMENT_CADENCE: dict[str, str] = {
    "strength_baseline_submaximal_test": "Every 8-12 weeks, or at mesocycle boundary",
    "full_movement_screen_re_run": "Every 12 weeks, or after any new injury flag resolves",
    "goal_intake_schema_full_review": "Every 12 weeks or on major life-change disclosure",
    "medical_clearance_re_confirmation": (
        "Every 6 months if pending_clearance unresolved, or immediately on new condition disclosure"
    ),
}

# ---------------------------------------------------------------------
# 11_...md Sec 7.1 -- Response Ladder by Risk Tier
# ---------------------------------------------------------------------
ADHERENCE_RESPONSE_LADDER: dict[AdherenceRiskTier, str] = {
    AdherenceRiskTier.LOW_RISK: "Continue standard progression",
    AdherenceRiskTier.MODERATE_RISK: (
        "Reduce weekly volume 10-15%, send barrier-check prompt, offer schedule flexibility"
    ),
    AdherenceRiskTier.HIGH_RISK: (
        "Downgrade to 2-3 day minimum-effective-dose template, shorten mesocycle to 2 weeks, "
        "emphasize habit consistency over performance metrics"
    ),
}

# ---------------------------------------------------------------------
# 11_...md Sec 8 -- Edge Cases (rule text kept as reference data; the
# branch logic for most of these is implemented directly in rules.py
# where it maps cleanly onto process_intake/process_check_in).
# ---------------------------------------------------------------------
EDGE_CASE_RULES: dict[str, str] = {
    "refuses_medical_disclosure": (
        "Do not proceed to full program generation; provide only general, low-intensity "
        "guidance and repeat the clearance request; document refusal"
    ),
    "client_under_13": (
        "Reject onboarding entirely; recommend youth-specific in-person coaching/physical "
        "education programs, not this system"
    ),
    "intake_internally_inconsistent": (
        "Weight movement screen results over self-report; flag discrepancy"
    ),
    "stops_submitting_checkins": (
        "After 2 missed check-in cycles, downgrade confidence in all readiness-based "
        "algorithms system-wide; default to conservative (yellow/orange tier) assumptions "
        "until data resumes"
    ),
    "body_fat_pct_wildly_inconsistent": (
        "Flag body_fat_estimate_unreliable, fall back to sex+activity-based default ranges "
        "(file 7) rather than trusting the specific number"
    ),
    "new_medical_condition_mid_program": (
        "Immediately re-run processIntake routing logic; do not wait for scheduled re-assessment"
    ),
    "contradictory_pregnancy_status_over_time": (
        "Always trust most recent disclosure; re-flag medical_clearance_required immediately, "
        "do not require re-onboarding delay"
    ),
    "minor_guardian_has_not_cosigned_waiver": (
        "Block program generation until guardian consent recorded; status = blocked_no_consent"
    ),
    "client_requests_health_data_deletion": (
        "Purge health object per data policy; downgrade to orange tier (no medical context = "
        "conservative default) until re-supplied"
    ),
}

# ---------------------------------------------------------------------
# 11_...md Sec 9 -- Intake-to-Downstream Data Contract
# ---------------------------------------------------------------------
DATA_CONTRACT: dict[str, list] = {
    "flags_and_confidence_tier": ["All files (gating logic)"],
    "baseline_performance_1rm_est": ["File 2 Section 18", "File 4/5 load prescriptions"],
    "mobility_flags_section_4": ["File 9 Section 5 (injury/limitation substitution)"],
    "equipment_available": ["File 9 Section 4"],
    "goals_primary_target_date": ["File 7 (goal-based modification)", "File 1 (split selection)"],
    "adherence_risk_tier": ["File 10 (recovery/deload triggers)", "File 1 (split simplification)"],
    "medical_conditions_pregnancy_status": ["File 12 (safety/red-flag engine) -- authoritative source"],
}
