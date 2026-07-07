/**
 * api.js — 백엔드 통신 계층.
 *
 * fetchJson 이 경로 prefix 를 보고 필요한 인증 헤더(Gemini 사용자 키,
 * Admin 토큰, 사용자 신원, 체크리스트 사용자 ID)를 자동으로 붙인다.
 * 컴포넌트에서는 헤더를 신경 쓰지 않고 경로만 호출하면 된다.
 */
import {
  STORAGE_KEYS,
  readAdminToken,
  readUserGeminiKey,
  readUserId,
  userAuthHeaders,
} from './storage';

/** 외부 법령 검색 링크 (법제처 AI 법령검색). */
export const LAW_URL = 'https://www.law.go.kr/ais/main.do';

/** 공종 목록 — 백엔드 checklists.TRADE_LIST 와 반드시 일치해야 한다. */
export const TRADE_LIST = ['배관공사', '보온공사', '덕트공사', '장비설치', '시험및검사'];

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

/** 상대 API 경로 → 절대 URL. 이미 절대 URL 이면 그대로 반환. */
export function apiUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE_URL}${path}`;
}

/** 인앱 PDF 뷰어 라우트 링크 생성. */
export function pdfViewerLink(url, page, title) {
  if (!url) return '';
  const params = new URLSearchParams({ url });
  if (page) params.set('page', String(page));
  if (title) params.set('title', title);
  return `/pdf-viewer?${params.toString()}`;
}

// 경로 prefix → 자동 첨부 헤더 규칙
const ADMIN_PATH_PREFIXES = ['/api/admin', '/api/migration', '/api/rag/', '/api/sites', '/api/drawing', '/api/site-issues', '/api/notices'];
const USER_MANAGED_PREFIXES = ['/api/drawing', '/api/site-issues', '/api/notices'];

/**
 * JSON API 호출. 실패(비 2xx) 시 `API {status}` 메시지로 throw 한다.
 * 경로에 따라 인증 헤더를 자동으로 추가한다.
 */
export async function fetchJson(path, options = {}) {
  const headers = { ...(options.headers || {}) };

  const userKey = readUserGeminiKey();
  if (userKey && (path === '/api/ask' || path.startsWith('/api/ask?'))) {
    headers['X-User-Gemini-Key'] = userKey;
  }

  const adminToken = readAdminToken();
  if (adminToken && ADMIN_PATH_PREFIXES.some((p) => path.startsWith(p))) {
    headers['X-Admin-Token'] = adminToken;
  }

  if (USER_MANAGED_PREFIXES.some((p) => path.startsWith(p))) {
    Object.assign(headers, userAuthHeaders());
  }

  if (path.startsWith('/api/checklists')) {
    const userId = readUserId();
    if (userId) headers['X-User-Id'] = encodeURIComponent(userId);
  }

  const response = await fetch(apiUrl(path), { ...options, headers });
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json();
}

/** ADMIN TOKEN 서버 검증. 성공 시 localStorage 에 저장하고 true 반환. */
export async function verifyAdminToken(token) {
  const clean = (token || '').trim();
  if (!clean) throw new Error('ADMIN TOKEN을 입력하세요.');
  const response = await fetch(apiUrl('/api/admin/verify'), {
    headers: { 'X-Admin-Token': clean },
  });
  if (!response.ok) throw new Error('ADMIN TOKEN이 올바르지 않습니다.');
  localStorage.setItem(STORAGE_KEYS.adminToken, clean);
  return true;
}
