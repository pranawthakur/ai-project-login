# Gym Build Plan — Phase 5 delivery notes (login-gate half)

This is scoped to `build-plan-v2.md`'s Phase 5 (see the top-level bundle's
`BUILD_STATUS.md`/`build-plan-v2.md`, shared across all three repos) — **not**
this repo's own internal engine-development phase numbering (HANDOFF.md,
`PHASE3_NOTES.md`, `handoffs/PHASE*_bw_gate_HANDOFF.md`), which is an
unrelated track. Named separately from those on purpose to avoid confusion.

## What Phase 5 needed from this repo
Per `build-plan-v2.md` §3 Phase 5: *"ai-project-login's login endpoint must
check members.status and return a 'renew to continue' response instead of
a normal session when status in ('payment_overdue', 'suspended')"* — the
actual enforcement of the T+5/T+15 statuses the gym-dashboard's new
lifecycle cron (`app/lifecycle.py`, other repo) now sets. The cron only
writes the status; this repo is what actually acts on it.

## New files
None — no new SQL migration, no new dependency (see below). Only edits to
existing files.

## Updated files
- **`app/membership.py`** — split the old single `get_current_member` into
  two:
  - `get_current_member` — now blocks `payment_overdue`/`suspended` with a
    *structured* 403 (`{code: "renewal_required", status, message}`) instead
    of the old flat string, so the frontend can tell "renew to continue"
    apart from every other 403 reason. Still the dependency every ordinary
    member-facing endpoint in `app/main.py` uses (workout generation,
    check-in, analytics, etc.) — this is the actual "denies login/check-in"
    behavior the plan asked for.
  - `get_current_member_allow_renewal_locked` (new) — identical identity
    check, but does **not** block on those two statuses. Used only by
    `app/renewal.py`'s two endpoints. Without this, a locked-out member
    couldn't reach the very screen that lets them pay their way back in —
    `get_current_member`'s block would fire before `renewal_status`/`pay_now`
    ever ran.
- **`app/renewal.py`** — both endpoints switched to the new permissive
  dependency (see above). Docstring updated to explain why.
- **`app/main.py`** — `POST /member/login` still issues a session token for
  `payment_overdue`/`suspended` members (deliberately not a 403 — same
  reasoning as above, a blocked login would trap them with no way to fix
  it), but the response now includes `renewal_required: true` and `status`
  so a caller can route them straight to the renewal screen instead of the
  normal dashboard. Any other non-active status (not a real value in this
  system today, kept fail-closed for a future one) is still a hard 403,
  unchanged.
- **`dashbord.html`** — the existing `GET /api/my-plan` 403 handler (which
  used to render a dead-end "Access restricted... contact your gym" message
  with no way out) now checks for the structured `renewal_required` detail
  and, when present, renders an actual recovery screen: fetches
  `GET /member/renewal-status` for that gym's plan catalog and lets the
  member tap a plan to call `POST /member/pay-now` and get redirected to
  Razorpay checkout — same mechanics as the Phase 3 renewal banner
  (`openPlanPicker`/`startPayment`), reimplemented standalone since the
  banner's own DOM no longer exists once `document.body` gets replaced for
  the restricted-access case. Any other 403 keeps the old plain message.

## Not touched
- `login.html` — no changes needed. It already just stores the token and
  redirects to `dashbord.html` regardless of `renewal_required`; the gate
  lives entirely in the `/api/my-plan` 403 handler on that page, which now
  branches correctly. The `renewal_required`/`status` fields added to the
  login response aren't consumed by `login.html` itself yet, but are there
  for any future caller (e.g. a native app) that wants to skip straight to
  the renewal screen without waiting on the my-plan round trip.
- No SQL migration — `members.status` is a free-text column with no CHECK
  constraint (see `ai-project-gym-dashboard/schema.sql`), so a third value
  (`payment_overdue`, alongside the existing `active`/`suspended`) needed no
  schema change on either side.
- No new Render env vars, no new dependency in `requirements.txt` — this
  half of Phase 5 reuses `MEMBER_SESSION_SECRET`, `GYM_DASHBOARD_BASE_URL`,
  and `MEMBER_APP_SERVICE_KEY`, all already set from Phase 3's onboarding.

## Sanity checks run
`py_compile` on `app/membership.py`, `app/renewal.py`, `app/main.py`.
`dashbord.html`'s three `<script>` blocks extracted and passed
`node --check`. `<div>`/`</div>` balanced (81/81), no duplicate `id`
attributes after the edit — same checks this repo's own Phase 4 notes
(other repo's `BUILD_STATUS.md`) describe running on `index.html`.

## Known gap, flagged not fixed
`get_current_member_allow_renewal_locked` has no rate limiting, same
pre-existing gap `/member/login` already has (noted in `main.py`'s own
comment above that endpoint). Not new to this phase, not addressed here.
