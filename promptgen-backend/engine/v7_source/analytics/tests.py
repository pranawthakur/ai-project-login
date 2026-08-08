"""app/engines/analytics/tests.py — run directly: python3 tests.py"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.analytics.scoring import compute_adherence
from engines.analytics.rules import stamp_plan_metadata
from engines.analytics.validators import validate_adherence_report
from engines.analytics.models import AdherenceTier

passed = 0
failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {name}")


# ── compute_adherence ────────────────────────────────────────────────────
r1 = compute_adherence("m1", 1, sets_prescribed=20, sets_logged=18)
check("90% logged -> HIGH tier", r1.tier == AdherenceTier.HIGH)
check("adherence_pct computed correctly", r1.adherence_pct == 90.0)

r2 = compute_adherence("m1", 1, sets_prescribed=20, sets_logged=12)
check("60% logged -> MODERATE tier", r2.tier == AdherenceTier.MODERATE)

r3 = compute_adherence("m1", 1, sets_prescribed=20, sets_logged=5)
check("25% logged -> LOW tier", r3.tier == AdherenceTier.LOW)

r4 = compute_adherence("m1", 1, sets_prescribed=0, sets_logged=0)
check("zero prescribed sets doesn't divide by zero", r4.adherence_pct == 0.0)

r5 = compute_adherence("m1", 1, sets_prescribed=20, sets_logged=25)
check("overachieving (>100%) still classifies as HIGH, not an error", r5.tier == AdherenceTier.HIGH and r5.adherence_pct == 125.0)

r6 = compute_adherence("m1", 3, sets_prescribed=20, sets_logged=18, prior_weekly_tiers=[AdherenceTier.HIGH, AdherenceTier.HIGH])
check("streak counts consecutive prior HIGH weeks plus current", r6.streak_weeks == 3)

r7 = compute_adherence("m1", 3, sets_prescribed=20, sets_logged=18, prior_weekly_tiers=[AdherenceTier.MODERATE, AdherenceTier.HIGH])
check("streak breaks at first non-HIGH prior week", r7.streak_weeks == 1)

check("no validation errors on a normal report", validate_adherence_report(r1) == [])

# ── stamp_plan_metadata ───────────────────────────────────────────────────
meta = stamp_plan_metadata("plan_123", "member_1", "fat_loss", "intermediate", engine_versions={"programming": "1.0"})
check("kb_version stamped correctly", meta.kb_version == "V7_Part7")
check("engine_versions carried through", meta.engine_versions["programming"] == "1.0")
check("goal/training_age carried through", meta.goal == "fat_loss" and meta.training_age == "intermediate")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
