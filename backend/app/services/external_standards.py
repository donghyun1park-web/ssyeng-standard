from __future__ import annotations

import html
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

from app.services.external_settings import get_kcsc_api_key

load_dotenv()


class ExternalStandardsAdapter:
    """External law/KCSC adapter.

    KCSC is implemented as a live HTTP adapter with a safe sample fallback.
    The frontend and MCP gateway only consume the normalized response shape, so
    the raw KCSC OpenAPI schema can change without forcing UI changes.
    """

    DEFAULT_KCSC_BASE_URL = "https://kcsc.re.kr/OpenApi"

    LAW_API_BASE_URL = os.getenv("LAW_API_BASE_URL", "").strip().rstrip("/")
    LAW_API_KEY = os.getenv("LAW_API_KEY", "").strip()
    KCSC_API_BASE_URL = (os.getenv("KCSC_API_BASE_URL", "").strip().rstrip("/") or DEFAULT_KCSC_BASE_URL)
    KCSC_API_KEY = os.getenv("KCSC_API_KEY", "").strip()
    EXTERNAL_TIMEOUT_SECONDS = float(os.getenv("EXTERNAL_TIMEOUT_SECONDS", "20"))
    KCSC_FETCH_VIEWER_ON_SEARCH = os.getenv("KCSC_FETCH_VIEWER_ON_SEARCH", "false").strip().lower() in {"1", "true", "yes", "y"}
    KCSC_VIEWER_TYPES = {"KCS", "KDS", "EXCS", "SMCS"}
    KCSC_STANDARD_TYPES = ("KDS", "KCS", "NHCS", "SMCS", "EXCS", "KRCCS", "KRACS", "LHCS", "KWCS")

    @staticmethod
    def _kcsc_api_key() -> str:
        return get_kcsc_api_key()

    LAW_SAMPLE = [
        {
            "id": "LAW-PREP-001",
            "source": "law",
            "title": "건축물 설비기준 관련 법령 검색 준비 항목",
            "category": "법령",
            "summary": "실제 국가법령정보 API 연결 전 검색 계약 검증용 샘플입니다.",
            "body": "국가법령정보 API 키가 설정되면 검색 결과에서 조문 본문을 받아 상세 화면에 표시합니다.",
            "reference": "LAW_API_BASE_URL / LAW_API_KEY 설정 후 실제 조문 검색으로 교체",
        },
        {
            "id": "LAW-PREP-002",
            "source": "law",
            "title": "소방·피난·방화 설비 관련 법령 검색 준비 항목",
            "category": "법령",
            "summary": "설비 기준 질의에서 법령 근거를 분리 제공하기 위한 준비 데이터입니다.",
            "body": "법령명, 조문번호, 시행일자, 소관부처 정보를 검색 결과와 상세 화면에 함께 표시합니다.",
            "reference": "법령명, 조문번호, 시행일자 필드를 실제 응답에 매핑 예정",
        },
    ]

    KCSC_SAMPLE = [
        {
            "id": "KCSC-PREP-001",
            "source": "kcsc",
            "title": "KCSC 기계설비 시공기준 검색 준비 항목",
            "category": "KCSC",
            "summary": "KCSC API 연결 전 기준 검색 화면과 MCP Tool 응답 검증용 샘플입니다.",
            "body": "KCSC_API_KEY가 설정되면 CodeViewer API를 통해 기준 본문을 추가로 불러옵니다.",
            "reference": "KCSC_API_KEY 설정 후 KCSC CodeList / CodeViewer API로 검색합니다.",
        },
        {
            "id": "KCSC-PREP-002",
            "source": "kcsc",
            "title": "배관·보온·수압시험 기준 검색 준비 항목",
            "category": "KCSC",
            "summary": "회사 지침서와 외부 기준 비교 기능의 입력 형태를 고정하기 위한 준비 데이터입니다.",
            "body": "기준코드와 제목을 누르면 상세 화면으로 이동하고, 가능한 경우 기준 본문을 보강합니다.",
            "reference": "기준코드, 제목, 본문, 개정일자 필드를 실제 응답에 매핑합니다.",
        },
    ]

    def status(self) -> dict[str, Any]:
        law_configured = bool(self.LAW_API_BASE_URL and self.LAW_API_KEY)
        kcsc_configured = bool(self.KCSC_API_BASE_URL and self._kcsc_api_key())
        return {
            "ok": True,
            "phase": "6.1-kcsc-live-adapter",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": [
                {
                    "id": "law",
                    "title": "법령 검색 어댑터",
                    "configured": law_configured,
                    "mode": "live-api-ready" if law_configured else "sample-fallback",
                    "required_env": ["LAW_API_BASE_URL", "LAW_API_KEY"],
                },
                {
                    "id": "kcsc",
                    "title": "KCSC 검색 어댑터",
                    "configured": kcsc_configured,
                    "mode": "live-api" if kcsc_configured else "sample-fallback",
                    "base_url": self._kcsc_root(),
                    "required_env": ["KCSC_API_KEY"],
                    "optional_env": ["KCSC_API_BASE_URL", "KCSC_FETCH_VIEWER_ON_SEARCH"],
                },
            ],
        }

    def search_law(self, query: str, limit: int = 5) -> dict[str, Any]:
        query = (query or "").strip()
        limit = self._safe_limit(limit)

        if not (self.LAW_API_BASE_URL and self.LAW_API_KEY):
            results = self._filter_samples(self.LAW_SAMPLE, query, limit)
            return {"ok": True, "source": "law", "mode": "sample-fallback", "query": query, "count": len(results), "items": results}

        if not query:
            return {"ok": True, "source": "law", "mode": "live-api", "query": query, "count": 0, "items": []}

        try:
            raw = self._law_search(query, limit)
            articles = self._extract_law_articles(raw)
            results = [self._normalize_law_article(item) for item in articles]
            results = [item for item in results if item]
            results = self._filter_law_items(results, query, limit)
            return {
                "ok": True,
                "source": "law",
                "mode": "live-api",
                "query": query,
                "count": len(results),
                "items": results,
                "raw_count": len(articles),
            }
        except Exception as exc:
            results = self._filter_samples(self.LAW_SAMPLE, query, limit)
            return {
                "ok": True,
                "source": "law",
                "mode": "live-api-error-fallback",
                "query": query,
                "count": len(results),
                "items": results,
                "error": str(exc)[:500],
            }

    def search_kcsc(
        self,
        query: str,
        limit: int = 5,
        types: list[str] | None = None,
        final_only: bool = False,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        query = (query or "").strip()
        limit = self._safe_limit(limit)
        if not self._kcsc_api_key():
            results = self._filter_samples(self.KCSC_SAMPLE, query, limit)
            results = self._decorate_kcsc_results(results, query, limit)
            return {"ok": True, "source": "kcsc", "mode": "sample-fallback", "query": query, "count": len(results), "items": results}

        try:
            raw = self._kcsc_code_list()
            records = self._extract_records(raw)
            normalized = [self._normalize_kcsc_list_item(item) for item in records]
            normalized = [item for item in normalized if item]

            # KCSC 서버가 인증은 통과시키면서 모든 필드 null만 돌려주는 상태 감지
            if not normalized:
                results = self._decorate_kcsc_results([], query, limit)
                return {
                    "ok": True,
                    "source": "kcsc",
                    "mode": "live-api-empty",
                    "query": query,
                    "count": len(results),
                    "items": results,
                    "raw_count": len(records),
                    "warning": (
                        "KCSC OpenAPI가 빈 응답을 반환했습니다. "
                        "발급된 인증키의 상태(validity)가 '정상'이 아닐 수 있습니다. "
                        "https://www.kcsc.re.kr/support/api 에 로그인 후 발급된 인증키의 상태를 확인하고, "
                        "'정상'이 아니면 [인증키 갱신] 버튼을 눌러 활성화하세요."
                    ),
                    "remediation_url": "https://www.kcsc.re.kr/support/api",
                }

            filtered = self._filter_kcsc_by_options(
                normalized,
                types=types,
                final_only=final_only,
                date_from=date_from,
                date_to=date_to,
            )
            results = self._filter_kcsc_items(filtered, query, limit)
            results = self._decorate_kcsc_results(results, query, limit)

            if self.KCSC_FETCH_VIEWER_ON_SEARCH:
                results = [self._attach_kcsc_viewer(item) for item in results]

            return {
                "ok": True,
                "source": "kcsc",
                "mode": "live-api",
                "query": query,
                "filters": {
                    "types": [item.upper() for item in (types or []) if item],
                    "final_only": final_only,
                    "date_from": date_from,
                    "date_to": date_to,
                },
                "count": len(results),
                "items": results,
                "raw_count": len(records),
            }
        except Exception as exc:  # keep app usable in the field even if API is temporarily unavailable
            results = self._filter_samples(self.KCSC_SAMPLE, query, limit)
            results = self._decorate_kcsc_results(results, query, limit)
            return {
                "ok": True,
                "source": "kcsc",
                "mode": "live-api-error-fallback",
                "query": query,
                "count": len(results),
                "items": results,
                "error": str(exc)[:500],
            }

    def get_kcsc_viewer(self, standard_type: str, code: str) -> dict[str, Any]:
        standard_type = (standard_type or "").strip().upper()
        code = (code or "").strip()
        if not self._kcsc_api_key():
            return {
                "ok": False,
                "source": "kcsc",
                "mode": "not-configured",
                "error": "KCSC_API_KEY가 설정되지 않았습니다.",
            }
        if standard_type not in {"KCS", "KDS", "EXCS", "SMCS"}:
            return {"ok": False, "source": "kcsc", "error": f"지원하지 않는 기준 유형입니다: {standard_type}"}
        if not code:
            return {"ok": False, "source": "kcsc", "error": "기준 코드가 비어 있습니다."}

        try:
            viewer_code, raw = self._kcsc_code_viewer_with_fallback(standard_type, code)
            return {
                "ok": True,
                "source": "kcsc",
                "mode": "live-api",
                "standard_type": standard_type,
                "code": viewer_code,
                "requested_code": code,
                "item": self._normalize_kcsc_viewer(raw, standard_type, viewer_code),
                "raw": raw,
            }
        except Exception as exc:
            return {"ok": False, "source": "kcsc", "mode": "live-api-error", "error": str(exc)[:700]}

    def unified_search(self, query: str, sources: list[str] | None = None, limit: int = 5) -> dict[str, Any]:
        selected = sources or ["law", "kcsc"]
        results: list[dict[str, Any]] = []
        diagnostics: dict[str, dict[str, Any]] = {}
        if "law" in selected:
            law_resp = self.search_law(query, limit=limit)
            results.extend(law_resp.get("items", []))
            diagnostics["law"] = {
                "mode": law_resp.get("mode"),
                "count": law_resp.get("count", 0),
                "warning": law_resp.get("warning"),
                "error": law_resp.get("error"),
            }
        if "kcsc" in selected:
            kcsc_resp = self.search_kcsc(query, limit=limit, final_only=True)
            results.extend(kcsc_resp.get("items", []))
            diagnostics["kcsc"] = {
                "mode": kcsc_resp.get("mode"),
                "count": kcsc_resp.get("count", 0),
                "warning": kcsc_resp.get("warning"),
                "error": kcsc_resp.get("error"),
                "remediation_url": kcsc_resp.get("remediation_url"),
            }
        return {
            "ok": True,
            "query": query,
            "sources": selected,
            "count": len(results),
            "items": results,
            "mode": "adapter-facade",
            "diagnostics": diagnostics,
        }

    def _law_search(self, query: str, limit: int) -> Any:
        # The configured URL already carries `?target=aiSearch`, so we append
        # OC (계정ID), type=JSON, query, and display(=limit) onto whatever separator fits.
        sep = "&" if "?" in self.LAW_API_BASE_URL else "?"
        url = (
            f"{self.LAW_API_BASE_URL}{sep}"
            f"OC={self.LAW_API_KEY}&type=JSON&display={max(1, min(limit * 2, 50))}&query={query}"
        )
        with httpx.Client(timeout=self.EXTERNAL_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(url)
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            # Some law.go.kr endpoints return JSON-with-charset that httpx already decodes;
            # fall back to a manual parse if Content-Type lies.
            import json as _json
            return _json.loads(response.text)

    @staticmethod
    def _extract_law_articles(payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        # 응답 형태: {"aiSearch": {"법령조문": [...]}}  /  {"LawSearch": {"law": [...]}}
        for outer_key in ["aiSearch", "AiSearch", "LawSearch", "lawSearch"]:
            section = payload.get(outer_key)
            if isinstance(section, dict):
                for inner_key in ["법령조문", "law", "Law", "조문", "article", "results"]:
                    entries = section.get(inner_key)
                    if isinstance(entries, list):
                        return [e for e in entries if isinstance(e, dict)]
                    if isinstance(entries, dict):
                        return [entries]
        return []

    @classmethod
    def _filter_law_items(cls, items: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
        if not query:
            return items[:limit]

        compact_query = cls._compact_search_text(query)
        terms = cls._search_terms(query)
        scored: list[tuple[int, dict[str, Any]]] = []

        for item in items:
            haystack = " ".join(
                str(item.get(key) or "")
                for key in ["title", "summary", "body", "law_name", "reference", "ministry"]
            )
            compact = cls._compact_search_text(haystack)
            score = 0

            if compact_query and compact_query in compact:
                score += 30
            for term in terms:
                if term and term in compact:
                    score += 8 if len(term) >= 2 else 2

            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

    @staticmethod
    def _compact_search_text(value: Any) -> str:
        return re.sub(r"\s+", "", str(value or "").lower())

    @classmethod
    def _search_terms(cls, query: str) -> list[str]:
        terms: list[str] = []

        def add(term: str) -> None:
            compact = cls._compact_search_text(term)
            if compact and compact not in terms:
                terms.append(compact)

        for token in re.findall(r"[0-9A-Za-z가-힣]+", str(query or "").lower()):
            if len(token) >= 2:
                add(token)
            if len(token) >= 4 and re.search(r"[가-힣]", token):
                for index in range(0, len(token) - 1, 2):
                    add(token[index:index + 2])

        compact_query = cls._compact_search_text(query)
        if len(compact_query) >= 2:
            add(compact_query)

        return terms

    @staticmethod
    def _normalize_law_article(raw: dict[str, Any]) -> dict[str, Any] | None:
        law_name = ExternalStandardsAdapter._first(raw, ["법령명", "법령명한글", "lawName", "name"])
        article_no = ExternalStandardsAdapter._first(raw, ["조문번호", "articleNo"])
        article_branch = ExternalStandardsAdapter._first(raw, ["조문가지번호"])
        article_serial = ExternalStandardsAdapter._first(raw, ["조문일련번호", "조문ID"])
        body = ExternalStandardsAdapter._first(raw, ["조문내용", "조문제목", "content"])
        ministry = ExternalStandardsAdapter._first(raw, ["소관부처명", "소관부처", "ministry"])
        effective = ExternalStandardsAdapter._first(raw, ["시행일자", "시행일", "effectiveDate"])
        law_id = ExternalStandardsAdapter._first(raw, ["법령ID", "법령일련번호", "id"])
        revision = ExternalStandardsAdapter._first(raw, ["제개정구분명", "revisionType"])

        if not (law_name or body):
            return None

        # Build human-readable title: "하수도법 제2조" 형태
        article_label = ""
        if article_no:
            try:
                normalized_no = str(int(article_no))
            except ValueError:
                normalized_no = article_no
            article_label = f"제{normalized_no}조"
            if article_branch and article_branch not in {"00", "0"}:
                article_label += f"의{int(article_branch) if article_branch.isdigit() else article_branch}"

        title_parts = [part for part in [law_name, article_label] if part]
        title = " ".join(title_parts) or law_name or "법령 조문"

        summary = (body or "").strip()
        if len(summary) > 240:
            summary = summary[:240].rstrip() + "…"

        ref_parts = []
        if ministry:
            ref_parts.append(ministry)
        if effective and len(effective) >= 8:
            ref_parts.append(f"시행 {effective[:4]}.{effective[4:6]}.{effective[6:8]}")
        if revision:
            ref_parts.append(revision)
        reference = " · ".join(ref_parts)

        item_id = "LAW-" + (article_serial or f"{law_id or 'X'}-{article_no or '0'}")

        return {
            "id": item_id,
            "source": "law",
            "title": title,
            "category": "법령",
            "summary": summary or title,
            "body": body,
            "reference": reference,
            "law_name": law_name,
            "article_no": article_no,
            "law_id": law_id,
            "effective_date": effective,
            "ministry": ministry,
        }

    def _kcsc_root(self) -> str:
        # KCSC_API_BASE_URL may be configured either as ".../OpenApi" or
        # ".../OpenApi/CodeList" — accept both by stripping a trailing endpoint
        # segment so we can append our own.
        base = self.KCSC_API_BASE_URL.rstrip("/")
        for endpoint in ("/CodeList", "/CodeViewer"):
            if base.endswith(endpoint):
                base = base[: -len(endpoint)]
                break
        return base

    def _kcsc_code_list(self) -> Any:
        url = f"{self._kcsc_root()}/CodeList"
        with httpx.Client(timeout=self.EXTERNAL_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(url, params={"key": self._kcsc_api_key()})
        response.raise_for_status()
        return response.json()

    def _kcsc_code_viewer(self, standard_type: str, code: str) -> Any:
        url = f"{self._kcsc_root()}/CodeViewer/{standard_type}/{code}"
        with httpx.Client(timeout=self.EXTERNAL_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(url, params={"key": self._kcsc_api_key()})
        response.raise_for_status()
        return response.json()

    def _kcsc_code_viewer_with_fallback(self, standard_type: str, code: str) -> tuple[str, Any]:
        candidates: list[str] = []

        def add_candidate(value: str | None) -> None:
            clean = (value or "").strip()
            if clean and clean not in candidates:
                candidates.append(clean)

        add_candidate(code)
        add_candidate(re.sub(r"\D", "", code))

        last_code = candidates[0]
        last_raw: Any = []
        for candidate in candidates:
            raw = self._kcsc_code_viewer(standard_type, candidate)
            last_code = candidate
            last_raw = raw
            if self._payload_has_records(raw):
                return candidate, raw

        resolved_code = self._resolve_kcsc_full_code(standard_type, code)
        if resolved_code and resolved_code not in candidates:
            last_code = resolved_code
            last_raw = self._kcsc_code_viewer(standard_type, resolved_code)
            if self._payload_has_records(last_raw):
                return resolved_code, last_raw

        return last_code, last_raw

    def _resolve_kcsc_full_code(self, standard_type: str, code: str) -> str | None:
        target = (code or "").replace(" ", "")
        if not target:
            return None
        try:
            records = self._extract_records(self._kcsc_code_list())
        except Exception:
            return None
        for record in records:
            if not isinstance(record, dict):
                continue
            if self._detect_standard_type(record) != standard_type:
                continue
            short_code = self._first(record, ["code"])
            full_code = self._first(record, ["fullCode", "standardCode", "stdFullCode"])
            compact_values = {str(value).replace(" ", "") for value in [short_code, full_code] if value}
            if target in compact_values:
                return full_code or short_code
        return None

    @classmethod
    def _normalize_kcsc_list_item(cls, raw: Any) -> dict[str, Any] | None:
        if not isinstance(raw, dict):
            return None
        code = cls._first(raw, ["code", "stdCode", "codeId", "id", "subCode", "detailCode"])
        full_code = cls._first(raw, ["fullCode", "standardCode", "stdFullCode", "codeFullName"])
        title = cls._first(raw, ["name", "title", "stdName", "codeName", "korName", "standardName"])
        standard_type = cls._detect_standard_type(raw)
        update_date = cls._first(raw, ["updateDate", "updDate", "revisionDate", "announceDate", "noticeDate", "enforcementDate", "date"])
        official_url = cls._kcsc_official_url(raw, full_code or code)
        if not code and not full_code and not title:
            return None
        viewer_code = full_code or code
        item_id = f"{standard_type or 'KCSC'}-{viewer_code or title}"
        summary_parts = [part for part in [full_code, title] if part]
        return {
            "id": item_id,
            "source": "kcsc",
            "standard_type": standard_type,
            "code": viewer_code,
            "list_code": code,
            "full_code": full_code,
            "title": title or full_code or code,
            "category": "KCSC",
            "summary": " / ".join(summary_parts) if summary_parts else "KCSC 기준 항목",
            "reference": f"CodeList:{code or full_code or ''}",
            "update_date": update_date,
            "official_url": official_url,
            "viewer_available": bool(standard_type in cls.KCSC_VIEWER_TYPES and viewer_code),
            "raw": raw,
        }

    @classmethod
    def _normalize_kcsc_viewer(cls, raw: Any, standard_type: str, code: str) -> dict[str, Any]:
        records = cls._extract_records(raw)
        if isinstance(raw, list) and raw and isinstance(raw[0], dict):
            primary = raw[0]
        elif isinstance(raw, dict):
            primary = raw
        else:
            primary = records[0] if records and isinstance(records[0], dict) else {}
        title = cls._first(primary, ["name", "title", "stdName", "codeName", "korName", "standardName"])
        body = cls._first(primary, ["content", "contents", "body", "text", "html", "article", "mainText"])
        body = cls._clean_text(body) if body else cls._viewer_body_from_payload(raw)
        full_code = cls._first(primary, ["fullCode", "standardCode", "stdFullCode"])
        return {
            "id": f"{standard_type}-{code}",
            "source": "kcsc",
            "standard_type": standard_type,
            "code": code,
            "full_code": full_code,
            "title": title or f"{standard_type} {code}",
            "category": "KCSC",
            "summary": (str(body)[:300] if body else f"{standard_type} {code} 상세 조회 결과"),
            "body": body,
            "official_url": cls._kcsc_official_url(primary, code),
        }

    @classmethod
    def _kcsc_official_url(cls, raw: dict[str, Any], code: str | None = None) -> str:
        viewer_no = cls._first(raw, ["no", "seq", "viewerNo", "standardNo", "standardSeq"])
        if viewer_no:
            return f"https://www.kcsc.re.kr/StandardCode/Viewer/{quote(str(viewer_no), safe='')}"
        if code:
            return f"https://www.kcsc.re.kr/standardCode/search?searchType=0&kcsc_cd={quote(str(code), safe='')}"
        return "https://www.kcsc.re.kr/standardCode/search?searchType=0&kcsc_cd="

    @classmethod
    def _kcsc_search_url(cls, query: str) -> str:
        return f"https://www.kcsc.re.kr/standardCode/search?kcsc_cd={quote(str(query or ''), safe='')}"

    @classmethod
    def _kcsc_result_url(cls, item: dict[str, Any], query: str) -> str:
        keyword = (
            item.get("full_code")
            or item.get("code")
            or item.get("list_code")
            or item.get("title")
            or query
            or ""
        )
        return cls._kcsc_search_url(str(keyword))

    @classmethod
    def _kcsc_official_search_item(cls, query: str) -> dict[str, Any]:
        clean = (query or "").strip()
        url = cls._kcsc_search_url(clean)
        encoded = quote(clean, safe="") or "ALL"
        return {
            "id": f"KCSC-OFFICIAL-SEARCH-{encoded}",
            "source": "kcsc",
            "title": f"KCSC 공식 검색: {clean}" if clean else "KCSC 공식 검색",
            "category": "KCSC",
            "summary": "KCSC API 키가 없거나 검색 결과가 비어 공식 KCSC 검색 페이지로 연결합니다.",
            "body": "",
            "reference": "KCSC official search",
            "source_url": url,
            "official_url": url,
            "viewer_available": False,
        }

    @classmethod
    def _decorate_kcsc_results(cls, results: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
        clean_query = (query or "").strip()
        if not results and clean_query:
            return [cls._kcsc_official_search_item(clean_query)]

        decorated: list[dict[str, Any]] = []
        fallback_url = cls._kcsc_search_url(clean_query) if clean_query else cls._kcsc_official_url({})
        for item in results[:limit]:
            enriched = dict(item)
            source_url = enriched.get("source_url") or cls._kcsc_result_url(enriched, clean_query) or fallback_url
            enriched["source_url"] = source_url
            enriched.setdefault("official_url", source_url)
            decorated.append(enriched)
        return decorated

    @classmethod
    def _viewer_body_from_payload(cls, payload: Any) -> str | None:
        fragments: list[str] = []

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                content = cls._first(value, ["contents", "content", "body", "text", "html", "article", "mainText"])
                if content:
                    fragments.append(cls._clean_text(content))
                for child in value.values():
                    if isinstance(child, (dict, list)):
                        walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(payload)

        unique: list[str] = []
        for fragment in fragments:
            if fragment and fragment not in unique:
                unique.append(fragment)
        return "\n\n".join(unique) if unique else None

    @staticmethod
    def _clean_text(value: Any) -> str:
        text = html.unescape(str(value or ""))
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text).replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\s*\n\s*", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def _payload_has_records(cls, payload: Any) -> bool:
        if payload is None:
            return False
        if isinstance(payload, list):
            return len(payload) > 0
        if isinstance(payload, dict):
            return bool(cls._extract_records(payload)) or bool(payload)
        return False

    @staticmethod
    def _extract_records(payload: Any) -> list[Any]:
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        candidate_keys = ["data", "items", "list", "result", "results", "body", "rows", "standardList"]
        for key in candidate_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = ExternalStandardsAdapter._extract_records(value)
                if nested:
                    return nested
        # Some APIs return a single object.
        if any(key in payload for key in ["code", "fullCode", "name", "title", "content", "contents"]):
            return [payload]
        return []

    @staticmethod
    def _first(raw: dict[str, Any], keys: list[str]) -> str | None:
        for key in keys:
            value = raw.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return None

    @classmethod
    def _detect_standard_type(cls, raw: dict[str, Any]) -> str | None:
        def matches_token(value: str, token: str) -> bool:
            return bool(re.search(rf"(^|[^A-Z0-9]){re.escape(token)}(?=$|[^A-Z]|[0-9])", value))

        keys = ["type", "standardType", "codeType", "stdType", "gbn", "kind", "cate"]
        for key in keys:
            value = str(raw.get(key) or "").upper()
            if value in cls.KCSC_STANDARD_TYPES:
                return value
            for token in cls.KCSC_STANDARD_TYPES:
                if matches_token(value, token):
                    return token
        joined = " ".join(str(value) for value in raw.values()).upper()
        for token in cls.KCSC_STANDARD_TYPES:
            if matches_token(joined, token):
                return token
        return None

    @classmethod
    def _filter_kcsc_by_options(
        cls,
        items: list[dict[str, Any]],
        types: list[str] | None = None,
        final_only: bool = False,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        selected_types = {str(item).strip().upper() for item in (types or []) if str(item).strip()}
        normalized_from = cls._normalize_date_filter(date_from)
        normalized_to = cls._normalize_date_filter(date_to)
        filtered: list[dict[str, Any]] = []

        for item in items:
            raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}

            if selected_types:
                standard_type = str(item.get("standard_type") or "").upper()
                raw_type = cls._detect_standard_type(raw) if raw else None
                if standard_type not in selected_types and raw_type not in selected_types:
                    continue

            if final_only and not cls._is_kcsc_final_item(item):
                continue

            if normalized_from or normalized_to:
                raw_date = cls._first(
                    raw,
                    ["updateDate", "updDate", "revisionDate", "announceDate", "noticeDate", "enforcementDate", "date"],
                ) if raw else None
                item_date = cls._normalize_date_filter(item.get("update_date") or raw_date)
                if normalized_from and (not item_date or item_date < normalized_from):
                    continue
                if normalized_to and (not item_date or item_date > normalized_to):
                    continue

            filtered.append(item)

        return filtered

    @classmethod
    def _is_kcsc_final_item(cls, item: dict[str, Any]) -> bool:
        raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
        explicit_keys = ["finalYn", "lastYn", "leafYn", "isLeaf", "isFinal", "latestYn"]
        for key in explicit_keys:
            if key not in raw:
                continue
            value = str(raw.get(key)).strip().lower()
            if value in {"y", "yes", "true", "1", "final", "last", "leaf", "최종"}:
                return True
            if value in {"n", "no", "false", "0"}:
                return False

        for key in ["children", "items", "list", "subList"]:
            value = raw.get(key)
            if isinstance(value, list) and value:
                return False

        code = str(item.get("full_code") or item.get("code") or "")
        digits = re.sub(r"\D", "", code)
        if len(digits) >= 6 and digits.endswith("00"):
            return False
        return True

    @staticmethod
    def _normalize_date_filter(value: Any) -> str | None:
        text = str(value or "").strip()
        if not text:
            return None
        match = re.search(r"(\d{4})\D*(\d{1,2})\D*(\d{1,2})", text)
        if not match:
            return None
        year, month, day = (int(part) for part in match.groups())
        try:
            datetime(year, month, day)
            return f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            return None

    @classmethod
    def _filter_kcsc_items(cls, items: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
        if not query:
            return items[:limit]
        lowered = cls._compact_search_text(query)
        terms = cls._search_terms(query)
        scored: list[tuple[int, dict[str, Any]]] = []
        for item in items:
            haystack = " ".join(str(value) for key, value in item.items() if key != "raw").lower()
            compact = cls._compact_search_text(haystack)
            score = 0
            if lowered in compact:
                score += 10
            for token in terms:
                if token and token in compact:
                    score += 3
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def _attach_kcsc_viewer(self, item: dict[str, Any]) -> dict[str, Any]:
        standard_type = item.get("standard_type")
        code = item.get("code")
        if not standard_type or not code:
            return item
        detail = self.get_kcsc_viewer(str(standard_type), str(code))
        if detail.get("ok") and detail.get("item"):
            enriched = dict(item)
            enriched["detail"] = detail["item"]
            return enriched
        return item

    @staticmethod
    def _safe_limit(limit: int) -> int:
        return max(1, min(int(limit or 5), 20))

    @classmethod
    def _filter_samples(cls, samples: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
        if not query:
            return samples[:limit]
        compact_query = cls._compact_search_text(query)
        terms = cls._search_terms(query)
        matched = []
        for item in samples:
            compact = cls._compact_search_text(" ".join(str(value) for value in item.values()))
            if compact_query in compact or any(term in compact for term in terms):
                matched.append(item)
        return matched[:limit]
