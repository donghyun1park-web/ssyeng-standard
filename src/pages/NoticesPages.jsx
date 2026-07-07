/**
 * NoticesPages — 공지사항 목록/작성 + 신규 공지 팝업.
 * 작성·삭제는 관리자 토큰 보유자 또는 can_manage_all 사용자만 가능.
 */
import { useCallback, useEffect, useState } from 'react';
import { apiUrl, fetchJson } from '../lib/api';
import { readAdminToken, userAuthHeaders } from '../lib/storage';
import { IcoX } from '../lib/icons';

/** 로그인 직후 최신 공지를 모달로 표시 (확인 시 lastNoticeId 저장 후 재표시 안 함). */
export function NoticePopup({ notice, onClose }) {
  return (
    <div className="notice-popup-overlay" onClick={onClose}>
      <div className="notice-popup-card" onClick={(e) => e.stopPropagation()}>
        <div className="notice-popup-header">
          <span className="notice-popup-badge">📢 공지사항</span>
          <button className="notice-popup-close" onClick={onClose} aria-label="닫기"><IcoX size={20} /></button>
        </div>
        <h2 className="notice-popup-title">{notice.title}</h2>
        <div className="notice-popup-meta">
          <span>{notice.poster}</span>
          <span>{notice.date}</span>
        </div>
        <div className="notice-popup-content">{notice.content}</div>
        {notice.file && (
          <a
            className="notice-file-link"
            href={apiUrl(notice.file.file_url)}
            target="_blank"
            rel="noreferrer"
            download={notice.file.original_name}
          >
            📎 {notice.file.original_name}
          </a>
        )}
        <button className="btn-primary notice-popup-confirm" onClick={onClose}>
          확인
        </button>
      </div>
    </div>
  );
}

export function NoticesPage({ appState }) {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const canManageNotices = !!readAdminToken() || !!appState.currentUser?.can_manage_all;

  const load = useCallback(() => {
    setLoading(true);
    fetchJson('/api/notices')
      .then((d) => setNotices(d.notices || []))
      .catch(() => setNotices([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id) => {
    if (!window.confirm('이 공지를 삭제하시겠습니까?')) return;
    try {
      const res = await fetch(apiUrl(`/api/notices/${id}`), {
        method: 'DELETE',
        headers: { 'X-Admin-Token': readAdminToken(), ...userAuthHeaders() },
      });
      if (res.ok) load();
      else alert('삭제 실패');
    } catch { alert('삭제 실패'); }
  };

  return (
    <section className="stack">
      <div className="page-header">
        <h2>공지사항</h2>
        {canManageNotices && (
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? '취소' : '+ 공지 작성'}
          </button>
        )}
      </div>

      {showForm && canManageNotices && (
        <NoticeForm
          currentUser={appState.currentUser}
          onSaved={() => { setShowForm(false); load(); }}
        />
      )}

      {loading ? (
        <div className="loading-row"><span className="spinner" />불러오는 중...</div>
      ) : notices.length === 0 ? (
        <div className="empty-hint">등록된 공지사항이 없습니다.</div>
      ) : notices.map((n) => (
        <div className="notice-card" key={n.id}>
          <div
            className="notice-card-header"
            onClick={() => setExpandedId(expandedId === n.id ? null : n.id)}
          >
            <div className="notice-card-title-row">
              <span className="notice-card-title">{n.title}</span>
              {n.file && <span className="notice-attach-icon" title="첨부파일 있음">📎</span>}
            </div>
            <div className="notice-card-meta">
              <span>{n.poster}</span>
              <span>{n.date}</span>
              <span className="notice-expand-icon">{expandedId === n.id ? '▲' : '▼'}</span>
            </div>
          </div>

          {expandedId === n.id && (
            <div className="notice-card-body">
              <p className="notice-card-content">{n.content}</p>
              {n.file && (
                <a
                  className="notice-file-link"
                  href={apiUrl(n.file.file_url)}
                  target="_blank"
                  rel="noreferrer"
                  download={n.file.original_name}
                >
                  📎 {n.file.original_name}
                  <span className="notice-file-size">
                    ({Math.round((n.file.size_bytes || 0) / 1024)}KB)
                  </span>
                </a>
              )}
              {canManageNotices && (
                <button className="btn-danger-sm" onClick={() => handleDelete(n.id)}>
                  삭제
                </button>
              )}
            </div>
          )}
        </div>
      ))}
    </section>
  );
}

function NoticeForm({ currentUser, onSaved }) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [poster, setPoster] = useState(currentUser?.name || '');
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) { setError('제목과 내용을 입력해주세요.'); return; }
    setSaving(true); setError('');
    try {
      const fd = new FormData();
      fd.append('title', title.trim());
      fd.append('content', content.trim());
      fd.append('poster', poster.trim() || (currentUser?.name || '관리자'));
      if (file) fd.append('file', file);
      const res = await fetch(apiUrl('/api/notices'), {
        method: 'POST',
        headers: { 'X-Admin-Token': readAdminToken(), ...userAuthHeaders() },
        body: fd,
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        setError(d.detail || '등록 실패');
        return;
      }
      onSaved();
    } catch { setError('서버 오류가 발생했습니다.'); }
    finally { setSaving(false); }
  };

  return (
    <div className="form-card">
      <h3>공지 작성</h3>
      <form onSubmit={handleSubmit} className="stack" style={{ gap: 10 }}>
        <div>
          <label className="field-label">제목 *</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="공지 제목" />
        </div>
        <div>
          <label className="field-label">내용 *</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="공지 내용을 입력하세요"
            rows={5}
            style={{ width: '100%', resize: 'vertical' }}
          />
        </div>
        <div>
          <label className="field-label">게시자</label>
          <input value={poster} onChange={(e) => setPoster(e.target.value)} placeholder="게시자 이름" />
        </div>
        <div>
          <label className="field-label">첨부파일 (선택, 최대 20MB)</label>
          <input
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.docx,.xlsx,.txt,.hwp"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          {file && <p className="settings-note">선택된 파일: {file.name}</p>}
        </div>
        {error && <p className="login-error">{error}</p>}
        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? '등록 중...' : '공지 등록'}
        </button>
      </form>
    </div>
  );
}
