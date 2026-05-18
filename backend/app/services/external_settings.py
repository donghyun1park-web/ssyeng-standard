from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.utils.json_store import load_json, save_json


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SETTINGS_PATH = DATA_DIR / "external_settings.json"

# Optional deployment default. Keep real keys in Render environment variables
# or in the admin-managed server data file, never in tracked source code.
DEFAULT_KCSC_API_KEY = os.getenv("KCSC_DEFAULT_API_KEY", "").strip()


class ExternalSettingsUpdate(BaseModel):
    kcsc_api_key: str | None = None


def _load() -> dict[str, Any]:
    return load_json(SETTINGS_PATH, default={})


def _save(data: dict[str, Any]) -> None:
    save_json(SETTINGS_PATH, data)


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 10:
        return "*" * len(value)
    return f"{value[:4]}{'*' * max(4, len(value) - 8)}{value[-4:]}"


def get_kcsc_api_key() -> str:
    data = _load()
    stored = str(data.get("kcsc_api_key", "")).strip()
    if stored:
        return stored
    env_key = os.getenv("KCSC_API_KEY", "").strip()
    if env_key:
        return env_key
    return DEFAULT_KCSC_API_KEY.strip()


def external_settings_status() -> dict[str, Any]:
    data = _load()
    stored = str(data.get("kcsc_api_key", "")).strip()
    env_key = os.getenv("KCSC_API_KEY", "").strip()
    key = get_kcsc_api_key()
    source = "custom" if stored else ("env" if env_key else "bundled-default")
    return {
        "ok": True,
        "kcsc": {
            "configured": bool(key),
            "masked_key": _mask(key),
            "source": source,
            "has_custom_key": bool(stored),
        },
    }


def update_external_settings(payload: ExternalSettingsUpdate) -> dict[str, Any]:
    data = _load()
    if payload.kcsc_api_key is not None:
        clean = payload.kcsc_api_key.strip()
        if clean:
            data["kcsc_api_key"] = clean
        else:
            data.pop("kcsc_api_key", None)
    _save(data)
    return external_settings_status()
