-- Enables logging out a single member session token (jti) without
-- rotating MEMBER_SESSION_SECRET for every member. Checked in
-- app/auth.py's verify_member_token(); written to by
-- app/auth.py's revoke_member_token(), called from POST /member/logout
-- in main.py.
--
-- Run this against the real Supabase project, same as every other file
-- in this sql/ folder — presence in the repo does not mean it has been
-- applied.

create table if not exists revoked_member_tokens (
    jti text primary key,
    member_id uuid not null,
    revoked_at timestamptz not null default now()
);

-- Optional cleanup: tokens are already worthless after 30 days (see
-- _TOKEN_TTL_SECONDS in app/auth.py), so rows older than that are safe to
-- prune periodically to keep this table small, e.g.:
--   delete from revoked_member_tokens where revoked_at < now() - interval '31 days';
