/**
 * main.jsx — 애플리케이션 진입점.
 * 로그인 게이트, 전역 상태(appState), 라우팅, 신규 공지 팝업을 담당한다.
 * 화면별 구현은 src/pages/*, 공용 로직은 src/lib/* 에 있다.
 */
import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import './App.css';

import fallbackItems from './data/standard_items.json';
import { apiUrl, fetchJson } from './lib/api';
import {
  STORAGE_KEYS,
  clearUser,
  readStorage,
  readUser,
  useNetworkStatus,
  useStoredState,
  writeStorage,
} from './lib/storage';
import { BottomNav, BrandStrip } from './components/common';

import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import SearchPage, { DetailPage } from './pages/SearchPage';
import { SiteListPage, SiteFormPage, SiteDetailPage } from './pages/SitesPages';
import { ChecklistPage, ChecklistDetailPage } from './pages/ChecklistPages';
import { NoticesPage, NoticePopup } from './pages/NoticesPages';
import SettingsPage from './pages/SettingsPage';
import AdminPage from './pages/AdminPage';
import PdfViewerPage from './pages/PdfViewerPage';

/** /api/standards 로드 — 실패 시 번들된 로컬 JSON 으로 폴백. */
function useStandardItems() {
  const [items, setItems] = useState(fallbackItems);
  useEffect(() => {
    fetchJson('/api/standards')
      .then((data) => setItems(Array.isArray(data.items) ? data.items : fallbackItems))
      .catch(() => setItems(fallbackItems));
  }, []);
  return items;
}

/** 로그인 직후 최신 공지가 미확인 상태면 팝업 알림으로 반환. */
function useLatestNotice(currentUser) {
  const [popupNotice, setPopupNotice] = useState(null);

  useEffect(() => {
    if (!currentUser) return;
    fetch(apiUrl('/api/notices'))
      .then((r) => r.json())
      .then((data) => {
        const latest = (data.notices || [])[0];
        if (!latest) return;
        const lastSeen = readStorage(STORAGE_KEYS.lastNoticeId, '');
        if (latest.id !== lastSeen) setPopupNotice(latest);
      })
      .catch(() => {});
  }, [currentUser]);

  const dismiss = () => {
    if (popupNotice) {
      writeStorage(STORAGE_KEYS.lastNoticeId, popupNotice.id);
      setPopupNotice(null);
    }
  };

  return [popupNotice, dismiss];
}

function App() {
  const [currentUser, setCurrentUser] = useState(() => readUser());
  const [recent, setRecent] = useStoredState(STORAGE_KEYS.recent, []);
  const [settings, setSettings] = useStoredState(STORAGE_KEYS.settings, {
    compactMode: false, showIds: false, largeTouch: false,
  });
  const networkOnline = useNetworkStatus();
  const items = useStandardItems();
  const [popupNotice, dismissPopup] = useLatestNotice(currentUser);

  const handleLogout = () => { clearUser(); setCurrentUser(null); };

  // 각 페이지에 전달되는 전역 상태 묶음
  const appState = {
    currentUser, handleLogout,
    recent, setRecent,
    settings, setSettings,
    items, networkOnline,
  };

  if (!currentUser) {
    return <LoginPage onLogin={setCurrentUser} />;
  }

  const shellClass = ['app', settings.compactMode && 'compact', settings.largeTouch && 'large-touch']
    .filter(Boolean)
    .join(' ');

  return (
    <BrowserRouter>
      <div className={shellClass}>
        <BrandStrip />
        {popupNotice && <NoticePopup notice={popupNotice} onClose={dismissPopup} />}
        <main className="page-shell">
          <Routes>
            <Route path="/" element={<HomePage appState={appState} />} />
            <Route path="/search" element={<SearchPage appState={appState} />} />
            <Route path="/item/:id" element={<DetailPage appState={appState} />} />
            <Route path="/sites" element={<SiteListPage />} />
            <Route path="/sites/new" element={<SiteFormPage />} />
            <Route path="/sites/:siteId" element={<SiteDetailPage appState={appState} />} />
            <Route path="/checklist" element={<ChecklistPage appState={appState} />} />
            <Route path="/checklist/:trade" element={<ChecklistDetailPage />} />
            <Route path="/notices" element={<NoticesPage appState={appState} />} />
            <Route path="/settings" element={<SettingsPage appState={appState} />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/pdf-viewer" element={<PdfViewerPage />} />
          </Routes>
        </main>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}

createRoot(document.getElementById('root')).render(<App />);
