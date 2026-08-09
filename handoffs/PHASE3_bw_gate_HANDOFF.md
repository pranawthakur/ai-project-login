# HANDOFF — Bodyweight-Relative-Strength Gate — PHASE 3 of 3 (complete)
# + this session's bugfix + admin-route auth fix

See `PHASE1_bw_gate_HANDOFF.md` and `PHASE2_bw_gate_HANDOFF.md` first.

## What Phase 3 actually did

### 1. `app/exercise_database.py` — `BW_GATE_REGRESSION_MAP` / `get_bw_gate_regression_exercise_ids()`
Hand-curated map from each of the 13 `_bw_gated` exercise_ids to its
specific easier bodyweight-regulated variant(s) — e.g. `pull_up` ->
(`assisted_pull_up`, `band_assisted_pull_up`), `pistol_squat` ->
(`assisted_pistol_squat`, `resistance_band_pistol_squat`),
`handstand_push_up` -> (`pike_push_up`,), etc. Deliberately NOT derived
from `_movement_id` grouping — that bucket is coarser than "same
capability" (e.g. `isolation_arm` lumps biceps curls in with triceps
dips; `squat` lumps pistol_squat next to Barbell Back Squat). Auto-
deriving from movement_id would let an easy Barbell Curl streak falsely
promote pull-up eligibility. Every id in the map verified to exist in
`EXERCISE_DB` and confirmed non-gated itself.

### 2. `app/main.py` — `_apply_bw_gate_promotion()`
Wired into `/api/regenerate` only, right after `_apply_latest_checkin_
to_profile` — NOT into `/result`. Baking a promotion into `profile`
before `/result`'s raw-intake lock-check comparison would corrupt that
comparison and cause spurious regeneration loops on every login; `/api/
regenerate` already has the established pattern (see `_apply_latest_
checkin_to_profile`) for server-computed overlays onto a stored intake.

Logic:
- Skip (no-op) if the gate's already open — `resolve_bw_gate_ok` already
  reads True (direct "yes" or passing WHtR on file).
- Skip if the member answered "no" THIS cycle explicitly — current,
  first-hand input beats an inferred pattern; never silently overridden.
- Otherwise, pull `workout_exercise_feedback` rows for the curated
  regression exercises (mapped via `get_bw_gate_regression_exercise_ids`
  -> display names via `get_full_exercise_profile`), reuse `feedback_
  engine.classify_feedback` + `check_consecutive_pattern` (its EXISTING
  3-in-a-row "too_easy" -> `suggest_progression` rule — no new threshold
  invented) against the last 3 logged cycles per regression exercise.
- If it fires: `profile["bw_capability_answer"] = "yes"`, logged via
  `decision_audit_engine.record_decision` (decision_type=
  "bw_gate_promotion") for traceability.
- Fails soft throughout — any read error leaves profile unchanged, never
  blocks generation, same posture as `_apply_latest_checkin_to_profile`.

No new tracking table — recomputed fresh from `workout_exercise_feedback`
on every `/api/regenerate` call, same posture as `plateau_engine.py`
recomputing plateau status fresh each time rather than caching a verdict
that could drift from the real feedback rows.

**Verified (7 cases, real `feedback_engine`/`exercise_database` code,
not mocked):** clean 3x "too_easy" promotes; mixed ratings don't; already-
passing WHtR skips; explicit "no" this cycle wins over history; a pain
note on one of the 3 cycles suppresses the pattern (via `feedback_engine`'s
own pain-keyword check); the dips-group regression exercise (separate
from the pull-up group) promotes independently; only 2 logged cycles
(below the 3-minimum) does not promote.

## Bug found and fixed this session: `resolve_bw_gate_ok()`

The "no signal at all -> True (ungated)" shortcut checked only 3 of the
4 args (`bw_capability_answer`, `bw_waist_cm`, `bw_body_fat_pct`) —
`bw_height_cm` was missing from the condition. Since `height_cm` is
ALWAYS populated on a real `/result` submission (defaults to `"170"` if
left blank), any member who just left the pull-up question and waist
measurement blank — the common case — took this shortcut and got `True`
(gate open, unrestricted) instead of `_passes_bw_gate`'s real fail-
conservative default (`False`). This silently defeated the entire Phase
1/2 gate design for most real users since Phase 2 shipped.

Fixed: the condition now checks all four args, matching the function's
own docstring intent (true zero-signal — a genuinely unmodified pre-
Phase-1 caller passing none of the four kwargs — still defaults to
`True`/ungated for backward compatibility; any real signal, including
just `height_cm`, now correctly falls through to `_passes_bw_gate`).

Verified: matches `_passes_bw_gate` output for the realistic blank-
profile case, and the original Phase 1/2 HANDOFF smoke-test assertions
(no-signal-at-all ungated; explicit "no"/"yes" override WHtR either
direction) still pass unchanged.

**Action needed:** any member whose active plan was already generated
under the old buggy (ungated) behavior won't retroactively re-gate until
their next `/api/regenerate` call. Decide whether that's fine to let ride
or worth a manual nudge before/around the mid-August launch.

## Second fix this session: `/api/admin/*` routes had NO auth at all

Eight routes (`/api/admin/health`, `/metrics`, `/kb-version`,
`/orchestration`, `/configuration`, `/governance`, plus two `POST`
routes — `/improvement-proposals`, `/research-integration`) had no auth
dependency whatsoever — callable by anyone, no login, no key. The two
`POST` routes let anyone write arbitrary governance/research-integration
rows.

Fixed with a new shared-secret dependency, `require_admin_key`, gating
all 8 — same fail-closed pattern as the existing `/generate/test`'s
`DEV_TEST_KEY`: unset `ADMIN_API_KEY` -> 503 (route disabled, never
silently open), wrong/missing `X-Admin-Api-Key` header -> 401, correct
key -> passes through unchanged. Added `admin_api_key: str = ""` to
`config.py`'s `Settings`, and `ADMIN_API_KEY` (`sync: false`) to both
`render.yaml` copies (root + `promptgen-backend/`) alongside the existing
`DEV_TEST_KEY` entry.

Verified: unit-tested all 4 states directly (unset+no-header -> 503,
set+wrong-header -> 401, set+no-header -> 401, set+correct-header ->
passes).

**Action needed (you, not me — needs Render dashboard access):** set a
real `ADMIN_API_KEY` value in Render's env vars, same as the other
`sync: false` secrets. Leaving it unset is safe (routes just 503) but
means you can't use them either.

## Still open (not touched this session — restated from `DEPLOY_READINESS.md`)
- Rotate `.env` secrets if this zip or an earlier one left your machine.
- Confirm the 6 pending SQL migrations have actually been run against the
  real Supabase project (listed in `DEPLOY_READINESS.md` item 3).
- `validator.py`'s `find_substitute()` repair path still defaults
  `bw_gate_ok=True` (permissive) — low priority, only matters for a rare
  duplicate-movement repair trying to substitute a gated exercise back in.
