import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class NimConfigurationError(RuntimeError):
    pass


class NimClientError(RuntimeError):
    pass


class NvidiaNimClient:
    """Small OpenAI-compatible NVIDIA NIM chat client.

    Environment variables:
    - NVIDIA_API_KEY: required for real NIM calls
    - NVIDIA_BASE_URL: defaults to https://integrate.api.nvidia.com/v1
    - NVIDIA_MODEL: defaults to meta/llama-3.1-70b-instruct
    - NVIDIA_TIMEOUT_SECONDS: defaults to 60
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("NVIDIA_API_KEY", "").strip()
        self.base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
        self.model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct").strip()
        self.timeout_seconds = float(os.getenv("NVIDIA_TIMEOUT_SECONDS", "60"))

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.model)

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 900) -> str:
        if not self.is_configured:
            raise NimConfigurationError("NVIDIA_API_KEY 또는 NVIDIA_MODEL이 설정되지 않았습니다.")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise NimClientError(f"NVIDIA NIM 요청 실패: {exc}") from exc

        if response.status_code >= 400:
            text = response.text[:700]
            raise NimClientError(f"NVIDIA NIM HTTP {response.status_code}: {text}")

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise NimClientError("NVIDIA NIM 응답 형식이 예상과 다릅니다.") from exc

        return str(content).strip()
