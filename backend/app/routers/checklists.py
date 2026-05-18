from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.utils.json_store import load_json, save_json

router = APIRouter(tags=["checklists"])

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RECORDS_PATH = DATA_DIR / "checklists.json"
ITEMS_PATH = DATA_DIR / "checklist_items.json"

TRADE_LIST = ["배관공사", "보온공사", "덕트공사", "장비설치", "시험및검사"]

# 기본 템플릿 — 사용자가 "기본 템플릿 불러오기" 시 자신의 (user_id, site_id) 공간으로 복사된다.
DEFAULT_TEMPLATES: dict[str, list[dict]] = {
    "배관공사": [
        {"text": "배관 관종, 관경, 재질이 도면 및 승인 자재와 일치하는가?", "related_page": ""},
        {"text": "배관 경로가 도면과 일치하는가?", "related_page": ""},
        {"text": "배관 구배가 기준에 맞게 시공되었는가?", "related_page": ""},
        {"text": "배관 지지간격이 회사 표준지침 기준 이내인가?", "related_page": "42"},
        {"text": "행거, 서포트, 앵커 고정 상태가 양호한가?", "related_page": "42"},
        {"text": "신축이음, 플렉시블 조인트 주변 지지가 적정한가?", "related_page": ""},
        {"text": "벽체·슬래브 관통부 슬리브 위치가 맞는가?", "related_page": ""},
        {"text": "관통부 방화충전 또는 마감 계획이 확인되었는가?", "related_page": ""},
        {"text": "밸브 설치 방향과 조작 공간이 적정한가?", "related_page": ""},
        {"text": "배관 간섭 사항이 없는가?", "related_page": ""},
        {"text": "용접부, 나사부, 플랜지 접합부 상태가 양호한가?", "related_page": ""},
        {"text": "수압시험 전 개방부, 말단부, 드레인 상태를 확인했는가?", "related_page": "73"},
    ],
    "보온공사": [
        {"text": "보온 대상 배관이 누락되지 않았는가?", "related_page": "58"},
        {"text": "보온재 종류와 두께가 회사 표준지침 기준에 맞는가?", "related_page": "58"},
        {"text": "보온 전 배관 수압시험이 완료되었는가?", "related_page": "73"},
        {"text": "배관 표면의 이물질, 수분, 녹 등이 제거되었는가?", "related_page": ""},
        {"text": "보온재 이음부가 벌어지지 않게 시공되었는가?", "related_page": ""},
        {"text": "곡관부, 밸브부, 플랜지부 보온 처리가 적정한가?", "related_page": ""},
        {"text": "옥외 배관 마감재 또는 보호커버가 적용되었는가?", "related_page": ""},
        {"text": "결로 우려 구간의 방습층이 연속적으로 시공되었는가?", "related_page": ""},
        {"text": "점검이 필요한 밸브, 플랜지, 스트레이너 부분의 탈착성이 확보되었는가?", "related_page": ""},
        {"text": "보온 마감 상태가 찢김, 틈, 처짐 없이 양호한가?", "related_page": ""},
    ],
    "덕트공사": [
        {"text": "덕트 경로와 치수가 도면과 일치하는가?", "related_page": ""},
        {"text": "덕트 재질(아연도강판 등)이 승인 자재와 일치하는가?", "related_page": ""},
        {"text": "덕트 행거 간격이 기준 이내인가?", "related_page": ""},
        {"text": "덕트 이음부 기밀 처리가 적정한가?", "related_page": ""},
        {"text": "방화댐퍼 위치가 도면과 일치하는가?", "related_page": ""},
        {"text": "방화댐퍼 작동 시험이 완료되었는가?", "related_page": ""},
        {"text": "청소구 위치와 크기가 적정한가?", "related_page": ""},
        {"text": "덕트 보온 처리가 완료되었는가?", "related_page": ""},
        {"text": "흡·배기 그릴, 디퓨저 위치 및 설치 상태가 적정한가?", "related_page": ""},
        {"text": "덕트 관통부 방화 처리가 완료되었는가?", "related_page": ""},
    ],
    "장비설치": [
        {"text": "장비 기초 위치와 크기가 도면과 일치하는가?", "related_page": ""},
        {"text": "방진 패드 또는 스프링 방진기가 적정하게 설치되었는가?", "related_page": ""},
        {"text": "장비 수평도가 확인되었는가?", "related_page": ""},
        {"text": "배관 연결부 플렉시블 조인트가 설치되었는가?", "related_page": ""},
        {"text": "전기 배선 및 제어 패널 연결이 완료되었는가?", "related_page": ""},
        {"text": "장비 점검 공간이 충분히 확보되었는가?", "related_page": ""},
        {"text": "드레인 배관 연결이 완료되었는가?", "related_page": ""},
        {"text": "안전밸브, 압력계, 온도계 설치 상태가 적정한가?", "related_page": ""},
        {"text": "장비 명판, 운전 방향 표시가 부착되었는가?", "related_page": ""},
        {"text": "시운전 전 이물질 제거 및 스트레이너 청소가 완료되었는가?", "related_page": ""},
    ],
    "시험및검사": [
        {"text": "시험 대상 구간이 명확히 구분되었는가?", "related_page": "73"},
        {"text": "시험 전 배관 지지, 말단 마감, 밸브 상태를 확인했는가?", "related_page": "73"},
        {"text": "수압시험 압력과 유지 시간이 기준에 맞는가?", "related_page": "73"},
        {"text": "시험 압력계 교정 상태를 확인했는가?", "related_page": ""},
        {"text": "시험 중 누수, 변형, 압력 저하가 없는가?", "related_page": ""},
        {"text": "시험 결과 사진을 촬영했는가?", "related_page": ""},
        {"text": "시험 기록지를 작성했는가?", "related_page": ""},
        {"text": "감리 또는 담당자 입회 여부를 기록했는가?", "related_page": ""},
        {"text": "보온, 매립, 천장 마감 전 검사가 완료되었는가?", "related_page": ""},
        {"text": "지적사항 조치 완료 여부를 확인했는가?", "related_page": ""},
    ],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_user(x_user_id: str | None) -> str:
    from urllib.parse import unquote
    raw = (x_user_id or "").strip()
    # 프론트엔드가 한글 등 비ASCII 문자를 URL 인코딩해서 보냄 → 디코드
    try:
        user = unquote(raw)
    except Exception:
        user = raw
    return user or "anonymous"


def _resolve_site(site_id: str | None) -> str:
    sid = (site_id or "").strip()
    return sid or "default"


def _load_items() -> dict:
    return load_json(ITEMS_PATH, default={"items": []})


def _save_items(data: dict) -> None:
    save_json(ITEMS_PATH, data)


def _load_records() -> dict:
    return load_json(RECORDS_PATH, default={"records": []})


def _save_records(data: dict) -> None:
    save_json(RECORDS_PATH, data)


def _site_items(site_id: str, trade: str | None = None) -> list[dict]:
    """현장(site_id) 기준으로 체크리스트 항목 조회 — 같은 현장 인원이 공유."""
    items = _load_items().get("items", [])
    result = [
        it for it in items
        if it.get("site_id") == site_id
        and (trade is None or it.get("trade") == trade)
    ]
    result.sort(key=lambda it: (it.get("sort_order", 0), it.get("created_at", "")))
    return result


def _site_records(site_id: str, trade: str | None = None) -> list[dict]:
    """현장(site_id) 기준으로 체크 기록 조회 — 같은 현장 인원이 공유."""
    records = _load_records().get("records", [])
    return [
        r for r in records
        if r.get("site_id", "default") == site_id
        and (trade is None or r.get("trade") == trade)
    ]


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/checklists/trades")
def list_trades():
    return {"trades": TRADE_LIST}


@router.get("/checklists")
def list_checklists(
    site_id: str = "",
    x_user_id: str = Header(default="", alias="X-User-Id"),
):
    user_id = _resolve_user(x_user_id)
    sid = _resolve_site(site_id)
    result = []
    for trade in TRADE_LIST:
        items = _site_items(sid, trade)
        records = _site_records(sid, trade)
        checked_count = sum(1 for r in records if r.get("status") in ("적합", "해당없음"))
        result.append({
            "trade": trade,
            "item_count": len(items),
            "checked_count": checked_count,
            "has_items": len(items) > 0,
        })
    return {"checklists": result, "user_id": user_id, "site_id": sid}


@router.get("/checklists/{trade}")
def get_checklist(
    trade: str,
    site_id: str = "",
    x_user_id: str = Header(default="", alias="X-User-Id"),
):
    if trade not in TRADE_LIST:
        raise HTTPException(status_code=404, detail="공종을 찾을 수 없습니다.")
    user_id = _resolve_user(x_user_id)
    sid = _resolve_site(site_id)
    items = _site_items(sid, trade)
    records_list = _site_records(sid, trade)
    records_by_item = {r["item_id"]: r for r in records_list if "item_id" in r}
    template_available = len(items) == 0 and trade in DEFAULT_TEMPLATES
    return {
        "trade": trade,
        "items": items,
        "records": records_by_item,
        "user_id": user_id,
        "site_id": sid,
        "template_available": template_available,
        "template_count": len(DEFAULT_TEMPLATES.get(trade, [])),
    }


class ItemCreate(BaseModel):
    site_id: str = ""
    trade: str
    text: str = Field(..., min_length=1, max_length=500)
    related_page: str = ""


@router.post("/checklists/items")
def create_item(
    body: ItemCreate,
    x_user_id: str = Header(default="", alias="X-User-Id"),
):
    if body.trade not in TRADE_LIST:
        raise HTTPException(status_code=400, detail="유효하지 않은 공종입니다.")
    user_id = _resolve_user(x_user_id)
    sid = _resolve_site(body.site_id)
    data = _load_items()
    items = data.setdefault("items", [])
    existing = _site_items(sid, body.trade)
    next_order = max([it.get("sort_order", 0) for it in existing], default=-1) + 1
    item = {
        "id": f"item-{uuid.uuid4().hex[:10]}",
        "created_by": user_id,   # 생성자 기록 (참고용)
        "site_id": sid,
        "trade": body.trade,
        "text": body.text.strip(),
        "related_page": body.related_page.strip(),
        "sort_order": next_order,
        "created_at": _now(),
        "updated_at": _now(),
    }
    items.append(item)
    _save_items(data)
    return {"ok": True, "item": item}


class ItemUpdate(BaseModel):
    text: str | None = None
    related_page: str | None = None
    sort_order: int | None = None


@router.put("/checklists/items/{item_id}")
def update_item(
    item_id: str,
    body: ItemUpdate,
    x_user_id: str = Header(default="", alias="X-User-Id"),
):
    data = _load_items()
    items = data.get("items", [])
    item = next((it for it in items if it.get("id") == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    # 현장 공유 모드: 같은 현장 인원이면 누구나 수정 가능
    if body.text is not None:
        text = body.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="항목 내용이 비어 있습니다.")
        item["text"] = text
    if body.related_page is not None:
        item["related_page"] = body.related_page.strip()
    if body.sort_order is not None:
        item["sort_order"] = body.sort_order
    item["updated_at"] = _now()
    _save_items(data)
    return {"ok": True, "item": item}


@router.delete("/checklists/items/{item_id}")
def delete_item(
    item_id: str,
    x_user_id: str = Header(default="", alias="X-User-Id"),
):
    data = _load_items()
    items = data.get("items", [])
    item = next((it for it in items if it.get("id") == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    # 현장 공유 모드: 같은 현장 인원이면 누구나 삭제 가능
    data["items"] = [it for it in items if it.get("id") != item_id]
    _save_items(data)

    # 함께 저장된 체크 기록도 정리
    rec_data = _load_records()
    rec_data["records"] = [r for r in rec_data.get("records", []) if r.get("item_id") != item_id]
    _save_records(rec_data)
    return {"ok": True}


class LoadTemplateBody(BaseModel):
    site_id: str = ""
    trade: str


@router.post("/checklists/load-template")
def load_template(
    body: LoadTemplateBody,
    x_user_id: str = Header(default="", alias="X-User-Id"),
):
    if body.trade not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=400, detail="템플릿이 없는 공종입니다.")
    user_id = _resolve_user(x_user_id)
    sid = _resolve_site(body.site_id)
    data = _load_items()
    items = data.setdefault("items", [])
    existing = _site_items(sid, body.trade)
    if existing:
        raise HTTPException(status_code=409, detail="이미 항목이 존재합니다. 빈 상태에서만 템플릿을 불러올 수 있습니다.")
    created = []
    for idx, tpl in enumerate(DEFAULT_TEMPLATES[body.trade]):
        new_item = {
            "id": f"item-{uuid.uuid4().hex[:10]}",
            "created_by": user_id,   # 템플릿 불러온 사람 기록
            "site_id": sid,
            "trade": body.trade,
            "text": tpl["text"],
            "related_page": tpl.get("related_page", ""),
            "sort_order": idx,
            "created_at": _now(),
            "updated_at": _now(),
        }
        items.append(new_item)
        created.append(new_item)
    _save_items(data)
    return {"ok": True, "items": created, "count": len(created)}


class CheckRecordUpsert(BaseModel):
    trade: str
    item_id: str
    status: Literal["미체크", "적합", "해당없음", "부적합"] = "미체크"
    memo: str = ""
    site_id: str = ""


@router.post("/checklists/record")
def upsert_check_record(
    body: CheckRecordUpsert,
    x_user_id: str = Header(default="", alias="X-User-Id"),
):
    if body.trade not in TRADE_LIST:
        raise HTTPException(status_code=400, detail="유효하지 않은 공종입니다.")
    user_id = _resolve_user(x_user_id)
    sid = _resolve_site(body.site_id)

    # 현장 공유 모드: 해당 site의 항목인지만 확인 (user_id 무관)
    items = _load_items().get("items", [])
    if not any(it.get("id") == body.item_id and it.get("site_id") == sid for it in items):
        raise HTTPException(status_code=400, detail="유효하지 않은 항목 ID입니다.")

    data = _load_records()
    records = data.setdefault("records", [])
    # 체크 기록은 item_id + site_id 기준으로 upsert (현장 공유)
    existing = next(
        (r for r in records
         if r.get("trade") == body.trade
         and r.get("item_id") == body.item_id
         and r.get("site_id", "default") == sid),
        None
    )
    if existing:
        existing["status"] = body.status
        existing["memo"] = body.memo
        existing["checked_by"] = user_id   # 마지막으로 체크한 사람
        existing["updated_at"] = _now()
        record = existing
    else:
        record = {
            "id": f"rec-{uuid.uuid4().hex[:10]}",
            "checked_by": user_id,   # 체크한 사람 기록
            "trade": body.trade,
            "item_id": body.item_id,
            "site_id": sid,
            "status": body.status,
            "memo": body.memo,
            "created_at": _now(),
            "updated_at": _now(),
        }
        records.append(record)
    _save_records(data)
    return {"ok": True, "record": record}


@router.delete("/checklists/record/{record_id}")
def delete_check_record(
    record_id: str,
    x_user_id: str = Header(default="", alias="X-User-Id"),
):
    data = _load_records()
    records = data.get("records", [])
    target = next((r for r in records if r.get("id") == record_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="레코드를 찾을 수 없습니다.")
    # 현장 공유 모드: 같은 현장 인원이면 누구나 삭제 가능
    data["records"] = [r for r in records if r.get("id") != record_id]
    _save_records(data)
    return {"ok": True}
