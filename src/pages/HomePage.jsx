/**
 * HomePage — 4대 기능 타일 + 법제처 외부 링크.
 */
import { NavLink } from 'react-router-dom';
import { LAW_URL } from '../lib/api';
import {
  IcoBell,
  IcoCheckSquare,
  IcoClipboard2,
  IcoExtLink,
  IcoFileSearch,
} from '../lib/icons';

const HOME_TILES = [
  { to: '/search',    Icon: IcoFileSearch,  title: '표준지침 검색',  desc: 'AI 답변 + 문서 검색' },
  { to: '/sites',     Icon: IcoClipboard2,  title: '현장이슈 공유',  desc: '현장별 도면검토 · 이슈' },
  { to: '/checklist', Icon: IcoCheckSquare, title: '체크리스트',     desc: '공종별 현장 점검' },
  { to: '/notices',   Icon: IcoBell,        title: '공지사항',       desc: '회사 · 현장 공지' },
];

export default function HomePage({ appState }) {
  return (
    <section className="page-shell">
      <div className="home-greet">
        {appState.currentUser ? `안녕하세요, ${appState.currentUser.name}님` : '안녕하세요'}
      </div>
      <div className="home-title">쌍용건설 설비시공표준</div>

      <div className="home-grid">
        {HOME_TILES.map(({ to, Icon, title, desc }) => (
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
