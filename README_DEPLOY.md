# 설비 시공표준 검색앱 1차 MVP 배포 가이드

## 목표 구조

1차 MVP는 빠르게 외부 테스트가 가능한 구조로 배포합니다.

```text
사용자 핸드폰
  -> Vercel HTTPS
  -> React/Vite PWA
  -> Render HTTPS
  -> FastAPI 백엔드
  -> Gemini API / 회사 지침 RAG / KCSC / 법령 API
```

정식 운영 전환 시 목표 구조는 다음입니다.

```text
사용자 핸드폰
  -> Firebase Hosting
  -> React/Vite PWA
  -> Google Cloud Run
  -> FastAPI 백엔드
  -> Cloud Storage
  -> Gemini API
```

## 현재 프로젝트 구조 주의

이 저장소는 프론트엔드 코드가 `frontend/`가 아니라 저장소 루트에 있습니다.

```text
package.json
vite.config.js
src/
public/
backend/
```

따라서 Vercel의 Root Directory는 `.` 또는 비워두는 값이 맞습니다. `frontend/` 폴더에는 기존 로컬 테스트용 `.env`만 있었고, 이번 배포 안내용으로 `frontend/.env.production`도 같이 두었지만 실제 Vite 빌드는 루트의 `.env.production`을 사용합니다.

## GitHub 업로드

```powershell
cd "C:\AI program\facility-standard-app-phase18-fixed"

git init
git add .
git commit -m "Initial MVP deploy setup"

git remote add origin https://github.com/본인계정/facility-standard-app.git
git branch -M main
git push -u origin main
```

`backend/.env`, `backend/.venv`, `node_modules`, `dist`, 업로드 파일과 백업 파일은 Git에 올리지 않습니다.

## 프론트엔드 환경변수

Vite 브라우저 코드에서 읽는 환경변수는 반드시 `VITE_` 접두어가 필요합니다.

루트 `.env.production`:

```env
VITE_API_BASE_URL=https://RENDER_BACKEND_URL_TO_BE_SET
```

Render 배포 후 발급된 URL로 바꿉니다.

```env
VITE_API_BASE_URL=https://facility-standard-app-backend.onrender.com
```

로컬에서 Vite proxy를 사용할 때는 비워둘 수 있습니다. 같은 도메인에서 FastAPI가 정적 파일을 서빙하는 방식도 빈 값으로 동작합니다.

## Vercel 배포

Vercel 프로젝트 설정:

```text
Framework Preset: Vite
Root Directory: .
Install Command: npm install
Build Command: npm run build
Output Directory: dist
```

Environment Variables:

```env
VITE_API_BASE_URL=https://Render에서_발급된_백엔드_URL
```

`vercel.json`은 `/external`, `/documents` 같은 React Router 경로에서 새로고침해도 `index.html`로 돌아가도록 설정합니다.

## Render 백엔드 배포

Render 프로젝트 설정:

```text
Service Type: Web Service
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

`backend/runtime.txt`에서 Python 3.11을 지정했습니다. 로컬에서 Python 3.14로 설치할 때 `pydantic-core` 빌드 문제가 났기 때문에 배포 환경은 3.11 계열을 권장합니다.

Render Environment Variables:

```env
APP_ENV=production
AI_PROVIDER=gemini
GEMINI_API_KEY=본인_Gemini_API_키
GEMINI_MODEL=gemini-2.5-flash
CORS_ALLOW_ORIGINS=https://본인앱.vercel.app
ADMIN_TOKEN=관리자_토큰
KCSC_API_KEY=본인_KCSC_API_키
LAW_API_BASE_URL=국가법령_API_URL
LAW_API_KEY=국가법령_API_키
```

법령/KCSC 키는 없으면 fallback 또는 빈 결과로 동작할 수 있지만, 외부 테스트 품질을 보려면 실제 키를 넣는 편이 좋습니다.

`render.yaml`도 추가해두었으므로 Render Blueprint로 시작할 수도 있습니다. 단, 실제 Vercel URL이 나오면 `CORS_ALLOW_ORIGINS` 값을 반드시 바꿔야 합니다.

## CORS 설정

FastAPI는 기본으로 로컬 개발 주소를 허용합니다.

```text
http://localhost:5173
http://127.0.0.1:5173
http://localhost:4173
http://127.0.0.1:4173
```

운영 배포에서는 Render 환경변수에 Vercel 주소를 넣습니다.

```env
CORS_ALLOW_ORIGINS=https://본인앱.vercel.app
```

여러 주소가 필요하면 쉼표로 구분합니다.

```env
CORS_ALLOW_ORIGINS=https://본인앱.vercel.app,https://preview-url.vercel.app
```

`allow_origins=["*"]`는 초기 디버깅 때만 임시로 쓰고, 운영에는 권장하지 않습니다.

## 백엔드 헬스체크

로컬:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET
```

Render:

```text
https://본인-render-api.onrender.com/api/health
```

정상 응답:

```json
{
  "ok": true,
  "service": "facility-standard-app-backend"
}
```

## PWA 점검

필수 조건:

```text
HTTPS 접속
manifest 존재
service worker 등록
192x192 아이콘 존재
512x512 아이콘 존재
display: standalone
start_url: /
```

현재 `vite.config.js`의 `vite-plugin-pwa` 설정에 다음 값이 들어 있습니다.

```text
name: 설비 시공표준 검색앱
short_name: 설비표준
display: standalone
start_url: /
theme_color: #12372a
background_color: #f5f7f6
icons: /icons/icon-192.svg, /icons/icon-512.svg
```

아이콘 파일은 `public/icons/`에 있습니다. 스토어 배포까지 갈 경우 PNG 아이콘도 추가하는 편이 좋습니다.

## 로컬 검증

프론트엔드:

```powershell
cd "C:\AI program\facility-standard-app-phase18-fixed"
npm install
npm run build
```

백엔드:

```powershell
cd "C:\AI program\facility-standard-app-phase18-fixed\backend"
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

헬스체크:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET
```

## 배포 후 체크리스트

```text
1. Render /api/health 접속 확인
2. Vercel 프론트엔드 접속 확인
3. 통합검색 실행
4. KCSC 상세검색 실행
5. Gemini 질문 실행
6. 브라우저 Console에서 CORS 오류 확인
7. 핸드폰 Chrome에서 접속
8. 홈 화면에 추가 또는 앱 설치 확인
9. 즐겨찾기/최근 본 항목 저장 확인
10. 새로고침 후 localStorage 유지 확인
```

## 1차 MVP에서 보류

```text
Cloud Run 전환
Cloud Storage 연동
Vector DB 정식 구성
사용자 로그인
회사 SSO
복잡한 권한관리
앱스토어/Play Store 등록
```

1차 목표는 외부 HTTPS 주소에서 접속되고, 핸드폰에서 앱처럼 설치되며, 검색과 Gemini API가 동작하는 것입니다.

## 정식 운영 전환 메모

정식 운영 때는 다음 순서로 전환합니다.

```text
1. Firebase Hosting에 Vite PWA 배포
2. FastAPI를 Cloud Run 컨테이너로 배포
3. 업로드 PDF와 RAG 원본 파일을 Cloud Storage로 이동
4. Cloud Run 서비스 계정에 Storage 권한 부여
5. 관리자 업로드/삭제 API가 로컬 파일 대신 Cloud Storage를 사용하도록 변경
6. 운영 도메인 기준 CORS와 Firebase Hosting rewrite 정리
```
