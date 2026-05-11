# facility-standard-app Phase 18.1 Gemini Provider

설비 시공표준 PWA의 Phase 18.1 Gemini API 전환 패치 패키지입니다.

중요 확인값:

```text
GET /api/health → phase: 18.1-gemini-ai-provider
```

## AI Provider 설정

`backend/.env`에서 Gemini 무료/테스트 모델을 기본 provider로 사용합니다.

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=Google_AI_Studio에서_발급받은_키
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_MODEL=gemini-2.5-flash
```

`AI_PROVIDER=nvidia`로 바꾸면 기존 NVIDIA NIM 설정을 사용할 수 있고, 외부 AI 키가 없거나 호출이 실패하면 `/api/ask`는 로컬 근거 요약 fallback으로 계속 응답합니다.

## 실행

```powershell
cd facility-standard-app-phase18-fixed\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

PC 확인:

```text
http://localhost:8000/api/health
http://localhost:8000
```

핸드폰 확인:

```text
http://<PC_IP>:8000
```

---

# facility-standard-app Phase 15

설비 시공표준 검색앱 Phase 15입니다.

## 핵심 추가 기능

- 데이터 등록 / 마이그레이션 화면: `/migration`
- CSV / JSON 회사 지침 항목 대량 검증
- 대기 배치 등록 후 수동 반영
- 반영 방식 선택: append / upsert / replace
- 현재 `standard_items.json` CSV/JSON 백업 다운로드
- CSV/JSON 등록 양식 다운로드
- 반영 전 자동 백업 생성
- 반영 후 표준 검색 데이터 자동 reload

## 실행

```powershell
scripts\install-dev.ps1
scripts\start-dev.ps1
```

## 주요 API

```text
GET  /api/migration/status
GET  /api/migration/template?format=csv
GET  /api/migration/template?format=json
POST /api/migration/validate
POST /api/migration/import
GET  /api/migration/batches
POST /api/migration/batches/{batch_id}/commit?mode=upsert
GET  /api/migration/export?format=json
GET  /api/migration/export?format=csv
```

## CSV 필드

필수:

```text
id, category, section, title, summary, body
```

선택:

```text
keywords, checklist
```

`keywords`와 `checklist`는 `|` 또는 `;`로 여러 값을 구분할 수 있습니다.


## Rebuilt download note

This package was recreated in the current session because the original `facility-standard-app-phase18.zip` artifact was no longer available in `/mnt/data`. It is based on the latest available project snapshot in this session and preserves the React + Vite PWA/FastAPI structure.
