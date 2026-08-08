"""
app/engines/feedback/constants.py

Every threshold here is an engineering default (see models.py docstring).
Change these freely if real user data suggests better cutoffs.
"""

# 1-5 star difficulty rating thresholds (your app's existing ExerciseFeedback.difficulty_rating scale)
RATING_TOO_EASY_MAX = 2          # rating <= this -> too_easy
RATING_TOO_HARD_MIN = 4          # rating >= this -> too_hard
# 3 falls in between -> appropriate

# Keyword scan for pain-adjacent language in free-text notes. Deliberately
# narrow and literal (substring match, case-insensitive) rather than any
# kind of NLP/sentiment model — false negatives are safer to review by a
# human than false positives silently overriding user intent, but this
# list should stay conservative and short.
PAIN_KEYWORDS = [
    "pain", "hurt", "sharp", "pinch", "pulled", "strain", "twinge",
    "sore joint", "clicking", "popping",
]

# Below this confidence, explanations get a hedge phrase appended rather
# than stated as fact.
LOW_CONFIDENCE_THRESHOLD = 0.5
