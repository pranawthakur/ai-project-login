import httpx
from app.config import settings


async def generate_with_ollama(prompt: str, system: str | None = None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages,
                    "temperature": 0,
                },
            )
            resp.raise_for_status()
        except httpx.ConnectError:
            raise RuntimeError("Could not reach Groq API. Check your API key.")

        data = resp.json()
        return data["choices"][0]["message"]["content"]