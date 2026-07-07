/**
 * SitesPages — 현장이슈 공유 (현장 목록 / 등록 / 상세 + 도면검토·이슈 CRUD).
 *
 * 권한 규칙: 관리자 토큰 보유자, can_manage_all 사용자, 또는 해당 현장
 * 소속(로그인 현장 일치) 사용자만 도면검토·이슈를 작성/수정할 수 있다.
 */
import { useEffect, useState } from 'react';
import { NavLink, useNavigate, useParams } from 'react-router-dom';
import { fetchJson } from '../lib/api';
import { readAdminToken } from '../lib/storage';
import { StatusBadge } from '../components/common';

const REVIEW_STATUS_OPTIONS = ['검토중', '협의중', '반영완료', '보류'];
const ISSUE_STATUS_OPTIONS = ['조치필요', '검토중', '협의중', '조치완료'];
const ISSUE_TRADE_OPTIONS = ['배관공사', '보온공사', '덕트공사', '장비설치', '시험및검사', '기타'];

export function SiteListPage() {
  const navigate = useNavigate();
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const canManageSites = !!readAdminToken();

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchJson('/api/sites');
      setSites(data.sites || []);
    } catch {
      setError('현장 목록을 불러올 수 없습니다. 백엔드를 확인하세요.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <section className="stack">
      <div className="page-header">
        <h2>현장이슈 공유</h2>
        {canManageSites && <button className="btn-primary" onClick={() => navigate('/sites/new')}>+ 현장 등록</button>}
      </div>

      {error && <div className="error-box">{error}</div>}
      {loading ? (
        <div className="loading-row"><span className="spinner" />불러오는 중...</div>
      ) : sites.length === 0 ? (
        <div className="empty-hint">
          등록된 현장이 없습니다.<br />
          {canManageSites && <button className="btn-link" onClick={() => navigate('/sites/new')}>첫 현장을 등록하세요</button>}
        </div>
      ) : sites.map((site) => (
        <div className="site-card" key={site.id}>
          <div className="site-card-header">
            <strong>{site.site_name}</strong>
            {site.site_scale && <span className="site-scale">{site.site_scale}</span>}
          </div>
          {(site.construction_start || site.construction_end) && (
            <p className="site-period">
              {site.construction_start && site.construction_end
                ? `${site.construction_start} ~ ${site.construction_end}`
                : site.construction_start || site.construction_end}
            </p>
          )}
          <p className="site-counts">
            도면검토 {site.drawing_review_count ?? 0}건 · 현장이슈 {site.issue_count ?? 0}건
          </p>
          <button className="btn-outline" onClick={() => navigate(`/sites/${site.id}`)}>열기</button>
        </div>
      ))}
    </section>
  );
}

export function SiteFormPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    site_name: '', site_scale: '', construction_start: '', construction_end: '',
    manager_name: '', description: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (key, val) => setForm((f) => ({ ...f, [key]: val }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.site_name.trim()) { setError('현장명을 입력하세요.'); return; }
    setLoading(true);
    try {
      await fetchJson('/api/sites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      navigate('/sites');
    } catch {
      setError('현장 등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="stack">
      <div className="page-header">
        <NavLink className="back-link" to="/sites">← 목록으로</NavLink>
        <h2>현장 등록</h2>
      </div>
      <form className="form-card" onSubmit={submit}>
        <label className="field-label">현장명 *</label>
        <input value={form.site_name} onChange={(e) => set('site_name', e.target.value)} placeholder="예: A현장 복합시설 신축공사" />
        <label className="field-label">현장규모</label>
        <input value={form.site_scale} onChange={(e) => set('site_scale', e.target.value)} placeholder="예: 지하 3층 / 지상 15층 / 연면적 45,000㎡" />
        <label className="field-label">공사 시작일</label>
        <input value={form.construction_start} onChange={(e) => set('construction_start', e.target.value)} placeholder="예: 2025.03.01" />
        <label className="field-label">공사 종료일</label>
        <input value={form.construction_end} onChange={(e) => set('construction_end', e.target.value)} placeholder="예: 2027.02.28" />
        <label className="field-label">담당자</label>
        <input value={form.manager_name} onChange={(e) => set('manager_name', e.target.value)} placeholder="예: 홍길동" />
        <label className="field-label">비고</label>
        <textarea value={form.description} onChange={(e) => set('description', e.target.value)} placeholder="기계실 위치, 주요 공종 등" rows={3} />
        {error && <div className="error-box">{error}</div>}
        <button type="submit" className="btn-primary" disabled={loading}>{loading ? '등록 중...' : '현장 등록'}</button>
      </form>
    </section>
  );
}

export function SiteDetailPage({ appState }) {
  const { siteId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('review');
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [showIssueForm, setShowIssueForm] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const resp = await fetchJson(`/api/sites/${siteId}`);
      setData(resp);
    } catch {
      setError('현장 정보를 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [siteId]);

  if (loading) return <section className="stack"><div className="loading-row"><span className="spinner" />불러오는 중...</div></section>;
  if (error || !data) return <section className="stack"><div className="error-box">{error || '오류 발생'}</div></section>;

  const site = data.site;
  const reviews = data.drawing_reviews || [];
  const issues = data.site_issues || [];
  const currentUser = appState.currentUser || {};
  const canManageSite = !!readAdminToken()
    || !!currentUser.can_manage_all
    || [site.id, site.site_name].includes(currentUser.site_name);

  return (
    <section className="stack">
      <div className="page-header">
        <NavLink className="back-link" to="/sites">← 현장 목록</NavLink>
        <h2>{site.site_name}</h2>
      </div>

      <div className="site-info-card">
        {site.site_scale && <p><span className="info-label">현장규모</span>{site.site_scale}</p>}
        {(site.construction_start || site.construction_end) && (
          <p><span className="info-label">공사기간</span>{site.construction_start} ~ {site.construction_end}</p>
        )}
        {site.manager_name && <p><span className="info-label">담당자</span>{site.manager_name}</p>}
        {site.description && <p className="site-desc">{site.description}</p>}
      </div>

      <div className="tab-row">
        <button className={tab === 'review' ? 'tab active' : 'tab'} onClick={() => setTab('review')}>
          도면검토 {reviews.length}건
        </button>
        <button className={tab === 'issue' ? 'tab active' : 'tab'} onClick={() => setTab('issue')}>
          현장이슈 {issues.length}건
        </button>
      </div>

      {tab === 'review' && (
        <>
          {canManageSite ? (
            <button className="btn-outline" onClick={() => setShowReviewForm(!showReviewForm)}>
              {showReviewForm ? '취소' : '+ 도면검토 추가'}
            </button>
          ) : (
            <div className="empty-hint">도면검토 관리는 해당 현장 인원 또는 관리 권한 인원만 가능합니다.</div>
          )}
          {showReviewForm && (
            <DrawingReviewForm siteId={siteId} onSaved={() => { setShowReviewForm(false); load(); }} />
          )}
          {reviews.length === 0 ? (
            <div className="empty-hint">등록된 도면검토가 없습니다.</div>
          ) : reviews.map((r) => (
            <DrawingReviewCard key={r.id} review={r} canManage={canManageSite} onChanged={load} />
          ))}
        </>
      )}

      {tab === 'issue' && (
        <>
          {canManageSite && (
            <button className="btn-outline" onClick={() => setShowIssueForm(!showIssueForm)}>
              {showIssueForm ? '취소' : '+ 이슈 추가'}
            </button>
          )}
          {showIssueForm && (
            <SiteIssueForm siteId={siteId} onSaved={() => { setShowIssueForm(false); load(); }} />
          )}
          {issues.length === 0 ? (
            <div className="empty-hint">등록된 현장이슈가 없습니다.</div>
          ) : issues.map((iss) => (
            <div className="issue-card" key={iss.id}>
              <div className="issue-header">
                <strong>{iss.issue_content}</strong>
                <StatusBadge status={iss.status} />
              </div>
              {iss.trade && <p className="issue-meta">공종: {iss.trade}</p>}
              {iss.location && <p className="issue-loc">위치: {iss.location}</p>}
              {iss.cause && <p className="issue-meta">원인: {iss.cause}</p>}
              {iss.action_content && <p className="issue-action">조치: {iss.action_content}</p>}
              {iss.related_standard && (
                <p className="issue-ref">
                  관련 기준: {iss.related_standard}
                  {iss.related_page && ` p.${iss.related_page}`}
                </p>
              )}
            </div>
          ))}
        </>
      )}
    </section>
  );
}

function DrawingReviewCard({ review, canManage, onChanged }) {
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState('');

  const handleDelete = async () => {
    if (!window.confirm('이 도면검토를 삭제하시겠습니까?')) return;
    setError('');
    try {
      await fetchJson(`/api/drawing-reviews/${review.id}`, { method: 'DELETE' });
      onChanged();
    } catch {
      setError('삭제 권한이 없거나 삭제에 실패했습니다.');
    }
  };

  if (editing) {
    return (
      <DrawingReviewForm
        review={review}
        onCancel={() => setEditing(false)}
        onSaved={() => { setEditing(false); onChanged(); }}
      />
    );
  }

  return (
    <div className="issue-card">
      <div className="issue-header">
        <strong>{review.review_content}</strong>
        <StatusBadge status={review.status} />
      </div>
      {review.location && <p className="issue-loc">위치: {review.location}</p>}
      {review.category && <p className="issue-meta">분류: {review.category}</p>}
      {review.action_plan && <p className="issue-action">조치방향: {review.action_plan}</p>}
      {(review.created_by_name || review.updated_by_name) && (
        <p className="issue-meta">
          {review.created_by_name && `작성: ${review.created_by_name}`}
          {review.updated_by_name && ` · 수정: ${review.updated_by_name}`}
        </p>
      )}
      {error && <div className="error-box">{error}</div>}
      {canManage && (
        <div className="button-row">
          <button className="btn-outline" onClick={() => setEditing(true)}>수정</button>
          <button className="btn-danger-sm" onClick={handleDelete}>삭제</button>
        </div>
      )}
    </div>
  );
}

function DrawingReviewForm({ siteId, review, onSaved, onCancel }) {
  const [form, setForm] = useState({
    category: review?.category || '',
    location: review?.location || '',
    review_content: review?.review_content || '',
    action_plan: review?.action_plan || '',
    status: review?.status || '검토중',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.review_content.trim()) { setError('검토 내용을 입력하세요.'); return; }
    setLoading(true);
    try {
      await fetchJson(review ? `/api/drawing-reviews/${review.id}` : '/api/drawing-reviews', {
        method: review ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(review ? form : { ...form, site_id: siteId }),
      });
      onSaved();
    } catch { setError('저장 권한이 없거나 저장에 실패했습니다.'); } finally { setLoading(false); }
  };

  return (
    <form className="form-card inline-form" onSubmit={submit}>
      <label className="field-label">분류</label>
      <input value={form.category} onChange={(e) => set('category', e.target.value)} placeholder="배관, 덕트, 전기 등" />
      <label className="field-label">검토 위치</label>
      <input value={form.location} onChange={(e) => set('location', e.target.value)} placeholder="예: 지하2층 기계실" />
      <label className="field-label">검토 내용 *</label>
      <textarea value={form.review_content} onChange={(e) => set('review_content', e.target.value)} rows={3} placeholder="검토 내용을 입력하세요" />
      <label className="field-label">조치 방향</label>
      <textarea value={form.action_plan} onChange={(e) => set('action_plan', e.target.value)} rows={2} placeholder="조치 방향" />
      <label className="field-label">상태</label>
      <select value={form.status} onChange={(e) => set('status', e.target.value)}>
        {REVIEW_STATUS_OPTIONS.map((s) => <option key={s}>{s}</option>)}
      </select>
      {error && <div className="error-box">{error}</div>}
      <div className="button-row">
        <button type="submit" className="btn-primary" disabled={loading}>{loading ? '저장 중...' : '저장'}</button>
        {onCancel && <button type="button" className="btn-outline" onClick={onCancel}>취소</button>}
      </div>
    </form>
  );
}

function SiteIssueForm({ siteId, onSaved }) {
  const [form, setForm] = useState({
    trade: '', location: '', issue_content: '', cause: '', action_content: '',
    status: '조치필요', related_standard: '', related_page: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.issue_content.trim()) { setError('이슈 내용을 입력하세요.'); return; }
    setLoading(true);
    try {
      await fetchJson('/api/site-issues', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, site_id: siteId }),
      });
      onSaved();
    } catch { setError('저장에 실패했습니다.'); } finally { setLoading(false); }
  };

  return (
    <form className="form-card inline-form" onSubmit={submit}>
      <label className="field-label">공종</label>
      <select value={form.trade} onChange={(e) => set('trade', e.target.value)}>
        <option value="">선택</option>
        {ISSUE_TRADE_OPTIONS.map((t) => <option key={t}>{t}</option>)}
      </select>
      <label className="field-label">위치</label>
      <input value={form.location} onChange={(e) => set('location', e.target.value)} placeholder="예: 지하2층 기계실" />
      <label className="field-label">이슈 내용 *</label>
      <textarea value={form.issue_content} onChange={(e) => set('issue_content', e.target.value)} rows={3} placeholder="이슈 내용을 입력하세요" />
      <label className="field-label">원인</label>
      <input value={form.cause} onChange={(e) => set('cause', e.target.value)} placeholder="원인 분석" />
      <label className="field-label">조치 내용</label>
      <textarea value={form.action_content} onChange={(e) => set('action_content', e.target.value)} rows={2} placeholder="조치 완료 내용" />
      <label className="field-label">상태</label>
      <select value={form.status} onChange={(e) => set('status', e.target.value)}>
        {ISSUE_STATUS_OPTIONS.map((s) => <option key={s}>{s}</option>)}
      </select>
      <label className="field-label">관련 기준</label>
      <input value={form.related_standard} onChange={(e) => set('related_standard', e.target.value)} placeholder="예: 기계설비 시공표준 2026" />
      <label className="field-label">관련 페이지</label>
      <input value={form.related_page} onChange={(e) => set('related_page', e.target.value)} placeholder="예: 42" />
      {error && <div className="error-box">{error}</div>}
      <button type="submit" className="btn-primary" disabled={loading}>{loading ? '저장 중...' : '저장'}</button>
    </form>
  );
}
