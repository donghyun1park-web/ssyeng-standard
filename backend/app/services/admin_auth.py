import hmac
import os

from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()


def has_valid_admin_token(token: str | None) -> bool:
    expected = os.getenv("ADMIN_TOKEN", "").strip()
    supplied = (token or "").strip()
    return bool(expected and supplied and hmac.compare_digest(supplied, expected))


def require_admin_token(x_admin_token: str = Header(default="", alias="X-Admin-Token")) -> None:
    expected = os.getenv("ADMIN_TOKEN", "").strip()
    supplied = (x_admin_token or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="ADMIN_TOKEN이 설정되지 않아 관리자 작업을 막았습니다.")
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="관리자 토큰이 필요합니다.")
