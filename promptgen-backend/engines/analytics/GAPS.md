# Analytics Engine — Coverage Gaps

**Not KB-sourced.** Both sources — `20_adherence_engine/README.md` and
`25_metadata_engine/README.md` — are 2-line stubs ("Scaffold for V7.").
Built at your request as an engineering design. 12/12 tests passing,
which proves internal consistency, not that these are the right
thresholds for your actual users.

## What it does
1. `compute_adherence(...)` — sets_logged / sets_prescribed as a
   percentage, bucketed into HIGH (>=80%) / MODERATE (>=50%) / LOW
   (<50%) tiers, with a consecutive-week streak counter for HIGH tier.
2. `stamp_plan_metadata(...)` — pure version bookkeeping: records which
   KB version and which engine versions produced a given plan. This half
   is genuinely low-risk regardless of KB backing — it's software
   metadata, not a fitness claim, so "not KB-sourced" barely matters here
   the way it does for the adherence thresholds.

## Known limitations, stated plainly
- The 80%/50% adherence cutoffs are round numbers chosen for
  readability, not derived from any study or the KB. If you want these
  to actually mean something (e.g. "80% adherence predicts X outcome"),
  that requires real usage data from your app, not a KB lookup — this
  isn't the kind of gap a fuller KB source would fill anyway, it's an
  empirical question about your specific users.
- Adherence is purely count-based (did they log a set at all) — it does
  not weight by whether the reps/weight logged met the target (that
  comparison already lives in the frontend progress-bar logic we built
  earlier in `result.html`). If you want a single unified adherence
  number that accounts for both "did they show up" and "did they hit the
  target," that's a deliberate design decision to make later, not
  something missing by oversight.
- `engine_versions` in PlanMetadata is a free-form dict with no
  enforced schema — nothing stops a caller from passing inconsistent
  version-string formats across engines. Worth tightening if this
  actually gets used for debugging plan-generation history.
