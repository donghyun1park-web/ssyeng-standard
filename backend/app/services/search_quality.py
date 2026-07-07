from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.services.standard_repository import StandardRepository
from app.services.synonyms import (
    DEFAULT_SYNONYMS,
    SYNONYM_PATH,
    load_synonyms as _load_synonyms,
)

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_+#./-]+")

FIELD_WEIGHTS = {
    "title": 12,
    "keywords": 9,
    "summary": 6,
    "category": 5,
    "section": 5,
    "checklist": 4,
    "body": 2,
    "id": 1,
}


def _ensure_synonyms() -> dict[str, list[str]]:
    # 공용 모듈(synonyms.py)에서 로드 — RAG 검색과 동일한 사전 사용
    return _load_synonyms()


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if len(t.strip()) >= 2]


def _field_text(item: dict[str, Any], field: str) -> str:
    value = item.get(field, "")
    if isinstance(value, list):
        return " ".join(str(v) for v in value)
    return str(value or "")


class SearchQualityService:
    def __init__(self) -> None:
        self.repo = StandardRepository()
        self.synonyms = _ensure_synonyms()

    def status(self) -> dict[str, Any]:
        items = self.repo.list_items()
        terms = self.term_frequency(limit=12)
        return {
            "ok": True,
            "phase": "14-search-quality",
            "item_count": len(items),
            "synonym_count": len(self.synonyms),
            "synonym_path": str(SYNONYM_PATH),
            "top_terms": terms,
            "features": {
                "weighted_field_search": True,
                "synonym_expansion": True,
                "category_section_filters": True,
                "matched_field_diagnostics": True,
                "zero_result_suggestions": True,
            },
        }

    def categories(self) -> dict[str, list[str]]:
        return self.repo.categories()

    def expand_query(self, query: str) -> dict[str, Any]:
        raw_tokens = _tokens(query)
        expanded = set(raw_tokens)
        matched_synonyms: dict[str, list[str]] = {}
        for token in raw_tokens:
            direct = self.synonyms.get(token, [])
            reverse = [key for key, vals in self.synonyms.items() if token in [v.lower() for v in vals]]
            values = list(dict.fromkeys([*direct, *reverse]))
            if values:
                matched_synonyms[token] = values
                expanded.update(v.lower() for v in values)
        if query.strip() and query.strip().lower() not in expanded:
            expanded.add(query.strip().lower())
        return {
            "query": query,
            "tokens": raw_tokens,
            "expanded_terms": sorted(expanded),
            "matched_synonyms": matched_synonyms,
        }

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        section: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        expansion = self.expand_query(query)
        terms = expansion["expanded_terms"]
        candidates = self.repo.list_items(category=category, section=section)
        scored: list[dict[str, Any]] = []

        for item in candidates:
            total_score = 0
            matched_fields: dict[str, list[str]] = defaultdict(list)
            for field, weight in FIELD_WEIGHTS.items():
                text = _field_text(item, field).lower()
                if not text:
                    continue
                for term in terms:
                    if not term:
                        continue
                    count = text.count(term)
                    if count:
                        total_score += weight * count
                        matched_fields[field].append(term)
                    # small token-level partial match for Korean compound words
                    field_tokens = _tokens(text)
                    if term in field_tokens:
                        total_score += max(1, weight // 2)
            if query.strip().lower() in _field_text(item, "title").lower():
                total_score += 15
            if total_score > 0:
                payload = dict(item)
                payload["search_score"] = total_score
                payload["matched_fields"] = {k: sorted(set(v)) for k, v in matched_fields.items()}
                payload["quality_label"] = self._quality_label(total_score)
                scored.append(payload)

        scored.sort(key=lambda item: (item["search_score"], item.get("title", "")), reverse=True)
        limited = scored[: max(1, min(limit, 100))]
        return {
            "ok": True,
            "query": query,
            "filters": {"category": category or "전체", "section": section or "전체"},
            "expansion": expansion,
            "count": len(limited),
            "total_matches": len(scored),
            "items": limited,
            "suggestions": self.suggestions(query, limit=6) if not limited else [],
        }

    def suggestions(self, query: str = "", limit: int = 8) -> list[str]:
        q_tokens = set(_tokens(query))
        candidates: Counter[str] = Counter()
        for item in self.repo.list_items():
            for key in ("title", "category", "section"):
                for token in _tokens(_field_text(item, key)):
                    candidates[token] += 3
            for keyword in item.get("keywords", []):
                for token in _tokens(str(keyword)):
                    candidates[token] += 5
        for key, values in self.synonyms.items():
            candidates[key] += 4
            for value in values:
                candidates[value.lower()] += 2
        results = [term for term, _ in candidates.most_common(80) if term not in q_tokens]
        return results[: max(1, min(limit, 20))]

    def term_frequency(self, limit: int = 20) -> list[dict[str, Any]]:
        counter: Counter[str] = Counter()
        for item in self.repo.list_items():
            text = " ".join(
                _field_text(item, f) for f in ["category", "section", "title", "keywords", "summary", "checklist"]
            )
            counter.update(_tokens(text))
        return [{"term": term, "count": count} for term, count in counter.most_common(limit)]

    @staticmethod
    def _quality_label(score: int) -> str:
        if score >= 35:
            return "강한 일치"
        if score >= 15:
            return "관련 높음"
        return "관련 가능"
