# HANDOFF — Bodyweight-Relative-Strength Gate — PHASE 1 of 3

(Kept as its own file rather than appended to the main HANDOFF.md so this
feature's phase history stays easy to follow on its own.)

## Problem
`select_day_exercises()` gated exercises only by `experience_raw`
(beginner/intermediate/advanced) — by design, no individual exercise was
ever gated by ability. Result: a 104kg beginner and a 60kg beginner get
offered the exact same pull-up/chin-up/dip pool, even though moving your
own full bodyweight through those movements is genuinely much harder at
higher bodyweight — but ONLY if that weight is fat, not muscle. Raw
bodyweight/BMI can't tell those two apart, so they were deliberately not
used as the gating signal.

## Phases
- **Phase 1 (this zip)** — data tagging + core gate function + wiring into
  the existing pool-filter step. Ships with **zero behavior change** —
  nothing calls the new gate yet.
- **Phase 2 (not built yet)** — collect the actual signal at intake
  (capability yes/no/unsure question, optional waist_cm) and pass it from
  `fitness_generator.py` into `select_day_exercises()`.
- **Phase 3 (not built yet)** — auto-promotion: if someone's stuck on the
  regression (e.g. `assisted_pull_up`) but check-in feedback shows it's
  consistently easy/fully completed over a cycle or two, flip them into the
  full pull-up pool next cycle without needing to re-ask.

## What Phase 1 actually did

### 1. Tagged 13 exercises `'_bw_gated': True` in `app/exercise_database.py`
Exercises where the load IS your bodyweight and can't be dialed down like a
barbell weight can:
`pull_up`, `chin_up`, `weighted_pull_up`, `weighted_chin_up`,
`kipping_pull_up`, `archer_pull_up`, `chest_to_bar_pull_up`,
`l_sit_pull_up`, `pistol_squat`, `dips_chest`, `dips_triceps`,
`handstand_push_up`, `decline_push_up`.

Their existing pool-mates (lat_pulldown, assisted_pull_up, assisted dip
machine, incline push-up, hack squat, etc.) are NOT tagged — they're the
safe fallback the gate falls through to.

### 2. `_passes_bw_gate()` — the actual decision, priority order
1. **Direct capability answer** (`"yes"`/`"no"`) — always wins when present.
   This is the only signal that tells a muscular-but-heavy person apart
   from an overweight person with certainty.
2. **Waist-to-height ratio** (`waist_cm / height_cm`), used when there's no
   direct answer. `< 0.53` passes, `>= 0.53` fails-conservative. WHtR beats
   BMI/raw weight here specifically because it isn't confounded by muscle
   mass the way a weight-based number is.
3. **body_fat_pct** (`< 22%` passes), only as a last resort — it's rarely
   filled in at intake today.
4. **Nothing at all** → fails conservative (regression offered instead).
   Never a permanent block — see Phase 3.

### 3. Wired into `_filter_pool()` / `select_day_exercises()`
Same fail-conservative pattern the injury filter already uses: gated
exercises are dropped from the pool and never reintroduced by the
equipment-relax fallback. New optional kwargs on `select_day_exercises()`:
`bw_capability_answer`, `bw_waist_cm`, `bw_height_cm`, `bw_body_fat_pct` —
all default to `None`. If **all** are `None` (true today — no caller passes
them yet), the gate is skipped entirely and behavior is byte-for-byte what
it was before this change.

## Verified (smoke test run during build, not just eyeballed)
- Zero kwargs passed → pull-up family still appears in rotation, unchanged.
- `bw_capability_answer="no"` → pull-up/chin-up/dip family never appears
  across 50 seeds; safe alternates (rows, pulldowns, assisted variants)
  fill the slot instead.
- `waist_cm=110, height_cm=170` (WHtR ≈ 0.65) → gated family never appears
  across 200 seeds.
- `waist_cm=80, height_cm=170` (WHtR ≈ 0.47) → gated family appears freely
  across 200 seeds, same as the ungated baseline.

## What Phase 2 needs to do
- Add capability question(s) to the intake form + `schemas.py`
  (e.g. `can_pull_up: str | None`, values "yes"/"no"/"unsure").
- Add optional `waist_cm` to the intake form (schema already has it at
  check-in time via `CheckinSubmission` — this just needs it earlier).
- In `fitness_generator.py`, read those fields out of the intake profile
  and pass them through to `select_day_exercises()` as
  `bw_capability_answer=`, `bw_waist_cm=`, `bw_height_cm=`.
- No changes needed to `exercise_database.py` itself for Phase 2 — the gate
  function and wiring are already done and tested in Phase 1.

## What Phase 3 needs to do
- Read per-exercise completion/difficulty history for the regression
  variant (`assisted_pull_up`, etc.) from the existing
  `workout_set_feedback` data, same source `plateau_engine.py` already
  reads.
- If a member has been consistently completing the regression at low
  difficulty for ~1-2 cycles, store an override that flips
  `bw_capability_answer` to `"yes"` effective next cycle's generation —
  no new tracking engine, reuse the existing feedback pipeline.
