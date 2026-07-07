/**
 * SearchPage — 회사 표준지침 통합 검색.
 *
 * 우선순위: ① 회사 표준(로컬 JSON + RAG 인덱스 PDF) ② KCSC 참고 ③ AI 답변.
 * 결과는 모듈 레벨 캐시에 저장되어 PDF 뷰어를 다녀와도(언마운트 후 복귀)
 * Gemini/KCSC API 를 재호출하지 않는다. 새로고침 시 초기화된다.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { NavLink, useParams, useSearchParams } from 'react-router-dom';
import { LAW_URL, apiUrl, fetchJson, pdfViewerLink } from '../lib/api';
import { IcoSparkles } from '../lib/icons';

// query → { ai, kcsc, rag } 각 상태 객체 (status/items/result/error)
const searchCache = new Map();

const IDLE_LIST = { status: 'idle', items: [], error: '' };
const IDLE_AI = { status: 'idle', result: null, error: '' };

/** 로컬 JSON 표준 항목 단순 부분일치 필터. */
function filterLocalItems(items, query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return items.filter((item) => {
    const hay = [item.id, item.category, item.section, item.title, item.summary, item.body, ...(item.keywords || [])]
      .join(' ')
      .toLowerCase();
    return hay.includes(q);
  });
}

export default function SearchPage({ appState }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQ = (searchParams.get('q') || '').trim();

  // 캐시 히트면 API 호출 없이 이전 결과로 초기화
  const cached = initialQ ? searchCache.get(initialQ) : null;

  const [query, setQuery] = useState(initialQ);
  const [submitted, setSubmitted] = useState(cached ? initialQ : '');
  const [kcscState, setKcscState] = useState(cached?.kcsc ?? IDLE_LIST);
  const [aiState, setAiState] = useState(cached?.ai ?? IDLE_AI);
  const [ragState, setRagState] = useState(cached?.rag ?? IDLE_LIST);

  const companyResults = useMemo(
    () => filterLocalItems(appState.items, submitted).slice(0, 8),
    [appState.items, submitted],
  );

  const runSearch = useCallback(async (rawQuery) => {
    const q = (rawQuery ?? query).trim();
    if (q.length < 2) return;
    setSubmitted(q);
    setQuery(q);
    if (searchParams.get('q') !== q) setSearchParams({ q }, { replace: true });

    if (searchCache.has(q)) {
      const hit = searchCache.get(q);
      setKcscState(hit.kcsc);
      setAiState(hit.ai);
      setRagState(hit.rag);
      return;
    }

    const loadingList = { status: 'loading', items: [], error: '' };
    const loadingAi = { status: 'loading', result: null, error: '' };
    setKcscState(loadingList);
    setAiState(loadingAi);
    setRagState(loadingList);

    // 세 요청이 각자 완료될 때마다 부분 갱신 후 캐시 저장
    const partial = { kcsc: loadingList, ai: loadingAi, rag: loadingList };
    const saveCache = () => searchCache.set(q, { ...partial });

    fetchJson('/api/external/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q, sources: ['kcsc'], limit: 5 }),
    }).then((data) => {
      const items = (data.items || []).filter((it) => (it.source || '').toLowerCase() === 'kcsc');
      partial.kcsc = { status: 'ready', items, error: '' };
      setKcscState(partial.kcsc); saveCache();
    }).catch(() => {
      partial.kcsc = { status: 'error', items: [], error: 'KCSC 검색에 연결할 수 없습니다.' };
      setKcscState(partial.kcsc); saveCache();
    });

    fetchJson('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, top_k: 5 }),
    }).then((data) => {
      partial.ai = { status: 'ready', result: data, error: '' };
      setAiState(partial.ai); saveCache();
    }).catch(() => {
      partial.ai = { status: 'error', result: null, error: 'AI 답변을 가져올 수 없습니다.' };
      setAiState(partial.ai); saveCache();
    });

    fetchJson(`/api/rag/search?q=${encodeURIComponent(q)}&limit=5`)
      .then((data) => {
        partial.rag = { status: 'ready', items: data.results || [], error: '' };
        setRagState(partial.rag); saveCache();
      })
      .catch(() => {
        partial.rag = { status: 'ready', items: [], error: '' };
        setRagState(partial.rag); saveCache();
      });
  }, [query, searchParams, setSearchParams]);

  // URL ?q= 변경(칩 클릭·뒤로가기) 처리 — 캐시 우선, 새 검색어만 API 호출
  useEffect(() => {
    const urlQ = (searchParams.get('q') || '').trim();
    if (urlQ.length < 2) return;
    if (searchCache.has(urlQ)) {
      const hit = searchCache.get(urlQ);
      setSubmitted(urlQ);
      setQuery(urlQ);
      setKcscState(hit.kcsc);
      setAiState(hit.ai);
      setRagState(hit.rag);
      return;
    }
    if (urlQ !== submitted) runSearch(urlQ);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const hasSubmitted = submitted.length >= 2;

  return (
    <section className="stack">
      <div className="page-header">
        <NavLink className="back-link" to="/">← 홈</NavLink>
        <h2>회사 표준지침 검색</h2>
      </div>

      <form className="search-form" onSubmit={(e) => { e.preventDefault(); runSearch(); }}>
        <div className="search-row">
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="예: 배관 지지 기준, 보온 두께" autoFocus />
          <button className="search-submit" type="submit" disabled={query.trim().length < 2}>검색</button>
        </div>
      </form>

      {!hasSubmitted ? (
        <div className="empty-hint">검색어를 입력하면 회사 표준지침을 먼저 보여드립니다.</div>
      ) : (
        <>
          <SearchSection title="회사 표준지침" tag="내부 기준" priority={1}>
            {companyResults.length === 0 && ragState.items.length === 0 && ragState.status !== 'loading' ? (
              <div className="section-empty">
                회사 표준지침에서 직접 관련 기준을 찾지 못했습니다.<br />
                아래 KCSC 참고 기준을 확인할 수 있습니다.<br />
                <small>현장 적용 전 담당자 검토가 필요합니다.</small>
              </div>
            ) : (
              <>
                {companyResults.map((item) => (
                  <CompanyResultCard key={item.id} item={item} appState={appState} />
                ))}
                {ragState.status === 'loading' && (
                  <div className="loading-row"><span className="spinner" />표준 문서 검색 중...</div>
                )}
                {ragState.items.map((chunk) => (
                  <RagChunkCard key={chunk.id} chunk={chunk} />
                ))}
              </>
            )}
          </SearchSection>

          <SearchSection title="KCSC 참고 기준" tag="국가건설기준센터" priority={2} note="KCSC는 참고 기준입니다. 현장 적용은 회사 표준지침과 계약도서를 우선 확인하세요.">
            {kcscState.status === 'loading' ? (
              <div className="loading-row"><span className="spinner" />검색 중...</div>
            ) : kcscState.status === 'error' ? (
              <div className="section-empty">{kcscState.error}</div>
            ) : kcscState.items.length === 0 ? (
              <div className="section-empty">관련 KCSC 참고 기준을 찾지 못했습니다.</div>
            ) : kcscState.items.map((item) => (
              <KcscCard key={item.id} item={item} />
            ))}
          </SearchSection>

          <a className="law-link-row" href={LAW_URL} target="_blank" rel="noreferrer">
            <span>법제처 AI 법령검색 바로가기</span>
            <span>법령은 공식 사이트에서 확인 ↗</span>
          </a>

          <AiAnswerPanel state={aiState} />
        </>
      )}
    </section>
  );
}

function SearchSection({ title, tag, priority, note, children }) {
  return (
    <details className="search-section" open>
      <summary className="search-section-head">
        <span className="section-priority">{priority}</span>
        <strong>{title}</strong>
        {tag && <span className="section-tag">{tag}</span>}
        <span className="section-caret">›</span>
      </summary>
      <div className="search-section-body">
        {children}
        {note && <p className="section-note">{note}</p>}
      </div>
    </details>
  );
}

function CompanyResultCard({ item, appState }) {
  const pdfUrl = item.pdf_url ? apiUrl(item.pdf_url) : null;
  const viewerLink = pdfUrl ? pdfViewerLink(pdfUrl, item.pdf_page, item.title) : null;

  return (
    <div className="result-card company-card">
      <div className="card-meta">
        <span>{item.category}</span>
        {item.section && <span>{item.section}</span>}
        {appState.settings?.showIds && <span>{item.id}</span>}
      </div>
      <NavLink to={`/item/${item.id}`} className="card-title">{item.title}</NavLink>
      <p className="card-summary">{item.summary}</p>
      {item.pdf_page && <p className="card-page">p.{item.pdf_page}</p>}
      <div className="card-actions">
        {viewerLink && <NavLink className="btn-pdf" to={viewerLink}>PDF 보기</NavLink>}
      </div>
    </div>
  );
}

/** 청크 텍스트에서 카드 제목 후보를 추출한다 (장/절 패턴 → 페이지 마커 직후 → 첫 60자). */
function extractChunkTitle(text) {
  if (!text) return '';
  const clean = text.replace(/\s+/g, ' ').trim();

  const sectionMatch = clean.match(/(\d{1,2}(?:[-.]\d{1,2}){0,2})\s+([가-힣A-Za-z][^[\d\n]{2,40})/);
  if (sectionMatch) return `${sectionMatch[1]} ${sectionMatch[2].trim()}`.slice(0, 60);

  const afterPage = clean.match(/\[p\.\d+\]\s*([^[\n]{4,60})/);
  if (afterPage) return afterPage[1].trim().slice(0, 60);

  return clean.slice(0, 60);
}

function RagChunkCard({ chunk }) {
  const pdfUrl = chunk.pdf_url ? apiUrl(chunk.pdf_url) : null;
  const viewerLink = pdfUrl ? pdfViewerLink(pdfUrl, chunk.page_start, chunk.document_title) : null;
  const structured = [chunk.chapter, chunk.section, chunk.clause].filter(Boolean).join(' > ');
  const cardTitle = structured || extractChunkTitle(chunk.text) || `청크 #${chunk.chunk_index}`;
  const preview = (chunk.text || '').slice(0, 180);

  return (
    <div className="result-card company-card">
      <div className="card-meta">
        <span>PDF 표준</span>
        {chunk.page_start && <span>p.{chunk.page_start}</span>}
      </div>
      <strong className="card-title">{cardTitle}</strong>
      <p className="card-summary">{preview}…</p>
      <div className="card-actions">
        {viewerLink && <NavLink className="btn-pdf" to={viewerLink}>PDF 보기</NavLink>}
      </div>
    </div>
  );
}

function KcscCard({ item }) {
  const sourceUrl = item.source_url || item.official_url;
  return (
    <div className="result-card kcsc-card">
      <div className="card-meta">
        <span>KCSC</span>
        {item.category && <span>{item.category}</span>}
        {item.id && <span>{item.id}</span>}
      </div>
      <strong className="card-title">{item.title}</strong>
      {item.summary && <p className="card-summary">{item.summary}</p>}
      {sourceUrl && (
        <div className="card-actions">
          <a className="btn-outline" href={sourceUrl} target="_blank" rel="noreferrer">원문 보기 ↗</a>
        </div>
      )}
    </div>
  );
}

function AiAnswerPanel({ state }) {
  const result = state.result;
  const docRefs = result?.document_references || [];

  return (
    <details className="ai-panel" open>
      <summary className="ai-panel-head">
        <IcoSparkles size={16} />
        <span className="section-priority ai-badge">AI</span>
        <strong>AI 답변</strong>
        <span className="section-tag">근거 기반 답변</span>
        <span className="section-caret">›</span>
      </summary>
      <div className="ai-panel-body">
        {state.status === 'loading' ? (
          <div className="loading-row"><span className="spinner" />AI가 근거를 분석하고 있습니다...</div>
        ) : state.status === 'error' ? (
          <div className="section-empty">{state.error}</div>
        ) : result ? (
          <>
            {result.provider_error && (
              <div className="notice warning">외부 AI 호출 실패로 로컬 근거 요약을 표시했습니다.</div>
            )}
            <pre className="ai-answer-text">{result.answer}</pre>
            <p className="ai-disclaimer">AI 답변은 참고용으로 활용하세요.</p>
            {docRefs.length > 0 && (
              <div className="ai-refs">
                {docRefs.map((ref) => {
                  const location = [ref.chapter, ref.section, ref.clause].filter(Boolean).join(' > ');
                  return (
                    <div key={ref.id} className="ai-ref-card">
                      <div className="card-meta">
                        <strong>{ref.document_title}</strong>
                        {ref.version && <span>{ref.version}</span>}
                      </div>
                      {location && <p className="ref-location">{location}</p>}
                    </div>
                  );
                })}
              </div>
            )}
          </>
        ) : (
          <div className="section-empty">검색어를 입력하면 AI 답변이 표시됩니다.</div>
        )}
      </div>
    </details>
  );
}

/** 로컬 JSON 표준 항목 상세 (검색 카드 제목 클릭 시). */
export function DetailPage({ appState }) {
  const { id } = useParams();
  const item = appState.items.find((entry) => entry.id === id);

  useEffect(() => {
    if (!item) return;
    appState.setRecent((current) => [item.id, ...current.filter((sid) => sid !== item.id)].slice(0, 20));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (!item) {
    return (
      <section className="stack">
        <NavLink className="back-link" to="/search">← 검색으로 돌아가기</NavLink>
        <div className="empty-hint">항목을 찾을 수 없습니다.</div>
      </section>
    );
  }

  const pdfUrl = item.pdf_url ? apiUrl(item.pdf_url) : '';
  const viewerLink = pdfUrl ? pdfViewerLink(pdfUrl, item.pdf_page, item.title) : '';

  return (
    <section className="stack">
      <NavLink className="back-link" to="/search">← 검색으로 돌아가기</NavLink>
      <article className="detail-card">
        <div className="card-meta">
          <span>{item.category}</span>
          {item.section && <span>{item.section}</span>}
        </div>
        <h2>{item.title}</h2>
        <p className="summary">{item.summary}</p>
        {viewerLink ? (
          <div className="pdf-area">
            <NavLink className="btn-pdf large" to={viewerLink}>
              PDF 보기{item.pdf_page ? ` · p.${item.pdf_page}` : ''}
            </NavLink>
          </div>
        ) : item.body ? (
          <p className="body-text">{item.body}</p>
        ) : null}
      </article>
    </section>
  );
}
