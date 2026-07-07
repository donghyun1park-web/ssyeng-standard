/**
 * icons.jsx — 인라인 lucide 스타일 SVG 아이콘.
 * 외부 아이콘 패키지 의존 없이 번들 크기를 최소화한다. (stroke 2, 24-grid)
 */
const I = ({ children, size = 20, color = 'currentColor', strokeWidth = 2 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"
    style={{ display: 'block', flexShrink: 0 }}>{children}</svg>
);

export const IcoHome        = (p) => <I {...p}><path d="M3 11l9-8 9 8M5 10v10h14V10"/></I>;
export const IcoSearch      = (p) => <I {...p}><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></I>;
export const IcoClipboard   = (p) => <I {...p}><rect x="8" y="3" width="8" height="4" rx="1"/><path d="M16 5h2a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h2"/><path d="M9 12h6M9 16h6M9 8h6"/></I>;
export const IcoBell        = (p) => <I {...p}><path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M11 21h2"/></I>;
export const IcoSettings    = (p) => <I {...p}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.06.06a2 2 0 1 1-2.82 2.82l-.06-.06a1.7 1.7 0 0 0-1.82-.33 1.7 1.7 0 0 0-1 1.51V20a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.11-1.51 1.7 1.7 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.82-2.82l.06-.06a1.7 1.7 0 0 0 .33-1.82 1.7 1.7 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.6 8.6a1.7 1.7 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.82-2.82l.06.06a1.7 1.7 0 0 0 1.82.33H9a1.7 1.7 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.51 1.7 1.7 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.82 2.82l-.06.06a1.7 1.7 0 0 0-.33 1.82V9a1.7 1.7 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.51 1z"/></I>;
export const IcoFileSearch  = (p) => <I {...p}><path d="M14 3v5h5"/><path d="M14 3l7 7v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><circle cx="11.5" cy="14.5" r="2.5"/><path d="m13.3 16.3 1.7 1.7"/></I>;
export const IcoCheckSquare = (p) => <I {...p}><rect x="3" y="5" width="18" height="16" rx="2"/><path d="m8 12 3 3 5-5"/></I>;
export const IcoClipboard2  = (p) => <I {...p}><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></I>;
export const IcoSparkles    = (p) => <I {...p}><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 3v4M21 5h-4M5 17v4M7 19H3"/></I>;
export const IcoExtLink     = (p) => <I {...p}><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></I>;
export const IcoX           = (p) => <I {...p}><path d="M18 6 6 18M6 6l12 12"/></I>;
export const IcoBranch      = (p) => <I {...p}><circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="9" r="2"/><path d="M6 8v8M16 9H10a4 4 0 0 0-4 4v3"/></I>;
export const IcoThermo      = (p) => <I {...p}><path d="M14 4a2 2 0 0 0-4 0v10.5a4 4 0 1 0 4 0z"/></I>;
export const IcoWind        = (p) => <I {...p}><path d="M9.5 8a3.5 3.5 0 1 1 0 8H2"/><path d="M11.5 16a3.5 3.5 0 1 0 0-8H2"/><path d="M21 12a4 4 0 1 0-8 0H2"/></I>;
export const IcoCog         = (p) => <I {...p}><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M22 12h-3M5 12H2M19 19l-2-2M7 7 5 5M19 5l-2 2M5 19l2-2"/></I>;
export const IcoFlask       = (p) => <I {...p}><path d="M10 2v7L4.2 19.4A2 2 0 0 0 6 22h12a2 2 0 0 0 1.8-2.6L14 9V2"/><path d="M8 2h8M7 16h10"/></I>;

/** 공종명 → 아이콘 매핑 (체크리스트 카드용) */
export const TRADE_ICONS_SVG = {
  '배관공사':  IcoBranch,
  '보온공사':  IcoThermo,
  '덕트공사':  IcoWind,
  '장비설치':  IcoCog,
  '시험및검사': IcoFlask,
};
