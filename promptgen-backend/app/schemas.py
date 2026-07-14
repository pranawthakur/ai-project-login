from pydantic import BaseModel


class GenerateRequest(BaseModel):
    prompt: str
    system: str | None = None
    bmi: float | None = None


class GenerateResponse(BaseModel):
    result: str


class FeedbackEntry(BaseModel):
    day_index: int
    day_name: str
    exercise: str
    set_number: int
    weight_kg: float | None = None
    difficulty: int | None = None  # 1-5 star rating the user gave THIS set
    # ── Phase 6 additions: needed for objective progression math. All
    # optional so any existing caller keeps working unmodified until it's
    # updated to send them.
    reps_completed:   int | None = None
    target_reps:      int | None = None
    target_weight_kg: float | None = None
    completed:        bool = True


class FeedbackSubmission(BaseModel):
    entries: list[FeedbackEntry]


# ── Phase 6: Biweekly Reassessment & Adaptive Progression ──────────────────
class CheckinSubmission(BaseModel):
    recovery:   str   # excellent | good | average | poor
    difficulty: str   # too_easy | easy | just_right | hard | too_hard
    soreness:   str   # none | mild | moderate | severe
    pain_areas: list[str] = []   # shoulder, elbow, wrist, lower_back, hip, knee, ankle, other
    pain_notes: str | None = None

    # Optional body measurements — program must continue normally if skipped.
    body_weight_kg: float | None = None
    waist_cm:       float | None = None
    chest_cm:       float | None = None
    arms_cm:        float | None = None
    thighs_cm:      float | None = None
    hips_cm:        float | None = None
    body_fat_pct:   float | None = None
