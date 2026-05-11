# Facility Standard API Phase 18.1

FastAPI 백엔드입니다.

## 주요 라우터

- `/api/health`
- `/api/standards`
- `/api/search`
- `/api/ask`
- `/api/rag/*`
- `/api/mcp/*`
- `/api/external/*`

## Gemini / AI Provider

`/api/ask`는 `AI_PROVIDER` 값에 따라 외부 AI provider를 선택합니다.

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_MODEL=gemini-2.5-flash
```

선택 우선순위:

```text
AI_PROVIDER=gemini + GEMINI_API_KEY 있음 → Gemini API
AI_PROVIDER=nvidia + NVIDIA_API_KEY 있음 → NVIDIA NIM
AI_PROVIDER=auto → Gemini 키, NVIDIA 키 순서로 자동 선택
외부 AI 설정 없음 또는 호출 실패 → local-summary-fallback
```

## Phase 6 핵심

외부 기준 검색 어댑터를 추가했습니다.

- 법령 검색: `/api/external/law/search`
- KCSC 검색: `/api/external/kcsc/search`
- 통합 검색: `/api/external/search`
- 상태 확인: `/api/external/status`

실제 API 계약 확정 전에는 샘플 fallback으로 동작합니다.


## KCSC API 실제 연결

KCSC 인증키는 프론트엔드에 넣지 말고 `backend/.env`에만 입력합니다.

```env
KCSC_API_BASE_URL=https://kcsc.re.kr/OpenApi
KCSC_API_KEY=발급받은_KCSC_API_KEY
KCSC_FETCH_VIEWER_ON_SEARCH=false
EXTERNAL_TIMEOUT_SECONDS=20
```

확인 URL:

```text
http://localhost:8000/api/external/status
http://localhost:8000/api/external/kcsc/search?q=수압시험
http://localhost:8000/api/external/kcsc/viewer/KCS/114010
```

`KCSC_FETCH_VIEWER_ON_SEARCH=true`로 설정하면 검색 결과마다 상세 조회를 추가 시도합니다. 응답속도가 느려질 수 있으므로 운영 기본값은 `false`입니다.
