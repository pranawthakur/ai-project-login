# Feedback / Explanation Engine — Coverage Gaps

**Not KB-sourced.** The only source, `26_explanation_engine/README.md`,
is a 2-line stub ("Foundation module."). Built at your request as an
engineering design, same treatment as `substitution` — every threshold
here is invented to be reasonable, not transcribed. 12/12 tests passing,
which proves internal consistency, not scientific correctness.

## What it does
1. `classify_feedback(rating, notes)` — turns your existing 1-5 star
   difficulty rating + free-text notes into an actionable category
   (too_easy / appropriate / too_hard / possible_pain_flag /
   insufficient_data). Pain-keyword detection in notes always overrides
   a numeric rating, by design — a user rating something 3/5 while
   mentioning a sharp twinge should never read as "fine."
2. `explain_decision(decision)` — turns another engine's structured
   output (e.g. progression's `ProgressionDecision`) into a plain-English
   sentence, via a template lookup on `reason_code`. Unmapped reason
   codes fall through to a generic template rather than erroring.

## Known limitations, stated plainly
- The pain-keyword list (`PAIN_KEYWORDS` in constants.py) is a short,
  literal, English-only substring match — not any kind of real NLP. It
  will miss creative phrasing and can false-positive on words like "sore"
  used casually (deliberately narrowed — "sore joint" is listed, bare
  "sore" is not, to reduce false positives at the cost of some misses).
  This needs real user data to tune properly.
- `_REASON_TEMPLATES` in algorithms.py only covers 3 reason codes right
  now (2 progression codes + 1 deload code) — extend this dict as other
  engines add reason codes, or explanations will fall back to a generic
  "Reason: x y z" sentence.
- Confidence scores (0.6-0.9) in FeedbackClassification are hand-picked
  to feel roughly ordered, not calibrated against any real outcome data.

## When you get a better source
Rebuild classify_feedback's thresholds and explain_decision's templates
from real content if it materializes — don't just patch these numbers,
since the whole design (which signals matter, in what order) might
change with a real source.
