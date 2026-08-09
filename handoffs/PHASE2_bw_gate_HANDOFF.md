# HANDOFF — Bodyweight-Relative-Strength Gate — PHASE 2 of 3

See `PHASE1_bw_gate_HANDOFF.md` first for the gate's design (priority
order: capability answer → WHtR → body_fat_pct → conservative default) and
the exercise tagging.

## Important correction from Phase 1
Phase 1 wired the gate into `exercise_database.py`'s own
`select_day_exercises()` — but that function turned out **not to be the
live path**. `fitness_generator.py` actually imports `select_day_exercises`
from **`app/exercise_selector.py`** (a separate, richer selector that
duplicate-movement-protects and goal-filters on top of the same
`_filter_pool`, calling it directly rather than going through
`exercise_database.py`'s wrapper). Phase 1's gate was correct but
effectively dormant — this phase fixes that by wiring the SAME gate into
the actual live selector, and both selectors now share one resolver
function so they can't drift apart again.

## What Phase 2 actually did

### 1. `app/exercise_database.py` — `resolve_bw_gate_ok()`
Extracted the "no signal → True, else ask `_passes_bw_gate`" logic Phase 1
had inlined into `select_day_exercises()` out into its own function, so
both selectors call the exact same decision path instead of two copies
that could quietly diverge later.

### 2. `app/exercise_selector.py` — the real live selector, now gated
- `select_day_exercises_detailed()` and its public wrapper
  `select_day_exercises()` both take the same four new optional kwargs as
  Phase 1's `exercise_database.py` version: `bw_capability_answer`,
  `bw_waist_cm`, `bw_height_cm`, `bw_body_fat_pct`.
- Both of its internal `_filter_pool(...)` calls (compound pool, isolation
  pool) now pass the resolved `bw_gate_ok` through — this is the actual
  fix; before this, the gate never touched a single real request.
- `find_substitute()` (used by `validator.py`'s repair pass) gained an
  optional `bw_gate_ok: bool = True` param — defaults to permissive since
  the repair path doesn't have per-member intake data in scope yet. Takes
  the already-resolved bool, not raw signals (nothing new to resolve at
  repair time). Not wired to real data yet — noted as a Phase 3+ nice-to-have,
  not required for this feature to work correctly.

### 3. `app/fitness_generator.py` — passes real profile data through
The single call site (`select_day_exercises(...)` inside the weekly-day
loop) now passes:
```
bw_capability_answer=profile.get("bw_capability_answer"),
bw_waist_cm=_to_float_or_none(profile.get("waist_cm")),
bw_height_cm=_to_float_or_none(profile.get("height_cm")),
bw_body_fat_pct=_to_float_or_none(profile.get("body_fat_pct")),
```
New helper `_to_float_or_none()` added — treats blank string, `None`, and
unparsable values all as `None` (so a skipped optional field correctly
reads as "no signal" rather than a wrong 0cm/0% value that could crash the
WHtR math or falsely fail someone).

### 4. `app/main.py` — `/result` intake endpoint
Two new optional `Form(...)` fields:
- `can_pull_up` ("yes" / "no" / "" for not-sure — stored as
  `profile["bw_capability_answer"]`, lowercased, blank → `None`)
- `waist_cm` (stored as `profile["waist_cm"]`, blank → `None`)

Both flow into the existing intake-lock/change-detection comparison
automatically (it already diffs the whole `profile` dict), so changing
either on a resubmit correctly triggers regeneration like any other field.

**Free synergy already in the codebase:** `_apply_latest_checkin_to_profile()`
(used by `/api/regenerate`) already overlays `waist_cm`/`body_fat_pct` from
a member's latest biweekly check-in onto `profile` before regeneration —
those are the exact same keys `fitness_generator.py` now reads for the
gate. So once a member logs a fresh waist measurement at check-in, their
*next* regenerated plan automatically re-evaluates the gate with the new
number, with zero extra plumbing. This is most of what Phase 3's
auto-promotion needs — Phase 3 mainly needs to handle the case where they
never update `waist_cm`/`can_pull_up` again but are visibly crushing the
regression in their workout feedback.

### 5. Frontend — `dashbord.html` (both copies: root + `promptgen-backend/`)
Added to the Basics card, right under the BMI box:
- "Can you currently do a full pull-up?" — `<select id="canPullUp">`
  (Not sure / Yes / No)
- "Waist (cm) — optional…" — `<input id="waistCm" type="number">`

Both added to `handleSubmit()`'s `body` `URLSearchParams` as `can_pull_up`
and `waist_cm`. The fast-diet endpoint (`/api/plan/diet`) does NOT need
these — it only builds a placeholder workout skeleton (no real exercise
selection happens there); the real `/result` call replays the exact same
stashed `body`, so the new fields reach the real selector correctly.

## Verified (real smoke test against `exercise_selector.select_day_exercises`,
the actual function `fitness_generator.py` calls — not a mock)
- No signal at all → gated exercises (Pull-Up, Chin-Up, etc.) still appear
  across 100 seeds — unchanged from pre-gate behavior.
- `waist_cm=110, height_cm=170` (WHtR≈0.65) → never appear, 200 seeds.
- `waist_cm=80, height_cm=170` (WHtR≈0.47) → appear freely, 200 seeds.
- `bw_capability_answer="no"` overrides even a lean WHtR → never appear.
- `bw_capability_answer="yes"` overrides even a heavy WHtR → appear freely.
- `_to_float_or_none` correctly treats `""`, `None`, `"abc"`, and `"0"` all
  as `None` (no false 0-value signal), and parses real numbers correctly.

## Known gap / not done this phase
- `find_substitute()`'s repair path in `validator.py` doesn't pass
  `bw_gate_ok` yet — defaults permissive. Low priority: this only matters
  if a duplicate-movement repair specifically tries to substitute a gated
  exercise back in, which is rare (repair swaps within the same slot's
  already-filtered candidates).
- No sandbox verification against a fully running server (this dev
  environment doesn't have the `supabase` package installed — unrelated to
  this change, same as the real deployment's `requirements.txt`
  dependency, not reproducible here). Core selection logic was verified
  directly against the real `exercise_selector` module instead.

## What Phase 3 needs to do
- Read per-exercise completion/difficulty history for the regression
  variant (`assisted_pull_up`, etc.) from `workout_set_feedback`, same
  source `plateau_engine.py` already reads.
- If a member has been consistently completing the regression at low
  difficulty for ~1-2 cycles AND hasn't already got a "yes"/passing WHtR on
  file, store an override so `bw_capability_answer` effectively reads
  `"yes"` for their next cycle's generation — reuse the existing feedback
  pipeline, no new tracking engine.
