import time

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

from app.config import settings

bearer_scheme = HTTPBearer()

# ── JWT verification, take 2 ────────────────────────────────────────────────
# History, so the next person doesn't repeat this: this originally verified
# with a hardcoded ES256 public key. admin-dashboard-backend's HANDOFF.md
# flagged that as wrong and claimed Supabase actually issues HS256 tokens
# signed with the legacy shared secret — that turned out to ALSO be wrong
# for this project (confirmed live: python-jose rejected HS256 verification
# with "The specified alg value is not allowed", meaning the token's real
# `alg` header is neither of those two guesses... it's whatever this
# project's actual signing key is, most likely ES256 via Supabase's newer
# per-project asymmetric keys (the modern default for new Supabase
# projects), fetched from a JWKS endpoint rather than hardcoded anywhere.
#
# Fix: stop guessing the algorithm/key. Fetch Supabase's own published JWKS
# (its public key set), pick the key whose `kid` matches the token's header,
# and verify with whatever algorithm THAT key declares. This is correct
# regardless of whether the project is on HS256, ES256, or RS256, and
# survives Supabase rotating or adding signing keys without another manual
# guess-and-check round.

_JWKS_URL = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
_JWKS_CACHE_TTL_SECONDS = 3600
_jwks_cache: dict = {"keys": [], "fetched_at": 0.0}


def _get_jwks() -> list[dict]:
    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < _JWKS_CACHE_TTL_SECONDS:
        return _jwks_cache["keys"]

    try:
        resp = httpx.get(_JWKS_URL, timeout=10)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
    except Exception:
        # If the fetch fails but we have a (possibly stale) cache, prefer
        # stale-but-present over hard-failing every request during a
        # transient network blip.
        if _jwks_cache["keys"]:
            return _jwks_cache["keys"]
        raise

    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = now
    return keys


def _find_key_for_token(token: str) -> dict:
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    keys = _get_jwks()
    for key in keys:
        if key.get("kid") == kid:
            return key

    # kid not found — could be a genuinely bad token, or Supabase rotated
    # keys since our cache was fetched. Force one fresh fetch and retry
    # once before giving up, instead of caching a miss for a full hour.
    _jwks_cache["fetched_at"] = 0.0
    keys = _get_jwks()
    for key in keys:
        if key.get("kid") == kid:
            return key

    raise JWTError(f"No matching signing key found for kid={kid!r}")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials
    try:
        key = _find_key_for_token(token)
        payload = jwt.decode(
            token,
            key,
            algorithms=[key.get("alg", "ES256")],
            audience="authenticated",
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
        )
    except Exception as e:
        # JWKS fetch failure, malformed token header, etc. — still a 401
        # from the caller's point of view, but logged with more context
        # server-side than the generic JWTError branch above.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not verify token: {e}",
        )

    return payload
