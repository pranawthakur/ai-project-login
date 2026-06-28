from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.auth import get_current_user
from app.ollama_client import generate_with_ollama
from app.schemas import GenerateRequest, GenerateResponse
from app.fitness_generator import SYSTEM_PROMPT, build_user_prompt, parse_llm_json, enforce_schema, render_dashboard


class ManualCORS(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return JSONResponse(
                content={},
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "86400",
                }
            )
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response


app = FastAPI(title="Prompt Generator API")
app.add_middleware(ManualCORS)


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Existing JSON API (kept intact) ─────────────────────────────────────────
@app.post("/api/generate", response_model=GenerateResponse)
async def generate(
    body: GenerateRequest,
    user: dict = Depends(get_current_user),
):
    try:
        result = await generate_with_ollama(body.prompt, body.system)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return GenerateResponse(result=result)


@app.get("/api/me")
def whoami(user: dict = Depends(get_current_user)):
    return {"sub": user.get("sub"), "email": user.get("email")}


# ── New: form POST → fitness_generator → Jinja2 dashboard ───────────────────
@app.post("/result", response_class=HTMLResponse)
async def result_page(
    request: Request,
    # Basic profile fields posted from dashbord.html
    name: str = Form(""),
    age: str = Form(""),
    gender: str = Form("Male"),
    height: str = Form(""),
    weight: str = Form(""),
    target: str = Form(""),
    goal: str = Form("Fat loss"),
    experience: str = Form("Intermediate"),
    activity: str = Form("moderate"),
    days: str = Form("4"),
    duration: str = Form("45-60 min"),
    diet: str = Form("Non-vegetarian"),
    meals: str = Form("4"),
    notes: str = Form(""),
    region: str = Form(""),
    budget: str = Form("medium"),
    allergies: str = Form("none"),
    equipment: str = Form("full gym"),
):
    # Map activity value to a readable string
    activity_map = {
        "sedentary":   "Sedentary (desk job, little exercise)",
        "light":       "Lightly active (1–3 days/week)",
        "moderate":    "Moderately active (3–5 days/week)",
        "very_active": "Very active (6–7 days/week)",
        "extreme":     "Extremely active (physical job + training)",
    }

    profile = {
        "name":               name or "User",
        "age":                age or "25",
        "gender":             gender,
        "height_cm":          height or "170",
        "current_weight_kg":  weight or "70",
        "goal":               goal,
        "activity_level":     activity_map.get(activity, activity),
        "diet_pref":          diet,
        "allergies":          allergies or "none",
        "equipment":          equipment or "full gym",
        "medical_notes":      notes or "none",
        # Extra context passed as notes
        "extra": (
            f"Target weight: {target} kg. "
            f"Training days/week: {days}. "
            f"Session duration: {duration}. "
            f"Meals per day: {meals}. "
            f"Region: {region or 'India'}. "
            f"Food budget: {budget}. "
            f"Experience level: {experience}."
        ),
    }

    user_prompt = build_user_prompt(profile)

    try:
        raw = await generate_with_ollama(user_prompt, system=SYSTEM_PROMPT)
    except RuntimeError as e:
        return HTMLResponse(
            content=f"<h2 style='font-family:sans-serif;padding:40px'>⚠️ Ollama error: {e}</h2>"
                    f"<p style='padding:0 40px'><a href='javascript:history.back()'>← Go back</a></p>",
            status_code=503,
        )

    try:
        data = parse_llm_json(raw)
        data = enforce_schema(data)
        html = render_dashboard(data)
    except (ValueError, Exception) as e:
        return HTMLResponse(
            content=f"<pre style='font-family:monospace;padding:40px;white-space:pre-wrap'>"
                    f"Parse error: {e}\n\nRaw Llama output:\n{raw}</pre>"
                    f"<p style='padding:0 40px'><a href='javascript:history.back()'>← Go back</a></p>",
            status_code=500,
        )

    return HTMLResponse(content=html)