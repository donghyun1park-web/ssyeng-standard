# 설비 시공표준 검색앱 (Facility Standard App)

회사 표준지침을 모바일에서 빠르게 검색하고 PDF 원문까지 바로 확인할 수 있는 현장용 PWA입니다.

- **프론트엔드**: React 19 + Vite (PWA), 모바일 우선 UI, in-app PDF.js 뷰어
- **백엔드**: FastAPI + Gemini/NVIDIA AI Provider + RAG (Firecrawl 옵션)
- **저장소**: JSON 파일 기반 (PostgreSQL 미사용, 무료 호스팅 친화)

---

## 핵심 기능

| 기능 | 설명 |
|---|---|
| 회사 표준지침 검색 | 키워드 + 카테고리 필터, AI 답변 인라인 표시 |
| AI 질의 | Gemini(기본) / NVIDIA NIM / 로컬 fallback, 근거 카드(p.XX + PDF 보기) |
| 앱 내부 PDF 뷰어 | 외부 앱 호출 없이 페이지 점프·줌·페이지 이동 |
| KCSC 참고 기준 | 회사 표준지침과 별도 섹션으로 분리 표시 |
| 법제처 AI 법령검색 | 공식 사이트로 외부 링크 |
| 현장이슈 공유대장 | 현장 등록 + 도면검토 + 이슈 CRUD (검색 X, 공유 O) |
| 체크리스트 | **사용자별·현장별·공종별** 개인 항목 + 추가/수정/삭제 + 기본 템플릿 불러오기 |
| 즐겨찾기 / 최근 본 항목 | LocalStorage 기반 |
| PWA 설치 | 안드로이드 홈 화면 추가 가능, APK 변환(PWABuilder) 가능 |

---

## 빠른 시작 (로컬 개발)

요구 환경: Windows 10/11 또는 macOS/Linux, **Python 3.11**, **Node.js 18+**

### 1) 클론 및 의존성 설치

```powershell
git clone https://github.com/donghyun1park-web/ssyeng-standard.git
cd ssyeng-standard

# 백엔드
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # PowerShell (Windows)
# 또는: source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cd ..

# 프론트엔드
npm install
```

### 2) 환경변수 설정

```powershell
# 백엔드 .env 생성
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

`backend/.env`에서 최소한 다음 두 값을 변경하세요:

```env
ADMIN_TOKEN=your-random-strong-token       # 관리자 페이지 + RAG 업로드용 (필수)
GEMINI_API_KEY=                            # 선택, 비워두면 로컬 fallback 답변 사용
```

Gemini 무료 키: [Google AI Studio](https://aistudio.google.com/apikey)에서 발급.

### 3) 동시 실행 (터미널 2개)

```powershell
# 터미널 1 — 백엔드
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 터미널 2 — 프론트엔드 (vite proxy로 /api → 백엔드)
npm run dev
```

### 4) 접속

| 위치 | URL |
|---|---|
| PC 브라우저 | http://localhost:5173 |
| 같은 와이파이의 폰 | `http://<PC의 LAN IP>:5173` |
| 백엔드 health | http://localhost:8000/api/health |

`<PC의 LAN IP>`는 PowerShell에서 `ipconfig`로 확인. Windows 방화벽에서 5173·8000 포트 인바운드 허용 필요.

---

## 폰에서 사용하기

### A. 브라우저 직접 접속 (가장 간단)
1. PC와 폰이 같은 와이파이에 연결
2. 폰 Chrome에서 `http://<PC_IP>:5173` 접속
3. Chrome 메뉴 → "홈 화면에 추가" → PWA로 설치됨

### B. APK 만들어 사내 배포 (PWABuilder)
1. 백엔드+프론트엔드를 HTTPS 도메인으로 배포 (아래 "배포" 섹션)
2. https://www.pwabuilder.com/ 접속
3. 배포된 URL 입력 → Android Package 다운로드 → 서명된 APK 받기
4. 사내 그룹웨어로 APK 공유 → "알 수 없는 출처" 허용 후 설치

---

## 첫 사용자 안내

### 일반 사용자
1. **설정 탭 → 사용자 이름 입력** (체크리스트 개인화에 사용)
2. **검색 탭**에서 키워드 검색 → AI 답변 + 회사 표준지침 + KCSC 카드 확인
3. **현장이슈 탭**에서 본인 현장 등록 → 도면검토/이슈 기록
4. **체크리스트 탭** → 현장 선택 → 공종 진입 → "기본 템플릿 불러오기" 또는 "+ 항목 추가"

### 관리자 (PDF 업로드 담당)
1. 설정 탭 → **Admin Token** 입력란에 `backend/.env`의 `ADMIN_TOKEN` 값 입력 → 저장
2. 설정 탭 → **관리자 문서 관리** 진입
3. **일반 PDF 업로드** (PyPDF) 또는 **Firecrawl PDF 파싱** 선택해서 업로드
4. 인덱싱 완료 → 검색·AI에서 PDF 근거 + 페이지 이동 사용 가능

---

## 데이터 저장 위치

모든 데이터는 `backend/data/` 안에 JSON 파일로 저장됩니다 (외부 DB 불필요):

| 파일 | 내용 |
|---|---|
| `standard_items.json` | 회사 표준 항목 (CSV/JSON 마이그레이션 결과) |
| `rag_index.json` | PDF 파싱 후 청크 + 벡터 인덱스 |
| `sites.json` | 현장 + 도면검토 + 현장이슈 |
| `checklist_items.json` | 사용자별·현장별 점검 항목 |
| `checklists.json` | 점검 기록 (체크 상태 + 메모) |
| `documents/` | 업로드된 원본 PDF |

⚠️ 위 파일들은 `.gitignore`로 제외 — 운영 환경에서 별도 백업 필요.

---

## 무료 배포 (Render + Vercel)

### 백엔드 → Render
1. https://render.com 가입 → GitHub 연동 → 이 리포 선택
2. `render.yaml` 자동 인식 (Dockerfile 빌드)
3. 환경변수 추가:
   - `ADMIN_TOKEN` (강력한 랜덤 문자열)
   - `GEMINI_API_KEY` (선택)
   - `CORS_ALLOW_ORIGINS` (Vercel 도메인)
4. 배포 완료 후 `https://your-app.onrender.com` URL 확보
5. ⚠️ Render 무료는 15분 미사용 시 sleep — 첫 요청 30~60초 지연 정상

### 프론트엔드 → Vercel
1. https://vercel.com 가입 → 같은 리포 연동
2. Framework: Vite 자동 감지
3. 환경변수 추가:
   - `VITE_API_BASE_URL=https://your-app.onrender.com`
4. 배포 완료 → `https://your-app.vercel.app`

### 인덱싱한 PDF 영속화
Render 무료 디스크는 휘발성 → 재배포 시 업로드한 PDF/인덱스가 사라집니다. 영구 저장이 필요하면:
- Render Persistent Disk (유료, 월 1$~)
- 또는 외부 스토리지 (Cloudflare R2 무료 10GB 등) 연동 필요

---

## 주요 API 엔드포인트

```text
GET    /api/health                              헬스체크
GET    /api/standards                           회사 표준 목록
GET    /api/search?q=&category=                 회사 표준 검색
POST   /api/ask                                 AI 질의 (Gemini/NVIDIA/local)
GET    /api/external/search                     KCSC 외부 검색

GET    /api/rag/documents                       인덱싱된 문서 목록
POST   /api/rag/upload         [Admin]         일반 PDF 업로드 (PyPDF)
POST   /api/rag/parse-pdf      [Admin]         Firecrawl PDF 파싱
GET    /api/rag/documents/{id}/file             PDF 파일 다운로드/뷰어

GET    /api/sites                               현장 목록
POST   /api/sites              [Admin]
GET    /api/site-issues?site_id=
POST   /api/site-issues        [Admin]
GET    /api/drawing-reviews?site_id=
POST   /api/drawing-reviews    [Admin]

GET    /api/checklists?site_id=                 [X-User-Id] 공종별 요약
GET    /api/checklists/{trade}?site_id=         [X-User-Id] 항목 + 체크 상태
POST   /api/checklists/items                    [X-User-Id] 항목 추가
PUT    /api/checklists/items/{id}               [X-User-Id] 본인 항목 수정
DELETE /api/checklists/items/{id}               [X-User-Id] 본인 항목 삭제
POST   /api/checklists/load-template            [X-User-Id] 기본 50+개 템플릿 복사
POST   /api/checklists/record                   [X-User-Id] 체크 상태 저장
```

[Admin] = `X-Admin-Token` 헤더 필요
[X-User-Id] = 사용자 식별 헤더 (앱이 자동 첨부)

---

## CSV 마이그레이션 형식

`backend/data/standard_items.json`을 CSV로 일괄 등록하려면 `/migration` 화면 사용.

필수 컬럼: `id, category, section, title, summary, body`
선택 컬럼: `keywords, checklist` (`|` 또는 `;`로 다중 값)

템플릿 다운로드: `GET /api/migration/template?format=csv`

---

## 트러블슈팅

| 증상 | 해결 |
|---|---|
| 폰에서 접속 안 됨 | Windows 방화벽에서 5173·8000 인바운드 허용. 공유기 AP isolation 확인 |
| PDF 뷰어 `toHex not a function` | `pdfjs-dist` 4.x 버전 사용 중인지 확인 (`npm ls pdfjs-dist`) |
| HMR 후 화면 빈 상태 | 브라우저 강력 새로고침 또는 시크릿 탭, `node_modules/.vite` 삭제 후 재시작 |
| AI 답변에 "provider_error" | `GEMINI_API_KEY` 미설정/잘못. 로컬 fallback 답변은 정상 동작 |
| 관리자 페이지 401 | 설정 탭에서 Admin Token 입력 + `backend/.env`의 값과 일치 확인 |
| 체크리스트 항목 안 보임 | 처음엔 비어있음 → "기본 템플릿 불러오기" 또는 "+ 항목 추가" |

---

## 라이선스 / 안내

사내 사용 목적. AI 답변·KCSC·법령은 모두 **참고용**입니다. 현장 적용 전 회사 표준지침, 설계도서, 계약서, 감리 지시사항과 함께 반드시 확인하세요.
