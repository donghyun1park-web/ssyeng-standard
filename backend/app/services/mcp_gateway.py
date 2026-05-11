from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.services.external_standards import ExternalStandardsAdapter
from app.services.standard_repository import StandardRepository


@dataclass(frozen=True)
class McpTool:
    name: str
    title: str
    server: str
    description: str
    input_schema: dict[str, Any]
    enabled: bool = True
    mode: str = "mock"


class McpGateway:
    """Lightweight MCP gateway facade for Phase 5.

    Phase 5 intentionally does not connect to live law/KCSC systems. It exposes a
    stable backend contract so the React app and future FastAPI services can call
    MCP-style tools. The implementation can later be replaced with a real MCP
    client without changing the frontend routes.
    """

    def __init__(self) -> None:
        self.repo = StandardRepository()
        self.external = ExternalStandardsAdapter()
        self.tools: list[McpTool] = [
            McpTool(
                name="company.search_company_standard",
                title="회사 지침서 검색",
                server="company-standard-mcp",
                description="로컬 JSON 기준에서 회사 설비 시공표준을 검색합니다.",
                input_schema={"query": "string", "category": "string|null", "limit": "integer"},
                mode="local",
            ),
            McpTool(
                name="company.get_standard_detail",
                title="회사 지침서 상세 조회",
                server="company-standard-mcp",
                description="표준 항목 ID로 상세 기준과 체크리스트를 조회합니다.",
                input_schema={"item_id": "string"},
                mode="local",
            ),
            McpTool(
                name="law.search_law",
                title="법령 검색",
                server="law-mcp",
                description="외부 기준 어댑터를 통해 법령 검색 결과를 반환합니다. API 미설정 시 샘플 fallback으로 동작합니다.",
                input_schema={"query": "string", "limit": "integer"},
                mode="external-adapter",
            ),
            McpTool(
                name="kcsc.search_standard",
                title="KCSC 기준 검색",
                server="kcsc-mcp",
                description="외부 기준 어댑터를 통해 KCSC 기준 검색 결과를 반환합니다. API 미설정 시 샘플 fallback으로 동작합니다.",
                input_schema={"query": "string", "limit": "integer"},
                mode="external-adapter",
            ),
            McpTool(
                name="report.make_checklist_report",
                title="점검 보고서 초안 생성",
                server="report-mcp",
                description="체크리스트 결과 보고서 출력 연결 예정 도구입니다.",
                input_schema={"item_ids": "string[]", "format": "pdf|xlsx|markdown"},
                enabled=False,
            ),
        ]

    def status(self) -> dict[str, Any]:
        enabled = [tool for tool in self.tools if tool.enabled]
        return {
            "ok": True,
            "phase": "6-external-adapter-ready",
            "mode": "gateway-with-external-adapters",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "servers": [
                {
                    "id": "company-standard-mcp",
                    "title": "회사 지침서 MCP",
                    "status": "connected-local",
                    "description": "현재 로컬 JSON repository와 연결되어 즉시 사용 가능합니다.",
                },
                {
                    "id": "law-mcp",
                    "title": "법령 MCP",
                    "status": "adapter-ready",
                    "description": "법령 검색 어댑터와 연결되었습니다. API 미설정 시 샘플 fallback으로 응답합니다.",
                },
                {
                    "id": "kcsc-mcp",
                    "title": "KCSC MCP",
                    "status": "adapter-ready",
                    "description": "KCSC 검색 어댑터와 연결되었습니다. API 미설정 시 샘플 fallback으로 응답합니다.",
                },
                {
                    "id": "report-mcp",
                    "title": "보고서 MCP",
                    "status": "prepared",
                    "description": "점검표/PDF/Excel 출력 연동 전 준비 서버입니다.",
                },
            ],
            "tool_count": len(self.tools),
            "enabled_tool_count": len(enabled),
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return [tool.__dict__ for tool in self.tools]

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = next((entry for entry in self.tools if entry.name == tool_name), None)
        if not tool:
            return {"ok": False, "error": f"Unknown MCP tool: {tool_name}"}

        if tool.name == "company.search_company_standard":
            query = str(arguments.get("query") or "").strip()
            category = arguments.get("category") or None
            limit = int(arguments.get("limit") or 5)
            results = self.repo.search(query=query, category=category, limit=max(1, min(limit, 20)))
            return {
                "ok": True,
                "tool": tool.name,
                "mode": "local-repository",
                "result": {
                    "count": len(results),
                    "items": [
                        {
                            "id": item.get("id"),
                            "title": item.get("title"),
                            "category": item.get("category"),
                            "section": item.get("section"),
                            "summary": item.get("summary"),
                        }
                        for item in results
                    ],
                },
            }

        if tool.name == "company.get_standard_detail":
            item_id = str(arguments.get("item_id") or "").strip()
            item = self.repo.get_item(item_id)
            if not item:
                return {"ok": False, "tool": tool.name, "error": f"표준 항목을 찾을 수 없습니다: {item_id}"}
            return {"ok": True, "tool": tool.name, "mode": "local-repository", "result": item}


        if tool.name == "law.search_law":
            query = str(arguments.get("query") or "").strip()
            limit = int(arguments.get("limit") or 5)
            return {"ok": True, "tool": tool.name, "mode": "external-adapter", "result": self.external.search_law(query, limit=limit)}

        if tool.name == "kcsc.search_standard":
            query = str(arguments.get("query") or "").strip()
            limit = int(arguments.get("limit") or 5)
            return {"ok": True, "tool": tool.name, "mode": "external-adapter", "result": self.external.search_kcsc(query, limit=limit)}

        return {
            "ok": True,
            "tool": tool.name,
            "mode": "prepared-only",
            "result": {
                "message": "이 MCP Tool은 Phase 5에서 계약만 고정했습니다. 실제 외부 연동은 다음 단계에서 구현합니다.",
                "received_arguments": arguments,
                "next_step": "실제 MCP 서버 URL, 인증 방식, 데이터 소스 정책을 확정한 뒤 구현합니다.",
            },
        }
