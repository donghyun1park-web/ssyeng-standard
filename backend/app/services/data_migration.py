import csv
import io
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STANDARD_PATH = DATA_DIR / "standard_items.json"
STAGING_DIR = DATA_DIR / "migration_staging"
BACKUP_DIR = DATA_DIR / "migration_backups"
REQUIRED_FIELDS = ["id", "category", "section", "title", "summary", "body"]
OPTIONAL_LIST_FIELDS = ["keywords", "checklist"]


def now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    # CSV 운영자가 쓰기 쉽게 |, ;, 줄바꿈을 모두 허용한다.
    return [part.strip() for part in re.split(r"[|;\n]+", text) if part.strip()]


def normalize_item(raw: dict[str, Any]) -> dict[str, Any]:
    item = {key: ("" if raw.get(key) is None else str(raw.get(key)).strip()) for key in REQUIRED_FIELDS}
    item["keywords"] = normalize_list(raw.get("keywords"))
    item["checklist"] = normalize_list(raw.get("checklist"))
    # 기존 데이터와의 호환을 위해 extra 필드는 유지하되 필수 필드가 우선한다.
    for key, value in raw.items():
        if key not in item and key not in OPTIONAL_LIST_FIELDS:
            item[key] = value
    return item


def load_current_items() -> list[dict[str, Any]]:
    if not STANDARD_PATH.exists():
        return []
    with STANDARD_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("standard_items.json must be a list")
    return data


@dataclass
class ValidationResult:
    ok: bool
    items: list[dict[str, Any]]
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]


class DataMigrationService:
    def __init__(self) -> None:
        ensure_dirs()

    def status(self) -> dict[str, Any]:
        batches = self.list_batches()["batches"]
        current_count = len(load_current_items())
        return {
            "ok": True,
            "phase": "15-data-migration",
            "current_item_count": current_count,
            "staged_batch_count": len(batches),
            "supported_formats": ["json", "csv"],
            "required_fields": REQUIRED_FIELDS,
            "list_fields": OPTIONAL_LIST_FIELDS,
            "staging_dir": str(STAGING_DIR),
        }

    def parse_bytes(self, content: bytes, filename: str) -> list[dict[str, Any]]:
        suffix = Path(filename).suffix.lower()
        text = content.decode("utf-8-sig")
        if suffix == ".json":
            data = json.loads(text)
            if isinstance(data, dict) and isinstance(data.get("items"), list):
                data = data["items"]
            if not isinstance(data, list):
                raise ValueError("JSON 파일은 배열 또는 {items: [...]} 형태여야 합니다.")
            return [normalize_item(row) for row in data if isinstance(row, dict)]
        if suffix == ".csv":
            reader = csv.DictReader(io.StringIO(text))
            return [normalize_item(row) for row in reader]
        raise ValueError("지원하지 않는 형식입니다. .json 또는 .csv 파일만 업로드하세요.")

    def validate_items(self, items: list[dict[str, Any]]) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        seen: set[str] = set()
        current_ids = {item.get("id") for item in load_current_items()}
        for idx, item in enumerate(items, start=1):
            row_errors = []
            for field in REQUIRED_FIELDS:
                if not str(item.get(field, "")).strip():
                    row_errors.append(f"필수 필드 누락: {field}")
            item_id = str(item.get("id", "")).strip()
            if item_id:
                if item_id in seen:
                    row_errors.append(f"파일 내부 중복 ID: {item_id}")
                seen.add(item_id)
                if item_id in current_ids:
                    warnings.append({"row": idx, "id": item_id, "message": "기존 항목과 ID가 같습니다. commit 시 upsert 모드에서는 덮어씁니다."})
            if not item.get("keywords"):
                warnings.append({"row": idx, "id": item_id, "message": "keywords가 비어 있습니다. 검색 정확도가 낮아질 수 있습니다."})
            if not item.get("checklist"):
                warnings.append({"row": idx, "id": item_id, "message": "checklist가 비어 있습니다."})
            if row_errors:
                errors.append({"row": idx, "id": item_id, "errors": row_errors})
        return ValidationResult(ok=not errors, items=items, errors=errors, warnings=warnings)

    def validate_upload(self, content: bytes, filename: str) -> dict[str, Any]:
        items = self.parse_bytes(content, filename)
        result = self.validate_items(items)
        return {
            "ok": result.ok,
            "count": len(result.items),
            "errors": result.errors,
            "warnings": result.warnings,
            "preview": result.items[:5],
        }

    def stage_upload(self, content: bytes, filename: str, note: str = "") -> dict[str, Any]:
        items = self.parse_bytes(content, filename)
        result = self.validate_items(items)
        if not result.ok:
            return {"ok": False, "count": len(items), "errors": result.errors, "warnings": result.warnings}
        batch_id = f"batch_{now_id()}"
        path = STAGING_DIR / f"{batch_id}.json"
        payload = {
            "batch_id": batch_id,
            "filename": filename,
            "note": note,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "count": len(items),
            "items": items,
            "warnings": result.warnings,
            "committed": False,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "batch_id": batch_id, "count": len(items), "warnings": result.warnings, "preview": items[:5]}

    def _batch_path(self, batch_id: str) -> Path:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "", batch_id)
        return STAGING_DIR / f"{safe}.json"

    def get_batch(self, batch_id: str) -> dict[str, Any]:
        path = self._batch_path(batch_id)
        if not path.exists():
            raise FileNotFoundError(batch_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def list_batches(self) -> dict[str, Any]:
        batches = []
        for path in sorted(STAGING_DIR.glob("batch_*.json"), reverse=True):
            payload = json.loads(path.read_text(encoding="utf-8"))
            batches.append({k: payload.get(k) for k in ["batch_id", "filename", "note", "created_at", "count", "committed"]})
        return {"ok": True, "batches": batches}

    def commit_batch(self, batch_id: str, mode: str = "upsert") -> dict[str, Any]:
        if mode not in {"append", "upsert", "replace"}:
            raise ValueError("mode는 append, upsert, replace 중 하나여야 합니다.")
        batch = self.get_batch(batch_id)
        new_items = batch.get("items", [])
        current = load_current_items()
        backup_path = BACKUP_DIR / f"standard_items_before_{batch_id}_{now_id()}.json"
        if STANDARD_PATH.exists():
            shutil.copy2(STANDARD_PATH, backup_path)
        if mode == "replace":
            merged = new_items
        elif mode == "append":
            merged = current + new_items
        else:
            by_id = {item.get("id"): item for item in current}
            for item in new_items:
                by_id[item.get("id")] = item
            merged = list(by_id.values())
        validation = self.validate_items(merged)
        if not validation.ok:
            return {"ok": False, "errors": validation.errors, "warnings": validation.warnings}
        STANDARD_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        batch["committed"] = True
        batch["committed_at"] = datetime.now(timezone.utc).isoformat()
        batch["commit_mode"] = mode
        self._batch_path(batch_id).write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "ok": True,
            "batch_id": batch_id,
            "mode": mode,
            "before_count": len(current),
            "imported_count": len(new_items),
            "after_count": len(merged),
            "backup_file": backup_path.name if backup_path.exists() else None,
        }

    def delete_batch(self, batch_id: str) -> dict[str, Any]:
        path = self._batch_path(batch_id)
        if not path.exists():
            raise FileNotFoundError(batch_id)
        path.unlink()
        return {"ok": True, "deleted": batch_id}

    def export_current(self, fmt: str) -> tuple[str, bytes, str]:
        items = load_current_items()
        if fmt == "json":
            return "standard_items_export.json", json.dumps(items, ensure_ascii=False, indent=2).encode("utf-8"), "application/json"
        if fmt == "csv":
            buf = io.StringIO()
            fieldnames = REQUIRED_FIELDS + OPTIONAL_LIST_FIELDS
            writer = csv.DictWriter(buf, fieldnames=fieldnames)
            writer.writeheader()
            for item in items:
                row = {field: item.get(field, "") for field in REQUIRED_FIELDS}
                row["keywords"] = "|".join(normalize_list(item.get("keywords")))
                row["checklist"] = "|".join(normalize_list(item.get("checklist")))
                writer.writerow(row)
            return "standard_items_export.csv", buf.getvalue().encode("utf-8-sig"), "text/csv"
        raise ValueError("format은 json 또는 csv만 가능합니다.")

    def template(self, fmt: str) -> tuple[str, bytes, str]:
        sample = [{
            "id": "MEP-NEW-001",
            "category": "기계설비",
            "section": "급수설비",
            "title": "급수펌프 설치 기준",
            "summary": "급수펌프 설치 전 확인해야 할 주요 기준입니다.",
            "body": "기초, 방진, 배관 접속, 점검 공간을 확인한다.",
            "keywords": ["급수펌프", "펌프", "방진"],
            "checklist": ["기초 수평 확인", "방진가대 설치 확인", "흡입/토출 배관 지지 확인"],
        }]
        if fmt == "json":
            return "standard_items_template.json", json.dumps(sample, ensure_ascii=False, indent=2).encode("utf-8"), "application/json"
        if fmt == "csv":
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=REQUIRED_FIELDS + OPTIONAL_LIST_FIELDS)
            writer.writeheader()
            row = sample[0].copy()
            row["keywords"] = "|".join(row["keywords"])
            row["checklist"] = "|".join(row["checklist"])
            writer.writerow(row)
            return "standard_items_template.csv", buf.getvalue().encode("utf-8-sig"), "text/csv"
        raise ValueError("format은 json 또는 csv만 가능합니다.")
