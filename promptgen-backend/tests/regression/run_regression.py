"""
Regression safety net for the V7 integration work.

Calls build_deterministic_workout_days() directly (not through the LLM
prompt/response path, not through main.py/routes) for the 4 fixed
profiles in profiles.py, and diffs the result against committed baseline
JSON in tests/regression/baselines/.

RUN THIS AFTER EVERY CHANGE:
    python3 tests/regression/run_regression.py            # compare vs baseline
    python3 tests/regression/run_regression.py --capture   # (re)write baseline

--- WHY THE MONKEYPATCH ---
build_deterministic_workout_days() builds its own RNG internally:

    rng = random.Random()

unseeded, on purpose (see its docstring: this gives variety across
re-runs in production). There is no seed parameter on the function and
nothing reads a global random.seed() either, since an unseeded
random.Random() pulls entropy from the OS rather than from global
module state.

To get a reproducible baseline without changing that production
behavior, this harness temporarily replaces random.Random inside the
fitness_generator module with a factory that ignores its arguments and
always returns a random.Random(FORCED_SEED) instance, for the duration
of the call only, then restores the real class. No production code is
touched by this.
"""
import copy
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app import fitness_generator as fg          # noqa: E402
from app import split_engine                      # noqa: E402
from tests.regression.profiles import PROFILES, FORCED_SEED  # noqa: E402

BASELINE_DIR = Path(__file__).resolve().parent / "baselines"


def _seeded_call(fn, *args, **kwargs):
    """Run fn with app.fitness_generator.random.Random forced to a fixed
    seed for the duration of the call. Harness-side only — does not
    touch app/fitness_generator.py."""
    real_random_class = fg.random.Random
    fg.random.Random = lambda *a, **kw: real_random_class(FORCED_SEED)
    try:
        return fn(*args, **kwargs)
    finally:
        fg.random.Random = real_random_class


def generate_days_for_profile(profile: dict) -> list:
    profile = copy.deepcopy(profile)
    exp_key = fg._resolve_exp_key(profile)
    vol = fg.EXERCISE_VOLUME[exp_key]

    split = split_engine.recommend_split({
        "experience": profile.get("experience", "intermediate").lower(),
        "days_per_week": int(profile.get("days_per_week", 4)),
        "session_duration": profile.get("session_duration", "45-60 min"),
        "goal": profile.get("goal", "fat loss"),
        "height_cm": profile.get("height_cm", 170),
        "current_weight_kg": profile.get("current_weight_kg", 70),
        "activity_key": profile.get("activity_key", "moderate"),
    })
    weekly_template = fg._build_weekly_template(
        split["sequence"], int(profile.get("days_per_week", 4))
    )

    days = _seeded_call(
        fg.build_deterministic_workout_days, profile, weekly_template, vol
    )
    return days


def run(capture: bool) -> int:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    failures = []

    for name, profile in PROFILES.items():
        days = generate_days_for_profile(profile)
        baseline_path = BASELINE_DIR / f"{name}.json"

        if capture:
            baseline_path.write_text(json.dumps(days, indent=2, sort_keys=True))
            print(f"[capture] {name}: baseline written ({baseline_path})")
            continue

        if not baseline_path.exists():
            failures.append((name, "no baseline file found \u2014 run with --capture first"))
            continue

        baseline = json.loads(baseline_path.read_text())
        if days != baseline:
            failures.append((name, "output differs from baseline"))
            print(f"[FAIL] {name}: output differs from baseline {baseline_path}")
            _print_diff(name, baseline, days)
        else:
            print(f"[PASS] {name}: matches baseline, zero drift")

    if capture:
        print(f"\nCaptured {len(PROFILES)} baseline(s) to {BASELINE_DIR}")
        return 0

    if failures:
        print(f"\n{len(failures)} of {len(PROFILES)} profile(s) FAILED:")
        for name, reason in failures:
            print(f"  - {name}: {reason}")
        return 1

    print(f"\nAll {len(PROFILES)} profiles PASSED \u2014 zero drift.")
    return 0


def _print_diff(name: str, baseline: list, actual: list):
    """Best-effort human-readable diff, day by day, exercise by exercise."""
    max_days = max(len(baseline), len(actual))
    for i in range(max_days):
        b_day = baseline[i] if i < len(baseline) else None
        a_day = actual[i] if i < len(actual) else None
        if b_day == a_day:
            continue
        print(f"    day[{i}] differs:")
        if b_day is None or a_day is None:
            print(f"      baseline={b_day!r}")
            print(f"      actual  ={a_day!r}")
            continue
        b_ex = b_day.get("exercises", [])
        a_ex = a_day.get("exercises", [])
        if b_ex != a_ex:
            b_names = [e.get("name") for e in b_ex]
            a_names = [e.get("name") for e in a_ex]
            print(f"      exercises baseline: {b_names}")
            print(f"      exercises actual:   {a_names}")
        for key in b_day.keys() | a_day.keys():
            if key == "exercises":
                continue
            if b_day.get(key) != a_day.get(key):
                print(f"      {key} baseline: {b_day.get(key)!r}")
                print(f"      {key} actual:   {a_day.get(key)!r}")


if __name__ == "__main__":
    capture = "--capture" in sys.argv
    sys.exit(run(capture))
