# Constraints (Safety) Engine — Coverage Gaps

Sources: files 12, 18, 19, 20 of KnowledgeBase V7 (safety/medical red
flags, plus adjacent gating logic). 43 tests pass.

This engine is genuinely KB-grounded — file 12 in particular contains
real decision trees (global safety gate, pain triage, condition-specific
constraints, medication interaction flags, disordered-eating routing)
that were already written close to pseudocode in the source, making this
one of the more direct, low-risk ports.

## Known gaps
- `condition_constraints()` falls back to a conservative RESTRICT for any
  condition not in `CONDITION_CONSTRAINTS` — this is a deliberate
  fail-safe default (restrict rather than proceed on unknown input), not
  a claim that every possible medical condition is covered by the table.
  The table only contains what file 12 §4 explicitly names.
- `ed_safety_route()`'s 2-flag confidence threshold for flagging possible
  disordered eating is cited to "file 12 Section 12 troubleshooting note"
  — verify this against the source directly before relying on it
  clinically; this is exactly the kind of threshold that should be
  double-checked by a human against the primary text, not just trusted
  because a citation comment exists.
- This engine imports `build_default_safe_template` from the programming
  engine (cross-engine dependency) — if programming's default-safe-template
  logic changes, re-run constraints' tests to confirm nothing broke
  silently on the other side of that import.
