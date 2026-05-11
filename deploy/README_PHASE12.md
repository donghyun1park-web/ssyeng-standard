# Phase 12 운영 전 최종 안정화

## 목적
이 단계는 새 기능 추가보다 현장 배포 전 안정성 검증을 우선합니다.

추가된 항목:
- `/api/diagnostics/status`
- `/api/diagnostics/checks`
- 프론트 `최종 진단` 화면
- Windows 설치/실행/빌드/헬스체크 스크립트
- Dockerfile / docker-compose.yml
- FastAPI에서 React `dist` 정적 파일 제공

## 개발 실행
```powershell
scripts\install-dev.ps1
scripts\start-dev.ps1
```

## 운영 빌드 검증
```powershell
scripts\build-prod.ps1
```

## Docker 실행
```powershell
copy backend\.env.example backend\.env
notepad backend\.env
docker compose up --build -d
```

접속:
- http://localhost:8000
- http://localhost:8000/docs
- http://localhost:8000/api/diagnostics/checks

## 운영 전 필수 확인
1. `backend/.env` 생성
2. `ADMIN_TOKEN` 설정
3. `KCSC_API_KEY` 설정
4. 필요 시 `NVIDIA_API_KEY` 설정
5. `npm run build` 완료 후 `dist/index.html` 존재 확인
6. `/api/diagnostics/checks`에서 error가 0인지 확인
