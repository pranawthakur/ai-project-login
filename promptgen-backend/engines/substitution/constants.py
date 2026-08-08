import json, os
_DIR = os.path.dirname(__file__)
DATA = json.load(open(os.path.join(_DIR, 'data.json')))
RULES_RAW = json.load(open(os.path.join(_DIR, 'rules_raw.json')))
SECTION_INDEX = json.load(open(os.path.join(_DIR, 'section_index.json')))

# ---------------------------------------------------------------------
# Engineering-default thresholds. The KB source for this engine
# (22_conflict_engine/README.md) is a one-line mandate with no numbers
# attached -- see models.py module docstring. These constants exist so
# every threshold used by rules.py lives in one place and can be tuned
# without touching logic; none of them should be presented to a user as
# a KB-sourced fact.
# ---------------------------------------------------------------------

# A joint is "high stress" at joint_stress >= this value, using the same
# 0-3 scale documented for the exercise_database engine (source: file 16
# Sec 1.1: 3 = "requires clean technique/limited volume").
HIGH_JOINT_STRESS_THRESHOLD = 3

# Flag JOINT_STRESS_STACK once this many *additional* high-stress hits
# land on the same joint within one session (i.e. a 2nd hit triggers it).
MAX_HIGH_STRESS_HITS_PER_JOINT = 1

# Flag PATTERN_REDUNDANCY once the same movement_pattern is used as the
# primary driver more than this many times in one session.
MAX_PATTERN_REPEATS_PER_SESSION = 2
