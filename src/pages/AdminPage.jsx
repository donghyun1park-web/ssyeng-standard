/**
 * AdminPage — ADMIN TOKEN 보유자 전용 데이터 관리.
 * KCSC 키, 현장명 DB, 로그인 명단, 표준지침 PDF 업로드를 관리한다.
 */
import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { fetchJson, verifyAdminToken } from '../lib/api';
import { readAdminToken } from '../lib/storage';
import { DataManagementAccessCard } from './SettingsPage';

export default function AdminPage() {
  const [authorized, setAuthorized] = useState(false);
  const [authChecking, setAuthChecking] = useState(true);
  const [status, setStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [authData, setAuthData] = useState({ users: [], sites: [] });
  const [externalSettings, setExternalSettings] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [parseForm, setParseForm] = useState({ document_title: '', version: '', revision_date: '' });

  const load = async () => {
    try {
      const [statusData, docsData, authDataResp, externalSettingsResp] = await Promise.all([
        fetchJson('/api/rag/status'),
        fetchJson('/api/rag/documents'),
        fetchJson('/api/admin/auth-data'),
        fetchJson('/api/admin/external-settings'),
      ]);
      setStatus(statusData);
      setDocuments(docsData.documents || []);
      setAuthData({ users: authDataResp.users || [], sites: authDataResp.sites || [] });
      setExternalSettings(externalSettingsResp);
    } catch { setMessage('백엔드에 연결할 수 없습니다.'); }
  };

  useEffect(() => {
    verifyAdminToken(readAdminToken())
      .then(() => setAuthorized(true))
      .catch(() => setAuthorized(false))
      .finally(() => setAuthChecking(false));
  }, []);

  useEffect(() => { if (authorized) load(); }, [authorized]);

  const uploadFile = async (event, useAdvancedParser) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setLoading(true); setMessage('');
    const form = new FormData();
    form.append('file', file);
    if (useAdvancedParser) {
      form.append('document_title', parseForm.document_title || file.name.replace(/\.[^.]+$/, ''));
      form.append('version', parseForm.version);
      form.append('revision_date', parseForm.revision_date);
    } else {
      form.append('document_title', file.name.replace(/\.[^.]+$/, ''));
    }
    const endpoint = useAdvancedParser ? '/api/rag/parse-pdf' : '/api/rag/upload';
    try {
      await fetchJson(endpoint, { method: 'POST', body: form });
      setMessage(`${file.name} 문서를 인덱싱했습니다.`);
      await load();
    } catch (err) {
      setMessage(`업로드 실패: ${err.message}`);
    } finally {
      event.target.value = ''; setLoading(false);
    }
  };

  if (authChecking) {
    return <section className="stack"><div className="loading-row"><span className="spinner" />ADMIN TOKEN 확인 중...</div></section>;
  }

  if (!authorized) {
    return (
      <section className="stack">
        <div className="page-header">
          <NavLink className="back-link" to="/settings">← 설정</NavLink>
          <h2>데이터 관리</h2>
        </div>
        <div className="settings-card">
          <h3>ADMIN TOKEN 필요</h3>
          <DataManagementAccessCard onAuthorized={() => setAuthorized(true)} />
        </div>
      </section>
    );
  }

  return (
    <section className="stack">
      <div className="page-header">
        <NavLink className="back-link" to="/settings">← 설정</NavLink>
        <h2>데이터 관리</h2>
      </div>

      <KcscKeyManager settings={externalSettings} onChanged={load} />
      <SitesManager sites={authData.sites} onChanged={load} />
      <UsersManager users={authData.users} onChanged={load} />

      <div className="settings-card">
        <h3>표준지침 상태</h3>
        <p>문서 {status?.documents ?? 0}개 · 청크 {status?.chunks ?? 0}개</p>
        <button className="btn-outline" onClick={load}>새로고침</button>
      </div>

      <div className="settings-card">
        <h3>고급 PDF 파싱 (권장)</h3>
        <p className="settings-note">pdfplumber를 사용해 표준지침 PDF를 고품질로 파싱합니다. 컬럼 레이아웃·표·한국어 텍스트 추출에 강합니다.</p>
        <label className="field-label">문서명</label>
        <input value={parseForm.document_title} onChange={(e) => setParseForm({ ...parseForm, document_title: e.target.value })} placeholder="예: 기계설비 시공표준 2026" />
        <label className="field-label">버전</label>
        <input value={parseForm.version} onChange={(e) => setParseForm({ ...parseForm, version: e.target.value })} placeholder="예: 2026" />
        <label className="field-label">개정일</label>
        <input value={parseForm.revision_date} onChange={(e) => setParseForm({ ...parseForm, revision_date: e.target.value })} placeholder="예: 2026-03-01" />
        <label className="file-upload-btn">
          고급 파싱으로 PDF 업로드
          <input type="file" accept=".pdf" onChange={(e) => uploadFile(e, true)} disabled={loading} style={{ display: 'none' }} />
        </label>
      </div>

      <div className="settings-card">
        <h3>일반 PDF 업로드</h3>
        <p className="settings-note">PyPDF를 사용한 기본 파싱입니다. TXT, MD, JSON, PDF, DOCX 지원.</p>
        <label className="file-upload-btn secondary">
          파일 업로드
          <input type="file" accept=".txt,.md,.json,.pdf,.docx" onChange={(e) => uploadFile(e, false)} disabled={loading} style={{ display: 'none' }} />
        </label>
      </div>

      {message && <div className="info-msg-box">{message}</div>}

      <div className="settings-card">
        <h3>인덱싱된 문서</h3>
        {documents.length === 0 ? (
          <p className="settings-note">아직 업로드된 문서가 없습니다.</p>
        ) : documents.map((doc) => (
          <div className="doc-row" key={doc.id}>
            <strong>{doc.title || doc.filename}</strong>
            <span>{doc.filename} · {doc.chunk_count}청크{doc.version ? ` · v${doc.version}` : ''}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

const KCSC_SOURCE_LABEL = {
  custom: '관리자 설정',
  env: 'Render 환경변수',
  'bundled-default': '기본 탑재키',
};

function KcscKeyManager({ settings, onChanged }) {
  const [draft, setDraft] = useState('');
  const [reveal, setReveal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const kcsc = settings?.kcsc || {};
  const sourceLabel = KCSC_SOURCE_LABEL[kcsc.source] || '미설정';

  const putKey = async (key, successMsg, failPrefix) => {
    setSaving(true); setMessage('');
    try {
      await fetchJson('/api/admin/external-settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kcsc_api_key: key }),
      });
      setDraft('');
      setMessage(successMsg);
      onChanged();
    } catch (err) {
      setMessage(`${failPrefix}: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const save = () => {
    if (!draft.trim()) {
      setMessage('저장할 KCSC API 키를 입력하세요. 기본키로 되돌리려면 복구 버튼을 사용하세요.');
      return;
    }
    putKey(draft.trim(), 'KCSC API 키를 저장했습니다.', '저장 실패');
  };

  const restoreDefault = () => {
    if (!window.confirm('관리자 설정 키를 지우고 기본 탑재 KCSC 키로 복구하시겠습니까?')) return;
    putKey('', '기본 탑재 KCSC 키로 복구했습니다.', '복구 실패');
  };

  return (
    <div className="settings-card">
      <h3>KCSC API 키 관리</h3>
      <p className="settings-note">
        현재 상태: <strong>{kcsc.configured ? '사용 가능' : '미설정'}</strong>
        {kcsc.masked_key && <> · {kcsc.masked_key}</>}
        {kcsc.source && <> · {sourceLabel}</>}
      </p>
      <div className="admin-inline-form">
        <input
          type={reveal ? 'text' : 'password'}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="새 KCSC API 키 입력"
          autoComplete="off"
        />
        <button className="btn-primary" onClick={save} disabled={saving}>{saving ? '저장 중...' : '저장'}</button>
      </div>
      <div className="button-row">
        <button className="btn-outline" onClick={() => setReveal((v) => !v)}>{reveal ? '숨기기' : '보기'}</button>
        <button className="btn-outline" onClick={restoreDefault} disabled={saving}>기본키 복구</button>
      </div>
      {message && <div className={message.includes('실패') || message.includes('입력') ? 'error-box' : 'info-msg-box'}>{message}</div>}
    </div>
  );
}

function SitesManager({ sites, onChanged }) {
  const [newSite, setNewSite] = useState('');
  const [editing, setEditing] = useState(null); // { original, name }
  const [message, setMessage] = useState('');

  const createSite = async () => {
    if (!newSite.trim()) return;
    setMessage('');
    try {
      await fetchJson('/api/admin/auth-sites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newSite.trim() }),
      });
      setNewSite('');
      onChanged();
    } catch (err) {
      setMessage(`현장명 추가 실패: ${err.message}`);
    }
  };

  const saveSite = async (original) => {
    const next = (editing?.name || '').trim();
    if (!next) return;
    setMessage('');
    try {
      await fetchJson(`/api/admin/auth-sites/${encodeURIComponent(original)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: next }),
      });
      setEditing(null);
      onChanged();
    } catch (err) {
      setMessage(`현장명 수정 실패: ${err.message}`);
    }
  };

  const deleteSite = async (site) => {
    if (!window.confirm(`${site} 현장명을 삭제하시겠습니까?`)) return;
    setMessage('');
    try {
      await fetchJson(`/api/admin/auth-sites/${encodeURIComponent(site)}`, { method: 'DELETE' });
      onChanged();
    } catch (err) {
      setMessage(`현장명 삭제 실패: ${err.message}`);
    }
  };

  return (
    <div className="settings-card">
      <h3>현장명 데이터베이스 관리</h3>
      <div className="admin-inline-form">
        <input value={newSite} onChange={(e) => setNewSite(e.target.value)} placeholder="현장명 추가" />
        <button className="btn-primary" onClick={createSite}>추가</button>
      </div>
      <div className="admin-list">
        {sites.map((site) => (
          <div className="admin-row" key={site}>
            {editing?.original === site ? (
              <input value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
            ) : (
              <strong>{site}</strong>
            )}
            <div className="button-row compact">
              {editing?.original === site ? (
                <>
                  <button className="btn-primary" onClick={() => saveSite(site)}>저장</button>
                  <button className="btn-outline" onClick={() => setEditing(null)}>취소</button>
                </>
              ) : (
                <>
                  <button className="btn-outline" onClick={() => setEditing({ original: site, name: site })}>수정</button>
                  <button className="btn-danger-sm" onClick={() => deleteSite(site)}>삭제</button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
      {message && <div className="error-box">{message}</div>}
    </div>
  );
}

function UsersManager({ users, onChanged }) {
  const [newUser, setNewUser] = useState({ name: '', sabun: '', can_manage_all: false });
  const [editing, setEditing] = useState(null); // { originalSabun, name, sabun, can_manage_all }
  const [message, setMessage] = useState('');

  const createUser = async () => {
    if (!newUser.name.trim() || !newUser.sabun.trim()) return;
    setMessage('');
    try {
      await fetchJson('/api/admin/auth-users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newUser.name.trim(),
          sabun: newUser.sabun.trim(),
          can_manage_all: !!newUser.can_manage_all,
        }),
      });
      setNewUser({ name: '', sabun: '', can_manage_all: false });
      onChanged();
    } catch (err) {
      setMessage(`사용자 추가 실패: ${err.message}`);
    }
  };

  const saveUser = async (originalSabun) => {
    setMessage('');
    try {
      await fetchJson(`/api/admin/auth-users/${encodeURIComponent(originalSabun)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editing.name.trim(),
          sabun: editing.sabun.trim(),
          can_manage_all: !!editing.can_manage_all,
        }),
      });
      setEditing(null);
      onChanged();
    } catch (err) {
      setMessage(`사용자 수정 실패: ${err.message}`);
    }
  };

  const deleteUser = async (user) => {
    if (!window.confirm(`${user.name} 사용자를 삭제하시겠습니까?`)) return;
    setMessage('');
    try {
      await fetchJson(`/api/admin/auth-users/${encodeURIComponent(user.sabun)}`, { method: 'DELETE' });
      onChanged();
    } catch (err) {
      setMessage(`사용자 삭제 실패: ${err.message}`);
    }
  };

  return (
    <div className="settings-card">
      <h3>로그인 명단 관리</h3>
      <div className="admin-user-add">
        <input value={newUser.name} onChange={(e) => setNewUser({ ...newUser, name: e.target.value })} placeholder="이름" />
        <input value={newUser.sabun} onChange={(e) => setNewUser({ ...newUser, sabun: e.target.value })} placeholder="사번" />
        <label className="admin-check">
          <input type="checkbox" checked={newUser.can_manage_all} onChange={(e) => setNewUser({ ...newUser, can_manage_all: e.target.checked })} />
          <span>관리권한</span>
        </label>
        <button className="btn-primary" onClick={createUser}>추가</button>
      </div>
      <div className="admin-list">
        {users.map((user) => {
          const isEditing = editing?.originalSabun === user.sabun;
          return (
            <div className="admin-row admin-user-row" key={user.sabun}>
              {isEditing ? (
                <>
                  <input value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
                  <input value={editing.sabun} onChange={(e) => setEditing({ ...editing, sabun: e.target.value })} />
                  <label className="admin-check">
                    <input type="checkbox" checked={editing.can_manage_all} onChange={(e) => setEditing({ ...editing, can_manage_all: e.target.checked })} />
                    <span>관리권한</span>
                  </label>
                </>
              ) : (
                <>
                  <strong>{user.name}</strong>
                  <span>사번 {user.sabun}</span>
                  <label className="admin-check">
                    <input type="checkbox" checked={!!user.can_manage_all} readOnly />
                    <span>공지·전체 도면검토</span>
                  </label>
                </>
              )}
              <div className="button-row compact">
                {isEditing ? (
                  <>
                    <button className="btn-primary" onClick={() => saveUser(user.sabun)}>저장</button>
                    <button className="btn-outline" onClick={() => setEditing(null)}>취소</button>
                  </>
                ) : (
                  <>
                    <button className="btn-outline" onClick={() => setEditing({ originalSabun: user.sabun, ...user })}>수정</button>
                    <button className="btn-danger-sm" onClick={() => deleteUser(user)}>삭제</button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
      {message && <div className="error-box">{message}</div>}
    </div>
  );
}
