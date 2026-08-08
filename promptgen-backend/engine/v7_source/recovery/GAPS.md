# Recovery Engine — Coverage Gaps

Recovery is a thin re-export of `engines.fatigue` (see fatigue/GAPS.md).
1 smoke test here proves the re-export works; the real 46-test suite
lives at `engines/fatigue/tests.py`. This is a deliberate architecture
choice given the KB source treats fatigue and recovery as one domain —
not a shortcut to avoid building recovery for real. If you get a fuller
KB source with recovery-specific rules (e.g. sleep-based recovery
scoring, HRV-adjacent logic) later, replace this re-export with a real
implementation rather than patching it.
