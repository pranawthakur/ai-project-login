"""
Fixed regression profiles for build_deterministic_workout_days().

These are the 4 profiles referenced in the multi-session integration task
notes: beginner_full_gym, intermediate_fatloss_home,
advanced_strength_knee_injury, intermediate_shoulder_impingement.

Recreated from scratch (not recovered from a prior session) based on the
fields build_user_prompt() / recommend_split() actually read from a
profile dict (see app/fitness_generator.py and app/split_engine.py).
If any of these turn out to not match what you originally used, tell me
and I'll adjust — the goal is a stable, meaningful baseline, not a
guessed one that silently drifts from what you actually tested before.
"""

PROFILES = {
    "beginner_full_gym": {
        "experience": "Beginner",
        "days_per_week": 3,
        "session_duration": "45-60 min",
        "goal": "muscle gain",
        "equipment": "full gym",
        "medical_notes": "none",
        "height_cm": 175,
        "current_weight_kg": 78,
        "activity_key": "moderate",
    },
    "intermediate_fatloss_home": {
        "experience": "Intermediate",
        "days_per_week": 4,
        "session_duration": "30-45 min",
        "goal": "fat loss",
        "equipment": "dumbbells, resistance bands, bodyweight",
        "medical_notes": "none",
        "height_cm": 165,
        "current_weight_kg": 72,
        "activity_key": "light",
    },
    "advanced_strength_knee_injury": {
        "experience": "Advanced",
        "days_per_week": 5,
        "session_duration": "60-75 min",
        "goal": "strength",
        "equipment": "full gym",
        "medical_notes": "knee injury, avoid deep knee flexion under load",
        "height_cm": 180,
        "current_weight_kg": 88,
        "activity_key": "high",
    },
    "intermediate_shoulder_impingement": {
        "experience": "Intermediate",
        "days_per_week": 4,
        "session_duration": "45-60 min",
        "goal": "muscle gain",
        "equipment": "full gym",
        "medical_notes": "shoulder impingement, avoid overhead pressing",
        "height_cm": 170,
        "current_weight_kg": 68,
        "activity_key": "moderate",
    },
}

# Same forced seed for every profile/run — determinism comes from the
# harness-side random.Random monkeypatch in run_regression.py, not from
# anything inside build_deterministic_workout_days() itself (it has no
# seed parameter; see run_regression.py docstring for why).
FORCED_SEED = 20260711
