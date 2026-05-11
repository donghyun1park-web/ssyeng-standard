import os

from pydantic import BaseModel, Field
from fastapi import APIRouter, Header
from dotenv import load_dotenv

from app.services.document_rag import DocumentRagStore
from app.services.gemini_client import GeminiClient, GeminiClientError, GeminiConfigurationError
from app.services.nvidia_nim_client import NvidiaNimClient, NimClientError, NimConfigurationError
from app.services.standard_repository import StandardRepository


load_dotenv()
router = APIRouter(tags=["ask"])
repo = StandardRepository()
rag_store = DocumentRagStore()
gemini = GeminiClient()
nim = NvidiaNimClient()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    category: str | None = None
    top_k: int = Field(default=5, ge=1, le=10)


class AskResponse(BaseModel):
    ok: bool
    mode: str
    question: str
    answer: str
    references: list[dict]
    document_references: list[dict] = Field(default_factory=list)
    model: str | None = None
    provider_error: str | None = None


def _reference_payload(items: list[dict]) -> list[dict]:
    return [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "category": item.get("category"),
            "section": item.get("section"),
            "summary": item.get("summary"),
        }
        for item in items
    ]


def _build_context(items: list[dict]) -> str:
    blocks = []
    for idx, item in enumerate(items, start=1):
        checklist = ", ".join(item.get("checklist", []))
        blocks.append(
            f"[근거 {idx}]\n"
            f"ID: {item.get('id')}\n"
            f"분류: {item.get('category')} / {item.get('section')}\n"
            f"제목: {item.get('title')}\n"
            f"요약: {item.get('summary')}\n"
            f"본문: {item.get('body')}\n"
            f"체크리스트: {checklist}"
        )
    return "\n\n".join(blocks)


def _requested_provider() -> str:
    provider = os.getenv("AI_PROVIDER", "auto").strip().lower()
    aliases = {
        "": "auto",
        "google": "gemini",
        "google-gemini": "gemini",
        "nim": "nvidia",
        "nvidia-nim": "nvidia",
    }
    return aliases.get(provider, provider)


def _provider_mode(provider: str | None) -> str:
    if provider == "gemini":
        return "gemini"
    if provider == "nvidia":
        return "nvidia-nim"
    return "local-summary-fallback"


def _provider_label(provider: str | None) -> str:
    if provider == "gemini":
        return "Gemini API"
    if provider == "nvidia":
        return "NVIDIA NIM"
    return "외부 AI"


def _select_ai_provider() -> tuple[str | None, object | None, str | None]:
    provider = _requested_provider()

    if provider == "gemini":
        if gemini.is_configured:
            return "gemini", gemini, None
        return None, None, "AI_PROVIDER=gemini 이지만 GEMINI_API_KEY 또는 GEMINI_MODEL이 설정되지 않았습니다."

    if provider == "nvidia":
        if nim.is_configured:
            return "nvidia", nim, None
        return None, None, "AI_PROVIDER=nvidia 이지만 NVIDIA_API_KEY 또는 NVIDIA_MODEL이 설정되지 않았습니다."

    if provider == "auto":
        if gemini.is_configured:
            return "gemini", gemini, None
        if nim.is_configured:
            return "nvidia", nim, None
        return None, None, "Gemini/NVIDIA API Key가 없어 로컬 근거 요약 모드로 동작합니다."

    return None, None, f"지원하지 않는 AI_PROVIDER={provider} 값입니다. gemini, nvidia, auto 중 하나를 사용하세요."


def _local_answer(question: str, items: list[dict], reason: str | None = None) -> str:
    lead = reason or "외부 AI provider가 설정되지 않아 로컬 근거 요약 모드로 답변합니다."
    if not items:
        return (
            f"{lead}\n\n"
            "현재 로컬 지침서에서 직접 관련 항목을 찾지 못했습니다. "
            "검색어를 더 구체화하거나 회사 지침서 데이터를 추가해야 합니다."
        )
    lines = [
        lead,
        "",
        "관련 기준 요약:",
    ]
    for item in items:
        lines.append(f"- {item.get('title')}: {item.get('summary')}")
    lines.extend([
        "",
        "현장 적용 시 위 항목의 상세 본문과 체크리스트를 함께 확인하세요.",
        "GEMINI_API_KEY를 설정하면 같은 근거를 바탕으로 Gemini가 자연어 답변을 생성합니다.",
    ])
    return "\n".join(lines)


def _fallback_response(
    *,
    question: str,
    matched_items: list[dict],
    references: list[dict],
    document_references: list[dict],
    reason: str,
    provider_error: str | None = None,
) -> AskResponse:
    suffix = "\n\n문서 RAG 검색 결과도 확인되었습니다." if document_references else ""
    return AskResponse(
        ok=True,
        mode="local-summary-fallback",
        question=question,
        answer=_local_answer(question, matched_items, reason) + suffix,
        references=references,
        document_references=document_references,
        model=None,
        provider_error=provider_error,
    )


@router.get("/ask/status")
def ask_status():
    selected_provider, selected_client, fallback_reason = _select_ai_provider()
    return {
        "ok": True,
        "ai_provider": _requested_provider(),
        "gemini_configured": gemini.is_configured,
        "nim_configured": nim.is_configured,
        "nvidia_configured": nim.is_configured,
        # 클라이언트가 X-User-Gemini-Key 헤더로 본인 키를 보낼 수 있는지 알려준다.
        "user_key_supported": True,
        "user_key_header": "X-User-Gemini-Key",
        "base_url": getattr(selected_client, "base_url", None) if selected_client else None,
        "model": getattr(selected_client, "model", None) if selected_client else None,
        "mode": _provider_mode(selected_provider),
        "fallback_reason": fallback_reason,
        "providers": {
            "gemini": {
                "configured": gemini.is_configured,
                "base_url": gemini.base_url,
                "model": gemini.model if gemini.model else None,
            },
            "nvidia": {
                "configured": nim.is_configured,
                "base_url": nim.base_url,
                "model": nim.model if nim.model else None,
            },
        },
        "rag": rag_store.status(),
    }


@router.post("/ask", response_model=AskResponse)
async def ask_standard(
    payload: AskRequest,
    x_user_gemini_key: str = Header(default="", alias="X-User-Gemini-Key"),
):
    question = payload.question.strip()
    user_gemini_key = (x_user_gemini_key or "").strip()
    matched_items = repo.search(query=question, category=payload.category, limit=payload.top_k)

    # 질문 전체 문장으로 검색이 약할 때 핵심 토큰 단순 재검색
    if not matched_items:
        tokens = [token for token in question.replace("?", " ").replace(",", " ").split() if len(token) >= 2]
        for token in tokens[:5]:
            matched_items = repo.search(query=token, category=payload.category, limit=payload.top_k)
            if matched_items:
                break

    references = _reference_payload(matched_items)
    document_chunks = rag_store.search(question, limit=payload.top_k)
    document_references = [
        {
            "id": chunk.get("id"),
            "document_id": chunk.get("document_id"),
            "document_title": chunk.get("document_title"),
            "filename": chunk.get("filename"),
            "chunk_index": chunk.get("chunk_index"),
            "chapter": chunk.get("chapter", ""),
            "section": chunk.get("section", ""),
            "clause": chunk.get("clause", ""),
            "page_start": chunk.get("page_start"),
            "page_end": chunk.get("page_end"),
            "pdf_url": chunk.get("pdf_url", ""),
            "version": chunk.get("version", ""),
            "score": chunk.get("score"),
            "preview": (chunk.get("text") or "")[:220],
        }
        for chunk in document_chunks
    ]

    # 사용자가 설정 화면에서 본인 Gemini 키를 입력했으면 그것을 우선 사용
    if user_gemini_key:
        selected_provider = "gemini"
        selected_client = gemini
        fallback_reason = None
    else:
        selected_provider, selected_client, fallback_reason = _select_ai_provider()

    if selected_client is None:
        return _fallback_response(
            question=question,
            matched_items=matched_items,
            references=references,
            document_references=document_references,
            reason=fallback_reason or "외부 AI provider를 사용할 수 없어 로컬 근거 요약 모드로 답변합니다.",
        )

    system_prompt = (
        "당신은 건축기계설비 현장 시공표준 검색앱의 답변 엔진입니다. "
        "반드시 제공된 회사 표준지침 근거 안에서만 답변하세요. "
        "근거가 부족하면 부족하다고 말하고 추정하지 마세요. "
        "답변은 현장 실무자가 바로 확인할 수 있도록 간결하게 작성하세요. "
        "답변 마지막에 반드시 다음 형식으로 근거를 표기하세요:\n"
        "근거: [문서명] [장/절/조항] p.[페이지번호]\n"
        "AI 답변은 참고용으로 활용하고, PDF 원문을 반드시 확인하세요."
    )
    user_prompt = (
        f"질문:\n{question}\n\n"
        f"회사 지침서 JSON 검색 근거:\n{_build_context(matched_items) if matched_items else '관련 JSON 근거 없음'}\n\n"
        f"업로드 문서 RAG 검색 근거:\n{rag_store.build_context(document_chunks) if document_chunks else '관련 업로드 문서 근거 없음'}"
    )

    chat_kwargs: dict = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 900,
    }
    if user_gemini_key and selected_provider == "gemini":
        chat_kwargs["api_key"] = user_gemini_key

    try:
        answer = await selected_client.chat(**chat_kwargs)
    except (GeminiConfigurationError, NimConfigurationError) as exc:
        return _fallback_response(
            question=question,
            matched_items=matched_items,
            references=references,
            document_references=document_references,
            reason=f"{_provider_label(selected_provider)} 설정 오류로 로컬 근거 요약 모드로 답변합니다.",
            provider_error=str(exc),
        )
    except (GeminiClientError, NimClientError) as exc:
        return _fallback_response(
            question=question,
            matched_items=matched_items,
            references=references,
            document_references=document_references,
            reason=f"{_provider_label(selected_provider)} 호출이 실패해 로컬 근거 요약 모드로 답변합니다.",
            provider_error=str(exc),
        )

    response_mode = _provider_mode(selected_provider)
    if user_gemini_key and selected_provider == "gemini":
        response_mode = "gemini-user-key"

    return AskResponse(
        ok=True,
        mode=response_mode,
        question=question,
        answer=answer,
        references=references,
        document_references=document_references,
        model=getattr(selected_client, "model", None),
    )
