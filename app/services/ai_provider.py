"""
Provider-agnostic AI interface.

The rest of the app only ever talks to `get_ai_provider()`. Today it can return
either the Gemini or OpenRouter implementation. Adding OpenAI, Claude, or any
future provider only requires implementing the AIProvider interface and adding
one line to the factory function at the bottom.
"""

from abc import ABC, abstractmethod
import requests

from app.core.config import settings


class AIProvider(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        json_mode: bool = False,
    ) -> str:
        """Return a completion as plain text (or JSON string if json_mode=True)."""
        raise NotImplementedError


# ==========================================================
# Gemini Provider
# ==========================================================

class GeminiProvider(AIProvider):
    def __init__(self) -> None:
        import google.generativeai as genai

        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to backend/.env before starting the server."
            )

        genai.configure(api_key=settings.GEMINI_API_KEY)

        self._genai = genai
        self._model_name = settings.GEMINI_MODEL

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        json_mode: bool = False,
    ) -> str:
        print("OpenRouter: Building model")

        generation_config = {}

        if json_mode:
            generation_config["response_mime_type"] = "application/json"

        model = self._genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_prompt,
            generation_config=generation_config or None,
        )
        print("OpenRouter: Sending Request")

        response = model.generate_content(user_prompt)
        print("OpenRouter: Response Received")

        return response.text


# ==========================================================
# OpenRouter Provider
# ==========================================================

class OpenRouterProvider(AIProvider):

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self) -> None:

        if not settings.OPENROUTER_API_KEY:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Add it to backend/.env."
            )

        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        json_mode: bool = False,
    ) -> str:

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "NorthStar AI",
        }

        payload = {
            "model": self.model,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        }
  
        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=60,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"OpenRouter Error {response.status_code}: {response.text}"
            )

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]

        except (KeyError, IndexError):
            raise RuntimeError(
                f"Unexpected OpenRouter response:\n{data}"
            )


# ==========================================================
# Provider Factory
# ==========================================================

_provider_instance: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    """
    Returns a singleton AI provider instance based on configuration.
    """

    global _provider_instance

    if _provider_instance is None:

        provider = settings.AI_PROVIDER.lower()

        if provider == "gemini":
            _provider_instance = GeminiProvider()

        elif provider == "openrouter":
            _provider_instance = OpenRouterProvider()

        else:
            raise ValueError(
                f"Unsupported AI_PROVIDER: {settings.AI_PROVIDER}"
            )

    return _provider_instance