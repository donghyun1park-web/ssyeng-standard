/**
 * ChecklistPages — 공종별 체크리스트 (현장 단위 공유).
 *
 * 같은 현장을 선택한 인원끼리 항목·체크 상태를 공유한다.
 * 현장 미선택 상태의 쓰기는 백엔드에서 400으로 차단되며,
 * 프론트에서도 로그인 현장을 기본값으로 강제한다.
 */
import { useCallback, useEffect, useState } from 'react';
import { NavLink, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { TRADE_LIST, apiUrl, fetchJson } from '../lib/api';
import { STORAGE_KEYS, readUserId } from '../lib/storage';
import { TRADE_ICONS_SVG } from '../lib/icons';

// 체크 상태 순환: 토글 클릭마다 다음 상태로 이동 (백엔드 Literal과 일치)
const STATUS_CYCLE = ['미체크', '적합', '해당없음', '부적합'];
const STATUS_ICONS = { '미체크': '□', '적합': '✓', '해당없음': '△', '부적합': '✕' };
const STATUS_CLASS = { '미체크': '', '적합': 'check-ok', '해당없음': 'check-na', '부적합': 'check-ng' };

/** 선택 현장을 localStorage 에 유지하는 훅 — 로그인 현장이 기본값. */
function useSelectedSite(loginSiteName) {
  const [siteId, setSiteId] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEYS.checklistSite) || loginSiteName || '';
    } catch {
      return loginSiteName || '';
    }
  });
  const update = useCallback((next) => {
    setSiteId(next);
    try {
      if (next) localStorage.setItem(STORAGE_KEYS.checklistSite, next);
      else localStorage.removeItem(STORAGE_KEYS.checklistSite);
    } catch { /* ignore */ }
  }, []);
  return [siteId, update];
}

export function ChecklistPage({ appState }) {
  const navigate = useNavigate();
  const [checklists, setChecklists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sites, setSites] = useState([]);
  const loginSiteName = appState.currentUser?.site_name || '';
  const [siteId, setSiteId] = useSelectedSite(loginSiteName);

  // 현장이 비면 로그인 현장으로 강제 (default 공용공간 혼입 방지)
  useEffect(() => {
    if (!siteId && loginSiteName) setSiteId(loginSiteName);
  }, [siteId, loginSiteName, setSiteId]);

  const load = useCallback(() => {
    if (!siteId) { setLoading(false); return; }
    setLoading(true);
    fetchJson(`/api/checklists?site_id=${encodeURIComponent(siteId)}`).then((data) => {
      setChecklists(data.checklists || []);
    }).catch(() => {
      setChecklists(TRADE_LIST.map((trade) => ({ trade, item_count: 0, checked_count: 0, has_items: false })));
    }).finally(() => setLoading(false));
  }, [siteId]);

  useEffect(() => { load(); }, [load]);

  // 현장 선택지 = 로그인 마스터 현장(auth) + 직접 등록 현장(site_issues) 병합
  useEffect(() => {
    Promise.all([
      fetch(apiUrl('/api/auth/sites')).then((r) => r.json()).catch(() => ({ sites: [] })),
      fetchJson('/api/sites').catch(() => ({ sites: [] })),
    ]).then(([authData, siteData]) => {
      const masterSites = (authData.sites || []).map((name) => ({ id: name, label: name }));
      const extraSites = (siteData.sites || [])
        .filter((s) => !masterSites.some((m) => m.id === s.site_name))
        .map((s) => ({ id: s.id, label: s.site_name }));
      setSites([...masterSites, ...extraSites]);
    });
  }, []);

  return (
    <section className="stack">
      <div className="page-header">
        <h2>체크리스트</h2>
        <span className="page-subtitle">공종별 · 현장별 점검 (현장 인원 공유)</span>
      </div>
      {appState.currentUser && (
        <p className="info-msg" style={{ margin: '0 0 8px' }}>
          <strong>{appState.currentUser.name}</strong> · 현장: <strong>{siteId || '선택 필요'}</strong>
        </p>
      )}

      <div className="settings-card">
        <label className="field-label">현장 선택</label>
        <select value={siteId} onChange={(e) => setSiteId(e.target.value)}>
          {!siteId && <option value="">-- 현장을 선택하세요 --</option>}
          {sites.map((s) => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
        <p className="settings-note">같은 현장을 선택한 인원이 체크리스트를 공유합니다.</p>
        {siteId && (
          <button
            className="btn btn-outline"
            style={{ marginTop: 10 }}
            onClick={() => window.open(apiUrl(`/api/checklists/export?site_id=${encodeURIComponent(siteId)}`), '_blank')}
          >
            엑셀로 내보내기
          </button>
        )}
      </div>

      {!siteId ? (
        <div className="empty-hint">현장을 먼저 선택하면 공종별 체크리스트가 표시됩니다.</div>
      ) : loading ? (
        <div className="loading-row"><span className="spinner" />불러오는 중...</div>
      ) : TRADE_LIST.map((trade) => {
        const info = checklists.find((c) => c.trade === trade) || { item_count: 0, checked_count: 0, has_items: false };
        const target = `/checklist/${encodeURIComponent(trade)}?site=${encodeURIComponent(siteId)}`;
        const Icon = TRADE_ICONS_SVG[trade];
        return (
          <div className="trade-card" key={trade} onClick={() => navigate(target)}>
            <div className="trade-icon">{Icon ? <Icon size={22} /> : '📋'}</div>
            <div style={{ flex: 1 }}>
              <div className="trade-name">{trade}</div>
              <div className="trade-status">
                {info.has_items ? `${info.checked_count} / ${info.item_count} 항목 완료` : '항목 없음 · 템플릿 불러오기 가능'}
              </div>
            </div>
            <div className="trade-progress">
              <div className="trade-num mono">{info.has_items ? `${info.checked_count} / ${info.item_count}` : '—'}</div>
              {info.item_count > 0 && (
                <div className="bar"><i style={{ width: `${Math.round(info.checked_count / info.item_count * 100)}%` }} /></div>
              )}
            </div>
          </div>
        );
      })}
    </section>
  );
}

export function ChecklistDetailPage() {
  const { trade } = useParams();
  const [searchParams] = useSearchParams();
  const decodedTrade = decodeURIComponent(trade);
  const siteId = searchParams.get('site') || '';
  const [items, setItems] = useState([]);
  const [records, setRecords] = useState({});
  const [templateAvailable, setTemplateAvailable] = useState(false);
  const [templateCount, setTemplateCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [addText, setAddText] = useState('');
  const [addPage, setAddPage] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState('');
  const [editPage, setEditPage] = useState('');
  const userId = readUserId();

  const load = useCallback(() => {
    setLoading(true);
    const q = siteId ? `?site_id=${encodeURIComponent(siteId)}` : '';
    fetchJson(`/api/checklists/${encodeURIComponent(decodedTrade)}${q}`).then((data) => {
      setItems(data.items || []);
      setRecords(data.records || {});
      setTemplateAvailable(!!data.template_available);
      setTemplateCount(data.template_count || 0);
      setError('');
    }).catch(() => setError('체크리스트를 불러올 수 없습니다.')).finally(() => setLoading(false));
  }, [decodedTrade, siteId]);

  useEffect(() => { load(); }, [load]);

  const getStatus = (itemId) => records[itemId]?.status || '미체크';

  const cycleStatus = async (itemId) => {
    const current = getStatus(itemId);
    const next = STATUS_CYCLE[(STATUS_CYCLE.indexOf(current) + 1) % STATUS_CYCLE.length];
    // 낙관적 업데이트 — 실패 시 에러만 표시 (다음 load에서 서버 상태로 복원됨)
    setRecords((r) => ({ ...r, [itemId]: { ...(r[itemId] || {}), status: next, item_id: itemId } }));
    try {
      await fetchJson('/api/checklists/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trade: decodedTrade, item_id: itemId, status: next, memo: records[itemId]?.memo || '', site_id: siteId }),
      });
    } catch {
      setError('상태 저장 실패 — 서버 연결을 확인하세요.');
    }
  };

  const loadTemplate = async () => {
    setBusy(true); setError('');
    try {
      await fetchJson('/api/checklists/load-template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ site_id: siteId, trade: decodedTrade }),
      });
      await load();
    } catch (err) {
      setError(`템플릿 불러오기 실패: ${err.message}`);
    } finally { setBusy(false); }
  };

  const addItem = async (e) => {
    e.preventDefault();
    if (!addText.trim()) return;
    setBusy(true); setError('');
    try {
      await fetchJson('/api/checklists/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ site_id: siteId, trade: decodedTrade, text: addText, related_page: addPage }),
      });
      setAddText(''); setAddPage('');
      await load();
    } catch (err) {
      setError(`항목 추가 실패: ${err.message}`);
    } finally { setBusy(false); }
  };

  const startEdit = (item) => {
    setEditingId(item.id);
    setEditText(item.text);
    setEditPage(item.related_page || '');
  };

  const saveEdit = async () => {
    if (!editText.trim()) return;
    setBusy(true); setError('');
    try {
      await fetchJson(`/api/checklists/items/${encodeURIComponent(editingId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: editText, related_page: editPage }),
      });
      setEditingId(null);
      await load();
    } catch (err) {
      setError(`수정 실패: ${err.message}`);
    } finally { setBusy(false); }
  };

  const deleteItem = async (itemId) => {
    if (!window.confirm('이 항목을 삭제할까요? 체크 기록도 함께 삭제됩니다.')) return;
    setBusy(true); setError('');
    try {
      await fetchJson(`/api/checklists/items/${encodeURIComponent(itemId)}`, { method: 'DELETE' });
      await load();
    } catch (err) {
      setError(`삭제 실패: ${err.message}`);
    } finally { setBusy(false); }
  };

  const checked = items.filter((item) => ['적합', '해당없음'].includes(getStatus(item.id))).length;

  return (
    <section className="stack">
      <div className="page-header">
        <NavLink className="back-link" to="/checklist">← 목록</NavLink>
        <h2>{decodedTrade}</h2>
        {items.length > 0 && (
          <span className="checklist-progress-badge">{checked} / {items.length}</span>
        )}
      </div>

      <div className="settings-note">
        사용자: <strong>{userId || 'anonymous'}</strong> · 현장: <strong>{siteId || '기본'}</strong>
      </div>

      {loading ? (
        <div className="loading-row"><span className="spinner" />불러오는 중...</div>
      ) : (
        <>
          {error && <div className="error-box">{error}</div>}

          {items.length === 0 && (
            <div className="settings-card">
              <h3>항목이 없습니다</h3>
              {templateAvailable && templateCount > 0 && (
                <>
                  <p className="settings-note">{templateCount}개의 기본 점검 항목을 내 리스트로 복사할 수 있습니다.</p>
                  <button className="btn-primary" disabled={busy} onClick={loadTemplate}>
                    기본 템플릿 불러오기 ({templateCount}개)
                  </button>
                </>
              )}
              <p className="settings-note" style={{ marginTop: 8 }}>또는 아래에서 직접 항목을 추가하세요.</p>
            </div>
          )}

          {items.length > 0 && (
            <div className="progress-bar-wrap">
              <div className="progress-bar" style={{ width: `${Math.round((checked / items.length) * 100)}%` }} />
            </div>
          )}

          <div className="check-items">
            {items.map((item) => {
              const status = getStatus(item.id);
              if (editingId === item.id) {
                return (
                  <div className="check-item" key={item.id}>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <input value={editText} onChange={(e) => setEditText(e.target.value)} placeholder="항목 내용" />
                      <input value={editPage} onChange={(e) => setEditPage(e.target.value)} placeholder="관련 페이지 (선택)" />
                      <div className="button-row">
                        <button className="btn-primary" disabled={busy} onClick={saveEdit}>저장</button>
                        <button className="btn-ghost" onClick={() => setEditingId(null)}>취소</button>
                      </div>
                    </div>
                  </div>
                );
              }
              return (
                <div className={`check-item ${STATUS_CLASS[status]}`} key={item.id}>
                  <button className="check-status-btn" onClick={() => cycleStatus(item.id)}>
                    {STATUS_ICONS[status]}
                  </button>
                  <span className="check-text">{item.text}</span>
                  {item.related_page && (
                    <span className="check-page" title={`관련 기준 p.${item.related_page}`}>p.{item.related_page}</span>
                  )}
                  <button className="btn-ghost" title="수정" onClick={() => startEdit(item)}>✏️</button>
                  <button className="btn-ghost" title="삭제" onClick={() => deleteItem(item.id)}>🗑️</button>
                </div>
              );
            })}
          </div>

          <form className="settings-card" onSubmit={addItem}>
            <h3>+ 항목 추가</h3>
            <input value={addText} onChange={(e) => setAddText(e.target.value)} placeholder="점검 항목 내용을 입력하세요" />
            <input value={addPage} onChange={(e) => setAddPage(e.target.value)} placeholder="관련 페이지 (선택)" style={{ marginTop: 6 }} />
            <button type="submit" className="btn-primary" disabled={busy || !addText.trim()} style={{ marginTop: 8 }}>
              {busy ? '저장 중...' : '추가'}
            </button>
          </form>

          {items.length > 0 && (
            <div className="check-legend">
              <span>□ 미체크</span><span className="check-ok">✓ 적합</span>
              <span className="check-na">△ 해당없음</span><span className="check-ng">✕ 부적합</span>
            </div>
          )}
        </>
      )}
    </section>
  );
}
