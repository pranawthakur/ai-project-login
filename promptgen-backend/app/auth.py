import time
import uuid

import bcrypt
from fastapi import HTTPException, status
from jose import jwt, JWTError

from app.config import settings

bearer_scheme_error_hint = (
    "Missing or invalid Authorization header. Log in again to get a new "
    "member session token."
)

# ── Member session tokens (self-issued, replaces Supabase Auth) ────────────
# History: this project used to verify Supabase Auth JWTs here (first via a
# hardcoded key guess, then via Supabase's JWKS endpoint — see git history
# for that saga). That entire mechanism depended on members signing up
# through Supabase Auth email/password on the frontend.
#
# That signup flow has been removed. The real, intended member-identity
# path is: a gym admin adds a member in gym-dashboard, which generates an
# 8-digit `login_code` on the `members` row. The member enters that code,
# plus a password (added in Phase 2 — see /member/login and
# /member/set-password in main.py), which looks the row up directly —
# no Supabase Auth user is ever created for a member. So there is nothing
# to verify against Supabase's JWKS anymore.
#
# Instead, this app now signs its own short-lived-ish HS256 tokens keyed by
# MEMBER_SESSION_SECRET. The token's only job is "prove you're the member
# with this id" for subsequent API calls — it is NOT a Supabase Auth token
# and Supabase's own auth.uid()/RLS machinery does not know about it (any
# endpoint that used to rely on RLS + auth.uid() for a member now needs an
# explicit member_id check against the token instead — see membership.py).

_ALG = "HS256"
_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days — long-lived on purpose,
# since members log in rarely (once, from a link their gym sent) and
# there's no email/password to fall back on if the session dies.


def issue_member_token(member_id: str, gym_id: str | None) -> str:
    if not settings.member_session_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MEMBER_SESSION_SECRET is not set on this deployment — "
                   "member login is disabled until it's configured.",
        )
    now = int(time.time())
    payload = {
        "sub": member_id,
        "gym_id": gym_id,
        "iat": now,
        "exp": now + _TOKEN_TTL_SECONDS,
        # A random jti isn't checked against a revocation list anywhere
        # (no such table exists yet) — noted as a follow-up gap, same
        # category as the missing rate-limit on /member/login and /member/set-password.
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.member_session_secret, algorithm=_ALG)


def verify_member_token(token: str) -> dict:
    if not settings.member_session_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MEMBER_SESSION_SECRET is not set on this deployment.",
        )
    try:
        payload = jwt.decode(token, settings.member_session_secret, algorithms=[_ALG])
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired session: {e}",
        )
    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token.",
        )
    return payload


# ── Member password hashing (Phase 2) ───────────────────────────────────────
# Phase 1 (the code-login fix already in this repo) authenticated members by
# `login_code` alone. The project decision for Phase 2 is: the code identifies
# WHICH member is logging in, and a password — set by the member on their
# first login — is what actually proves it's them. A member row created by
# gym-dashboard's "Add Member" has `login_code` but no `password_hash` (that
# column starts NULL — gym-dashboard was intentionally not touched to add
# it). NULL `password_hash` is exactly how "first login, no password yet" is
# detected; see `find_member_by_login_code` callers in main.py.
#
# bcrypt truncates/ignores input past 72 bytes by design — not handled
# specially here since member passwords are short, human-typed strings, not
# machine-generated secrets that could realistically hit that length.
_BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed/empty hash stored somehow — treat as "does not match"
        # rather than raising, so a bad row can't 500 the login endpoint.
        return False
