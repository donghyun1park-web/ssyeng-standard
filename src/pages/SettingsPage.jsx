/**
 * SettingsPage — 사용자 정보, Gemini 키, 화면 설정, 데이터 관리 진입.
 * ADMIN TOKEN 검증에 성공해야 데이터 관리(/admin)로 입장한다.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchJson, verifyAdminToken } from '../lib/api';
import { STORAGE_KEYS, readAdminToken, readUserGeminiKey } from '../lib/storage';

export default function SettingsPage({ appState }) {
  const navigate = useNavigate();
  const { settings, setSettings } = appState;

  const toggle = (key) => (e) => setSettings({ ...settings, [key]: e.target.checked });

  return (
    <section className="stack">
      <div className="page-header">
        <h2>설정</h2>
      </div>

      <div className="settings-card">
        <h3>사용자 정보</h3>
        {appState.currentUser && (
          <div className="user-info-row">
            <div className="user-info-avatar">{appState.currentUser.name.slice(0, 1)}</div>
            <div className="user-info-text">
              <strong>{appState.currentUser.name}</strong>
              <small>사번: {appState.currentUser.sabun}</small>
            </div>
          </div>
        )}
        <button className="btn-outline" style={{ marginTop: 12 }} onClick={() => {
          if (window.confirm('로그아웃 하시겠습니까?')) appState.handleLogout();
        }}>로그아웃</button>
      </div>

      <GeminiKeyCard />

      <div className="settings-card">
        <h3>화면 설정</h3>
        <label className="setting-row">
          <span><strong>간격 줄이기</strong><small>작은 화면에서 더 많은 항목 표시</small></span>
          <input type="checkbox" checked={settings.compactMode} onChange={toggle('compactMode')} />
        </label>
        <label className="setting-row">
          <span><strong>큰 터치 영역</strong><small>현장 장갑 사용을 고려한 버튼 간격</small></span>
          <input type="checkbox" checked={settings.largeTouch} onChange={toggle('largeTouch')} />
        </label>
        <label className="setting-row">
          <span><strong>표준 ID 표시</strong><small>검색 결과에 문서 ID 표시</small></span>
          <input type="checkbox" checked={settings.showIds} onChange={toggle('showIds')} />
        </label>
      </div>

      <div className="settings-card">
        <h3>데이터 관리</h3>
        <DataManagementAccessCard onAuthorized={() => navigate('/admin')} />
        <button className="btn-danger" style={{ marginTop: 8 }} onClick={() => {
          if (window.confirm('저장된 체크리스트, 설정이 모두 삭제됩니다. 계속하시겠습니까?')) {
            localStorage.clear();
            location.reload();
          }
        }}>로컬 저장 데이터 초기화</button>
      </div>
    </section>
  );
}

/** 개인 Gemini API 키 입력 — 이 기기 브라우저에만 저장된다. */
function GeminiKeyCard() {
  const [storedKey, setStoredKey] = useState(() => readUserGeminiKey());
  const [draft, setDraft] = useState(storedKey);
  const [reveal, setReveal] = useState(false);
  const [saved, setSaved] = useState(false);
  const masked = storedKey ? (storedKey.length <= 8 ? '••••••••' : storedKey.slice(0, 4) + '••••' + storedKey.slice(-4)) : '';

  const save = () => {
    const clean = draft.trim();
    try {
      if (clean) localStorage.setItem(STORAGE_KEYS.geminiUserKey, clean);
      else localStorage.removeItem(STORAGE_KEYS.geminiUserKey);
      setStoredKey(clean); setSaved(true); setTimeout(() => setSaved(false), 2000);
    } catch { /* ignore */ }
  };
  const clear = () => {
    setDraft('');
    try { localStorage.removeItem(STORAGE_KEYS.geminiUserKey); } catch { /* ignore */ }
    setStoredKey('');
  };

  return (
    <div className="settings-card">
      <h3>Google Gemini API Key</h3>
      <p className="settings-note">본인의 Gemini 키를 입력하면 AI 답변이 내 키로 호출됩니다. 키는 이 기기 브라우저에만 저장됩니다.{' '}
        <a href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer">키 발급 ↗</a>
      </p>
      <input type={reveal ? 'text' : 'password'} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="AIza... 로 시작하는 키 붙여넣기" autoComplete="off" />
      <div className="button-row">
        <button className="btn-primary" onClick={save}>저장</button>
        <button className="btn-outline" onClick={() => setReveal((v) => !v)}>{reveal ? '숨기기' : '보기'}</button>
        {storedKey && <button className="btn-ghost" onClick={clear}>지우기</button>}
      </div>
      {saved && <p className="success-msg">저장되었습니다.</p>}
      {storedKey && !saved && <p className="info-msg">내 키 사용 중: {masked}</p>}
    </div>
  );
}

/** ADMIN TOKEN 확인 후 데이터 관리 화면으로 입장시키는 카드. */
export function DataManagementAccessCard({ onAuthorized }) {
  const [draft, setDraft] = useState(() => readAdminToken());
  const [reveal, setReveal] = useState(false);
  const [checking, setChecking] = useState(false);
  const [message, setMessage] = useState('');

  const enter = async () => {
    setChecking(true); setMessage('');
    try {
      await verifyAdminToken(draft);
      onAuthorized();
    } catch (err) {
      setMessage(err.message || 'ADMIN TOKEN 확인에 실패했습니다.');
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="stack" style={{ gap: 10 }}>
      <p className="settings-note">현장명 데이터베이스, 로그인 명단, PDF 업로드 관리는 서버 ADMIN TOKEN 확인 후 입장합니다.</p>
      <input
        type={reveal ? 'text' : 'password'}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        placeholder="ADMIN TOKEN 입력"
        autoComplete="off"
      />
      <div className="button-row">
        <button className="btn-primary" onClick={enter} disabled={checking}>{checking ? '확인 중...' : '데이터 관리 입장'}</button>
        <button className="btn-outline" onClick={() => setReveal((v) => !v)}>{reveal ? '숨기기' : '보기'}</button>
      </div>
      {message && <p className="login-error">{message}</p>}
    </div>
  );
}
