from pydantic import BaseModel


class GenerateRequest(BaseModel):
    prompt: str
    system: str | None = None
    bmi: float | None = None


class GenerateResponse(BaseModel):
    result: str
