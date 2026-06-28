"""
fitness_generator.py
──────────────────────────────────────────────────────────────────────────────
1. Build a system prompt that tells the LLM EXACTLY what JSON to return.
2. Call your LLM (Ollama / RunPod — swap in your actual call).
3. Parse the JSON and render it into dashboard_template.html via Jinja2.

Output: a ready-to-serve HTML string (write to file or return from FastAPI).
──────────────────────────────────────────────────────────────────────────────
"""

import json
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


# ── TEMPLATE DIR ─────────────────────────────────────────────────────────────
# Folder is "Templates" (capital T), file is "result.html"
TEMPLATE_DIR = Path(__file__).parent.parent / "Templates"
TEMPLATE_FILE = "result.html"


# ── LLM SYSTEM PROMPT ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are an expert fitness coach and dietitian specialising in Indian gym clients.

CRITICAL OUTPUT RULES — READ BEFORE GENERATING:
1. Output ONLY a raw JSON object. Nothing before it, nothing after it.
2. Do NOT wrap JSON in markdown code fences (no ```json, no ```, no backticks of any kind).
3. Do NOT add comments inside the JSON (no // or /* */ comments).
4. Do NOT add trailing commas after the last item in any array or object.
5. All string values must use straight double-quotes only (no smart/curly quotes).
6. Boolean values must be lowercase: true or false (not True/False/TRUE/FALSE).
7. Null values must be written as null (not None/NULL).
8. Every required field in the schema below MUST be present — do not skip any key.
9. If you are unsure of a value, use a sensible default rather than omitting the field.
10. Your response must parse successfully with Python's json.loads() with zero modifications.

The JSON must follow this EXACT schema (copy the key names precisely):

{
  "user": {
    "name": "Full name of the client",
    "current_weight": 90,          // integer kg
    "target_weight": "82–84"       // string, e.g. "82–84" or "78"
  },
  "plan": {
    "goal_label": "Fat Loss Plan",  // short label shown in header, e.g. "Fat Loss Plan" / "Muscle Gain Plan"
    "daily_calories": 2200,         // integer
    "protein_range": "170–180g",    // string shown in header sub-line
    "daily_protein_g": 175,         // integer for stat card
    "weight_to_lose": "~6–8 kg to lose",  // string
    "calorie_phase": "Calorie deficit"     // string, e.g. "Calorie deficit" / "Lean bulk"
  },
  "workout": {
    "weekly_schedule": [
      // 7 entries, one per day Mon–Sun
      {
        "short": "Mon",     // 3-letter abbreviation
        "label": "Push",    // short workout label; "Rest" for rest days
        "is_rest": false,   // boolean
        "bar_width": 88     // integer 10–100; use 15 for rest days
      }
      // … repeat for Tue, Wed, Thu, Fri, Sat, Sun
    ],
    "days": [
      // 7 entries — same order Mon–Sun
      {
        "short": "MON",       // 3-letter UPPERCASE for the dot badge
        "name": "Monday",     // full day name
        "type": "Push Day — Chest · Shoulders · Triceps",  // subtitle
        "is_rest": false,
        "warmup": "5 min treadmill · arm circles · shoulder rolls",  // omit if is_rest
        "exercises": [        // omit if is_rest
          {
            "name": "Chest Press (Machine)",
            "muscle": "Pecs · anterior delt",
            "sets": "4",      // string
            "reps": "10–12 reps"  // string
          }
          // … more exercises
        ],
        "safety": "Keep chest up, shoulders back, wrists neutral."  // omit if is_rest
      }
      // … repeat for all 7 days (is_rest days only need short/name/type/is_rest)
    ]
  },
  "diet": {
    "meals": [
      {
        "id": "breakfast",          // unique snake_case id used in HTML — do NOT change across plans
        "tab_label": "Breakfast",
        "title": "Breakfast",
        "kcal_range": "600–650",    // string
        "options": [
          {
            "food": "80g Oats + 300ml Milk + 3 Eggs",
            "kcal": 650,            // integer
            "protein_g": 38         // integer
          }
          // … 3 options per meal
        ]
      },
      { "id": "mid",      "tab_label": "Mid-Morning", ... },
      { "id": "lunch",    "tab_label": "Lunch",       ... },
      { "id": "post",     "tab_label": "Post-Workout", ... },
      { "id": "dinner",   "tab_label": "Dinner",      ... }
    ]
  },
  "recovery": {
    "daily_nonneg": [
      // 4 items shown in Overview non-negotiables grid
      { "icon": "💧", "value": "3.5–4 L", "label": "Water" },
      { "icon": "👟", "value": "10K",     "label": "Steps" },
      { "icon": "🌙", "value": "8–9 h",   "label": "Sleep" },
      { "icon": "☀️", "value": "A.M.",    "label": "Sunlight" }
    ],
    "key_numbers": [
      // 4 items shown in Recovery tab key numbers grid
      { "icon": "💧", "value": "3.5–4 L", "label": "Water daily" },
      { "icon": "👟", "value": "10,000",  "label": "Steps daily" },
      { "icon": "🌙", "value": "7.5–9 h", "label": "Sleep target" },
      { "icon": "⏰", "value": "2 PM",    "label": "Last caffeine" }
    ],
    "tip_sections": [
      {
        "title": "Sleep protocol",
        "tips": [
          "No screens 60 min before bed — kills cortisol spike",
          "No caffeine after 2 PM, no matter what",
          "Morning sunlight within 30 min of waking — sets circadian rhythm",
          "Cool room, dark environment = deeper sleep"
        ]
      },
      {
        "title": "Active recovery",
        "tips": [
          "8000–10000 steps daily — even on rest days",
          "Foam roll quads, hamstrings, upper back after training",
          "Light walk or mobility on rest days — don't just sit",
          "If soreness is extreme, skip the day — don't push into injury"
        ]
      }
    ]
  }
}

Rules:
- Use only kirana/sabzi mandi ingredients for diet options (no exotic items).
- Avoid high-risk exercises (barbell squat, deadlift, barbell bench press, overhead barbell press).
- Recommend supplements ONLY from: whey protein, creatine, electrolytes — always add doctor-consult note in safety if mentioning supplements.
- Macro calculations via Mifflin-St Jeor equation.

FINAL REMINDER: Output ONLY the raw JSON object. No commentary, no markdown, no code fences.
The very first character of your response must be '{' and the very last must be '}'.
"""


# ── BUILD USER PROMPT ─────────────────────────────────────────────────────────
def build_user_prompt(profile: dict) -> str:
    """Convert a client intake profile dict into the LLM user message."""
    return f"""
Client profile:
- Name: {profile['name']}
- Age: {profile['age']}
- Gender: {profile['gender']}
- Height: {profile['height_cm']} cm
- Current weight: {profile['current_weight_kg']} kg
- Goal: {profile['goal']}
- Activity level: {profile['activity_level']}
- Diet preference: {profile.get('diet_pref', 'non-veg')}
- Allergies / restrictions: {profile.get('allergies', 'none')}
- Available equipment: {profile.get('equipment', 'full gym')}
- Medical notes: {profile.get('medical_notes', 'none')}

Additional context: {profile.get('extra', '')}

Generate the complete fitness dashboard JSON as per the schema.
"""


# ── PARSE LLM RESPONSE ────────────────────────────────────────────────────────
def parse_llm_json(raw: str) -> dict:
    """
    Auto-repair and parse JSON from Llama/local LLM responses.

    Handles all known Llama schema-violation patterns:
      1. Markdown code fences  ```json … ```
      2. Inline // and /* */ comments
      3. Trailing commas before ] or }
      4. Python-style True / False / None literals
      5. Smart / curly quotes → straight double-quotes
      6. Leading/trailing prose outside the JSON object
      7. Single-quoted strings → double-quoted strings (best-effort)
    """
    text = raw

    # 1. Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.replace("```", "").strip()

    # 2. Extract the outermost { … } block — ignore any prose before/after
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(
            f"No JSON object found in LLM response.\n\nRaw output:\n{raw[:500]}"
        )
    text = match.group(0)

    # 3. Remove // single-line comments (outside strings — good-enough heuristic)
    text = re.sub(r"(?<!:)//[^\n\"]*", "", text)

    # 4. Remove /* … */ block comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    # 5. Replace Python/Java boolean/null literals with JSON equivalents
    #    Use word boundaries so "True" inside a string value is also handled safely.
    text = re.sub(r"\bTrue\b", "true", text)
    text = re.sub(r"\bFalse\b", "false", text)
    text = re.sub(r"\bNone\b", "null", text)
    text = re.sub(r"\bNULL\b", "null", text)

    # 6. Replace curly / smart quotes with straight double-quotes
    for ch in "\u201c\u201d\u2018\u2019\u00ab\u00bb":
        text = text.replace(ch, '"')

    # 7. Remove trailing commas before ] or } (JSON doesn't allow them)
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # 8. First parse attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 9. Best-effort: convert single-quoted strings to double-quoted
    #    (handles simple cases where Llama outputs {'key': 'value'})
    try:
        # Replace 'value' patterns not already inside double-quoted context
        single_to_double = re.sub(
            r"'([^'\\]*(?:\\.[^'\\]*)*)'",
            lambda m: '"' + m.group(1).replace('"', '\\"') + '"',
            text,
        )
        # Re-apply trailing comma fix after the replacement
        single_to_double = re.sub(r",\s*([}\]])", r"\1", single_to_double)
        return json.loads(single_to_double)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM returned JSON that could not be auto-repaired: {e}\n\n"
            f"Cleaned text (first 800 chars):\n{text[:800]}\n\n"
            f"Original raw output (first 500 chars):\n{raw[:500]}"
        )


# ── SCHEMA ENFORCER ───────────────────────────────────────────────────────────
_RECOVERY_DEFAULT = {
    "daily_nonneg": [
        {"icon": "💧", "value": "3.5–4 L", "label": "Water"},
        {"icon": "👟", "value": "10K",     "label": "Steps"},
        {"icon": "🌙", "value": "8–9 h",   "label": "Sleep"},
        {"icon": "☀️", "value": "A.M.",    "label": "Sunlight"},
    ],
    "key_numbers": [
        {"icon": "💧", "value": "3.5–4 L", "label": "Water daily"},
        {"icon": "👟", "value": "10,000",  "label": "Steps daily"},
        {"icon": "🌙", "value": "7.5–9 h", "label": "Sleep target"},
        {"icon": "⏰", "value": "2 PM",    "label": "Last caffeine"},
    ],
    "tip_sections": [
        {
            "title": "Sleep protocol",
            "tips": [
                "No screens 60 min before bed — kills cortisol spike",
                "No caffeine after 2 PM, no matter what",
                "Morning sunlight within 30 min of waking — sets circadian rhythm",
                "Cool room, dark environment = deeper sleep",
            ],
        },
        {
            "title": "Active recovery",
            "tips": [
                "8000–10000 steps daily — even on rest days",
                "Foam roll quads, hamstrings, upper back after training",
                "Light walk or mobility on rest days — don't just sit",
                "If soreness is extreme, skip the day — don't push into injury",
            ],
        },
    ],
}


def enforce_schema(data: dict) -> dict:
    """
    Guarantee all keys the Jinja2 template needs are present.
    Fills in sensible defaults for any top-level section Llama omitted
    (most commonly: 'recovery', extra fields inside 'plan'/'user').
    Does NOT overwrite values the LLM did return.
    """
    # Top-level sections that must exist
    data.setdefault("user", {})
    data.setdefault("plan", {})
    data.setdefault("workout", {})
    data.setdefault("diet", {"meals": []})
    data.setdefault("recovery", {})

    # Fill recovery sub-keys individually so partial LLM output is preserved
    for key, default in _RECOVERY_DEFAULT.items():
        data["recovery"].setdefault(key, default)

    # Ensure plan has all expected fields
    plan_defaults = {
        "goal_label":      "Fat Loss Plan",
        "daily_calories":  2000,
        "protein_range":   "120–150g",
        "daily_protein_g": 135,
        "weight_to_lose":  "—",
        "calorie_phase":   "Calorie deficit",
    }
    for key, val in plan_defaults.items():
        data["plan"].setdefault(key, val)

    # Ensure user has all expected fields
    user_defaults = {
        "name":           "User",
        "current_weight": 0,
        "target_weight":  "—",
    }
    for key, val in user_defaults.items():
        data["user"].setdefault(key, val)

    # Ensure workout has weekly_schedule and days
    data["workout"].setdefault("weekly_schedule", [])
    data["workout"].setdefault("days", [])

    # Ensure each meal has 'options' list with at least one item
    for meal in data["diet"].get("meals", []):
        meal.setdefault("options", [])
        meal.setdefault("kcal_range", "—")
        for opt in meal["options"]:
            opt.setdefault("kcal", 0)
            opt.setdefault("protein_g", 0)

    return data


def render_dashboard(data: dict) -> str:
    """Render the Jinja2 template with the parsed LLM data dict."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False  # HTML template, not user-supplied
    )
    tmpl = env.get_template(TEMPLATE_FILE)
    return tmpl.render(**data)


# ── MAIN PIPELINE ─────────────────────────────────────────────────────────────
def generate_dashboard(profile: dict, llm_caller) -> str:
    """
    Full pipeline:
      profile      — dict with client intake fields (see build_user_prompt)
      llm_caller   — callable(system_prompt, user_prompt) -> str
                     Plug in your Ollama / RunPod / OpenAI wrapper here.
    Returns:
      Rendered HTML string.
    """
    user_prompt = build_user_prompt(profile)
    raw_response = llm_caller(SYSTEM_PROMPT, user_prompt)
    data = parse_llm_json(raw_response)
    data = enforce_schema(data)
    return render_dashboard(data)


# ── EXAMPLE: MOCK CALL (for local testing without a real LLM) ─────────────────
if __name__ == "__main__":
    import requests  # pip install requests

    # ── swap this with your actual Ollama / RunPod call ──
    def ollama_caller(system_prompt: str, user_prompt: str) -> str:
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "nemotron3:33b",   # your Ollama model name
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ]
            },
            timeout=300
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    # Sample intake profile
    test_profile = {
        "name": "Prince Thakur",
        "age": 22,
        "gender": "male",
        "height_cm": 175,
        "current_weight_kg": 90,
        "goal": "fat loss",
        "activity_level": "moderately active (3–4 gym sessions/week)",
        "diet_pref": "non-veg",
        "allergies": "none",
        "equipment": "full gym",
        "medical_notes": "none"
    }

    html_output = generate_dashboard(test_profile, ollama_caller)

    out_path = Path("output_dashboard.html")
    out_path.write_text(html_output, encoding="utf-8")
    print(f"✅ Dashboard written to {out_path.resolve()}")