"""Recovery module is a re-export of engines.fatigue (see __init__.py for
why). Its real test suite lives at engines/fatigue/tests.py -- this file
just proves the re-export actually works."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from engines.recovery import decide_deload, ClientRecoveryState

d = decide_deload(ClientRecoveryState(training_age_years=1, weeks_since_last_deload=10))
assert d.deload_needed is True and d.reason == "scheduled_deload_due", "recovery re-export broken"
print("1 passed, 0 failed (re-export smoke test -- see engines/fatigue/tests.py for full 46-test suite)")
