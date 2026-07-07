/**
 * storage.js — localStorage/sessionStorage 접근과 사용자 세션 헬퍼.
 *
 * 모든 저장 키는 STORAGE_KEYS 한 곳에서 관리한다.
 * 브라우저 저장소 접근은 사파리 프라이빗 모드 등에서 throw 할 수 있으므로
 * 항상 try/catch로 감싼다.
 */
import { useCallback, useEffect, useState } from 'react';

export const STORAGE_KEYS = {
  recent: 'facility-standard:recent',
  settings: 'facility-standard:settings',
  geminiUserKey: 'facility-standard:gemini-user-key',
  adminToken: 'facility-standard:admin-token',
  userId: 'facility-standard:user-id',        // 구버전 호환 (사번 미로그인 시)
  checklistSite: 'facility-standard:checklist-site',
  user: 'facility-standard:user',             // { name, sabun, site_name, can_manage_all }
  lastNoticeId: 'facility-standard:last-notice-id',
};

// ── 원시 읽기/쓰기 ────────────────────────────────────────────────────────────

export function readStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function writeStorage(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* quota/private mode */ }
}

// ── 키/토큰 리더 ──────────────────────────────────────────────────────────────

export function readUserGeminiKey() {
  try { return (localStorage.getItem(STORAGE_KEYS.geminiUserKey) || '').trim(); } catch { return ''; }
}

export function readAdminToken() {
  try { return (localStorage.getItem(STORAGE_KEYS.adminToken) || '').trim(); } catch { return ''; }
}

// ── 로그인 세션 ───────────────────────────────────────────────────────────────
// remember=true 면 localStorage(영구), false 면 sessionStorage(탭 종료 시 소멸).

export function readUser() {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.user) || sessionStorage.getItem(STORAGE_KEYS.user) || '';
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveUser(user, remember) {
  try {
    const val = JSON.stringify(user);
    if (remember) {
      localStorage.setItem(STORAGE_KEYS.user, val);
      sessionStorage.removeItem(STORAGE_KEYS.user);
    } else {
      sessionStorage.setItem(STORAGE_KEYS.user, val);
      localStorage.removeItem(STORAGE_KEYS.user);
    }
  } catch { /* ignore */ }
}

export function clearUser() {
  try {
    localStorage.removeItem(STORAGE_KEYS.user);
    sessionStorage.removeItem(STORAGE_KEYS.user);
  } catch { /* ignore */ }
}

/** 체크리스트 X-User-Id 용 식별자 — 로그인 사번 우선, 구버전 저장값 fallback. */
export function readUserId() {
  const user = readUser();
  if (user && user.sabun) return user.sabun.trim();
  try { return (localStorage.getItem(STORAGE_KEYS.userId) || '').trim(); } catch { return ''; }
}

/** 공지·현장이슈 API 에 사용자 신원을 전달하는 헤더 (한글은 URL 인코딩). */
export function userAuthHeaders() {
  const user = readUser();
  if (!user) return {};
  const headers = {};
  if (user.name) headers['X-User-Name'] = encodeURIComponent(user.name);
  if (user.sabun) headers['X-User-Sabun'] = encodeURIComponent(user.sabun);
  if (user.site_name) headers['X-User-Site'] = encodeURIComponent(user.site_name);
  return headers;
}

// ── React 훅 ─────────────────────────────────────────────────────────────────

/** localStorage 와 동기화되는 useState. */
export function useStoredState(key, fallback) {
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

/** 온라인/오프라인 상태. */
export function useNetworkStatus() {
  const [online, setOnline] = useState(() => navigator.onLine);
  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => {
      window.removeEventListener('online', on);
      window.removeEventListener('offline', off);
    };
  }, []);
  return online;
}
