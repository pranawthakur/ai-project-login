# Substitution (Exercise Conflict) Engine — Coverage Gaps

**Read this before trusting this engine the way you'd trust
exercise_database, programming, or constraints.**

## This engine is not KB-grounded

Its sole source, `22_conflict_engine/README.md`, is literally two lines:

    # Exercise Conflict Engine
    Rules to avoid conflicting exercise combinations.

manifest.json confirms "tables_extracted": 0 and rules_raw.json is an
empty `{}` — there is no populated rule, threshold, or example anywhere
in this KB for what counts as a "conflicting" exercise combination.

Every concrete rule in this module (joint-stress-stack detection at 2
hits = moderate / 3 hits = high severity, pattern-redundancy at 3x same
pattern, equipment-contention logic) is an **engineering design choice**
built to satisfy that one-line mandate — invented to be reasonable, not
transcribed from anything the KB actually specifies. This was disclosed
in the code's own docstrings by whoever built it (a good practice — the
gap was labeled, not hidden), but it means this engine's actual
correctness is a matter of your judgment/testing, not verifiable against
a source document the way the others are.

## What this means practically

- Fine to run and integrate — it's tested (32 passing tests) and doesn't
  do anything unsafe. But those tests validate internal consistency
  (the code does what the code says), not correctness against real
  exercise science, because there's no source for "correctness" to be
  measured against here.
- The specific thresholds (2 hits = moderate, 3 = high, etc.) should be
  treated as a reasonable starting default you can and probably should
  tune based on real user feedback/outcomes, not as settled numbers.
- If you get a fuller KB source that actually defines conflict rules
  later, this whole engine should be rebuilt from that source rather than
  patched — the current version is a placeholder built to spec, not a
  transcription.
