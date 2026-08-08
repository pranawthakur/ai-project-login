# Programming Engine — Coverage Gaps

Sources: 1_Master_Workout_Split_Table.md, 2_Programming_Rules.md,
3/4/5_Beginner/Intermediate/Advanced_Programming.md,
6_Intensity_Techniques.md, 7_Goal_Based_Modifications.md,
8_Weekly_Muscle_Volume.md, 13_Cardio_and_Conditioning_Programming.md,
14_Default_Safe_Template_and_Coach_Override.md.

This is the best-sourced engine — all of the above are substantive,
table-dense top-level files, not stub folders. 147 tests pass, all pinned
to literal source values (rep ranges, RIR bands, RPE-to-RIR conversion,
tempo, rest, progression models).

## Known gaps
- The "athletic" goal's rep prescription is a compound string
  ("1-5 (power) / 6-12 (accessory)") rather than a single range — callers
  that need one number for athletic-goal exercises must decide themselves
  whether a given exercise is a power or accessory slot; this engine does
  not classify that.
- Split-selection scoring (`goal_fit`, `fatigue_fit`, `adherence_fit`
  weighted formula) lives in `17_Periodization_and_AI_Decision_Engine.md`,
  which is NOT one of this engine's sources — it wasn't ported here. If
  you want automatic split selection (vs. just volume/reps/rest lookup
  for a split already chosen), that's separate, unbuilt work.
