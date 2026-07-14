# Phase 3 — KB V7 Retrieval + Trainer Review: delivery notes

## Fixed along the way
`engine/exercise_enrichment.py` imports `engine.v7_source.exercise_database`,
but `engine/v7_source/` was missing from the uploaded project package (only
present in the separate v7-integration-phase1 zip). Copied it in — without
this, `knowledge_retriever.py` (and the already-existing enrichment adapter)
would ImportError at startup.

## New files
- `app/knowledge_retriever.py` — the only module that imports `engine.*` /
  `engines.*` directly now. Wraps: exercise enrichment (5 full V7 records),
  condition constraints (`engines.constraints`), and movement-pattern facts
  (`engines.biomechanics`, mapped from this app's ~20-tag taxonomy to V7's
  10-pattern enum — patterns with no honest analog map to `None`, not a
  guess). `functools.lru_cache` on every wrapper.
- `app/trainer_review.py` — builds a deterministic substitution whitelist
  per exercise (via `exercise_selector`/`exercise_database`, same machinery
  the deterministic core uses), assembles bounded KB context via
  `knowledge_retriever`, prompts Gemini with a strict JSON-only contract,
  parses defensively (fails to "no changes" on any parse error, never
  raises into the pipeline).
- `app/review_validation.py` — re-derives equipment/injury safety and the
  protected-compound-pattern rule (leg day must stay squat-pattern) for
  every proposed substitution from scratch, checked against the
  deterministic whitelist. Rejects anything outside it — verified with a
  fake "invented exercise" in testing (see below).

## Updated files
- `app/validator.py` — now goes through `knowledge_retriever.condition_constraints()`
  instead of importing `engines.constraints` directly; added a bonus
  cross-check against V7's `who_should_avoid` text for the exercises that
  have full enrichment records.
- `app/exercise_selector.py` — every selected exercise now carries a
  `kb_context` field (V7 enrichment or `None`, additive-only — doesn't change
  selection). `find_substitute()` gained a third preference tier: if V7
  documents a pain-free substitute for the exercise being replaced that
  matches a disclosed injury, prefer it.
- `app/fitness_generator.py` — added `build_and_review_workout_days()`
  (wraps the **unmodified** `build_deterministic_workout_days()` with the
  Trainer Review + Review Validation stages) and an async
  `generate_dashboard_with_review()` sibling to the existing
  `generate_dashboard()`.

## Deliberately NOT done in this pass
- **`main.py` is untouched.** Its `/result` route still calls
  `build_deterministic_workout_days()` directly, not the new
  `build_and_review_workout_days()` — per this phase's "preserve existing
  APIs" instruction, wiring the live route to the new async pipeline is a
  one-line swap left as a deliberate follow-up, not bundled in silently.
  Until that swap happens, Trainer Review does not run in production.
- **`progression.py` / `split_engine.py` / `equipment.py` / frontend**:
  untouched, per the task's explicit "do not modify" list.
- **`engines/substitution`, `engines/feedback`, `engines/analytics`**: not
  wrapped by `knowledge_retriever.py` — their own `GAPS.md` files call them
  placeholders built from stubs, not real KB source (same finding as
  v7pkg/README.md's earlier audit). Wrapping them would present placeholder
  data as if it were grounded.

## Verified
- `tests/regression/run_regression.py --capture` then re-run: **4/4 PASS,
  zero drift** — the deterministic core's output is byte-identical before
  and after this change (the new `kb_context` field lives only on
  intermediate `picks` dicts inside `exercise_selector.py`, never on the
  final day/exercise dicts the regression baseline snapshots).
- Manual async run of `build_and_review_workout_days()` end-to-end with a
  fake LLM caller.
- Manual test of `trainer_review.review_workout()` +
  `review_validation.apply_review()`: a valid, whitelisted substitution was
  accepted; a fabricated exercise name ("Totally Invented Exercise 9000")
  was rejected with reason
  `trainer_suggested_exercise_outside_deterministic_candidates`.

## Suggested next steps (not done here)
1. Review this delivery, then wire `main.py`'s `_run()` to call
   `await build_and_review_workout_days(...)` instead of
   `build_deterministic_workout_days(...)` — the one deliberate live-route
   change left undone.
2. Add a regression-style fixture for `trainer_review.py` /
   `review_validation.py` themselves (this delivery's tests were manual,
   ad hoc scripts, not committed test files, given the phase's scope).
3. Decide whether Trainer Review should run per-request or be cached
   alongside the plan (a live Gemini call adds latency to `/result`).
