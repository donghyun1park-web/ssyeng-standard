/**
 * LoginPage — 이름(ID) + 사번(PASS) + 현장 선택 로그인.
 * 서버(/api/auth/login)가 명단을 검증하며, '저장하기' 여부에 따라
 * 세션이 localStorage(영구) 또는 sessionStorage(탭 한정)에 저장된다.
 */
import { useEffect, useState } from 'react';
import { apiUrl } from '../lib/api';
import { saveUser } from '../lib/storage';
import { BrandStrip } from '../components/common';

export default function LoginPage({ onLogin }) {
  const [name, setName] = useState('');
  const [sabun, setSabun] = useState('');
  const [siteName, setSiteName] = useState('');
  const [sites, setSites] = useState([]);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(apiUrl('/api/auth/sites'))
      .then((r) => r.json())
      .then((data) => setSites(data.sites || []))
      .catch(() => setSites([]));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimName = name.trim();
    const trimSabun = sabun.trim();
    if (!trimName || !trimSabun) { setError('이름과 사번을 모두 입력해주세요.'); return; }
    if (!siteName) { setError('현장을 선택해주세요.'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await fetch(apiUrl('/api/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimName, sabun: trimSabun, site_name: siteName }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || '이름 또는 사번이 올바르지 않습니다.');
        return;
      }
      const { user } = await res.json();
      saveUser(user, remember);
      onLogin(user);
    } catch {
      setError('서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <BrandStrip />
      <div className="login-card">
        <div className="login-logo">
          <h1>쌍용건설 설비시공표준</h1>
          <div className="sub">이름과 사번으로 시작하세요</div>
        </div>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <label className="field-label">이름 (ID)</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="예: 홍길동"
              autoFocus
              autoComplete="name"
            />
          </div>
          <div className="login-field">
            <label className="field-label">사번 (PASS)</label>
            <input
              type="password"
              value={sabun}
              onChange={(e) => setSabun(e.target.value)}
              placeholder="사번 입력"
              autoComplete="current-password"
            />
          </div>
          <div className="login-field">
            <label className="field-label">현장 선택</label>
            <select
              value={siteName}
              onChange={(e) => setSiteName(e.target.value)}
              className="login-site-select"
            >
              <option value="">-- 현장을 선택하세요 --</option>
              {sites.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <label className="login-remember">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
            />
            <span>저장하기 (다음 방문 시 자동 로그인)</span>
          </label>
          {error && <p className="login-error">{error}</p>}
          <button type="submit" className="btn-primary login-btn" disabled={loading}>
            {loading ? '확인 중...' : '시작하기'}
          </button>
        </form>
      </div>
    </div>
  );
}
