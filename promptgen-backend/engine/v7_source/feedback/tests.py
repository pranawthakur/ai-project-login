"""app/engines/feedback/tests.py — run directly: python3 tests.py"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engines.feedback.rules import classify_feedback
from engines.feedback.algorithms import explain_decision
from engines.feedback.models import FeedbackCategory

passed = 0
failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {name}")


# ── classify_feedback ─────────────────────────────────────────────────────
check("rating 1 -> too_easy", classify_feedback(1, None).category == FeedbackCategory.TOO_EASY)
check("rating 5 -> too_hard", classify_feedback(5, None).category == FeedbackCategory.TOO_HARD)
check("rating 3 -> appropriate", classify_feedback(3, None).category == FeedbackCategory.APPROPRIATE)
check("no rating, no notes -> insufficient_data", classify_feedback(None, None).category == FeedbackCategory.INSUFFICIENT_DATA)
check("pain keyword overrides an easy rating", classify_feedback(1, "felt a sharp pinch in my shoulder").category == FeedbackCategory.POSSIBLE_PAIN_FLAG)
check("pain keyword detected even with no rating", classify_feedback(None, "sharp pain in knee").category == FeedbackCategory.POSSIBLE_PAIN_FLAG)
check("neutral notes don't trigger pain flag", classify_feedback(3, "felt great, good pump").category == FeedbackCategory.APPROPRIATE)
result = classify_feedback(2, "a little sore")
check("'sore' alone (not 'sore joint') doesn't trigger pain flag", result.category == FeedbackCategory.TOO_EASY)

# ── explain_decision — duck-typed input ─────────────────────────────────────
class FakeDecision:
    def __init__(self, action, magnitude, reason_code):
        self.action, self.magnitude, self.reason_code = action, magnitude, reason_code

d1 = FakeDecision("increase_weight", 2.5, "RIR_BELOW_TARGET_3_WEEKS")
exp1 = explain_decision(d1)
check("known reason_code produces its template", "harder than the target" in exp1.detail)
check("summary includes action and signed magnitude", exp1.summary == "Increase Weight (+2.5)")

d2 = FakeDecision("hold", None, "SOME_UNMAPPED_CODE")
exp2 = explain_decision(d2)
check("unmapped reason_code falls through to generic template, not an error", "some unmapped code" in exp2.detail)

d3 = FakeDecision(None, None, None)
exp3 = explain_decision(d3)
check("no reason_code and no action still produces something readable", len(exp3.detail) > 0)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
