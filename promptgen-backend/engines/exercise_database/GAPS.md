# Exercise Database Engine — Coverage Gaps

This file lists exactly what KnowledgeBase V7 (Part 7) does NOT specify,
so nothing here gets silently filled with a guessed value. If a field
isn't listed as populated below, it is genuinely absent from the source,
not an oversight in transcription.

## 1. Only 5 exercises have a full ~30-field record

The KB states its own scope directly (file 16, Purpose section): it
"populates the schema for representative exercises across every major
pattern," not an exhaustive library. The 5 it worked a full example for:

  sq_001  Barbell Back Squat (High Bar)     — squat
  hg_001  Conventional Deadlift              — hinge
  hp_001  Barbell Bench Press                — horizontal_push
  vp_001  Standing Barbell Overhead Press    — vertical_push
  hpl_001 Barbell Bent-Over Row              — horizontal_pull

No full record exists in the KB for: vertical_pull, lunge/unilateral,
any core pattern, carry, or any isolation exercise. Every exercise named
in those patterns only has the lighter AlternativeEntry fields (name,
skill, fatigue_rating, sfr_score, use_case) — see lookup_tables.py's
ALTERNATIVES_MATRIX / CORE_ALTERNATIVES / ISOLATION_ALTERNATIVES.

## 2. Fields genuinely missing from every AlternativeEntry

For ~35 exercises across the alternatives matrices, the KB does not give:
  - primary_muscles / secondary_muscles / stabilizers
  - joint_stress (per-site 0-3 breakdown)
  - equipment_required (only implied by name, e.g. "Barbell Row" — not
    encoded as a structured list anywhere in the source)
  - regressions / progressions (except where the exercise itself appears
    in one of the 4 named ladders in file 9 §7 — squat, horizontal push,
    vertical pull, hinge only)
  - substitutions_pain_free, execution_cues, common_mistakes,
    coaching_tips, tempo_default, rep_range_optimal

None of these were fabricated to fill the gap. Any future consumer of
AlternativeEntry that needs one of these fields either needs a fuller KB
source, or should treat the exercise as "insufficiently specified" rather
than programming around a guessed value.

## 3. `contraindicated_by_flag` — no such field exists in the source

File 16 §12's pseudocode references `e.contraindicated_by_flag` as a
filter input, but no populated Exercise record in the KB actually has
this field — the schema in §1 doesn't list it either. algorithms.py
approximates it using `substitutions_pain_free` keys (the closest actual
populated data expressing "this flag is relevant to this exercise"), and
this approximation is called out inline in algorithms.py's docstring, not
hidden.

## 4. Equipment substitution / injury substitution tables are not exhaustive

file 9 §4 covers 9 named barbell exercises; §5 covers 6 named
injury/issue categories. Any exercise or condition outside those lists
returns None from rules.py — that's a correct "not covered," not a bug.

## 5. Sex-based and age-based notes (file 9 §9, §10) are prose, not encoded

These sections are qualitative guidance ("female clients often prioritize
glute/hamstring development...") without thresholds or a decision
structure to make deterministic. They were deliberately NOT converted
into a scoring rule, since doing so would mean inventing the thresholds
ourselves. If you want these operationalized, that requires either a
product decision on the actual rule (e.g. "always add 1 extra glute
isolation slot regardless of goal") or a fuller source that states one.
