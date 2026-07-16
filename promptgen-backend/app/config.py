from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_jwt_secret: str
    supabase_service_role_key: str
    demo_gym_id: str
    gemini_api_key: str

    # Signs/verifies this app's own member session tokens, issued by
    # POST /member/login or POST /member/set-password (see app/auth.py).
    # Replaces Supabase Auth entirely for members as of the code+password
    # migration — members never get a Supabase auth.users row anymore, so
    # there is no JWKS/Supabase JWT to verify on incoming requests, only
    # this token. Unset -> those routes fail loud with 503 rather than
    # signing tokens with a blank/guessable key.
    member_session_secret: str = ""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    frontend_origin: str = "http://127.0.0.1:5500,https://ai-project-login-44q4.vercel.app"

    # Dedicated target for the /member/login redirect (main.py). Deliberately
    # SEPARATE from frontend_origin above - that's a CORS allow-list, order
    # isn't guaranteed to put the real prod URL first (the default above
    # literally lists localhost first), so reusing it for a redirect target
    # was a bug, not a shortcut. Set to project #2's real URL - the
    # ai-project-login Vercel deploy, NOT admin-dashboard-backend's separate
    # Vercel project - e.g. https://ai-project-login-44q4.vercel.app
    member_frontend_url: str = ""

    # Optional. Gates POST /generate/test (see main.py) - the dev-console's
    # AI Engine Test page sends this back as X-Dev-Test-Key. Unset -> the
    # route returns 503 rather than running unauthenticated, matching the
    # "fail loudly, don't fabricate" pattern ai_testing.py's own comment
    # already commits to on the dev-console side.
    dev_test_key: str = ""

    @property
    def frontend_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origin.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
