"""
synonyms.py — 검색어 동의어 확장 (RAG 검색 / 검색품질 서비스 공용).

search_synonyms.json 을 로드해 '행거'↔'지지금구', '보온'↔'단열' 같은
현장 용어 변형을 검색에 반영한다. document_rag 와 search_quality 가
공통으로 사용하되, 서로를 import 하지 않도록 독립 모듈로 분리했다.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
SYNONYM_PATH = DATA_DIR / "search_synonyms.json"

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_+#./-]+")

# 파일이 없을 때 사용하는 기본 사전. search_synonyms.json 이 우선한다.
DEFAULT_SYNONYMS: dict[str, list[str]] = {
    "펌프": ["급수펌프", "순환펌프", "가압펌프", "pump"],
    "급수": ["상수", "급수배관", "급수펌프"],
    "배관": ["파이프", "관", "pipe", "배관공사"],
    "보온": ["단열", "결로방지", "보냉", "insulation"],
    "소방": ["스프링클러", "옥내소화전", "소화배관"],
    "위생": ["오수", "배수", "통기관", "위생기구"],
    "환기": ["덕트", "송풍기", "배기", "급기"],
    "수압": ["수압시험", "기밀시험", "압력시험"],
    "밸브": ["차단밸브", "체크밸브", "감압밸브", "valve"],
    "동파": ["동결방지", "보온", "열선"],
    # 현장 용어 변형 보강
    "지지": ["지지금구", "행거", "서포트", "지지대", "받침"],
    "행거": ["지지", "지지금구", "hanger", "달대"],
    "구배": ["기울기", "경사", "물매", "slope"],
    "슬리브": ["관통부", "관통슬리브", "sleeve"],
    "관통부": ["슬리브", "관통슬리브", "방화충전"],
    "신축이음": ["익스팬션", "expansion", "신축조인트"],
    "방화댐퍼": ["fd", "방화댐파", "화재댐퍼"],
    "그릴": ["디퓨저", "레지스터", "취출구"],
    "게이지": ["압력계", "gauge", "계기"],
    "플랜지": ["flange", "이음쇠"],
}


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if len(t.strip()) >= 2]


def load_synonyms() -> dict[str, list[str]]:
    """search_synonyms.json 을 로드. 없으면 기본 사전을 파일로 생성 후 반환."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SYNONYM_PATH.exists():
        try:
            SYNONYM_PATH.write_text(
                json.dumps(DEFAULT_SYNONYMS, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
        return dict(DEFAULT_SYNONYMS)
    try:
        data = json.loads(SYNONYM_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {
                str(k): [str(v) for v in vals]
                for k, vals in data.items()
                if isinstance(vals, list)
            }
    except Exception:
        pass
    return dict(DEFAULT_SYNONYMS)


def synonym_terms(tokens: list[str], synonyms: dict[str, list[str]] | None = None) -> list[str]:
    """원본 토큰 목록에 대해, 추가로 검색에 넣을 동의어 토큰을 반환한다.

    - 정방향(사전 키 → 값) + 역방향(값 → 키) 모두 확장
    - 소문자화·중복 제거
    - 원본 토큰은 제외 (호출부에서 원본은 이미 처리하므로)
    """
    syn = synonyms if synonyms is not None else load_synonyms()
    originals = {t.lower() for t in tokens}
    expanded: list[str] = []
    seen: set[str] = set(originals)

    # 역방향 조회를 위한 인덱스: 값(소문자) → 키
    reverse_index: dict[str, list[str]] = {}
    for key, vals in syn.items():
        for v in vals:
            reverse_index.setdefault(v.lower(), []).append(key)

    for token in originals:
        candidates: list[str] = []
        candidates.extend(syn.get(token, []))
        candidates.extend(reverse_index.get(token, []))
        for cand in candidates:
            c = cand.lower()
            if c and c not in seen:
                seen.add(c)
                expanded.append(c)
    return expanded
