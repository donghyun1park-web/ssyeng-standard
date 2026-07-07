/**
 * common.jsx — 여러 페이지에서 공유하는 소형 컴포넌트.
 */
import { NavLink } from 'react-router-dom';
import { IcoBell, IcoClipboard, IcoHome, IcoSearch, IcoSettings } from '../lib/icons';

/** 상단 브랜드 스트립 (쌍용건설 CI). */
export function BrandStrip() {
  return (
    <header className="brand-strip" aria-label="Ssangyong E&C MEP standard brand">
      <div className="brand-strip-logo">
        <img src="/brand/ssangyong-ci-en.jpg" alt="SSANGYONG" />
        <span>MEP-STD</span>
      </div>
    </header>
  );
}

const NAV_TABS = [
  { to: '/',         label: '홈',       Icon: IcoHome },
  { to: '/search',   label: '검색',     Icon: IcoSearch },
  { to: '/sites',    label: '현장이슈', Icon: IcoClipboard },
  { to: '/notices',  label: '공지사항', Icon: IcoBell },
  { to: '/settings', label: '설정',     Icon: IcoSettings },
];

/** 하단 5탭 내비게이션. */
export function BottomNav() {
  return (
    <nav className="bottom-nav">
      {NAV_TABS.map(({ to, label, Icon }) => (
        <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
          <Icon size={22} />
          <small>{label}</small>
        </NavLink>
      ))}
    </nav>
  );
}

const STATUS_BADGE_CLASS = {
  '검토중': 'badge-blue',
  '협의중': 'badge-orange',
  '반영완료': 'badge-green',
  '보류': 'badge-gray',
  '조치필요': 'badge-red',
  '조치완료': 'badge-green',
};

/** 도면검토/현장이슈 상태 배지. */
export function StatusBadge({ status }) {
  return <span className={`status-badge ${STATUS_BADGE_CLASS[status] || 'badge-gray'}`}>{status}</span>;
}
