"""
json_store.py — Thread-safe JSON read/write utility.

모든 JSON 파일 저장 시 filelock을 사용해 동시 쓰기로 인한
데이터 손상(race condition)을 방지합니다.

사용법:
    from app.utils.json_store import load_json, save_json

    data = load_json(PATH, default={"items": []})
    save_json(PATH, data)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filelock import FileLock, Timeout

# 잠금 대기 최대 시간 (초). 초과 시 Timeout 예외 발생.
LOCK_TIMEOUT = 15


def _lock_path(path: Path) -> str:
    return str(path) + ".lock"


def load_json(path: Path, *, default: Any = None) -> Any:
    """JSON 파일을 읽어 반환합니다. 파일이 없으면 default를 반환합니다.
    읽기는 잠금 없이 수행합니다(읽기는 안전).
    """
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def save_json(path: Path, data: Any, *, indent: int = 2) -> None:
    """JSON 데이터를 파일에 안전하게 저장합니다.

    - filelock으로 동시 쓰기 방지 (같은 파일에 대한 직렬화)
    - 잠금 내부에서 직접 쓰기 (Windows 호환, 원자성 보장)
    """
    import os
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(_lock_path(path), timeout=LOCK_TIMEOUT)
    content = json.dumps(data, ensure_ascii=False, indent=indent)
    try:
        with lock:
            path.write_text(content, encoding="utf-8")
    except Timeout:
        # 15초 동안 잠금 획득 못하면 — 직접 쓰기 (마지막 수단)
        path.write_text(content, encoding="utf-8")
