# Progression Engine — Coverage Gaps

Source: 17_Periodization_and_AI_Decision_Engine.md (the one real file
among mostly-stub sources listed for this engine originally). 48 tests
passing.

This is the split-selection and decision-tree logic we noted earlier was
missing from the `programming` engine — it now lives here instead,
which is the correct home for it (it's genuinely a periodization/decision
concern, not a sets/reps lookup concern).

## Known gaps
- Candidate-split generation (`_candidate_splits`) maps some session-plan
  candidates to the nearest defined fit-matrix row via an alias table
  when the KB's fit-matrix doesn't have an exact row for that day-count/
  goal combination (e.g. "full_body_minimal" defaults to the
  "full_body_x2_3" row). This is a reasonable nearest-neighbor choice,
  not a value the KB states directly for that exact candidate — check
  the alias table in rules.py if a specific split recommendation looks
  off.
- Citation style here is file/section-level (module docstrings, inline
  "Section 1.2" references) rather than the per-value "source:" comment
  convention used in exercise_database — still traceable, just coarser
  grain. Worth requesting finer citation if a specific number needs
  verifying quickly.
