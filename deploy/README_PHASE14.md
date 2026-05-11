# Phase 14 - 데이터 품질 / 검색 정확도 고도화

## 목적
현장 사용자가 회사 지침서를 검색할 때 단순 문자열 포함 검색만으로 누락되는 항목을 줄이고, 검색 결과가 왜 노출되었는지 확인할 수 있게 한다.

## 추가 기능
- 동의어 확장 검색
- 제목/키워드/요약/본문/체크리스트 필드별 가중치 검색
- 분류(category) / 목차(section) 필터
- 검색어 확장 결과 표시
- 결과별 점수 및 매칭 필드 표시
- 검색 결과 0건일 때 추천 검색어 제공
- 상위 검색 용어 진단

## 주요 API
```text
GET  /api/search-quality/status
GET  /api/search-quality/suggestions?q=펌프
GET  /api/search-quality/terms
POST /api/search-quality/search
```

## 동의어 관리
동의어 파일 위치:

```text
backend/data/search_synonyms.json
```

예시:

```json
{
  "펌프": ["급수펌프", "순환펌프", "가압펌프", "pump"],
  "보온": ["단열", "결로방지", "insulation"]
}
```

운영자가 회사 용어에 맞게 이 파일을 수정하면 검색 품질 진단 화면과 고급 검색 API에 즉시 반영된다. 운영 서버에서는 수정 후 백엔드 재시작을 권장한다.

## 화면
프론트 경로:

```text
/quality
```

홈 화면의 “검색 품질 진단” 메뉴에서 진입할 수 있다.
