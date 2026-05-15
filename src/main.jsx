import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, NavLink, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import * as pdfjsLib from 'pdfjs-dist/build/pdf.mjs';
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import './App.css';
import fallbackItems from './data/standard_items.json';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

const updateSW = () => {};

// ── Lucide SVG Icons ──────────────────────────────────────────────────────────
const I = ({ children, size = 20, color = 'currentColor', strokeWidth = 2 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"
    style={{ display: 'block', flexShrink: 0 }}>{children}</svg>
);
const IcoHome        = (p) => <I {...p}><path d="M3 11l9-8 9 8M5 10v10h14V10"/></I>;
const IcoSearch      = (p) => <I {...p}><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></I>;
const IcoClipboard   = (p) => <I {...p}><rect x="8" y="3" width="8" height="4" rx="1"/><path d="M16 5h2a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h2"/><path d="M9 12h6M9 16h6M9 8h6"/></I>;
const IcoBell        = (p) => <I {...p}><path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M11 21h2"/></I>;
const IcoSettings    = (p) => <I {...p}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.06.06a2 2 0 1 1-2.82 2.82l-.06-.06a1.7 1.7 0 0 0-1.82-.33 1.7 1.7 0 0 0-1 1.51V20a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.11-1.51 1.7 1.7 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.82-2.82l.06-.06a1.7 1.7 0 0 0 .33-1.82 1.7 1.7 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.6 8.6a1.7 1.7 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.82-2.82l.06.06a1.7 1.7 0 0 0 1.82.33H9a1.7 1.7 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.51 1.7 1.7 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.82 2.82l-.06.06a1.7 1.7 0 0 0-.33 1.82V9a1.7 1.7 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.51 1z"/></I>;
const IcoFileSearch  = (p) => <I {...p}><path d="M14 3v5h5"/><path d="M14 3l7 7v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><circle cx="11.5" cy="14.5" r="2.5"/><path d="m13.3 16.3 1.7 1.7"/></I>;
const IcoCheckSquare = (p) => <I {...p}><rect x="3" y="5" width="18" height="16" rx="2"/><path d="m8 12 3 3 5-5"/></I>;
const IcoClipboard2  = (p) => <I {...p}><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></I>;
const IcoSparkles    = (p) => <I {...p}><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 3v4M21 5h-4M5 17v4M7 19H3"/></I>;
const IcoExtLink     = (p) => <I {...p}><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></I>;
const IcoPaperclip   = (p) => <I {...p}><path d="m21 9-9 9a5 5 0 0 1-7-7l9-9a3 3 0 0 1 4 4l-9 9a1 1 0 0 1-2-2l8-8"/></I>;
const IcoArrowLeft   = (p) => <I {...p}><path d="M19 12H5M12 19l-7-7 7-7"/></I>;
const IcoChevronDown = (p) => <I {...p}><path d="m6 9 6 6 6-6"/></I>;
const IcoX           = (p) => <I {...p}><path d="M18 6 6 18M6 6l12 12"/></I>;
const IcoWrench      = (p) => <I {...p}><path d="M14.7 6.3a4 4 0 1 1 5 5l-11 11-3-3 1.5-1.5L4 14.2A4 4 0 0 1 9 9z"/></I>;
const IcoBranch      = (p) => <I {...p}><circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="9" r="2"/><path d="M6 8v8M16 9H10a4 4 0 0 0-4 4v3"/></I>;
const IcoThermo      = (p) => <I {...p}><path d="M14 4a2 2 0 0 0-4 0v10.5a4 4 0 1 0 4 0z"/></I>;
const IcoWind        = (p) => <I {...p}><path d="M9.5 8a3.5 3.5 0 1 1 0 8H2"/><path d="M11.5 16a3.5 3.5 0 1 0 0-8H2"/><path d="M21 12a4 4 0 1 0-8 0H2"/></I>;
const IcoCog         = (p) => <I {...p}><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M22 12h-3M5 12H2M19 19l-2-2M7 7 5 5M19 5l-2 2M5 19l2-2"/></I>;
const IcoFlask       = (p) => <I {...p}><path d="M10 2v7L4.2 19.4A2 2 0 0 0 6 22h12a2 2 0 0 0 1.8-2.6L14 9V2"/><path d="M8 2h8M7 16h10"/></I>;
const IcoPlus        = (p) => <I {...p}><path d="M12 5v14M5 12h14"/></I>;
const IcoPencil      = (p) => <I {...p}><path d="M14.7 6.3a2 2 0 0 1 0 2.8l-7 7-3.7 1 1-3.7 7-7a2 2 0 0 1 2.8 0z"/><path d="m13 7 4 4"/></I>;
const IcoTrash       = (p) => <I {...p}><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></I>;

const TRADE_ICONS_SVG = {
  '배관공사':  IcoBranch,
  '보온공사':  IcoThermo,
  '덕트공사':  IcoWind,
  '장비설치':  IcoCog,
  '시험및검사': IcoFlask,
};

const STORAGE_KEYS = {
  favorites: 'facility-standard:favorites',
  recent: 'facility-standard:recent',
  checklist: 'facility-standard:checklist-v2',
  settings: 'facility-standard:settings',
  installDismissed: 'facility-standard:install-dismissed',
  geminiUserKey: 'facility-standard:gemini-user-key',
  adminToken: 'facility-standard:admin-token',
  userId: 'facility-standard:user-id',
  checklistSite: 'facility-standard:checklist-site',
  user: 'facility-standard:user', // { name, sabun }
  lastNoticeId: 'facility-standard:last-notice-id',
};

const LAW_URL = 'https://www.law.go.kr/ais/main.do';

function readUserGeminiKey() {
  try { return (localStorage.getItem(STORAGE_KEYS.geminiUserKey) || '').trim(); } catch { return ''; }
}
function readAdminToken() {
  try { return (localStorage.getItem(STORAGE_KEYS.adminToken) || '').trim(); } catch { return ''; }
}
function readUser() {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.user) || sessionStorage.getItem(STORAGE_KEYS.user) || '';
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}
function saveUser(user, remember) {
  try {
    const val = JSON.stringify(user);
    if (remember) {
      localStorage.setItem(STORAGE_KEYS.user, val);
      sessionStorage.removeItem(STORAGE_KEYS.user);
    } else {
      sessionStorage.setItem(STORAGE_KEYS.user, val);
      localStorage.removeItem(STORAGE_KEYS.user);
    }
  } catch {}
}
function clearUser() {
  try {
    localStorage.removeItem(STORAGE_KEYS.user);
    sessionStorage.removeItem(STORAGE_KEYS.user);
  } catch {}
}
function readUserId() {
  const user = readUser();
  if (user && user.sabun) return user.sabun.trim();
  try { return (localStorage.getItem(STORAGE_KEYS.userId) || '').trim(); } catch { return ''; }
}
function readStorage(key, fallback) {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback; } catch { return fallback; }
}
function writeStorage(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
}

function useStoredState(key, fallback) {
  const [value, setValue] = useState(() => readStorage(key, fallback));
  const update = useCallback((next) => {
    setValue((current) => {
      const resolved = typeof next === 'function' ? next(current) : next;
      writeStorage(key, resolved);
      return resolved;
    });
  }, [key]);
  return [value, update];
}

function useNetworkStatus() {
  const [online, setOnline] = useState(() => navigator.onLine);
  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off); };
  }, []);
  return online;
}

function useServiceWorkerNotice() {
  const [updateReady, setUpdateReady] = useState(false);
  const [offlineReady, setOfflineReady] = useState(false);
  useEffect(() => {
    const onUpdate = () => setUpdateReady(true);
    const onOffline = () => setOfflineReady(true);
    window.addEventListener('facility-sw-update', onUpdate);
    window.addEventListener('facility-offline-ready', onOffline);
    return () => {
      window.removeEventListener('facility-sw-update', onUpdate);
      window.removeEventListener('facility-offline-ready', onOffline);
    };
  }, []);
  return { updateReady, offlineReady, setUpdateReady, setOfflineReady };
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

function apiUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE_URL}${path}`;
}

function pdfViewerLink(url, page, title) {
  if (!url) return '';
  const params = new URLSearchParams({ url });
  if (page) params.set('page', String(page));
  if (title) params.set('title', title);
  return `/pdf-viewer?${params.toString()}`;
}

async function fetchJson(path, options = {}) {
  const userKey = readUserGeminiKey();
  if (userKey && (path === '/api/ask' || path.startsWith('/api/ask?'))) {
    options = { ...options, headers: { ...(options.headers || {}), 'X-User-Gemini-Key': userKey } };
  }
  const adminToken = readAdminToken();
  const adminPath = path.startsWith('/api/migration') || path.startsWith('/api/rag/') || path.startsWith('/api/sites') || path.startsWith('/api/drawing') || path.startsWith('/api/site-issues') || path.startsWith('/api/notices');
  if (adminToken && adminPath) {
    options = { ...options, headers: { ...(options.headers || {}), 'X-Admin-Token': adminToken } };
  }
  if (path.startsWith('/api/checklists')) {
    const userId = readUserId();
    if (userId) options = { ...options, headers: { ...(options.headers || {}), 'X-User-Id': encodeURIComponent(userId) } };
  }
  const response = await fetch(apiUrl(path), options);
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json();
}

function useStandardItems() {
  const [items, setItems] = useState(fallbackItems);
  const [apiStatus, setApiStatus] = useState({ mode: 'fallback', message: '로컬 JSON 사용 중' });
  const refreshItems = async () => {
    try {
      const data = await fetchJson('/api/standards');
      setItems(Array.isArray(data.items) ? data.items : fallbackItems);
      setApiStatus({ mode: 'online', message: `백엔드 연결됨 · ${data.count ?? data.items?.length ?? 0}개 항목` });
    } catch {
      setItems(fallbackItems);
      setApiStatus({ mode: 'fallback', message: 'FastAPI 미연결 · 로컬 JSON 사용 중' });
    }
  };
  useEffect(() => { refreshItems(); }, []);
  return { items, apiStatus, refreshItems };
}

function toggleFavorite(id, appState) {
  appState.setFavorites((current) =>
    current.includes(id) ? current.filter((fid) => fid !== id) : [...current, id]
  );
}

// ── Login Page ────────────────────────────────────────────────────────────────

function LoginPage({ onLogin }) {
  const [name, setName] = useState('');
  const [sabun, setSabun] = useState('');
  const [siteName, setSiteName] = useState('');
  const [sites, setSites] = useState([]);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // 앱 시작 시 현장 목록 로드
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

function App() {
  const [currentUser, setCurrentUser] = useState(() => readUser());
  const [recent, setRecent] = useStoredState(STORAGE_KEYS.recent, []);
  const [checked, setChecked] = useStoredState(STORAGE_KEYS.checklist, {});
  const [settings, setSettings] = useStoredState(STORAGE_KEYS.settings, {
    compactMode: false, showIds: false, largeTouch: false,
  });
  const [popupNotice, setPopupNotice] = useState(null);
  const networkOnline = useNetworkStatus();
  const swNotice = useServiceWorkerNotice();
  const { items, apiStatus, refreshItems } = useStandardItems();

  const handleLogout = () => { clearUser(); setCurrentUser(null); };

  const dismissPopup = () => {
    if (popupNotice) {
      try { localStorage.setItem(STORAGE_KEYS.lastNoticeId, popupNotice.id); } catch {}
      setPopupNotice(null);
    }
  };

  // 신규 공지 팝업 체크 (앱 시작 시)
  useEffect(() => {
    if (!currentUser) return;
    fetch(apiUrl('/api/notices'))
      .then((r) => r.json())
      .then((data) => {
        const list = data.notices || [];
        if (!list.length) return;
        const latest = list[0];
        const lastSeen = (() => { try { return localStorage.getItem(STORAGE_KEYS.lastNoticeId) || ''; } catch { return ''; } })();
        if (latest.id !== lastSeen) setPopupNotice(latest);
      })
      .catch(() => {});
  }, [currentUser]);

  const appState = {
    recent, setRecent,
    checked, setChecked, settings, setSettings,
    items, apiStatus, refreshItems, networkOnline, swNotice,
    currentUser, handleLogout,
  };

  if (!currentUser) {
    return <LoginPage onLogin={(user) => setCurrentUser(user)} />;
  }

  return (
    <BrowserRouter>
      <div className={['app', settings.compactMode ? 'compact' : '', settings.largeTouch ? 'large-touch' : ''].filter(Boolean).join(' ')}>
        <BrandStrip />
        <SwNotice appState={appState} />
        {popupNotice && <NoticePopup notice={popupNotice} onClose={dismissPopup} />}
        <main className="page-shell">
          <Routes>
            <Route path="/" element={<HomePage appState={appState} />} />
            <Route path="/search" element={<SearchPage appState={appState} />} />
            <Route path="/item/:id" element={<DetailPage appState={appState} />} />
            <Route path="/sites" element={<SiteListPage />} />
            <Route path="/sites/new" element={<SiteFormPage />} />
            <Route path="/sites/:siteId" element={<SiteDetailPage />} />
            <Route path="/checklist" element={<ChecklistPage appState={appState} />} />
            <Route path="/checklist/:trade" element={<ChecklistDetailPage appState={appState} />} />
            <Route path="/notices" element={<NoticesPage appState={appState} />} />
            <Route path="/settings" element={<SettingsPage appState={appState} />} />
            <Route path="/admin" element={<AdminPage appState={appState} />} />
            <Route path="/pdf-viewer" element={<PdfViewerPage />} />
          </Routes>
        </main>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}

// ── Bottom Navigation ─────────────────────────────────────────────────────────

function BrandStrip() {
  return (
    <header className="brand-strip" aria-label="Ssangyong E&C MEP standard brand">
      <div className="brand-strip-logo">
        <img src="/brand/ssangyong-ci-en.jpg" alt="SSANGYONG" />
        <span>MEP-STD</span>
      </div>
    </header>
  );
}

function BottomNav() {
  const tabs = [
    { to: '/',         label: '홈',       Icon: IcoHome },
    { to: '/search',   label: '검색',     Icon: IcoSearch },
    { to: '/sites',    label: '현장이슈', Icon: IcoClipboard },
    { to: '/notices',  label: '공지사항', Icon: IcoBell },
    { to: '/settings', label: '설정',     Icon: IcoSettings },
  ];
  return (
    <nav className="bottom-nav">
      {tabs.map(({ to, label, Icon }) => (
        <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => isActive ? 'active' : ''}>
          <Icon size={22} />
          <small>{label}</small>
        </NavLink>
      ))}
    </nav>
  );
}

// ── SW Notice ─────────────────────────────────────────────────────────────────

function SwNotice({ appState }) {
  const { swNotice } = appState;
  if (swNotice.updateReady) {
    return (
      <div className="sw-notice">
        <span>새 버전이 준비되었습니다.</span>
        <button className="mini-button" onClick={() => updateSW(true)}>업데이트</button>
        <button className="ghost-button" onClick={() => swNotice.setUpdateReady(false)}>닫기</button>
      </div>
    );
  }
  if (swNotice.offlineReady) {
    return (
      <div className="sw-notice soft">
        <span>오프라인 사용 준비 완료</span>
        <button className="ghost-button" onClick={() => swNotice.setOfflineReady(false)}>확인</button>
      </div>
    );
  }
  return null;
}

// ── Home Page ─────────────────────────────────────────────────────────────────

function HomePage({ appState }) {
  const tiles = [
    { to: '/search',    Icon: IcoFileSearch,  title: '표준지침 검색',  desc: 'AI 답변 + 문서 검색' },
    { to: '/sites',     Icon: IcoClipboard2,  title: '현장이슈 공유',  desc: '현장별 도면검토 · 이슈' },
    { to: '/checklist', Icon: IcoCheckSquare, title: '체크리스트',     desc: '공종별 현장 점검' },
    { to: '/notices',   Icon: IcoBell,        title: '공지사항',       desc: '회사 · 현장 공지' },
  ];
  return (
    <section className="page-shell">
      <div className="home-greet">
        {appState.currentUser ? `안녕하세요, ${appState.currentUser.name}님` : '안녕하세요'}
      </div>
      <div className="home-title">쌍용건설 설비시공표준</div>

      <div className="home-grid">
        {tiles.map(({ to, Icon, title, desc }) => (
          <NavLink key={to} className="home-tile" to={to}>
            <div className="tile-icon"><Icon size={26} /></div>
            <div className="tile-title">{title}</div>
            <div className="tile-desc">{desc}</div>
          </NavLink>
        ))}
      </div>

      <a className="law-card" href={LAW_URL} target="_blank" rel="noreferrer">
        <div>
          <div className="law-title">법제처 AI 법령검색</div>
          <div className="law-sub">법령은 공식 사이트에서 확인</div>
        </div>
        <IcoExtLink size={16} />
      </a>

      {!appState.networkOnline && (
        <div className="offline-notice">오프라인 상태 · 로컬 기준으로 동작합니다.</div>
      )}
    </section>
  );
}

// ── Search Page ───────────────────────────────────────────────────────────────

// 모듈 레벨 캐시 — 컴포넌트 언마운트(PDF 보기 후 뒤로가기 등)에도 유지됨.
// 페이지 새로고침 시 초기화된다.
const _searchCache = new Map();
// 구조: query -> { ai: aiState, kcsc: kcscState, rag: ragState }

function filterLocalItems(items, query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return items.filter((item) => {
    const hay = [item.id, item.category, item.section, item.title, item.summary, item.body, ...(item.keywords || [])].join(' ').toLowerCase();
    return hay.includes(q);
  });
}

function SearchPage({ appState }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQ = (searchParams.get('q') || '').trim();

  // 캐시에서 초기 상태 복원 (PDF 뷰어에서 돌아온 경우 재호출 방지)
  const _cached0 = initialQ ? _searchCache.get(initialQ) : null;

  const [query, setQuery] = useState(initialQ);
  const [submitted, setSubmitted] = useState(_cached0 ? initialQ : '');
  const [kcscState, setKcscState] = useState(_cached0?.kcsc ?? { status: 'idle', items: [], error: '' });
  const [aiState, setAiState]   = useState(_cached0?.ai   ?? { status: 'idle', result: null, error: '' });
  const [ragState, setRagState] = useState(_cached0?.rag  ?? { status: 'idle', items: [], error: '' });

  const companyResults = useMemo(() => filterLocalItems(appState.items, submitted).slice(0, 8), [appState.items, submitted]);

  const runSearch = useCallback(async (rawQuery) => {
    const q = (rawQuery ?? query).trim();
    if (q.length < 2) return;
    setSubmitted(q);
    setQuery(q);
    if (searchParams.get('q') !== q) setSearchParams({ q }, { replace: true });

    // 이미 캐시된 결과가 있으면 API 호출 없이 복원
    if (_searchCache.has(q)) {
      const hit = _searchCache.get(q);
      setKcscState(hit.kcsc);
      setAiState(hit.ai);
      setRagState(hit.rag);
      return;
    }

    const nextKcsc = { status: 'loading', items: [], error: '' };
    const nextAi   = { status: 'loading', result: null, error: '' };
    const nextRag  = { status: 'loading', items: [], error: '' };
    setKcscState(nextKcsc);
    setAiState(nextAi);
    setRagState(nextRag);

    // 캐시 수집용 — 세 요청이 각자 완료될 때마다 저장
    const partial = { kcsc: nextKcsc, ai: nextAi, rag: nextRag };
    const saveCache = () => _searchCache.set(q, { ...partial });

    fetchJson('/api/external/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q, sources: ['kcsc'], limit: 5 }),
    }).then((data) => {
      const kcsc = (data.items || []).filter((it) => (it.source || '').toLowerCase() === 'kcsc');
      const s = { status: 'ready', items: kcsc, error: '' };
      partial.kcsc = s; setKcscState(s); saveCache();
    }).catch(() => {
      const s = { status: 'error', items: [], error: 'KCSC 검색에 연결할 수 없습니다.' };
      partial.kcsc = s; setKcscState(s); saveCache();
    });

    fetchJson('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, top_k: 5 }),
    }).then((data) => {
      const s = { status: 'ready', result: data, error: '' };
      partial.ai = s; setAiState(s); saveCache();
    }).catch(() => {
      const s = { status: 'error', result: null, error: 'AI 답변을 가져올 수 없습니다.' };
      partial.ai = s; setAiState(s); saveCache();
    });

    fetchJson(`/api/rag/search?q=${encodeURIComponent(q)}&limit=5`)
      .then((data) => {
        const s = { status: 'ready', items: data.results || [], error: '' };
        partial.rag = s; setRagState(s); saveCache();
      })
      .catch(() => {
        const s = { status: 'ready', items: [], error: '' };
        partial.rag = s; setRagState(s); saveCache();
      });
  }, [query, searchParams, setSearchParams]);

  useEffect(() => {
    const urlQ = (searchParams.get('q') || '').trim();
    if (urlQ.length < 2) return;
    // 캐시가 있으면 상태만 복원하고 API 호출하지 않음
    if (_searchCache.has(urlQ)) {
      const hit = _searchCache.get(urlQ);
      setSubmitted(urlQ);
      setQuery(urlQ);
      setKcscState(hit.kcsc);
      setAiState(hit.ai);
      setRagState(hit.rag);
      return;
    }
    // 새 검색어일 때만 API 호출
    if (urlQ !== submitted) {
      runSearch(urlQ);
    }
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
          {/* 1순위: AI 답변 */}
          <AiAnswerPanel state={aiState} appState={appState} />

          {/* 2순위: 회사 표준지침 (JSON + 인덱싱된 PDF 통합) */}
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

          {/* 3순위: KCSC 참고 기준 */}
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

          {/* 법령 링크 */}
          <a className="law-link-row" href={LAW_URL} target="_blank" rel="noreferrer">
            <span>법제처 AI 법령검색 바로가기</span>
            <span>법령은 공식 사이트에서 확인 ↗</span>
          </a>
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
  const pdfPage = item.pdf_page;
  const viewerLink = pdfUrl ? pdfViewerLink(pdfUrl, pdfPage, item.title) : null;

  return (
    <div className="result-card company-card">
      <div className="card-meta">
        <span>{item.category}</span>
        {item.section && <span>{item.section}</span>}
        {appState.settings?.showIds && <span>{item.id}</span>}
      </div>
      <NavLink to={`/item/${item.id}`} className="card-title">{item.title}</NavLink>
      <p className="card-summary">{item.summary}</p>
      {pdfPage && <p className="card-page">p.{pdfPage}</p>}
      <div className="card-actions">
        {viewerLink && (
          <NavLink className="btn-pdf" to={viewerLink}>PDF 보기</NavLink>
        )}
      </div>
    </div>
  );
}

// 청크 텍스트에서 가장 의미있는 제목 후보 추출
function extractChunkTitle(text) {
  if (!text) return '';
  const clean = text.replace(/\s+/g, ' ').trim();

  // 1) 장/절/조 패턴 우선 (예: "03 옥내배관공사", "03-1 옥내 급수,급탕배관공사", "07-2 시공관련사항")
  const sectionMatch = clean.match(/(\d{1,2}(?:[-.]\d{1,2}){0,2})\s+([가-힣A-Za-z][^[\d\n]{2,40})/);
  if (sectionMatch) {
    return `${sectionMatch[1]} ${sectionMatch[2].trim()}`.slice(0, 60);
  }

  // 2) [p.N] 마커 직후 첫 구절
  const afterPage = clean.match(/\[p\.\d+\]\s*([^[\n]{4,60})/);
  if (afterPage) return afterPage[1].trim().slice(0, 60);

  // 3) fallback: 텍스트 첫 60자
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
        {viewerLink && (
          <NavLink className="btn-pdf" to={viewerLink}>PDF 보기</NavLink>
        )}
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

function AiAnswerPanel({ state, appState }) {
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

// ── Detail Page ───────────────────────────────────────────────────────────────

function DetailPage({ appState }) {
  const { id } = useParams();
  const item = appState.items.find((entry) => entry.id === id);

  useEffect(() => {
    if (!item) return;
    appState.setRecent((current) => [item.id, ...current.filter((sid) => sid !== item.id)].slice(0, 20));
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
  const pdfPage = item.pdf_page;
  const viewerLink = pdfUrl ? pdfViewerLink(pdfUrl, pdfPage, item.title) : '';

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
              PDF 보기{pdfPage ? ` · p.${pdfPage}` : ''}
            </NavLink>
          </div>
        ) : item.body ? (
          <p className="body-text">{item.body}</p>
        ) : null}
      </article>
    </section>
  );
}

// ── Site Issues Pages ─────────────────────────────────────────────────────────

function SiteListPage() {
  const navigate = useNavigate();
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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
        <button className="btn-primary" onClick={() => navigate('/sites/new')}>+ 현장 등록</button>
      </div>

      {error && <div className="error-box">{error}</div>}
      {loading ? (
        <div className="loading-row"><span className="spinner" />불러오는 중...</div>
      ) : sites.length === 0 ? (
        <div className="empty-hint">
          등록된 현장이 없습니다.<br />
          <button className="btn-link" onClick={() => navigate('/sites/new')}>첫 현장을 등록하세요</button>
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

function SiteFormPage() {
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

function SiteDetailPage() {
  const { siteId } = useParams();
  const navigate = useNavigate();
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
          <button className="btn-outline" onClick={() => setShowReviewForm(!showReviewForm)}>
            {showReviewForm ? '취소' : '+ 도면검토 추가'}
          </button>
          {showReviewForm && (
            <DrawingReviewForm siteId={siteId} onSaved={() => { setShowReviewForm(false); load(); }} />
          )}
          {reviews.length === 0 ? (
            <div className="empty-hint">등록된 도면검토가 없습니다.</div>
          ) : reviews.map((r) => (
            <div className="issue-card" key={r.id}>
              <div className="issue-header">
                <strong>{r.review_content}</strong>
                <StatusBadge status={r.status} />
              </div>
              {r.location && <p className="issue-loc">위치: {r.location}</p>}
              {r.category && <p className="issue-meta">분류: {r.category}</p>}
              {r.action_plan && <p className="issue-action">조치방향: {r.action_plan}</p>}
            </div>
          ))}
        </>
      )}

      {tab === 'issue' && (
        <>
          <button className="btn-outline" onClick={() => setShowIssueForm(!showIssueForm)}>
            {showIssueForm ? '취소' : '+ 이슈 추가'}
          </button>
          {showIssueForm && (
            <SiteIssueForm siteId={siteId} onSaved={() => { setShowIssueForm(false); load(); }} />
          )}
          {issues.length === 0 ? (
            <div className="empty-hint">등록된 현장이슈가 없습니다.</div>
          ) : issues.map((iss) => (
            <div className="issue-card" key={iss.id}>
              <div className="issue-header">
                <strong>{iss.issue_content}</strong>
                <StatusBadge status={iss.status} type="issue" />
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

function StatusBadge({ status, type }) {
  const colorMap = {
    '검토중': 'badge-blue', '협의중': 'badge-orange', '반영완료': 'badge-green', '보류': 'badge-gray',
    '조치필요': 'badge-red', '조치완료': 'badge-green',
  };
  return <span className={`status-badge ${colorMap[status] || 'badge-gray'}`}>{status}</span>;
}

function DrawingReviewForm({ siteId, onSaved }) {
  const STATUS_OPTIONS = ['검토중', '협의중', '반영완료', '보류'];
  const [form, setForm] = useState({ category: '', location: '', review_content: '', action_plan: '', status: '검토중' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.review_content.trim()) { setError('검토 내용을 입력하세요.'); return; }
    setLoading(true);
    try {
      await fetchJson('/api/drawing-reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, site_id: siteId }),
      });
      onSaved();
    } catch { setError('저장에 실패했습니다.'); } finally { setLoading(false); }
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
        {STATUS_OPTIONS.map((s) => <option key={s}>{s}</option>)}
      </select>
      {error && <div className="error-box">{error}</div>}
      <button type="submit" className="btn-primary" disabled={loading}>{loading ? '저장 중...' : '저장'}</button>
    </form>
  );
}

function SiteIssueForm({ siteId, onSaved }) {
  const STATUS_OPTIONS = ['조치필요', '검토중', '협의중', '조치완료'];
  const TRADE_OPTIONS = ['배관공사', '보온공사', '덕트공사', '장비설치', '시험및검사', '기타'];
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
        {TRADE_OPTIONS.map((t) => <option key={t}>{t}</option>)}
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
        {STATUS_OPTIONS.map((s) => <option key={s}>{s}</option>)}
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

// ── Checklist Pages ───────────────────────────────────────────────────────────

const TRADE_LIST = ['배관공사', '보온공사', '덕트공사', '장비설치', '시험및검사'];
const TRADE_ICONS = { '배관공사': '🔧', '보온공사': '🌡', '덕트공사': '💨', '장비설치': '⚙', '시험및검사': '🧪' };

function useSelectedSite(loginSiteName) {
  const [siteId, setSiteId] = useState(() => {
    try {
      // 로그인 시 선택한 현장을 우선 사용, 없으면 저장된 값
      return localStorage.getItem(STORAGE_KEYS.checklistSite) || loginSiteName || '';
    } catch { return loginSiteName || ''; }
  });
  const update = useCallback((next) => {
    setSiteId(next);
    try {
      if (next) localStorage.setItem(STORAGE_KEYS.checklistSite, next);
      else localStorage.removeItem(STORAGE_KEYS.checklistSite);
    } catch {}
  }, []);
  return [siteId, update];
}

function ChecklistPage({ appState }) {
  const navigate = useNavigate();
  const [checklists, setChecklists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sites, setSites] = useState([]);
  const loginSiteName = appState.currentUser?.site_name || '';
  const [siteId, setSiteId] = useSelectedSite(loginSiteName);

  const load = useCallback(() => {
    setLoading(true);
    const q = siteId ? `?site_id=${encodeURIComponent(siteId)}` : '';
    fetchJson(`/api/checklists${q}`).then((data) => {
      setChecklists(data.checklists || []);
    }).catch(() => {
      setChecklists(TRADE_LIST.map((trade) => ({ trade, item_count: 0, checked_count: 0, has_items: false })));
    }).finally(() => setLoading(false));
  }, [siteId]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    // 마스터 현장 목록(auth)과 직접 등록 현장(site_issues) 모두 표시
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
          <strong>{appState.currentUser.name}</strong> · 현장: <strong>{siteId || '미선택'}</strong>
        </p>
      )}

      <div className="settings-card">
        <label className="field-label">현장 선택</label>
        <select value={siteId} onChange={(e) => setSiteId(e.target.value)}>
          <option value="">-- 현장을 선택하세요 --</option>
          {sites.map((s) => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
        <p className="settings-note">같은 현장을 선택한 인원이 체크리스트를 공유합니다.</p>
      </div>

      {loading ? (
        <div className="loading-row"><span className="spinner" />불러오는 중...</div>
      ) : TRADE_LIST.map((trade) => {
        const info = checklists.find((c) => c.trade === trade) || { item_count: 0, checked_count: 0, has_items: false };
        const target = `/checklist/${encodeURIComponent(trade)}${siteId ? `?site=${encodeURIComponent(siteId)}` : ''}`;
        return (
          <div className="trade-card" key={trade} onClick={() => navigate(target)}>
            <div className="trade-icon">
              {(() => { const Icon = TRADE_ICONS_SVG[trade]; return Icon ? <Icon size={22} /> : '📋'; })()}
            </div>
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

function ChecklistDetailPage({ appState }) {
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

  const STATUS_CYCLE = ['미체크', '적합', '해당없음', '부적합'];
  const STATUS_ICONS = { '미체크': '□', '적합': '✓', '해당없음': '△', '부적합': '✕' };
  const STATUS_CLASS = { '미체크': '', '적합': 'check-ok', '해당없음': 'check-na', '부적합': 'check-ng' };

  const getStatus = (itemId) => records[itemId]?.status || '미체크';
  const cycleStatus = async (itemId) => {
    const current = getStatus(itemId);
    const next = STATUS_CYCLE[(STATUS_CYCLE.indexOf(current) + 1) % STATUS_CYCLE.length];
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
              const isEditing = editingId === item.id;
              if (isEditing) {
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

// ── Saved Page ────────────────────────────────────────────────────────────────

// ── Notice Popup ──────────────────────────────────────────────────────────────

function NoticePopup({ notice, onClose }) {
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

// ── Notices Page ──────────────────────────────────────────────────────────────

function NoticesPage({ appState }) {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const isAdmin = !!readAdminToken();

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
        headers: { 'X-Admin-Token': readAdminToken() },
      });
      if (res.ok) load();
      else alert('삭제 실패');
    } catch { alert('삭제 실패'); }
  };

  return (
    <section className="stack">
      <div className="page-header">
        <h2>공지사항</h2>
        {isAdmin && (
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? '취소' : '+ 공지 작성'}
          </button>
        )}
      </div>

      {showForm && isAdmin && (
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
              {isAdmin && (
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
        headers: { 'X-Admin-Token': readAdminToken() },
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

// ── Settings Page ─────────────────────────────────────────────────────────────

function SettingsPage({ appState }) {
  return (
    <section className="stack">
      <div className="page-header">
        <h2>설정</h2>
      </div>

      {/* 사용자 정보 */}
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
      <AdminTokenCard />

      <div className="settings-card">
        <h3>화면 설정</h3>
        <label className="setting-row">
          <span><strong>간격 줄이기</strong><small>작은 화면에서 더 많은 항목 표시</small></span>
          <input type="checkbox" checked={appState.settings.compactMode}
            onChange={(e) => appState.setSettings({ ...appState.settings, compactMode: e.target.checked })} />
        </label>
        <label className="setting-row">
          <span><strong>큰 터치 영역</strong><small>현장 장갑 사용을 고려한 버튼 간격</small></span>
          <input type="checkbox" checked={appState.settings.largeTouch}
            onChange={(e) => appState.setSettings({ ...appState.settings, largeTouch: e.target.checked })} />
        </label>
        <label className="setting-row">
          <span><strong>표준 ID 표시</strong><small>검색 결과에 문서 ID 표시</small></span>
          <input type="checkbox" checked={appState.settings.showIds}
            onChange={(e) => appState.setSettings({ ...appState.settings, showIds: e.target.checked })} />
        </label>
      </div>

      <div className="settings-card">
        <h3>데이터 관리</h3>
        <NavLink className="btn-outline block" to="/admin">관리자 문서 관리</NavLink>
        <button className="btn-danger" style={{ marginTop: 8 }} onClick={() => {
          if (window.confirm('저장된 즐겨찾기, 체크리스트, 설정이 모두 삭제됩니다. 계속하시겠습니까?')) {
            localStorage.clear();
            location.reload();
          }
        }}>로컬 저장 데이터 초기화</button>
      </div>
    </section>
  );
}

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
    } catch {}
  };
  const clear = () => {
    setDraft('');
    try { localStorage.removeItem(STORAGE_KEYS.geminiUserKey); } catch {}
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

function AdminTokenCard() {
  const [storedToken, setStoredToken] = useState(() => readAdminToken());
  const [draft, setDraft] = useState(storedToken);
  const [reveal, setReveal] = useState(false);
  const [saved, setSaved] = useState(false);
  const masked = storedToken ? (storedToken.length <= 8 ? '••••••••' : storedToken.slice(0, 4) + '••••' + storedToken.slice(-4)) : '';

  const save = () => {
    const clean = draft.trim();
    try {
      if (clean) localStorage.setItem(STORAGE_KEYS.adminToken, clean);
      else localStorage.removeItem(STORAGE_KEYS.adminToken);
      setStoredToken(clean); setSaved(true); setTimeout(() => setSaved(false), 2000);
    } catch {}
  };
  const clear = () => {
    setDraft('');
    try { localStorage.removeItem(STORAGE_KEYS.adminToken); } catch {}
    setStoredToken('');
  };

  return (
    <div className="settings-card">
      <h3>Admin Token</h3>
      <p className="settings-note">문서 업로드와 데이터 관리는 서버의 ADMIN_TOKEN과 같은 값이 필요합니다.</p>
      <input type={reveal ? 'text' : 'password'} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="backend/.env의 ADMIN_TOKEN 입력" autoComplete="off" />
      <div className="button-row">
        <button className="btn-primary" onClick={save}>저장</button>
        <button className="btn-outline" onClick={() => setReveal((v) => !v)}>{reveal ? '숨기기' : '보기'}</button>
        {storedToken && <button className="btn-ghost" onClick={clear}>지우기</button>}
      </div>
      {saved && <p className="success-msg">저장되었습니다.</p>}
      {storedToken && !saved && <p className="info-msg">관리자 토큰 사용 중: {masked}</p>}
    </div>
  );
}

// ── Admin Page ────────────────────────────────────────────────────────────────

function AdminPage({ appState }) {
  const [status, setStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [parseForm, setParseForm] = useState({ document_title: '', version: '', revision_date: '' });

  const load = async () => {
    try {
      const [statusData, docsData] = await Promise.all([fetchJson('/api/rag/status'), fetchJson('/api/rag/documents')]);
      setStatus(statusData);
      setDocuments(docsData.documents || []);
    } catch { setMessage('백엔드에 연결할 수 없습니다.'); }
  };

  useEffect(() => { load(); }, []);

  const uploadFile = async (event, useFirecrawl) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setLoading(true); setMessage('');
    const form = new FormData();
    form.append('file', file);
    if (useFirecrawl) {
      form.append('document_title', parseForm.document_title || file.name.replace(/\.[^.]+$/, ''));
      form.append('version', parseForm.version);
      form.append('revision_date', parseForm.revision_date);
    } else {
      form.append('document_title', file.name.replace(/\.[^.]+$/, ''));
    }
    const endpoint = useFirecrawl ? '/api/rag/parse-pdf' : '/api/rag/upload';
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

  return (
    <section className="stack">
      <div className="page-header">
        <NavLink className="back-link" to="/settings">← 설정</NavLink>
        <h2>관리자 문서 관리</h2>
      </div>

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

// ── PDF Viewer (in-app) ───────────────────────────────────────────────────────

function PdfViewerPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const url = searchParams.get('url') || '';
  const initialPage = Math.max(1, parseInt(searchParams.get('page') || '1', 10) || 1);
  const title = searchParams.get('title') || 'PDF 보기';

  const canvasRef = useRef(null);
  const pdfRef = useRef(null);
  const renderTaskRef = useRef(null);
  const [numPages, setNumPages] = useState(0);
  const [pageNum, setPageNum] = useState(initialPage);
  const [zoom, setZoom] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true); setError('');
    const adminToken = readAdminToken();
    const headers = {};
    if (adminToken && url.includes('/api/rag/')) headers['X-Admin-Token'] = adminToken;

    const task = pdfjsLib.getDocument({ url, httpHeaders: headers, withCredentials: false });
    task.promise.then((pdf) => {
      if (cancelled) return;
      pdfRef.current = pdf;
      setNumPages(pdf.numPages);
      setPageNum((p) => Math.min(Math.max(1, p), pdf.numPages));
      setLoading(false);
    }).catch((err) => {
      if (cancelled) return;
      setError(`PDF를 불러올 수 없습니다: ${err.message || err}`);
      setLoading(false);
    });

    return () => {
      cancelled = true;
      try { task.destroy(); } catch {}
      if (pdfRef.current) { try { pdfRef.current.destroy(); } catch {} pdfRef.current = null; }
    };
  }, [url]);

  useEffect(() => {
    const pdf = pdfRef.current;
    const canvas = canvasRef.current;
    if (!pdf || !canvas || pageNum < 1 || pageNum > pdf.numPages) return;
    let cancelled = false;

    if (renderTaskRef.current) {
      try { renderTaskRef.current.cancel(); } catch {}
    }

    pdf.getPage(pageNum).then((page) => {
      if (cancelled) return;
      const containerWidth = canvas.parentElement?.clientWidth || window.innerWidth;
      const baseViewport = page.getViewport({ scale: 1 });
      const fitScale = (containerWidth - 16) / baseViewport.width;
      const scale = Math.max(0.5, fitScale * zoom);
      const viewport = page.getViewport({ scale });
      const ctx = canvas.getContext('2d');
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.floor(viewport.width * ratio);
      canvas.height = Math.floor(viewport.height * ratio);
      canvas.style.width = `${Math.floor(viewport.width)}px`;
      canvas.style.height = `${Math.floor(viewport.height)}px`;
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      const task = page.render({ canvasContext: ctx, viewport });
      renderTaskRef.current = task;
      task.promise.catch((err) => {
        if (err?.name !== 'RenderingCancelledException') console.error('PDF render error', err);
      });
    });

    return () => { cancelled = true; };
  }, [pageNum, zoom, numPages]);

  const goPrev = () => setPageNum((p) => Math.max(1, p - 1));
  const goNext = () => setPageNum((p) => Math.min(numPages || p, p + 1));
  const zoomIn = () => setZoom((z) => Math.min(4, +(z + 0.25).toFixed(2)));
  const zoomOut = () => setZoom((z) => Math.max(0.5, +(z - 0.25).toFixed(2)));
  const zoomReset = () => setZoom(1.0);

  return (
    <section className="pdf-viewer-page">
      <div className="pdf-viewer-toolbar">
        <button className="btn-ghost" onClick={() => navigate(-1)}>← 닫기</button>
        <strong className="pdf-viewer-title">{title}</strong>
        <a className="btn-outline" href={url} target="_blank" rel="noreferrer" title="외부 브라우저로 열기">↗</a>
      </div>

      {loading ? (
        <div className="loading-row" style={{ padding: 24 }}><span className="spinner" />PDF 불러오는 중...</div>
      ) : error ? (
        <div className="error-box" style={{ margin: 16 }}>{error}</div>
      ) : (
        <>
          <div className="pdf-viewer-canvas-wrap">
            <canvas ref={canvasRef} className="pdf-viewer-canvas" />
          </div>
          <div className="pdf-viewer-controls">
            <button className="btn-outline" onClick={goPrev} disabled={pageNum <= 1}>◀</button>
            <input
              className="pdf-page-input"
              type="number"
              min={1}
              max={numPages}
              value={pageNum}
              onChange={(e) => {
                const v = parseInt(e.target.value, 10);
                if (!Number.isNaN(v)) setPageNum(Math.min(Math.max(1, v), numPages));
              }}
            />
            <span className="pdf-page-total">/ {numPages}</span>
            <button className="btn-outline" onClick={goNext} disabled={pageNum >= numPages}>▶</button>
            <span className="pdf-zoom-controls">
              <button className="btn-outline" onClick={zoomOut} title="축소">−</button>
              <button className="btn-outline" onClick={zoomReset} title="원래 크기">{Math.round(zoom * 100)}%</button>
              <button className="btn-outline" onClick={zoomIn} title="확대">+</button>
            </span>
          </div>
        </>
      )}
    </section>
  );
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

createRoot(document.getElementById('root')).render(<App />);
