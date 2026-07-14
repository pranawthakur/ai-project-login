# Fatigue Engine — Coverage Gaps

46 tests passing. Real content — this was one of the engines previously
believed to have "nothing but a 2-line stub" behind it; that assessment
was wrong for `fatigue` specifically (right for `analytics`/`feedback`,
which remain broken). Re-verify which source file actually backs this
before assuming coverage elsewhere follows the same pattern.

## Known gaps
- Same citation-granularity note as progression: file/section-level
  citations in docstrings rather than per-value comments. Fine for
  spot-checking a whole rule, slower for verifying one specific number.
- `recovery` is implemented as a re-export of this module (see
  `engines/recovery/__init__.py`) rather than a separate implementation —
  intentional, since the KB apparently treats fatigue and recovery as one
  domain here, not a shortcut. If recovery-specific rules ever get their
  own dedicated KB source, this re-export should be replaced with real
  recovery-specific logic instead of continuing to borrow fatigue's.
