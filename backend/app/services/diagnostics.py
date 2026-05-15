from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.services.external_settings import get_kcsc_api_key

load_dotenv()

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent
DATA_DIR = BACKEND_ROOT / "data"
STANDARD_ITEMS = DATA_DIR / "standard_items.json"


class DiagnosticsService:
    """Lightweight production-readiness checks for field deployment."""

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "phase": "18.1-gemini-ai-provider",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "project_root": str(PROJECT_ROOT),
        }

    def run_checks(self) -> dict[str, Any]:
        checks = [
            self._check_standard_json(),
            self._check_required_dirs(),
            self._check_env_security(),
            self._check_kcsc_config(),
            self._check_ai_provider_config(),
            self._check_admin_token(),
            self._check_frontend_build_folder(),
        ]
        errors = [c for c in checks if c["level"] == "error"]
        warnings = [c for c in checks if c["level"] == "warning"]
        return {
            "ok": not errors,
            "phase": "18.1-gemini-ai-provider",
            "summary": {
                "total": len(checks),
                "passed": len([c for c in checks if c["level"] == "ok"]),
                "warnings": len(warnings),
                "errors": len(errors),
            },
            "checks": checks,
        }

    def _check_standard_json(self) -> dict[str, Any]:
        if not STANDARD_ITEMS.exists():
            return self._result("standard_items_json", "error", "backend/data/standard_items.json 파일이 없습니다.")
        try:
            data = json.loads(STANDARD_ITEMS.read_text(encoding="utf-8"))
        except Exception as exc:
            return self._result("standard_items_json", "error", f"JSON 파싱 실패: {exc}")
        if not isinstance(data, list) or not data:
            return self._result("standard_items_json", "error", "표준 항목 JSON은 비어 있지 않은 배열이어야 합니다.")
        required = {"id", "category", "section", "title", "summary", "body", "keywords", "checklist"}
        missing = []
        ids = set()
        duplicate_ids = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                missing.append(f"#{idx}: object 아님")
                continue
            absent = sorted(required - set(item.keys()))
            if absent:
                missing.append(f"{item.get('id', idx)}: {', '.join(absent)}")
            item_id = item.get("id")
            if item_id in ids:
                duplicate_ids.append(item_id)
            ids.add(item_id)
        if missing or duplicate_ids:
            message = "; ".join(filter(None, [
                f"필수 필드 누락 {missing[:3]}" if missing else "",
                f"중복 ID {duplicate_ids[:5]}" if duplicate_ids else "",
            ]))
            return self._result("standard_items_json", "error", message)
        return self._result("standard_items_json", "ok", f"표준 항목 {len(data)}개 검증 완료")

    def _check_required_dirs(self) -> dict[str, Any]:
        required = [DATA_DIR, BACKEND_ROOT / "uploads", BACKEND_ROOT / "reports", BACKEND_ROOT / "backups"]
        created = []
        for path in required:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                created.append(path.name)
        if created:
            return self._result("required_dirs", "warning", f"누락 디렉터리를 자동 생성했습니다: {', '.join(created)}")
        return self._result("required_dirs", "ok", "data/uploads/reports/backups 디렉터리 확인 완료")

    def _check_env_security(self) -> dict[str, Any]:
        env_file = BACKEND_ROOT / ".env"
        if not env_file.exists():
            return self._result("env_file", "warning", "backend/.env가 없습니다. .env.example을 복사해서 운영값을 입력하세요.")
        return self._result("env_file", "ok", "backend/.env 파일 확인 완료")

    def _check_kcsc_config(self) -> dict[str, Any]:
        key = get_kcsc_api_key()
        if not key:
            return self._result("kcsc_api", "warning", "KCSC_API_KEY 미설정: 샘플 fallback으로 동작합니다.")
        if len(key) < 20:
            return self._result("kcsc_api", "warning", "KCSC_API_KEY 길이가 짧아 보입니다. 값을 다시 확인하세요.")
        return self._result("kcsc_api", "ok", f"KCSC_API_KEY 설정됨: {self._mask(key)}")

    def _check_ai_provider_config(self) -> dict[str, Any]:
        provider = os.getenv("AI_PROVIDER", "auto").strip().lower() or "auto"
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
        nvidia_model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct").strip()

        if provider in {"gemini", "google", "google-gemini"}:
            if not gemini_key:
                return self._result("ai_provider", "warning", "AI_PROVIDER=gemini 이지만 GEMINI_API_KEY 미설정: /api/ask는 로컬 근거 요약 fallback으로 동작합니다.")
            return self._result("ai_provider", "ok", f"Gemini 설정됨: {self._mask(gemini_key)} · model={gemini_model or 'default'}")

        if provider in {"nvidia", "nim", "nvidia-nim"}:
            if not nvidia_key:
                return self._result("ai_provider", "warning", "AI_PROVIDER=nvidia 이지만 NVIDIA_API_KEY 미설정: /api/ask는 로컬 근거 요약 fallback으로 동작합니다.")
            return self._result("ai_provider", "ok", f"NVIDIA NIM 설정됨: {self._mask(nvidia_key)} · model={nvidia_model or 'default'}")

        if provider == "auto":
            if gemini_key:
                return self._result("ai_provider", "ok", f"AI_PROVIDER=auto · Gemini 우선 사용: {self._mask(gemini_key)} · model={gemini_model or 'default'}")
            if nvidia_key:
                return self._result("ai_provider", "ok", f"AI_PROVIDER=auto · NVIDIA NIM 사용: {self._mask(nvidia_key)} · model={nvidia_model or 'default'}")
            return self._result("ai_provider", "warning", "Gemini/NVIDIA API Key 미설정: /api/ask는 로컬 근거 요약 fallback으로 동작합니다.")

        return self._result("ai_provider", "warning", f"지원하지 않는 AI_PROVIDER={provider}: gemini, nvidia, auto 중 하나를 사용하세요.")

    def _check_admin_token(self) -> dict[str, Any]:
        token = os.getenv("ADMIN_TOKEN", "").strip()
        if not token:
            return self._result("admin_token", "warning", "ADMIN_TOKEN 미설정: 로컬 MVP 모드입니다. 운영 전 반드시 설정하세요.")
        if len(token) < 8:
            return self._result("admin_token", "warning", "ADMIN_TOKEN이 너무 짧습니다. 8자 이상을 권장합니다.")
        return self._result("admin_token", "ok", "ADMIN_TOKEN 설정 완료")

    def _check_frontend_build_folder(self) -> dict[str, Any]:
        dist = PROJECT_ROOT / "dist"
        index = dist / "index.html"
        if not index.exists():
            return self._result("frontend_dist", "warning", "dist/index.html이 없습니다. 운영 배포 전 npm run build를 실행하세요.")
        return self._result("frontend_dist", "ok", "React production build 산출물 확인 완료")

    @staticmethod
    def _mask(value: str) -> str:
        if len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"

    @staticmethod
    def _result(name: str, level: str, message: str) -> dict[str, str]:
        return {"name": name, "level": level, "message": message}
