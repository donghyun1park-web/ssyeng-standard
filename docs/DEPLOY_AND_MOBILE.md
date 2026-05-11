# 배포 & 모바일 앱 가이드

이 문서는 세 가지를 다룹니다:
1. 사용자별 Gemini API 키 — 이미 구현됨, 사용법
2. 모바일 앱으로 만드는 두 가지 방식 (PWA / Capacitor)
3. 서버 배포 절차 (Docker)
4. 관리자 토큰과 배포 보안

---

## 1. 개인 Gemini API 키 사용 (구현 완료)

### 사용자가 할 일
1. https://aistudio.google.com/apikey 에서 본인 Gemini 키 발급
2. 앱 → **설정 (⚙)** → **Google Gemini API Key** 칸에 키 붙여넣고 **저장**
3. 이후 모든 AI 종합판단은 이 키로 호출됨. AI 패널 상단에 `내 키` 배지가 표시됨

### 동작 원리
- 키는 **사용자 브라우저의 localStorage에만** 저장됨 (`facility-standard:gemini-user-key`)
- AI 호출 시 자동으로 `X-User-Gemini-Key` HTTP 헤더에 실어 백엔드로 전송
- 백엔드는 이 헤더가 있으면 그 키로 Gemini 호출, 없으면 `.env`의 공유 키를 사용
- 서버 `.env`는 어떤 식으로도 변경되지 않음
- 키를 비우고 저장하면 다시 공유 키 모드로 돌아감

### 보안 메모
- 사용자 키는 `https`로 백엔드까지만 전송됨 — 백엔드는 그 키로 Google에 호출하고 응답만 돌려줌
- 백엔드는 사용자 키를 로그/DB/파일 어디에도 저장하지 않음 (헤더 → 메모리 → Google 호출 → 폐기)
- 동일 기기/브라우저에서만 키가 유지됨. 다른 기기에 자동 동기화되지 않음
- 브라우저 `localStorage` 저장 방식이므로 공용 기기에서는 저장하지 말고, 운영 배포 시 외부 스크립트 추가를 피하고 CSP를 적용하는 것을 권장

---

## 1-1. 관리자 토큰 사용 (문서/데이터 변경 보호)

문서 RAG 등록과 데이터 마이그레이션은 운영 데이터가 바뀌는 작업이므로 `ADMIN_TOKEN`으로 보호됩니다.

### 서버 설정
`backend/.env`에 긴 임의 문자열을 넣습니다.

```env
ADMIN_TOKEN=충분히_긴_관리자_토큰
```

### 관리자 사용법
1. 앱 → **설정 (⚙)** → **Admin Token** 칸에 서버와 같은 토큰 입력
2. 문서 업로드, 텍스트 인덱싱, 데이터 등록/반영/삭제/백업 다운로드 요청 시 `X-Admin-Token` 헤더가 자동 전송됨
3. 토큰을 비우면 관리자 작업은 차단됨

`ADMIN_TOKEN`이 서버에 설정되지 않은 경우에도 관리자 작업은 열리지 않고 차단됩니다.

---

## 2. 모바일 앱으로 만들기

### 옵션 A — PWA "홈 화면에 추가" (가장 빠름, 권장)

이미 `vite-plugin-pwa`가 설치돼 있어 바로 PWA로 동작합니다.

**Android (Chrome / Samsung Internet)**
1. 브라우저로 배포된 URL 접속
2. 메뉴 → **앱 설치** 또는 **홈 화면에 추가**
3. 홈 화면 아이콘으로 실행 — 주소창 없는 풀스크린 앱처럼 동작

**iPhone (Safari)**
1. Safari로 URL 접속 (다른 브라우저는 PWA 설치 불가)
2. 공유 → **홈 화면에 추가**
3. 홈 화면 아이콘으로 실행

> 앱 안의 `현장` 화면에 **「휴대폰 홈 화면에 설치」** 안내 카드가 자동으로 뜹니다.

**제한**
- iOS는 PWA에 일부 제약 (백그라운드 푸시 등) — 이 앱 기능에는 영향 없음
- 앱 스토어/플레이 스토어에 올라가지 않음

### 옵션 B — Capacitor로 네이티브 .apk / .ipa 빌드 (스토어 배포용)

스토어 배포가 필요한 경우 [Capacitor](https://capacitorjs.com/)로 PWA를 네이티브로 감쌀 수 있습니다.

```bash
# 1) 의존성 설치
npm install --save @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios

# 2) 프로젝트 초기화 (한 번만)
npx cap init "설비 시공표준" com.example.facility --web-dir=dist

# 3) 빌드 & 동기화 (배포 때마다)
npm run build
npx cap add android      # 또는 ios
npx cap copy
npx cap open android     # Android Studio 열림 → APK/AAB 빌드
```

**필요한 환경**
- Android: Android Studio + JDK 17
- iOS: macOS + Xcode (Windows에서 빌드 불가)

**capacitor.config.json 권장 설정**
```json
{
  "appId": "com.example.facility",
  "appName": "설비 시공표준",
  "webDir": "dist",
  "server": {
    "url": "https://your-server.com",
    "cleartext": false
  }
}
```
> `server.url`을 **배포된 백엔드 URL**로 지정하면 앱이 항상 최신 버전을 받습니다 (앱 스토어 재심사 없이 업데이트). 오프라인 우선이라면 `server.url`을 빼고 `webDir`만 사용하세요.

### 옵션 C — Bubblewrap으로 TWA (Trusted Web Activity)

Android 전용. PWA를 그대로 Play Store에 올리는 경량 방식.
```bash
npm install -g @bubblewrap/cli
bubblewrap init --manifest=https://your-server.com/manifest.webmanifest
bubblewrap build
```

---

## 3. 서버 배포

### 사전 점검
- `backend/.env` 의 키들 (`GEMINI_API_KEY`, `KCSC_API_KEY`, `LAW_API_KEY`) 정상인지 확인
- `backend/.env` 의 `ADMIN_TOKEN` 설정 — 문서 업로드/데이터 등록에 필요
- `frontend/.env` 의 `VITE_API_BASE_URL` — 같은 도메인으로 배포할 거면 빈 문자열로 두면 됨
- `.dockerignore`가 `backend/.env`, `node_modules`, 업로드/백업 폴더를 제외하는지 확인

### 가장 간단한 방법 — Docker 한 컨테이너 (이미 구성됨)

`Dockerfile`이 이미 멀티스테이지로 frontend(`vite build`) → backend(`uvicorn`)를 한 이미지에 합칩니다.
백엔드가 정적 파일도 같이 서빙하므로 **포트 8000 하나만** 열면 됩니다.

**로컬에서**
```bash
docker compose up --build -d
# http://localhost:8000 접속
```

**서버(VPS)에서**
1. Docker / Docker Compose 설치된 Ubuntu/Debian 서버 준비
2. 코드 업로드 (`git clone` 또는 rsync)
3. `backend/.env` 작성
4. `docker compose up --build -d`
5. 80/443 포트로 노출하려면 앞단에 nginx 또는 Caddy 둘 것 — 예시:

**Caddyfile** (Caddy 사용 시 — 자동 HTTPS)
```
your-domain.com {
    reverse_proxy localhost:8000
}
```

### 추천 호스팅 옵션
| 호스팅 | 강점 | 비용 |
|---|---|---|
| **Railway** | Dockerfile 그대로 인식. 1-click 배포. | 월 $5~ |
| **Fly.io** | 글로벌 엣지. `fly launch` 한 줄. | 무료 티어 있음 |
| **Render** | Git push로 자동 배포. | 무료 티어 (잠자기 있음) |
| **AWS Lightsail / 네이버클라우드 / KT클라우드** | 한국 리전, VPS | 월 $5~ |

### Railway 예시 (가장 빠름)
1. GitHub에 push
2. railway.app → **New Project → Deploy from GitHub**
3. Variables 탭에 `.env` 키들 입력
4. 자동으로 빌드/배포. 도메인 자동 할당
5. 첫 배포 후 PWA `manifest`의 도메인을 그 URL로 맞춰 두면 끝

### 배포 후 체크리스트
- [ ] `https://도메인/api/health` 200 OK
- [ ] `https://도메인/api/external/status` 에 `law: live-api`, `kcsc: live-api` 표시
- [ ] 앱 접속 → 통합검색에서 ① 회사 ② 법령 ③ KCSC ④ AI 모두 응답
- [ ] 설정에서 Gemini 키 저장 → AI 패널에 `내 키` 배지 노출 확인
- [ ] 설정에서 Admin Token 저장 → 문서 업로드/데이터 등록 동작 확인
- [ ] Android Chrome에서 **앱 설치** → 홈 화면 아이콘 실행 확인

---

## 4. 자주 만나는 문제

| 증상 | 원인 / 조치 |
|---|---|
| AI 패널에 `local-summary-fallback` | 사용자 키 미입력 + 서버 .env에도 키 없음. 설정에 본인 키 넣거나 서버 .env에 GEMINI_API_KEY 추가 |
| 문서 업로드/데이터 등록이 `401` | 설정 화면의 Admin Token이 서버 `ADMIN_TOKEN`과 다름 |
| 문서 업로드/데이터 등록이 `503` | 서버 `backend/.env`에 `ADMIN_TOKEN`이 비어 있음 |
| KCSC가 `live-api-empty` 경고 | KCSC 인증키 만료. https://www.kcsc.re.kr/support/api 에서 인증키 갱신 |
| 법령이 항상 같은 2건만 | 어댑터가 stub 모드 — `LAW_API_BASE_URL`/`LAW_API_KEY` 누락. `.env` 확인 |
| 앱이 PWA 설치 안내를 안 띄움 | https 필요 (localhost는 예외). Caddy/nginx 등으로 HTTPS 적용 |
| iOS Safari에서 키 입력이 풀림 | 사파리 비공개 모드는 localStorage가 휘발성 — 일반 모드 사용 |
