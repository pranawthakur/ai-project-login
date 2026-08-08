"""
progression_engine.py
────────────────────────────────────────────────────────────────────────────
Phase 6 — Biweekly Reassessment & Adaptive Progression.

SOLE AUTHORITY for progression decisions. 100% deterministic Python — no
LLM call anywhere in this file, on purpose (see Phase 6 spec: "Do NOT use
the LLM to decide progression"). An LLM may narrate `compute()`'s output
to the user elsewhere (trainer_review.py-style), but it never runs first
and never overrides anything here.

Inputs come from checkin_engine.assemble_reassessment_inputs(). This
module is pure — it takes that dict in and returns a decision dict out,
no Supabase calls, so it's trivially unit-testable.

Pipeline:
    analyze_workout_history()   -> objective per-exercise + overall metrics
    classify_progress()         -> Improving / Maintaining / Plateaued / Regressing
    detect_plateau()            -> bool + updated plateau_counter
    detect_deload()             -> bool + reason
    compute_adaptations()       -> the actual load/volume/exercise decisions
    compute()                   -> runs the full pipeline, returns everything
"""
from __future__ import annotations
from datetime import datetime, timezone

# ── Tunables (kept as module constants, not magic numbers, per doc style
#    used elsewhere in this codebase e.g. programming_rules.py) ────────────
DELOAD_INTERVAL_CYCLES   = 4          # 1 cycle = 2 weeks -> ~6-8 weeks
PLATEAU_CYCLE_THRESHOLD  = 2          # consecutive no-improvement reassessments
MIN_ADHERENCE_FOR_PROGRESSION = 0.80  # 80% completion, per spec's plateau criteria
LOAD_INCREMENT_KG        = 2.5        # standard plate-loadable jump
LOAD_INCREMENT_PCT_SMALL = 0.025      # ~2.5% conservative bump
LOAD_INCREMENT_PCT_BIG   = 0.05       # ~5% aggressive bump (Too Easy)
DELOAD_VOLUME_CUT_PCT    = 0.40       # midpoint of the spec's 30-50% range


# ── 1. OBJECTIVE ANALYSIS ───────────────────────────────────────────────────
def _epley_1rm(weight: float, reps: int) -> float:
    """Estimated 1RM, Epley formula. Standard, deterministic, no ML."""
    if not weight or not reps:
        return 0.0
    return round(weight * (1 + reps / 30), 1)


def analyze_workout_history(logs: list[dict], prev_logs: list[dict],
                             prescribed_exercises: list[str] | None = None) -> dict:
    """Turns raw logged-set rows into objective metrics. Never asks the
    user anything — this is exactly the "Automatically Collected Data"
    section of the spec.

    logs / prev_logs: rows from checkin_engine.get_cycle_workout_logs()
    for the current / previous cycle (each row = one logged set; a row
    only exists if the member actually logged it — there's no explicit
    "skipped" marker in the source tables).

    prescribed_exercises: every exercise name the member was actually
    given this cycle (from plans.plan_json). Used to compute completion %
    and missed exercises by diffing prescribed vs logged, since the
    underlying tables only record what WAS logged, not what was skipped.
    """
    prescribed_exercises = prescribed_exercises or []
    logged_exercise_names = {r["exercise"] for r in logs}
    missed_exercises = sorted(set(prescribed_exercises) - logged_exercise_names)

    total_prescribed = len(set(prescribed_exercises)) or None
    completion_pct = (
        round(len(logged_exercise_names & set(prescribed_exercises)) / total_prescribed, 3)
        if total_prescribed else (1.0 if logs else 0.0)
    )

    total_sets = len(logs)
    missed_sets = len(missed_exercises)  # approximation: no per-set prescribed count available

    # Per-exercise rollup: current cycle heaviest set + its estimated 1RM,
    # vs. same exercise's heaviest set/1RM last cycle.
    def _best_set_per_exercise(rows: list[dict]) -> dict:
        best: dict[str, dict] = {}
        for r in rows:
            w = r.get("weight_kg") or 0
            reps = r.get("reps_completed") or 0
            rm = _epley_1rm(w, reps)
            cur = best.get(r["exercise"])
            if cur is None or rm > cur["est_1rm"]:
                best[r["exercise"]] = {
                    "weight_kg": w, "reps": reps, "est_1rm": rm,
                }
        return best

    current_best = _best_set_per_exercise(logs)
    prev_best = _best_set_per_exercise(prev_logs)

    exercise_trends = {}
    prs = []
    for name, cur in current_best.items():
        prev = prev_best.get(name)
        if prev is None:
            trend = "new"
            delta_1rm = 0.0
        else:
            delta_1rm = round(cur["est_1rm"] - prev["est_1rm"], 1)
            if delta_1rm > 0.5:
                trend = "improved"
            elif delta_1rm < -0.5:
                trend = "regressed"
            else:
                trend = "maintained"
        exercise_trends[name] = {
            "current": cur, "previous": prev,
            "delta_est_1rm": delta_1rm, "trend": trend,
        }
        if trend == "improved" and (prev is None or cur["est_1rm"] > prev["est_1rm"]):
            prs.append(name)

    total_volume = round(sum(
        (r.get("weight_kg") or 0) * (r.get("reps_completed") or 0)
        for r in logs
    ), 1)
    prev_volume = round(sum(
        (r.get("weight_kg") or 0) * (r.get("reps_completed") or 0)
        for r in prev_logs
    ), 1)
    volume_delta_pct = (
        round((total_volume - prev_volume) / prev_volume, 3)
        if prev_volume else None
    )

    improved_count = sum(1 for t in exercise_trends.values() if t["trend"] == "improved")
    regressed_count = sum(1 for t in exercise_trends.values() if t["trend"] == "regressed")

    return {
        "total_sets": total_sets,
        "logged_sets": total_sets,
        "missed_sets": missed_sets,
        "completion_pct": completion_pct,
        "missed_exercises": missed_exercises,
        "exercise_trends": exercise_trends,
        "personal_records": prs,
        "total_volume": total_volume,
        "volume_delta_pct": volume_delta_pct,
        "improved_exercise_count": improved_count,
        "regressed_exercise_count": regressed_count,
    }


# ── 2. BODY MEASUREMENT ANALYSIS (supporting evidence only) ────────────────
def analyze_measurements(checkin: dict, prev_checkin: dict | None, goal: str) -> dict:
    """Never the sole signal — spec explicitly says never rely solely on
    body weight. Returns a small supporting-evidence dict, or empty if no
    measurements were given (fields are all optional)."""
    if not prev_checkin:
        return {}

    goal_l = (goal or "").lower()
    is_fat_loss = any(t in goal_l for t in ("fat loss", "weight loss", "cut", "lean"))
    is_muscle_gain = any(t in goal_l for t in ("muscle", "bulk", "hypertrophy"))

    out = {}
    bw, prev_bw = checkin.get("body_weight_kg"), prev_checkin.get("body_weight_kg")
    if bw is not None and prev_bw is not None:
        delta = round(bw - prev_bw, 2)
        out["body_weight_delta_kg"] = delta
        if is_fat_loss:
            out["body_weight_signal"] = "favorable" if delta <= 0 else "unfavorable"
        elif is_muscle_gain:
            out["body_weight_signal"] = "favorable" if delta >= 0 else "unfavorable"

    waist, prev_waist = checkin.get("waist_cm"), prev_checkin.get("waist_cm")
    if waist is not None and prev_waist is not None:
        delta = round(waist - prev_waist, 2)
        out["waist_delta_cm"] = delta
        if is_fat_loss:
            out["waist_signal"] = "favorable" if delta <= 0 else "unfavorable"

    for key in ("chest_cm", "arms_cm", "thighs_cm"):
        cur, prev = checkin.get(key), prev_checkin.get(key)
        if cur is not None and prev is not None:
            delta = round(cur - prev, 2)
            out[f"{key}_delta"] = delta
            if is_muscle_gain:
                out[f"{key}_signal"] = "favorable" if delta >= 0 else "unfavorable"

    return out


# ── 3. PROGRESS CLASSIFICATION ──────────────────────────────────────────────
def classify_progress(metrics: dict, checkin: dict) -> str:
    """Improving / Maintaining / Plateaued / Regressing.
    Order of precedence matters here — regression and injury signals
    override everything else."""
    improved = metrics["improved_exercise_count"]
    regressed = metrics["regressed_exercise_count"]
    total_tracked = max(1, improved + regressed + sum(
        1 for t in metrics["exercise_trends"].values() if t["trend"] == "maintained"
    ))

    has_pain = bool(checkin.get("pain_areas")) and checkin["pain_areas"] != ["none"]
    recovery_poor = checkin.get("recovery") == "poor"

    if regressed > improved and regressed / total_tracked >= 0.4:
        return "regressing"
    if recovery_poor and regressed > 0:
        return "regressing"
    if improved / total_tracked >= 0.3 and not has_pain:
        return "improving"
    if improved == 0 and regressed == 0:
        return "maintaining"
    if improved > 0:
        return "improving"
    return "maintaining"


# ── 4. PLATEAU DETECTION ────────────────────────────────────────────────────
def detect_plateau(progress_state: str, metrics: dict, checkin: dict,
                    reassessment_history: list[dict]) -> tuple[bool, int]:
    """Returns (is_plateaued, new_plateau_counter).
    Criteria per spec: no improvement in major lifts for 2-3 consecutive
    reassessments, adherence >=80%, recovery not Poor, no blocking injury."""
    prior_counter = reassessment_history[0]["plateau_counter"] if reassessment_history else 0

    no_improvement_this_cycle = progress_state in ("maintaining", "regressing")
    adherence_ok = metrics["completion_pct"] >= MIN_ADHERENCE_FOR_PROGRESSION
    recovery_ok = checkin.get("recovery") != "poor"
    no_blocking_pain = not checkin.get("pain_areas") or checkin["pain_areas"] == ["none"]

    if no_improvement_this_cycle and adherence_ok and recovery_ok and no_blocking_pain:
        new_counter = prior_counter + 1
    else:
        new_counter = 0

    is_plateaued = new_counter >= PLATEAU_CYCLE_THRESHOLD
    return is_plateaued, new_counter


# ── 5. DELOAD DETECTION ─────────────────────────────────────────────────────
def detect_deload(checkin: dict, metrics: dict, reassessment_history: list[dict],
                   cycle_number: int) -> tuple[bool, str | None]:
    """Returns (should_deload, reason)."""
    cycles_since_deload = cycle_number
    for r in reassessment_history:
        if r.get("is_deload"):
            cycles_since_deload = cycle_number - r["cycle_number"]
            break
    else:
        cycles_since_deload = cycle_number  # never deloaded

    if cycles_since_deload >= DELOAD_INTERVAL_CYCLES:
        return True, f"{cycles_since_deload} cycles since last deload (interval reached)"

    if checkin.get("recovery") == "poor":
        return True, "poor recovery reported"

    if checkin.get("soreness") in ("moderate", "severe"):
        return True, f"{checkin['soreness']} soreness reported"

    if checkin.get("pain_areas") and checkin["pain_areas"] != ["none"]:
        return True, f"pain reported: {', '.join(checkin['pain_areas'])}"

    if metrics["regressed_exercise_count"] > metrics["improved_exercise_count"] and metrics["total_sets"] > 0:
        return True, "declining performance across multiple exercises"

    return False, None


# ── 6. ADAPTATION DECISIONS ─────────────────────────────────────────────────
_DIFFICULTY_MULTIPLIER = {
    "too_easy":   LOAD_INCREMENT_PCT_BIG,
    "easy":       LOAD_INCREMENT_PCT_SMALL * 1.5,
    "just_right": LOAD_INCREMENT_PCT_SMALL,
    "hard":       LOAD_INCREMENT_PCT_SMALL * 0.5,
    "too_hard":   0.0,
}


def compute_exercise_progressions(metrics: dict, difficulty: str,
                                   progress_state: str, is_deload: bool) -> dict:
    """Per-exercise next-cycle target weight. This is the deterministic
    equivalent of the spec's Bench Press 60kg->62.5kg example — every
    exercise progresses independently off its OWN trend, not a global %."""
    out = {}
    pct = _DIFFICULTY_MULTIPLIER.get(difficulty, LOAD_INCREMENT_PCT_SMALL)

    for name, trend in metrics["exercise_trends"].items():
        cur = trend["current"]
        weight = cur["weight_kg"] or 0
        if weight <= 0:
            continue  # bodyweight-only movement, nothing to load-progress

        if is_deload:
            new_weight = round((weight * (1 - DELOAD_VOLUME_CUT_PCT)) / 2.5) * 2.5
            action = "deload"
        elif trend["trend"] == "regressed" or progress_state == "regressing":
            new_weight = weight  # hold, don't push a regressing lift
            action = "hold"
        elif trend["trend"] == "improved" or progress_state == "improving":
            new_weight = round((weight * (1 + pct)) / 2.5) * 2.5
            action = "increase_load"
        else:  # maintained
            if pct > 0:
                new_weight = round((weight * (1 + pct * 0.5)) / 2.5) * 2.5
                action = "increase_load"
            else:
                new_weight = weight
                action = "hold"

        out[name] = {
            "current_weight_kg": weight,
            "target_weight_kg": max(0, new_weight),
            "action": action,
        }
    return out


def compute_adaptations(metrics: dict, checkin: dict, progress_state: str,
                         is_plateaued: bool, plateau_counter: int,
                         is_deload: bool, deload_reason: str | None) -> dict:
    """The actual set of decisions the spec asks for: load / reps / sets /
    rotate / reduce volume / deload / regressions / substitutions."""
    actions: list[str] = []
    volume_multiplier = 1.0
    difficulty = checkin.get("difficulty", "just_right")

    if is_deload:
        actions.append("deload")
        volume_multiplier = 1 - DELOAD_VOLUME_CUT_PCT
    elif metrics["completion_pct"] < MIN_ADHERENCE_FOR_PROGRESSION:
        actions.append("reduce_volume")
        actions.append("simplify_program")
        volume_multiplier = 0.85
    elif is_plateaued:
        actions.append("rotate_exercises")
        actions.append("rep_range_adjustment")
        if difficulty in ("too_easy", "easy"):
            actions.append("increase_intensity")
            volume_multiplier = 1.05
    elif progress_state == "regressing":
        actions.append("reduce_volume")
        volume_multiplier = 0.9
    elif progress_state == "improving":
        if difficulty == "too_easy":
            actions.append("increase_load_aggressive")
            actions.append("increase_sets")
            volume_multiplier = 1.10
        else:
            actions.append("increase_load_conservative")
            volume_multiplier = 1.0 if difficulty != "hard" else 0.95
    else:  # maintaining, not plateaued yet
        actions.append("maintain_progression")

    if checkin.get("pain_areas") and checkin["pain_areas"] != ["none"]:
        actions.append("apply_exercise_substitutions")

    exercise_progressions = compute_exercise_progressions(
        metrics, difficulty, progress_state, is_deload,
    )

    return {
        "actions": actions,
        "volume_multiplier": round(volume_multiplier, 3),
        "exercise_progressions": exercise_progressions,
        "is_deload": is_deload,
        "deload_reason": deload_reason,
        "is_plateaued": is_plateaued,
        "plateau_counter": plateau_counter,
    }


# ── 7. PIPELINE ENTRY POINT ─────────────────────────────────────────────────
def compute(inputs: dict, goal: str = "") -> dict:
    """Runs the full deterministic pipeline. `inputs` = the dict returned
    by checkin_engine.assemble_reassessment_inputs()."""
    checkin = inputs["checkin"]
    cycle_number = inputs["cycle_number"]

    metrics = analyze_workout_history(
        inputs["workout_logs"], inputs["prev_workout_logs"],
        inputs.get("prescribed_exercises"),
    )
    measurement_signals = analyze_measurements(checkin, inputs.get("prev_checkin"), goal)

    progress_state = classify_progress(metrics, checkin)
    is_plateaued, plateau_counter = detect_plateau(
        progress_state, metrics, checkin, inputs["reassessment_history"],
    )
    is_deload, deload_reason = detect_deload(
        checkin, metrics, inputs["reassessment_history"], cycle_number,
    )

    adaptations = compute_adaptations(
        metrics, checkin, progress_state, is_plateaued, plateau_counter,
        is_deload, deload_reason,
    )

    return {
        "member_id": inputs["member_id"],
        "cycle_number": cycle_number,
        "progress_state": progress_state,
        "compliance_pct": metrics["completion_pct"],
        "is_deload": is_deload,
        "plateau_counter": plateau_counter,
        "metrics": metrics,
        "measurement_signals": measurement_signals,
        "adaptations": adaptations,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
