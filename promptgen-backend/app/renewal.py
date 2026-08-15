"""
Phase 3 — User Interface: renewal window + Pay Now + plan picker.

This app never talks to Razorpay directly — that's all in
ai-project-gym-dashboard (Phase 2). This module does two things:

  1. GET /member/renewal-status — reads the member's own row + their
     gym's membership_plans catalog DIRECTLY from this app's own Supabase
     client. No cross-repo call needed for this part: all three repos
     share one Supabase project (see build-plan-v2.md §4), so
     membership_plans and members are just as readable here as in
     gym-dashboard, read-only.

  2. POST /member/pay-now — the one part that DOES need gym-dashboard:
     creating the actual Razorpay Payment Link requires that gym's
     decrypted Razorpay keys, which only gym-dashboard's process ever
     holds (crypto_utils.py there, never here). This calls gym-dashboard's
     POST /api/gym/{gym_id}/members/{member_id}/payment-link with the
     shared X-Service-Key header (see that repo's payments_razorpay.py
     Phase 3 addition) — this app has already verified the member's own
     session token via get_current_member_allow_renewal_locked before ever
     reaching this point, so the service-key call is on behalf of an
     already-authenticated member, not a blind proxy.

Phase 5 addition (build-plan-v2.md §3): both endpoints below use
get_current_member_allow_renewal_locked, not app.main's usual
get_current_member — a member in 'payment_overdue' or 'suspended' (the two
statuses the gym-dashboard lifecycle cron can now set) is exactly who needs
these two endpoints to recover, so they can't be gated behind the same
"must be active" check every other member-facing endpoint uses. See
app/membership.py for the reasoning.

No separate "check payment status" endpoint is needed: after Razorpay
checkout, the member is redirected back to callback_url (this app's
frontend), which just re-calls GET /member/renewal-status — by then
gym-dashboard's webhook (Phase 2) has already updated the shared
`members` row directly, so the truth is already sitting in the same
table this endpoint reads. Whether the redirect fires before or after
the webhook lands is exactly why the frontend polls a couple of times
instead of trusting a single read (see dashbord.html).
"""

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.db import supabase
from app.membership import get_current_member_allow_renewal_locked

logger = logging.getLogger("renewal")

router = APIRouter(tags=["renewal"])

# Renewal surfaces from T-3 days before expiry onward, or immediately if
# already expired (build-plan-v2.md Phase 3) — same 3-day window Phase 5's
# T-3 reminder trigger uses, deliberately kept as one constant here rather
# than two separately-tuned numbers.
RENEWAL_WINDOW_DAYS = 3


@router.get("/member/renewal-status")
def renewal_status(member: dict = Depends(get_current_member_allow_renewal_locked)):
    from datetime import datetime, timezone

    gym_id = member.get("gym_id")
    expiry_raw = member.get("expiry_date")
    expiry = datetime.fromisoformat(expiry_raw).date() if expiry_raw else None
    today = datetime.now(timezone.utc).date()

    days_until_expiry = (expiry - today).days if expiry else None
    is_expired = expiry is not None and expiry < today
    should_show_renewal = expiry is None or is_expired or days_until_expiry <= RENEWAL_WINDOW_DAYS

    plans_res = (
        supabase.table("membership_plans")
        .select("id,name,duration_months,price")
        .eq("gym_id", gym_id)
        .eq("is_active", True)
        .order("duration_months")
        .execute()
    )

    return {
        "status": member.get("status"),
        "expiry_date": expiry_raw,
        "days_until_expiry": days_until_expiry,
        "is_expired": is_expired,
        "should_show_renewal": should_show_renewal,
        "current_plan": member.get("membership_plan"),
        "plans": plans_res.data or [],
    }


class PayNowRequest(BaseModel):
    plan_id: str


@router.post("/member/pay-now")
def pay_now(body: PayNowRequest, member: dict = Depends(get_current_member_allow_renewal_locked)):
    if not settings.gym_dashboard_base_url:
        raise HTTPException(
            status_code=503,
            detail="GYM_DASHBOARD_BASE_URL is not configured on this deployment — Pay Now is disabled.",
        )
    if not settings.member_app_service_key:
        raise HTTPException(
            status_code=503,
            detail="MEMBER_APP_SERVICE_KEY is not configured on this deployment — Pay Now is disabled.",
        )

    gym_id = member.get("gym_id")
    member_id = member["id"]

    callback_url = (
        f"{settings.member_frontend_url}/dashbord.html?payment=return"
        if settings.member_frontend_url
        else None
    )

    url = f"{settings.gym_dashboard_base_url}/api/gym/{gym_id}/members/{member_id}/payment-link"
    try:
        resp = httpx.post(
            url,
            json={"plan_id": body.plan_id, "callback_url": callback_url},
            headers={"X-Service-Key": settings.member_app_service_key},
            timeout=15.0,
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Could not reach the payments service: {e}")

    if resp.status_code >= 400:
        logger.warning("gym-dashboard payment-link request failed (%s): %s", resp.status_code, resp.text)
        # Pass through gym-dashboard's own detail where possible (e.g. "plan
        # not found", "Razorpay not configured for this gym") rather than a
        # generic message — these are all things the member/gym can act on.
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise HTTPException(status_code=502, detail=f"Could not create payment link: {detail}")

    data = resp.json()
    return {"short_url": data["short_url"], "amount": data.get("amount")}
