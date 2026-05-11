# Phase 5 MCP server placeholders

이 폴더는 실제 MCP 서버를 붙이기 전 서버별 책임을 고정하기 위한 자리입니다.

- `company-standard-mcp`: 회사 지침서 검색/상세/체크리스트 도구
- `law-mcp`: 법령 검색/조문 조회/비교 도구
- `kcsc-mcp`: KCSC 기준 검색/상세 조회 도구
- `report-mcp`: 점검표/보고서 출력 도구

현재 Phase 5에서는 `app.services.mcp_gateway.McpGateway`가 Mock Gateway 역할을 합니다.
실제 MCP SDK 또는 외부 MCP 서버를 붙일 때는 프론트엔드 API 계약(`/api/mcp/*`)을 유지하고 Gateway 내부만 교체합니다.
