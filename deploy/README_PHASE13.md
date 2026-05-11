# Phase 13 - 현장 모바일 사용성 고도화

## 목표
실제 휴대폰 현장 사용 기준으로 PWA 사용성을 보강했다.

## 추가 기능
- 현장 모바일 모드(`/field`)
- 온라인/오프라인 상태 표시
- PWA 설치 안내 카드
- Service Worker 업데이트 알림
- 빠른 검색어 버튼
- 현장 메모 localStorage 저장
- 진행 중 체크리스트 요약
- 큰 터치 영역 설정
- `/api/mobile/status` 점검 API

## 확인 URL
```text
http://localhost:8000/api/mobile/status
http://localhost:8000/api/health
http://localhost:5173/field
```

## 현장 사용 절차
1. 휴대폰 Chrome/Edge에서 앱 접속
2. 홈 화면 또는 현장 모드에서 설치 안내 확인
3. 홈 화면에 추가 또는 앱 설치
4. 자주 쓰는 기준은 즐겨찾기 등록
5. 네트워크 불안정 시 로컬 JSON/최근 항목/체크리스트로 계속 사용

## 주의
- AI/RAG/KCSC 기능은 백엔드와 네트워크가 필요하다.
- 오프라인에서는 로컬 JSON, 즐겨찾기, 최근 항목, 체크리스트, 현장 메모 중심으로 사용한다.
