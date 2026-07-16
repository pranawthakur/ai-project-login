-- Phase 2: member login_code + password
--
-- gym-dashboard's "Add Member" flow is intentionally NOT modified as part
-- of this phase, so it keeps creating `members` rows with `login_code` but
-- nothing password-related. This column starts NULL for every existing and
-- future member created that way — that NULL is exactly what the backend
-- (app/membership.py / app/main.py) uses to detect "this member needs to
-- set a password" on their first login.
--
-- Run this once against the Supabase project this backend points at
-- (SUPABASE_URL in .env). Nothing in the application code runs this
-- automatically — there is no migration runner wired up in this repo.

alter table public.members
  add column if not exists password_hash text;

-- No backfill needed/possible: there is no prior password to migrate from
-- (Phase 1 had no password at all, and pre-Phase-1 Supabase Auth passwords,
-- if any existed in production, were never stored on this table and are
-- not recoverable). Every member simply sets a password the first time
-- they log in after this migration runs.
