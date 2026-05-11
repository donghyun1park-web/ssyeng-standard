import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class GeminiConfigurationError(RuntimeError):
    pass


class GeminiClientError(RuntimeError):
    pass


class GeminiClient:
    """Small REST client for Gemini generateContent.

    Environment variables:
    - GEMINI_API_KEY: required for real Gemini calls
    - GEMINI_BASE_URL: defaults to https://generativelanguage.googleapis.com/v1beta
    - GEMINI_MODEL: defaults to gemini-2.5-flash
    - GEMINI_TIMEOUT_SECONDS: defaults to 60
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.timeout_seconds = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "60"))

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.model)

    @property
    def model_path(self) -> str:
        return self.model if self.model.startswith("models/") else f"models/{self.model}"

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 900,
        api_key: str | None = None,
    ) -> str:
        # Per-call api_key overrides the env-default. Useful when each end-user
        # supplies their own Gemini key from the app's settings screen.
        effective_key = (api_key or "").strip() or self.api_key
        if not (effective_key and self.model):
            raise GeminiConfigurationError("GEMINI_API_KEY 또는 GEMINI_MODEL이 설정되지 않았습니다.")

        payload = self._build_payload(messages, temperature=temperature, max_tokens=max_tokens)
        headers = {
            "x-goog-api-key": effective_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/{self.model_path}:generateContent",
                    headers=headers,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise GeminiClientError(f"Gemini API 요청 실패: {exc}") from exc

        if response.status_code >= 400:
            text = response.text[:700]
            raise GeminiClientError(f"Gemini API HTTP {response.status_code}: {text}")

        return self._extract_text(response.json())

    def _build_payload(self, messages: list[dict[str, str]], *, temperature: float, max_tokens: int) -> dict[str, Any]:
        system_parts: list[dict[str, str]] = []
        contents: list[dict[str, Any]] = []

        for message in messages:
            role = (message.get("role") or "user").strip().lower()
            content = (message.get("content") or "").strip()
            if not content:
                continue
            if role == "system":
                system_parts.append({"text": content})
                continue
            contents.append({
                "role": "model" if role in {"assistant", "model"} else "user",
                "parts": [{"text": content}],
            })

        if not contents:
            raise GeminiConfigurationError("Gemini 요청에 보낼 사용자 메시지가 없습니다.")

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_parts:
            payload["system_instruction"] = {"parts": system_parts}
        return payload

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        try:
            candidate = data["candidates"][0]
            parts = candidate["content"]["parts"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GeminiClientError("Gemini API 응답 형식이 예상과 다릅니다.") from exc

        text = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()
        if not text:
            finish_reason = candidate.get("finishReason")
            raise GeminiClientError(f"Gemini API 응답에 텍스트가 없습니다. finishReason={finish_reason or 'unknown'}")
        return text
