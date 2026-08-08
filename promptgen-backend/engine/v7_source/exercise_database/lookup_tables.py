"""
app/engines/exercise_database/lookup_tables.py

Every table below is transcribed directly from KnowledgeBase V7:
    16_Exercise_Intelligence_Database.md  -> EXERCISES, ALTERNATIVES_MATRIX,
                                              PROGRESSION_REGRESSION_LADDERS (§7 overlap)
    9_Exercise_Selection_Rules.md         -> TIER_EXAMPLES (§1), PATTERN_WEEKLY_MINIMUMS (§2),
                                              PRIMARY_SECONDARY_ISOLATION_BY_MUSCLE (§3),
                                              EQUIPMENT_SUBSTITUTION (§4), INJURY_SUBSTITUTION (§5),
                                              GYM_CONTEXT_ADJUSTMENT (§6), LADDERS (§7),
                                              TRAINING_AGE_SELECTION_PHILOSOPHY (§8)

Only 5 exercises have a full Exercise record (KB itself only worked one
full example per pattern) — see GAPS.md for exactly what's missing and why.
"""

from __future__ import annotations
from .models import (
    Exercise, AlternativeEntry, JointStress, MovementPattern,
    SkillRequirement as SR, EvidenceStrength as EV,
)

# ── file 16 §2.1 — full record, squat pattern ───────────────────────────────
SQ_001 = Exercise(
    exercise_id="sq_001", name="Barbell Back Squat (High Bar)",
    movement_pattern=MovementPattern.SQUAT,
    primary_muscles=["quadriceps", "gluteus_maximus"],
    secondary_muscles=["adductors", "erector_spinae", "core"],
    stabilizers=["core", "upper_back"],
    skill_requirement=SR.HIGH, difficulty=4, fatigue_rating=5, stimulus_rating=5, sfr_score=1.0,
    joint_stress=JointStress(knee=2, shoulder=1, lower_back=2, elbow=0, wrist=1),
    equipment_required=["barbell", "squat_rack"],
    strength_curve="ascending",
    resistance_profile_notes="Hardest at bottom (out of the hole), easier at lockout.",
    rom_notes="Full depth = hip crease below top of knee; partial ROM reduces stimulus to glutes/adductors disproportionately",
    tempo_default="3-1-1-0", rep_range_optimal="3-10 for strength/hypertrophy overlap", warmup_sets_recommended=3,
    execution_cues=["Brace before unracking", "Knees track over toes", "Chest up, neutral spine", "Drive through mid-foot"],
    common_mistakes=["Heels rising (ankle mobility)", "Butt wink at depth", "Knees caving (valgus)", "Losing brace mid-rep"],
    coaching_tips=["Cue 'spread the floor' for knee tracking", "Use box squat variant to teach depth/sit-back pattern"],
    regressions=["Goblet squat", "Box squat (higher box)", "Bodyweight squat"],
    progressions=["Pause squat", "Pin squat", "Front squat (higher core demand)"],
    substitutions_equipment=["Safety-bar squat", "Smith machine squat"],
    substitutions_pain_free={"ankle_mobility_limited": "Heel-elevated goblet squat", "lower_back_flagged": "Leg press", "knee_pain": "Box squat to higher box, reduced depth"},
    machine_alternative="Leg press (45-degree)", home_alternative="Goblet squat / Bulgarian split squat with available load",
    who_should_avoid=["Uncleared cardiac condition (Valsalva risk)", "Acute lower back flare", "Unresolved knee valgus pattern (file 11 Sec 4) without correction first"],
    who_benefits_most=["Strength/powerlifting goals", "General lower-body hypertrophy", "Athletes needing triple-extension carryover"],
    best_goals=["strength", "powerlifting", "hypertrophy"], best_splits=["upper_lower", "full_body", "ppl"],
    advanced_variations=["Pause squat", "Tempo squat", "Chain/band-resisted squat"], evidence_strength=EV.HIGH,
)

# ── file 16 §3.1 — full record, hinge pattern ───────────────────────────────
HG_001 = Exercise(
    exercise_id="hg_001", name="Conventional Deadlift",
    movement_pattern=MovementPattern.HINGE,
    primary_muscles=["gluteus_maximus", "hamstrings", "erector_spinae"],
    secondary_muscles=["lats", "traps", "forearms/grip"],
    stabilizers=["core", "lats"],
    skill_requirement=SR.HIGH, difficulty=4, fatigue_rating=5, stimulus_rating=5, sfr_score=1.0,
    joint_stress=JointStress(knee=1, shoulder=1, lower_back=3, elbow=0, wrist=1),
    equipment_required=["barbell", "plates"],
    strength_curve="ascending",
    resistance_profile_notes="Hardest off the floor; sticking point commonly just above knee.",
    rom_notes="Full ROM floor-to-lockout; hip hinge, not squat-pull",
    tempo_default="1-0-1-1 (controlled eccentric, no bounce)",
    rep_range_optimal="1-8 for strength; higher reps increase lower-back fatigue disproportionately",
    warmup_sets_recommended=4,
    execution_cues=["Bar over mid-foot", "Lats engaged before pull ('protect armpits')", "Push floor away, not just pull bar up", "Neutral spine throughout"],
    common_mistakes=["Rounding lower back", "Bar drifting away from shins", "Hyperextending at lockout", "Jerking bar off floor"],
    coaching_tips=["Cue 'slack out of the bar' before pulling", "Use trap bar variant if lower-back flag present and pattern is otherwise cleared"],
    regressions=["Romanian deadlift (partial ROM)", "Trap bar deadlift (reduced lower-back moment arm)", "Kettlebell deadlift"],
    progressions=["Deficit deadlift", "Pause deadlift (below knee)"],
    substitutions_equipment=["Trap bar deadlift", "Dumbbell deadlift"],
    substitutions_pain_free={"lower_back_flagged_history": "Trap bar deadlift or 45-degree back extension", "hinge_pattern_incompetent": "Do not load; use wall-tap RDL drill for 2-4 weeks first", "grip_limited": "Straps or Romanian deadlift with lighter load"},
    machine_alternative="45-degree back extension + hip thrust combination (no true machine equivalent for full hinge)",
    home_alternative="Dumbbell/kettlebell Romanian deadlift",
    who_should_avoid=["Active lower-back flag (file 12 Sec 3) until cleared/reintroduced (file 12 Sec 7)", "Uncleared cardiac condition", "hinge_pattern_incompetent flag unresolved"],
    who_benefits_most=["Posterior chain strength goals", "Powerlifting", "General strength/athleticism"],
    best_goals=["strength", "powerlifting", "hypertrophy"], best_splits=["upper_lower", "full_body", "ppl"],
    advanced_variations=["Deficit deadlift", "Snatch-grip deadlift", "Pause deadlift"], evidence_strength=EV.HIGH,
)

# ── file 16 §4.1 — full record, horizontal push pattern ─────────────────────
HP_001 = Exercise(
    exercise_id="hp_001", name="Barbell Bench Press",
    movement_pattern=MovementPattern.HORIZONTAL_PUSH,
    primary_muscles=["pectoralis_major", "anterior_deltoid"], secondary_muscles=["triceps"],
    stabilizers=["rotator_cuff", "core", "upper_back"],
    skill_requirement=SR.MODERATE, difficulty=3, fatigue_rating=3, stimulus_rating=4, sfr_score=1.3,
    joint_stress=JointStress(knee=0, shoulder=2, lower_back=0, elbow=1, wrist=1),
    equipment_required=["barbell", "bench", "rack"],
    strength_curve="ascending then descending near lockout (bell-ish)",
    resistance_profile_notes="Sticking point typically mid-range, just above chest.",
    rom_notes="Bar touches chest (or just above per shoulder comfort), full elbow extension at top",
    tempo_default="2-1-1-0", rep_range_optimal="3-12", warmup_sets_recommended=3,
    execution_cues=["Retract/depress scapula before unracking", "Slight arch, feet planted", "Bar path slightly diagonal, not straight vertical", "Elbows ~45-75 degrees from torso, not flared to 90"],
    common_mistakes=["Flared elbows causing shoulder strain", "Bouncing bar off chest", "Losing scapular retraction mid-set", "Uneven bar path"],
    coaching_tips=["Cue 'bend the bar' for lat engagement", "Use board press or spoto press to address specific sticking points"],
    regressions=["Dumbbell bench press (more natural shoulder path)", "Push-up", "Machine chest press"],
    progressions=["Pause bench press", "Close-grip bench (triceps bias)", "Spoto press"],
    substitutions_equipment=["Dumbbell bench press", "Machine chest press", "Push-up variations"],
    substitutions_pain_free={"shoulder_pain_anterior": "Neutral-grip dumbbell press or push-up with reduced ROM", "thoracic_mobility_limited": "Slight incline dumbbell press, ensure adequate bench arch/setup"},
    machine_alternative="Machine chest press (plate-loaded or selectorized)", home_alternative="Push-up (weighted with backpack if needed for progression)",
    who_should_avoid=["Active shoulder impingement flag until cleared", "Uncleared cardiac condition for max-effort attempts"],
    who_benefits_most=["Upper-body strength goals", "Powerlifting", "General hypertrophy"],
    best_goals=["strength", "powerlifting", "hypertrophy"], best_splits=["upper_lower", "ppl", "bro_split"],
    advanced_variations=["Board press", "Chain/band-resisted bench", "Spoto press"], evidence_strength=EV.HIGH,
)

# ── file 16 §5.1 — full record, vertical push pattern ───────────────────────
VP_001 = Exercise(
    exercise_id="vp_001", name="Standing Barbell Overhead Press",
    movement_pattern=MovementPattern.VERTICAL_PUSH,
    primary_muscles=["anterior_deltoid", "medial_deltoid"], secondary_muscles=["triceps", "upper_pectoralis"],
    stabilizers=["core", "rotator_cuff", "upper_back"],
    skill_requirement=SR.MODERATE, difficulty=3, fatigue_rating=3, stimulus_rating=4, sfr_score=1.3,
    joint_stress=JointStress(knee=0, shoulder=3, lower_back=1, elbow=1, wrist=1),
    equipment_required=["barbell", "rack"],
    strength_curve="ascending",
    resistance_profile_notes="Sticking point just above head level clearing the face.",
    rom_notes="Full lockout overhead, bar path close to face then back over midline",
    tempo_default="2-0-1-0", rep_range_optimal="5-12", warmup_sets_recommended=3,
    execution_cues=["Brace core hard (no lower-back arch substitute)", "Squeeze glutes to prevent lean-back", "Press bar in slight arc around face"],
    common_mistakes=["Excessive lower-back arch to compensate for thoracic/shoulder mobility limits", "Flaring elbows too wide at start", "Incomplete lockout"],
    coaching_tips=["If thoracic_mobility_limited flag present (file 11 Sec 4), cap ROM and use landmine press instead"],
    regressions=["Landmine press", "Seated dumbbell press (back-supported)", "Machine shoulder press"],
    progressions=["Push press (adds leg drive)", "Behind-neck press (advanced, high mobility requirement, use cautiously)"],
    substitutions_equipment=["Dumbbell overhead press", "Machine shoulder press"],
    substitutions_pain_free={"thoracic_mobility_limited": "Landmine press (per file 11 Sec 4 response)", "shoulder_impingement_flag": "Neutral-grip landmine press or leaning lateral raise emphasis instead"},
    machine_alternative="Machine shoulder press (neutral or standard grip)", home_alternative="Dumbbell overhead press",
    who_should_avoid=["Active shoulder impingement", "Unresolved thoracic_mobility_limited flag for full-ROM barbell version"],
    who_benefits_most=["Shoulder strength/hypertrophy", "Athletic overhead performance"],
    best_goals=["strength", "hypertrophy", "athletic_performance"], best_splits=["upper_lower", "ppl", "bro_split"],
    advanced_variations=["Push press", "Z-press (seated, no back support)"], evidence_strength=EV.HIGH,
)

# ── file 16 §6.1 — full record, horizontal pull pattern ─────────────────────
HPL_001 = Exercise(
    exercise_id="hpl_001", name="Barbell Bent-Over Row",
    movement_pattern=MovementPattern.HORIZONTAL_PULL,
    primary_muscles=["latissimus_dorsi", "rhomboids", "mid_trapezius"], secondary_muscles=["biceps", "rear_deltoid"],
    stabilizers=["erector_spinae", "core"],
    skill_requirement=SR.MODERATE, difficulty=3, fatigue_rating=3, stimulus_rating=4, sfr_score=1.3,
    joint_stress=JointStress(knee=0, shoulder=1, lower_back=2, elbow=1, wrist=0),
    equipment_required=["barbell"],
    strength_curve="flat", resistance_profile_notes="Fairly even tension throughout ROM.",
    rom_notes="Bar to lower ribs/upper abdomen, full stretch at bottom without lower-back rounding",
    tempo_default="2-0-1-1", rep_range_optimal="6-15", warmup_sets_recommended=2,
    execution_cues=["Hinge to ~45-60 degrees torso angle", "Neutral spine maintained throughout", "Pull elbows back, not just up", "Squeeze shoulder blades at top"],
    common_mistakes=["Using momentum/body English to move weight", "Rounding lower back under load", "Shrugging instead of retracting scapula"],
    coaching_tips=["If lower_back flag present, use chest-supported row variant instead"],
    regressions=["Chest-supported row (machine or bench)", "Seated cable row", "Band row"],
    progressions=["Pendlay row (dead-stop, more explosive)", "Yates row (underhand grip)"],
    substitutions_equipment=["Dumbbell row (single-arm)", "Cable row", "Machine row"],
    substitutions_pain_free={"lower_back_flagged": "Chest-supported row or seated cable row", "grip_limited": "Straps or machine row with handle attachment"},
    machine_alternative="Chest-supported machine row", home_alternative="Band row or single-arm dumbbell row (supported)",
    who_should_avoid=["Active lower-back flag (use chest-supported alternative instead)"],
    who_benefits_most=["Back thickness/strength", "Postural correction (pairs with postural_imbalance flag response, file 11 Sec 4)"],
    best_goals=["hypertrophy", "strength", "general_health"], best_splits=["upper_lower", "ppl", "bro_split"],
    advanced_variations=["Pendlay row", "Meadows row (landmine)"], evidence_strength=EV.HIGH,
)

EXERCISES: dict[str, Exercise] = {e.exercise_id: e for e in (SQ_001, HG_001, HP_001, VP_001, HPL_001)}


def _alt(name, pattern, skill, fatigue, sfr, use_case, sub_pattern=None):
    return AlternativeEntry(name=name, movement_pattern=pattern, skill_requirement=skill,
                             fatigue_rating=fatigue, sfr_score=sfr, use_case=use_case, sub_pattern=sub_pattern)

# ── alternatives matrices — file 16 §2.2, 3.2, 4.2, 7.1, 8, 9, 10, 11 ───────
ALTERNATIVES_MATRIX: dict[MovementPattern, list[AlternativeEntry]] = {
    MovementPattern.SQUAT: [
        _alt("Back Squat", MovementPattern.SQUAT, SR.HIGH, 5, 1.0, "Primary strength driver, green tier only"),
        _alt("Front Squat", MovementPattern.SQUAT, SR.HIGH, 4, 1.1, "More quad bias, less lower-back load, needs mobility"),
        _alt("Goblet Squat", MovementPattern.SQUAT, SR.LOW, 2, 1.5, "Beginners, DEFAULT_SAFE_TEMPLATE, teaching depth"),
        _alt("Leg Press", MovementPattern.SQUAT, SR.LOW, 3, 1.3, "Joint-friendly quad volume, high-rep hypertrophy"),
        _alt("Hack Squat (machine)", MovementPattern.SQUAT, SR.MODERATE, 3, 1.4, "Quad-focused hypertrophy, lower skill demand than free-weight"),
        _alt("Bulgarian Split Squat", MovementPattern.SQUAT, SR.MODERATE, 3, 1.2, "Unilateral imbalance correction (file 11 Sec 4), limited equipment"),
        _alt("Box Squat", MovementPattern.SQUAT, SR.MODERATE, 4, 1.1, "Teaching depth/hip-hinge-in-squat, powerlifting specificity"),
    ],
    MovementPattern.HINGE: [
        _alt("Conventional Deadlift", MovementPattern.HINGE, SR.HIGH, 5, 1.0, "Primary strength driver, green tier"),
        _alt("Trap Bar Deadlift", MovementPattern.HINGE, SR.MODERATE, 4, 1.3, "Lower back-friendlier, good beginner-to-intermediate bridge"),
        _alt("Romanian Deadlift", MovementPattern.HINGE, SR.MODERATE, 3, 1.4, "Hamstring/glute hypertrophy focus, teaches hinge pattern"),
        _alt("45-Degree Back Extension", MovementPattern.HINGE, SR.LOW, 2, 1.5, "High-rep posterior chain, very joint-friendly"),
        _alt("Glute Bridge / Hip Thrust", MovementPattern.HINGE, SR.LOW, 2, 1.6, "Glute-focused hypertrophy, DEFAULT_SAFE_TEMPLATE-appropriate"),
        _alt("Good Morning", MovementPattern.HINGE, SR.HIGH, 4, 1.0, "Advanced posterior chain, high skill/technique demand"),
    ],
    MovementPattern.HORIZONTAL_PUSH: [
        _alt("Barbell Bench Press", MovementPattern.HORIZONTAL_PUSH, SR.MODERATE, 3, 1.3, "Primary strength/hypertrophy driver"),
        _alt("Dumbbell Bench Press", MovementPattern.HORIZONTAL_PUSH, SR.LOW_MODERATE, 3, 1.4, "Shoulder-friendlier path, unilateral imbalance correction"),
        _alt("Machine Chest Press", MovementPattern.HORIZONTAL_PUSH, SR.LOW, 2, 1.6, "High-rep hypertrophy, beginners, DEFAULT_SAFE_TEMPLATE progression step"),
        _alt("Push-up (weighted/banded)", MovementPattern.HORIZONTAL_PUSH, SR.LOW, 2, 1.5, "No-equipment default, home training"),
        _alt("Incline Dumbbell Press", MovementPattern.HORIZONTAL_PUSH, SR.MODERATE, 3, 1.4, "Upper-chest emphasis"),
        _alt("Dip (chest-leaning)", MovementPattern.HORIZONTAL_PUSH, SR.MODERATE_HIGH, 4, 1.1, "Advanced, high shoulder stress if uncontrolled"),
    ],
    MovementPattern.HORIZONTAL_PULL: [
        _alt("Barbell Bent-Over Row", MovementPattern.HORIZONTAL_PULL, SR.MODERATE, 3, 1.3, "Primary back-thickness driver"),
        _alt("Chest-Supported Row", MovementPattern.HORIZONTAL_PULL, SR.LOW, 2, 1.6, "Lower-back-friendly, high-rep hypertrophy"),
        _alt("Seated Cable Row", MovementPattern.HORIZONTAL_PULL, SR.LOW, 2, 1.5, "Beginner-friendly, consistent tension"),
        _alt("Single-Arm Dumbbell Row", MovementPattern.HORIZONTAL_PULL, SR.LOW_MODERATE, 2, 1.5, "Unilateral imbalance correction"),
        _alt("Inverted Row (bodyweight)", MovementPattern.HORIZONTAL_PULL, SR.LOW, 2, 1.4, "Home/no-equipment default"),
        _alt("Band Row", MovementPattern.HORIZONTAL_PULL, SR.LOW, 1, 1.4, "DEFAULT_SAFE_TEMPLATE, home minimal-equipment"),
    ],
    MovementPattern.VERTICAL_PULL: [
        _alt("Weighted Pull-Up", MovementPattern.VERTICAL_PULL, SR.HIGH, 4, 1.2, "Advanced back width, requires baseline strength"),
        _alt("Bodyweight Pull-Up", MovementPattern.VERTICAL_PULL, SR.MODERATE_HIGH, 3, 1.4, "Standard back-width driver, requires sufficient relative strength"),
        _alt("Assisted Pull-Up (machine/band)", MovementPattern.VERTICAL_PULL, SR.MODERATE, 3, 1.4, "Bridge for clients who can't yet perform full pull-up"),
        _alt("Lat Pulldown", MovementPattern.VERTICAL_PULL, SR.LOW, 2, 1.5, "Beginner-friendly, adjustable load, DEFAULT_SAFE_TEMPLATE-adjacent"),
        _alt("Straight-Arm Pulldown", MovementPattern.VERTICAL_PULL, SR.LOW, 1, 1.3, "Lat isolation, low systemic fatigue, good finisher"),
    ],
    MovementPattern.LUNGE: [
        _alt("Walking Lunge", MovementPattern.LUNGE, SR.MODERATE, 4, 1.1, "Athletic carryover, higher balance demand"),
        _alt("Reverse Lunge", MovementPattern.LUNGE, SR.LOW_MODERATE, 3, 1.3, "Knee-friendlier than forward lunge, good default"),
        _alt("Bulgarian Split Squat", MovementPattern.LUNGE, SR.MODERATE, 3, 1.2, "Unilateral imbalance correction (file 11 Sec 4), strong quad/glute stimulus"),
        _alt("Step-Up", MovementPattern.LUNGE, SR.LOW, 2, 1.4, "Beginner-friendly, adjustable height for difficulty"),
    ],
    MovementPattern.CARRY: [
        _alt("Farmer Carry", MovementPattern.CARRY, SR.LOW, 3, 1.5, "Grip/trap/core, very high transferability, low technical demand"),
        _alt("Suitcase Carry (single-side)", MovementPattern.CARRY, SR.LOW, 2, 1.5, "Anti-lateral-flexion core, unilateral correction"),
        _alt("Overhead Carry", MovementPattern.CARRY, SR.MODERATE, 3, 1.2, "Shoulder stability, requires adequate overhead mobility first"),
    ],
}

# file 16 §9 — core patterns carry a sub_pattern column the others don't
CORE_ALTERNATIVES: list[AlternativeEntry] = [
    _alt("Plank", MovementPattern.CORE_ANTI_EXTENSION, SR.LOW, 1, 1.5, "Baseline core endurance (file 11 Sec 3)", "anti_extension"),
    _alt("Dead Bug", MovementPattern.CORE_ANTI_EXTENSION, SR.LOW, 1, 1.4, "DEFAULT_SAFE_TEMPLATE, low back rehab-friendly", "anti_extension"),
    _alt("Pallof Press", MovementPattern.CORE_ANTI_ROTATION, SR.LOW_MODERATE, 1, 1.5, "Rotational stability, athletic carryover", "anti_rotation"),
    _alt("Hanging Leg Raise", MovementPattern.CORE_ANTI_EXTENSION, SR.MODERATE_HIGH, 3, 1.1, "Advanced, high grip/shoulder demand", "anti_extension/flexion"),
    _alt("Ab Wheel Rollout", MovementPattern.CORE_ANTI_EXTENSION, SR.HIGH, 3, 1.0, "Advanced, avoid if lower-back flag active", "anti_extension"),
    _alt("Side Plank", MovementPattern.CORE_ANTI_LATERAL_FLEXION, SR.LOW, 1, 1.4, "Obliques/QL, low joint stress", "anti_lateral_flexion"),
]

# file 16 §11 — selected high-SFR isolation examples (pattern field reused loosely per KB's own table)
ISOLATION_ALTERNATIVES: list[AlternativeEntry] = [
    _alt("Leg Curl (machine)", MovementPattern.HIP_DOMINANT_ISOLATION, SR.LOW, 1, 1.7, "Excellent hamstring isolation, very low systemic fatigue"),
    _alt("Leg Extension (machine)", MovementPattern.KNEE_DOMINANT_ISOLATION, SR.LOW, 1, 1.6, "Quad isolation; caution (reduce load, avoid full lockout snap) with anterior knee pain flags"),
    _alt("Lateral Raise (dumbbell/cable)", MovementPattern.SHOULDER_ISOLATION, SR.LOW, 1, 1.6, "Medial delt, high hypertrophy value per fatigue cost"),
    _alt("Bicep Curl (dumbbell/barbell/cable)", MovementPattern.ELBOW_FLEXION, SR.LOW, 1, 1.6, "Standard arm accessory"),
    _alt("Triceps Pushdown (cable)", MovementPattern.ELBOW_EXTENSION, SR.LOW, 1, 1.6, "Standard arm accessory, low joint stress"),
    _alt("Calf Raise (standing/seated)", MovementPattern.CALF, SR.LOW, 1, 1.5, "High frequency tolerance, low systemic fatigue"),
    _alt("Face Pull (cable/band)", MovementPattern.SHOULDER_ISOLATION, SR.LOW, 1, 1.6, "Prescribed at elevated frequency for postural_imbalance flag (file 11 Sec 4)"),
]

# ── file 9 §1 — classification tier examples (not exhaustive, KB's own examples) ──
TIER_EXAMPLES = {
    "primary": ["Back Squat", "Deadlift", "Bench Press", "Overhead Press", "Weighted Pull-up", "Barbell Row"],
    "secondary": ["Leg Press", "Incline DB Press", "Lat Pulldown", "DB Row", "Bulgarian Split Squat"],
    "isolation": ["Leg Extension", "Leg Curl", "Lateral Raise", "Biceps Curl", "Triceps Pushdown", "Calf Raise"],
}

# ── file 9 §2 — minimum weekly touches per pattern (min, max|None) ─────────
PATTERN_WEEKLY_MINIMUMS = {
    MovementPattern.SQUAT: (2, None),
    MovementPattern.HINGE: (2, None),
    MovementPattern.HORIZONTAL_PUSH: (2, None),
    MovementPattern.HORIZONTAL_PULL: (2, None),
    MovementPattern.VERTICAL_PUSH: (1, 2),
    MovementPattern.VERTICAL_PULL: (1, 2),
    MovementPattern.LUNGE: (1, 2),   # KB: "Unilateral Lower"
    MovementPattern.CARRY: (1, 2),   # KB: "Carry/Core Stability"
}

# ── file 9 §3 — primary/secondary/isolation by muscle ("—" kept as None) ───
PRIMARY_SECONDARY_ISOLATION_BY_MUSCLE = {
    "chest":            {"primary": ["Barbell Bench Press"], "secondary": ["Incline DB Press", "Machine Press"], "isolation": ["Cable Fly", "Pec Deck"]},
    "back_lats":        {"primary": ["Weighted Pull-up", "Barbell Row"], "secondary": ["Lat Pulldown", "Chest-Supported Row"], "isolation": ["Straight-Arm Pulldown"]},
    "back_upper_traps": {"primary": ["Barbell Row", "Pendlay Row"], "secondary": ["Face Pull", "Seated Cable Row (high)"], "isolation": ["Shrugs", "Rear Delt Fly"]},
    "shoulders_front_side": {"primary": ["Overhead Press"], "secondary": ["DB Shoulder Press"], "isolation": ["Lateral Raise", "Front Raise"]},
    "shoulders_rear":   {"primary": None, "secondary": ["Face Pull"], "isolation": ["Rear Delt Fly", "Reverse Pec Deck"]},
    "quads":            {"primary": ["Back Squat"], "secondary": ["Front Squat", "Leg Press", "Hack Squat"], "isolation": ["Leg Extension"]},
    "hamstrings":       {"primary": ["Romanian Deadlift"], "secondary": ["Good Morning"], "isolation": ["Leg Curl (seated/lying)"]},
    "glutes":           {"primary": ["Hip Thrust", "Deadlift"], "secondary": ["Bulgarian Split Squat", "Walking Lunge"], "isolation": ["Cable Kickback", "Glute Bridge"]},
    "biceps":           {"primary": None, "secondary": ["Barbell Curl"], "isolation": ["DB Curl", "Cable Curl", "Preacher Curl"]},
    "triceps":          {"primary": None, "secondary": ["Close-Grip Bench", "Dips"], "isolation": ["Pushdown", "Overhead Extension"]},
    "calves":           {"primary": None, "secondary": ["Standing Calf Raise"], "isolation": ["Seated Calf Raise"]},
    "abs":              {"primary": None, "secondary": ["Hanging Leg Raise", "Cable Crunch"], "isolation": ["Weighted Crunch", "Ab Wheel"]},
}

# ── file 9 §4 — equipment substitution table ────────────────────────────────
EQUIPMENT_SUBSTITUTION = {
    "Back Squat":       {"dumbbell": "Goblet Squat / DB Split Squat", "machine": "Leg Press / Hack Squat", "bodyweight_band": "Bodyweight Squat / Band Squat"},
    "Deadlift":         {"dumbbell": "DB RDL", "machine": "Leg Curl + Back Extension combo", "bodyweight_band": "Single-leg RDL (bodyweight)"},
    "Bench Press":      {"dumbbell": "DB Bench Press", "machine": "Chest Press Machine", "bodyweight_band": "Push-up (weighted with backpack if needed)"},
    "Overhead Press":   {"dumbbell": "DB Shoulder Press", "machine": "Machine Shoulder Press", "bodyweight_band": "Pike Push-up"},
    "Barbell Row":      {"dumbbell": "DB Row", "machine": "Chest-Supported Row Machine / Cable Row", "bodyweight_band": "Inverted Row (bar/table) / Band Row"},
    "Pull-up (weighted)": {"dumbbell": None, "machine": "Lat Pulldown / Assisted Pull-up Machine", "bodyweight_band": "Band-Assisted Pull-up"},
    "Barbell Curl":     {"dumbbell": "DB Curl", "machine": "Cable Curl", "bodyweight_band": "Band Curl"},
    "Close-Grip Bench": {"dumbbell": "DB Floor Press", "machine": "Triceps Pushdown Machine", "bodyweight_band": "Diamond Push-up"},
    "Hip Thrust (barbell)": {"dumbbell": "DB Hip Thrust", "machine": "Glute Machine", "bodyweight_band": "Bodyweight Hip Thrust / Single-leg glute bridge"},
}

# ── file 9 §5 — injury-based substitution (rule: pain -> stop & substitute
# immediately; general fatigue/burn is NOT the same signal, does not trigger this) ──
INJURY_SUBSTITUTION = {
    "shoulder_impingement": {"avoid": ["Behind-the-neck press", "Upright Row", "Deep dips"], "substitute": ["Landmine Press", "Neutral-grip DB Press", "Face Pulls for health"]},
    "lower_back_pain_flareup": {"avoid": ["Barbell Deadlift", "Good Morning", "Loaded spinal flexion (weighted sit-ups)"], "substitute": ["Trap Bar Deadlift", "Hip Thrust", "Back Extension (controlled ROM)", "Dead Bug for core"]},
    "knee_pain_patellofemoral": {"avoid": ["Deep leg press", "Full ROM leg extension under heavy load"], "substitute": ["Box Squat (higher box)", "Leg Press (moderate ROM, feet higher on platform)", "Reverse Nordic (light)"]},
    "elbow_pain_tendinopathy": {"avoid": ["Heavy close-grip bench", "Skull crushers with heavy load"], "substitute": ["Rope Pushdown (neutral grip)", "Reduce load and volume temporarily", "Isometric holds"]},
    "wrist_pain": {"avoid": ["Barbell Front Squat (front rack)", "Straight-bar curls"], "substitute": ["Cross-arm front squat or Goblet Squat", "EZ-bar or DB curls (neutral/rotated grip)"]},
    "hip_impingement_fai": {"avoid": ["Deep barbell back squat", "Deep lunges"], "substitute": ["Box Squat to comfortable depth", "Trap Bar Deadlift", "Leg Press with limited depth"]},
}

# ── file 9 §6 — gym context adjustment ───────────────────────────────────────
GYM_CONTEXT_ADJUSTMENT = {
    "home_bodyweight_only": "Prioritize unilateral/tempo manipulation to increase difficulty (e.g., slow eccentric pistol squat progressions, deficit push-ups) since load is limited",
    "home_db_bands": "Nearly full programming capability for beginner-intermediate; bands fill in for cable-based isolation work (face pulls, pushdowns, pull-aparts)",
    "home_barbell_rack": "Full primary compound capability; isolation limited without cables — substitute DB/band isolation",
    "commercial_full_equipment": "No constraints; follow standard tables directly",
}

# ── file 9 §7 — progression/regression ladders, easiest to hardest ─────────
PROGRESSION_REGRESSION_LADDERS = {
    MovementPattern.SQUAT: ["Bodyweight Squat", "Box Squat (high box)", "Goblet Squat", "Front Squat (light)", "Back Squat", "Back Squat + pause/tempo variations"],
    MovementPattern.HORIZONTAL_PUSH: ["Wall Push-up", "Incline Push-up", "Knee Push-up", "Full Push-up", "Deficit Push-up", "Weighted Push-up", "Barbell/DB Bench Press"],
    MovementPattern.VERTICAL_PULL: ["Dead Hang", "Band-Assisted Pull-up", "Negative Pull-up", "Full Pull-up", "Weighted Pull-up"],
    MovementPattern.HINGE: ["Hip Hinge Drill (dowel)", "Bodyweight RDL", "DB RDL", "Barbell RDL", "Conventional/Sumo Deadlift"],
}

# ── file 9 §8 — exercise selection philosophy by training age ──────────────
TRAINING_AGE_SELECTION_PHILOSOPHY = {
    "beginner": "Simple, stable, machine/DB-biased; limited exercise count per pattern to build competency",
    "intermediate": "Introduce free-weight variation, unilateral work, weak-point accessories",
    "advanced": "Full toolkit including SFR-optimized substitutions late in mesocycles, specialization-specific exercise selection, exercise variation rotation to manage staleness",
}
