# UI/UX 디자인 PRD — Claude Design Language 전면 적용
## 설비 시공표준 검색앱 (ssyeng-standard) v2.1 Design Overhaul

> **문서 목적**: Claude AI 디자인 기능을 활용해 앱 전체를 리브랜딩한다.  
> 이 PRD는 디자인 작업자(또는 Claude AI)가 **단독으로 읽고 구현할 수 있을 만큼** 상세하게 작성되었다.  
> **기능은 100% 유지한다. 레이아웃·색·타이포그래피·컴포넌트만 재설계한다.**

---

## 목차

1. 기술 스택 & 제약
2. 디자인 시스템 (토큰·타이포·색·공간·컴포넌트)
3. 전역 레이아웃
4. 화면별 상세 스펙 (10개 화면)
5. 공통 컴포넌트 카탈로그
6. 인터랙션 & 애니메이션
7. 다크모드
8. 접근성
9. 구현 체크리스트

---

## 1. 기술 스택 & 절대 제약

### 1.1 스택 (변경 불가)
| 항목 | 기술 |
|------|------|
| Frontend | React 19, Vite 7, React Router v6 |
| 스타일 | CSS (App.css 단일 파일, CSS Variables) — Tailwind·CSS Modules·styled-components **사용 금지** |
| PDF 렌더링 | pdfjs-dist (기존 코드 유지) |
| 폰트 로딩 | `@import url(Google Fonts)` 또는 `@fontsource` npm 패키지 |
| 아이콘 | 현재: 유니코드 이모지 → 교체 대상: lucide-react (npm install lucide-react) |
| Backend | FastAPI (변경 없음) |

### 1.2 파일 구조 (변경 불가)
```
src/
  main.jsx     ← 모든 컴포넌트 (단일 파일, 2,038줄)
  App.css      ← 모든 스타일 (단일 파일, 1,559줄)
  data/standard_items.json
```

### 1.3 기능 유지 의무 (절대 건드리지 말 것)
- 모든 API 호출 (`fetchJson`, `fetch`) — URL, method, body 변경 금지
- 라우팅 (`<Route path=...>`) — 경로 변경 금지
- localStorage/sessionStorage 키 — 변경 금지
- PDF 뷰어 동작 (pdfjsLib) — 변경 금지
- 로그인 인증 로직 (`/api/auth/login`) — 변경 금지
- 체크리스트 4단계 상태 토글 로직 — 변경 금지

---

## 2. 디자인 시스템

### 2.1 폰트 (Typography System)

#### 선택 근거
Anthropic이 사용하는 Tiempos(serif) + Styrene(sans) 조합을 오픈 라이선스로 재현:
- **Heading/Display**: `Source Serif 4` (serif, 가변 폰트, Google Fonts)
- **Body/UI**: `Pretendard Variable` (sans, 한글 최적화, woff2)
- **숫자/코드**: `JetBrains Mono` (tabular-nums, 페이지번호·사번 등)

#### 폰트 로딩 (App.css 최상단)
```css
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,300..900;1,8..60,300..900&family=JetBrains+Mono:wght@400;500&display=swap');
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
```

#### CSS 폰트 변수
```css
--font-serif: "Source Serif 4", "Noto Serif KR", Georgia, serif;
--font-sans:  "Pretendard Variable", "Pretendard", -apple-system, system-ui, sans-serif;
--font-mono:  "JetBrains Mono", "Consolas", monospace;
```

#### 타입 스케일 (Major Third 1.25 비율)
```
--text-xs:     12px / 1.5  / sans  400
--text-sm:     13px / 1.55 / sans  400
--text-base:   15px / 1.65 / sans  400   ← 현장 가독성 최소 기준
--text-lg:     17px / 1.6  / sans  400
--text-xl:     19px / 1.5  / sans  600
--text-2xl:    22px / 1.4  / sans  700
--text-3xl:    27px / 1.3  / serif 600   ← 페이지 타이틀
--text-4xl:    34px / 1.2  / serif 700   ← Hero 섹션
```

#### 한글 최적화 규칙
```css
/* 본문 */
letter-spacing: -0.01em;
word-break: keep-all;
overflow-wrap: break-word;

/* 헤딩 */
letter-spacing: -0.02em;
word-break: keep-all;
```

---

### 2.2 색상 팔레트 (Color Tokens)

#### 라이트 모드 (기본)
```css
:root {
  /* Background */
  --bg-base:      #FAF9F5;   /* warm cream — 메인 배경 */
  --bg-surface:   #FFFFFF;   /* 카드, 모달 배경 */
  --bg-elevated:  #F5F4EF;   /* 인풋, hover 배경 */
  --bg-muted:     #ECEAE2;   /* disabled, 구분선 */

  /* Text */
  --text-primary:   #1C1B18;   /* warm black — 주요 텍스트 */
  --text-secondary: #5A5955;   /* 보조 텍스트 (날짜, meta) */
  --text-tertiary:  #8C8A84;   /* placeholder, disabled */
  --text-inverse:   #FAF9F5;   /* 버튼 위 텍스트 */

  /* Border */
  --border-subtle:  #E8E6DE;   /* 카드 기본 테두리 */
  --border-default: #D4D1C7;   /* 인풋 테두리 */
  --border-strong:  #1C1B18;   /* 강조 테두리 */

  /* Brand Accent */
  --accent:         #C96342;   /* Claude warm orange */
  --accent-hover:   #AE5235;
  --accent-muted:   #F5E0D8;   /* 배지 배경, soft 영역 */

  /* Semantic */
  --success:        #2D7A57;
  --success-muted:  #E0F0E8;
  --warning:        #B07A1A;
  --warning-muted:  #FDF3D7;
  --danger:         #B84040;
  --danger-muted:   #FCEAEA;
  --info:           #3A5FA5;
  --info-muted:     #E4EAF8;

  /* Overlay */
  --overlay:        rgba(28, 27, 24, 0.5);
}
```

#### 다크 모드
```css
[data-theme="dark"] {
  --bg-base:      #1E1D1A;
  --bg-surface:   #28271F;
  --bg-elevated:  #322F27;
  --bg-muted:     #3C3A31;

  --text-primary:   #F0EFE9;
  --text-secondary: #ABA89F;
  --text-tertiary:  #76746D;
  --text-inverse:   #1C1B18;

  --border-subtle:  #3C3A31;
  --border-default: #4E4B41;
  --border-strong:  #F0EFE9;

  --accent:         #E08B6A;
  --accent-hover:   #EDA082;
  --accent-muted:   #3D2A20;

  --success:        #4CAF80;
  --success-muted:  #1A3326;
  --warning:        #D4A030;
  --warning-muted:  #2E2410;
  --danger:         #E06060;
  --danger-muted:   #2E1414;
  --info:           #6A90D4;
  --info-muted:     #1A2440;
}
```

---

### 2.3 간격 시스템 (Spacing)
```css
--space-1:  4px
--space-2:  8px
--space-3:  12px
--space-4:  16px
--space-5:  20px
--space-6:  24px
--space-8:  32px
--space-10: 40px
--space-12: 48px
--space-16: 64px
```

### 2.4 모서리 반경 (Border Radius)
```css
--radius-sm:   6px    /* 배지, 칩, 작은 버튼 */
--radius-md:   10px   /* 인풋, 일반 버튼 */
--radius-lg:   14px   /* 카드 */
--radius-xl:   20px   /* 모달, 바텀시트, 로그인 카드 */
--radius-full: 999px  /* 알약형 버튼, 아바타 */
```

### 2.5 그림자 (Shadow)
```css
--shadow-xs: 0 1px 2px rgba(28,27,24,0.04);
--shadow-sm: 0 2px 6px rgba(28,27,24,0.06), 0 1px 2px rgba(28,27,24,0.04);
--shadow-md: 0 4px 16px rgba(28,27,24,0.08), 0 2px 4px rgba(28,27,24,0.04);
--shadow-lg: 0 8px 32px rgba(28,27,24,0.12), 0 4px 8px rgba(28,27,24,0.06);
/* dark mode: shadow 대신 border를 강조 */
```

### 2.6 전환 (Transition)
```css
--transition-fast:   120ms cubic-bezier(0.2, 0, 0.2, 1);
--transition-base:   200ms cubic-bezier(0.2, 0, 0.2, 1);
--transition-slow:   320ms cubic-bezier(0.2, 0, 0.2, 1);
```

---

## 3. 전역 레이아웃

### 3.1 앱 컨테이너
```
전체 화면: max-width 480px, margin 0 auto (데스크탑에서 모바일처럼)
background: var(--bg-base)
font-family: var(--font-sans)
color: var(--text-primary)
```

### 3.2 페이지 쉘 (page-shell)
```
padding: 16px 16px 80px   ← 하단 BottomNav 높이(64px) + 여백
```

### 3.3 BottomNav
```
position: fixed
bottom: 0
height: 64px (+ safe-area-inset-bottom)
background: var(--bg-surface)
border-top: 1px solid var(--border-subtle)
display: grid; grid-template-columns: repeat(5, 1fr)
backdrop-filter: blur(12px)  ← 반투명 효과
```

**BottomNav 탭 (5개 고정)**
| # | 경로 | 아이콘 (lucide) | 라벨 |
|---|------|-----------------|------|
| 1 | `/` | `<Home />` | 홈 |
| 2 | `/search` | `<Search />` | 검색 |
| 3 | `/sites` | `<ClipboardList />` | 현장이슈 |
| 4 | `/notices` | `<Bell />` | 공지사항 |
| 5 | `/settings` | `<Settings />` | 설정 |

**탭 상태 스타일**
```
기본: 아이콘 var(--text-tertiary) / 라벨 var(--text-tertiary) / 12px sans 500
활성: 아이콘 var(--accent) / 라벨 var(--accent) / 12px sans 700
     활성 탭 상단에 2px accent 라인 (또는 배경 accent-muted dot)
```

---

## 4. 화면별 상세 스펙

---

### 4.1 LoginPage `/login` (진입점)

#### 레이아웃
```
min-height: 100vh
display: flex; align-items: center; justify-content: center
background: var(--bg-base)
padding: 24px 20px
```

#### 카드
```
max-width: 400px; width: 100%
background: var(--bg-surface)
border: 1px solid var(--border-subtle)
border-radius: var(--radius-xl)
padding: 40px 32px 36px
box-shadow: var(--shadow-md)
```

#### 내부 구조 (위→아래)
1. **로고 영역**
   - 아이콘: `<Wrench />` (lucide) 40px, color: var(--accent)
   - 앱 이름: "설비 시공표준" — font: var(--font-serif), size: 28px, weight: 700, color: var(--text-primary)
   - 부제: "이름과 사번으로 시작하세요" — 14px sans, color: var(--text-secondary), margin-top: 6px

2. **폼 (margin-top: 32px, gap: 16px)**

   **이름 필드 (ID)**
   ```
   label: "이름 (ID)" — 12px sans 600, color: var(--text-secondary), margin-bottom: 6px
   input: 
     padding: 12px 14px
     border: 1px solid var(--border-default)
     border-radius: var(--radius-md)
     font-size: 15px; font-family: var(--font-sans)
     background: var(--bg-elevated)
     :focus → border-color: var(--accent); outline: 2px solid var(--accent-muted); background: var(--bg-surface)
     placeholder color: var(--text-tertiary)
   ```

   **사번 필드 (PASS)**
   ```
   동일 스타일, type="password"
   placeholder: "사번 입력"
   ```

   **현장 선택 드롭다운**
   ```
   label: "현장 선택" — 동일 스타일
   select:
     width: 100%
     padding: 12px 14px
     border: 1px solid var(--border-default)
     border-radius: var(--radius-md)
     font-size: 15px; font-family: var(--font-sans)
     background: var(--bg-elevated)
     appearance: auto
     color: var(--text-primary)
     :focus → border-color: var(--accent); outline: 2px solid var(--accent-muted)
   ```

   **저장하기 체크박스**
   ```
   display: flex; align-items: center; gap: 10px
   label: "저장하기 (다음 방문 시 자동 로그인)" — 13px sans 400, color: var(--text-secondary)
   checkbox: 16x16px, accent-color: var(--accent)
   ```

   **오류 메시지** (조건부 표시)
   ```
   background: var(--danger-muted)
   border: 1px solid #F5C6C6
   border-radius: var(--radius-sm)
   padding: 10px 14px
   font-size: 13px; color: var(--danger)
   ```

   **시작하기 버튼**
   ```
   width: 100%
   padding: 14px
   background: var(--accent)
   color: var(--text-inverse)
   font-size: 16px; font-weight: 700; font-family: var(--font-sans)
   border: none; border-radius: var(--radius-md); cursor: pointer
   :hover → background: var(--accent-hover)
   :disabled → opacity: 0.55; cursor: not-allowed
   transition: var(--transition-fast)
   ```

3. **로딩 상태**: 버튼 텍스트 "확인 중..." + 인라인 스피너 (CSS border-radius 회전)

---

### 4.2 HomePage `/`

#### 헤더
```
padding: 20px 0 12px
```
- 인사 텍스트: "안녕하세요, {name}님" — 16px sans 400, color: var(--text-secondary)
- 타이틀: "설비 시공표준" — 28px **serif** 700, color: var(--text-primary), letter-spacing: -0.02em

#### 4개 핵심 카드 그리드
```css
display: grid;
grid-template-columns: 1fr 1fr;
gap: var(--space-3);
margin-top: var(--space-5);
```

**각 카드 스펙**
```
background: var(--bg-surface)
border: 1px solid var(--border-subtle)
border-radius: var(--radius-lg)
padding: 20px 16px
display: flex; flex-direction: column; gap: 8px
cursor: pointer
transition: var(--transition-fast)

:hover → 
  border-color: var(--border-default)
  box-shadow: var(--shadow-sm)
  transform: translateY(-1px)
```

**카드 내부 구조**
```
1. 아이콘 (lucide, 28px, color: var(--accent))
2. 제목: 15px serif 600, color: var(--text-primary)
3. 설명: 12px sans 400, color: var(--text-secondary)
```

**4개 카드 매핑**
| 카드 | 아이콘 | 제목 | 설명 | 링크 |
|------|--------|------|------|------|
| 검색 | `<FileSearch />` | 표준지침 검색 | AI 답변 + 문서 검색 | `/search` |
| 현장이슈 | `<Clipboard />` | 현장이슈 공유 | 현장별 도면검토·이슈 | `/sites` |
| 체크리스트 | `<CheckSquare />` | 체크리스트 | 공종별 현장 점검 | `/checklist` |
| 공지사항 | `<Bell />` | 공지사항 | 회사·현장 공지 | `/notices` |

#### 법제처 링크 카드
```
margin-top: var(--space-4)
background: var(--bg-elevated)
border: 1px solid var(--border-subtle)
border-radius: var(--radius-lg)
padding: 14px 16px
display: flex; align-items: center; justify-content: space-between
color: var(--text-secondary)
text-decoration: none
font-size: 14px

왼쪽: "법제처 AI 법령검색" (14px sans 600) + "법령은 공식 사이트에서 확인" (12px)
오른쪽: <ExternalLink /> 16px, color: var(--text-tertiary)
```

#### 빠른 검색 칩
```
margin-top: var(--space-5)
섹션 라벨: "자주 찾는 항목" — 11px sans 600, color: var(--text-tertiary), letter-spacing: 0.06em, text-transform: uppercase
```

**칩 스타일**
```
display: inline-flex; align-items: center
padding: 6px 14px
background: var(--bg-elevated)
border: 1px solid var(--border-subtle)
border-radius: var(--radius-full)
font-size: 13px; color: var(--text-secondary)
cursor: pointer; white-space: nowrap

:hover → background: var(--accent-muted); border-color: var(--accent); color: var(--accent)
transition: var(--transition-fast)
```

칩 목록: `배관 지지`, `보온 두께`, `수압시험`, `덕트 행거`, `방화댐퍼`, `배관 구배`

---

### 4.3 SearchPage `/search`

#### 검색 바 (sticky)
```
position: sticky; top: 0; z-index: 10
background: var(--bg-base)
padding: 12px 0 8px
border-bottom: 1px solid var(--border-subtle)
```

**검색 입력**
```
display: flex; gap: 8px

input:
  flex: 1
  padding: 12px 16px
  border: 1.5px solid var(--border-default)
  border-radius: var(--radius-md)
  font-size: 15px; font-family: var(--font-sans)
  background: var(--bg-surface)
  placeholder: "어떤 표준을 찾으시나요?" (serif italic 권장)
  :focus → border-color: var(--accent)

버튼:
  padding: 12px 18px
  background: var(--accent); color: white
  border-radius: var(--radius-md)
  font-size: 14px; font-weight: 600
```

#### AI 답변 패널 (AiAnswerPanel)

**기능 유지 필수**: AI 답변 텍스트, 문서 참조(제목/장/절/페이지), PDF 보기 버튼

**디자인 스펙**
```
background: var(--bg-surface)
border: 1px solid var(--accent-muted)
border-left: 4px solid var(--accent)    ← 좌측 강조 라인
border-radius: var(--radius-lg)
padding: 20px

헤더:
  display: flex; align-items: center; gap: 8px
  아이콘: <Sparkles /> 16px, color: var(--accent)
  텍스트: "AI 답변" — 13px sans 700, color: var(--accent)
  + 로딩 시 "분석 중..." spinner

답변 본문:
  font-family: var(--font-serif)
  font-size: 16px; line-height: 1.75
  color: var(--text-primary)
  margin-top: 12px
  white-space: pre-wrap; word-break: keep-all

문서 참조 섹션 (border-top 구분):
  margin-top: 16px; padding-top: 14px
  border-top: 1px solid var(--border-subtle)
  
  라벨: "근거 문서" — 11px sans 700, color: var(--text-tertiary), text-transform: uppercase
  
  각 참조:
    padding: 8px 10px
    background: var(--bg-elevated)
    border-radius: var(--radius-sm)
    font-size: 13px; color: var(--text-secondary)
    
    표시 형식: "[문서명] [장/절] p.[페이지]"
    PDF 보기 버튼: accent ghost 버튼
```

#### 검색 결과 섹션 (SearchSection)

**섹션 헤더 (`<details>` summary)**
```
display: flex; align-items: center; gap: 10px
padding: 14px 16px
background: var(--bg-elevated)
border-radius: var(--radius-md)
cursor: pointer; list-style: none

우선순위 배지:
  1순위(회사표준): background var(--accent), color white
  2순위(PDF): background var(--info-muted), color var(--info)  
  3순위(KCSC): background var(--bg-muted), color var(--text-secondary)

섹션명: 15px sans 600
태그: 11px sans 500, padding 2px 8px, border-radius var(--radius-full)
섹션 화살표: <ChevronRight /> 16px, color var(--text-tertiary), rotate 90deg when open
```

#### 회사 표준 결과 카드 (CompanyResultCard)
```
background: var(--bg-surface)
border: 1px solid var(--border-subtle)
border-left: 3px solid var(--accent)    ← 회사표준 강조
border-radius: var(--radius-lg)
padding: 16px

meta 라인:
  display: flex; gap: 6px; flex-wrap: wrap
  font-size: 11px sans 500
  각 태그: padding 2px 8px, background var(--bg-elevated), border-radius var(--radius-full)

제목:
  font-size: 15px; font-weight: 600; color: var(--text-primary)
  margin: 8px 0 4px

요약:
  font-size: 13px; color: var(--text-secondary); line-height: 1.6
  display: -webkit-box; -webkit-line-clamp: 3; overflow: hidden

페이지:
  font-family: var(--font-mono); font-size: 12px; color: var(--text-tertiary)
  "p.42" 형식

액션:
  display: flex; gap: 8px; margin-top: 12px

PDF 보기 버튼:
  padding: 6px 14px
  background: var(--accent); color: white
  border-radius: var(--radius-sm); font-size: 12px; font-weight: 600
```

#### RAG 청크 카드 (RagChunkCard)
```
CompanyResultCard와 동일하되 border-left: 3px solid var(--info)
meta 태그에 "PDF 표준" 표시
```

#### KCSC 카드 (KcscCard)
```
CompanyResultCard와 동일하되:
border-left: 3px solid var(--border-default)   ← 차분한 강도
meta에 "KCSC 참조" 라벨
카드 전체에 opacity: 0.9 (낮은 우선순위 시각화)
```

---

### 4.4 DetailPage `/item/:id`

```
뒤로 가기: "<- 검색으로 돌아가기"
  display: flex; align-items: center; gap: 6px
  <ArrowLeft /> 16px
  font-size: 14px; color: var(--text-secondary)

article:
  background: var(--bg-surface)
  border: 1px solid var(--border-subtle)
  border-radius: var(--radius-lg)
  padding: 24px 20px

meta 라인: 동일 스타일
제목 h2: 24px serif 600, color var(--text-primary), word-break: keep-all
요약: 16px sans 400, line-height: 1.7, color var(--text-secondary), margin-top: 12px
PDF 보기 버튼: 큰 버튼 (padding 14px 24px, 100% width)
본문(body): 14px sans, line-height: 1.75, white-space: pre-wrap
```

---

### 4.5 SiteListPage `/sites`

#### 페이지 헤더
```
display: flex; justify-content: space-between; align-items: flex-start
h2: "현장이슈" — 24px serif 600
버튼 "새 현장 등록": accent primary 버튼
```

#### 현장 카드
```
background: var(--bg-surface)
border: 1px solid var(--border-subtle)
border-radius: var(--radius-lg)
padding: 18px 16px
cursor: pointer
:hover → border-color var(--border-default), box-shadow var(--shadow-xs)

상단 행:
  현장명: 17px serif 600, color var(--text-primary)
  우측: 작성일 — 12px mono, color var(--text-tertiary)

하단 행 (카운트):
  도면검토 N건 / 현장이슈 N건 — 각각 작은 배지
  배지: 11px sans 600, padding 2px 8px, border-radius var(--radius-full)
  도면검토 → info-muted/info 색상
  현장이슈 → warning-muted/warning 색상 (미해결 이슈 있을 때 accent로)

하단: 현장 규모, 기간, 담당자 — 12px sans, color var(--text-secondary)
```

---

### 4.6 SiteDetailPage `/sites/:siteId`

#### 탭 (도면검토 / 현장이슈)
```
display: flex; gap: 0
border-bottom: 2px solid var(--border-subtle)

각 탭:
  padding: 10px 20px
  font-size: 14px; font-weight: 600; color: var(--text-secondary)
  border-bottom: 2px solid transparent
  cursor: pointer
  margin-bottom: -2px    ← border overlap trick

활성 탭:
  color: var(--accent)
  border-bottom-color: var(--accent)
  background: transparent
```

#### 이슈/검토 카드
```
background: var(--bg-surface)
border: 1px solid var(--border-subtle)
border-radius: var(--radius-lg)
padding: 16px

제목: 15px sans 600, color var(--text-primary)
메타: 공종, 위치, 원인 — 12px sans, color var(--text-secondary)
상태 배지: (아래 StatusBadge 스펙 참조)
조치내용: 13px sans, color var(--text-secondary), margin-top 8px
```

#### StatusBadge 스펙
```
display: inline-flex; align-items: center
padding: 3px 10px
border-radius: var(--radius-full)
font-size: 11px; font-weight: 600

도면검토:
  검토중:   background var(--info-muted),    color var(--info)
  협의중:   background var(--warning-muted), color var(--warning)
  반영완료: background var(--success-muted), color var(--success)
  보류:     background var(--bg-muted),      color var(--text-secondary)

현장이슈:
  조치필요: background var(--danger-muted),  color var(--danger)
  검토중:   background var(--info-muted),    color var(--info)
  협의중:   background var(--warning-muted), color var(--warning)
  조치완료: background var(--success-muted), color var(--success)
```

#### 인라인 폼 (DrawingReviewForm, SiteIssueForm)
```
background: var(--bg-elevated)
border: 1px solid var(--border-subtle)
border-radius: var(--radius-lg)
padding: 20px
margin-top: 12px

각 필드:
  label: 12px sans 600, color var(--text-secondary), margin-bottom 6px
  input/select/textarea:
    padding: 10px 12px
    border: 1px solid var(--border-default)
    border-radius: var(--radius-sm)
    font-size: 14px; font-family: var(--font-sans)
    width: 100%
    background: var(--bg-surface)
    :focus → border-color var(--accent)

textarea: min-height 80px; resize: vertical
select: appearance: auto

버튼 행: display flex; gap 8px; justify-content flex-end; margin-top 16px
```

---

### 4.7 ChecklistPage `/checklist`

#### 공종 카드 그리드 (세로 스택)
각 공종 카드는 클릭 시 `/checklist/:trade?site=...` 로 이동

```
background: var(--bg-surface)
border: 1px solid var(--border-subtle)
border-radius: var(--radius-lg)
padding: 18px 16px
cursor: pointer
display: flex; align-items: center; gap: 14px
:hover → box-shadow var(--shadow-sm); border-color var(--border-default)

좌측 아이콘:
  width: 44px; height: 44px
  border-radius: var(--radius-md)
  background: var(--accent-muted)
  display: flex; align-items: center; justify-content: center
  lucide 아이콘 20px, color: var(--accent)

중앙 텍스트:
  공종명: 16px serif 600, color var(--text-primary)
  상태: "N / M 항목 완료" — 13px sans, color var(--text-secondary)

우측 진행률:
  숫자: M/N — 18px mono 600, color var(--text-primary)
  작은 원형 progress (CSS border-radius trick) 또는 라인 프로그레스
```

**공종별 아이콘**
| 공종 | lucide 아이콘 |
|------|--------------|
| 배관공사 | `<Pipette />` 또는 `<GitBranch />` |
| 보온공사 | `<Thermometer />` |
| 덕트공사 | `<Wind />` |
| 장비설치 | `<Cog />` |
| 시험및검사 | `<FlaskConical />` |

#### 현장 선택 드롭다운
```
settings-card 스타일 (배경 var(--bg-elevated))
label: "현장 선택" 12px sans 600
select: 동일 인풋 스타일
안내: "같은 현장 선택 시 체크리스트 공유" — 12px sans, color var(--text-tertiary)
```

---

### 4.8 ChecklistDetailPage `/checklist/:trade`

#### 상단 헤더
```
공종명: 22px serif 600
현장: "현장: {siteName}" — 13px mono, color var(--text-secondary)
진행률 바:
  height: 6px
  background: var(--bg-muted)
  border-radius: var(--radius-full)
  fill: var(--accent) (적합+해당없음 비율)
  margin: 12px 0
진행률 텍스트: "{done}/{total} 완료" — 14px mono 600, color var(--accent)
```

#### 체크 항목 (CheckItem)
```
background: var(--bg-surface)
border: 1px solid var(--border-subtle)
border-radius: var(--radius-md)
padding: 14px 14px 14px 12px
display: flex; align-items: flex-start; gap: 12px

좌측 토글 버튼:
  width: 36px; height: 36px; flex-shrink: 0
  border-radius: var(--radius-sm)
  border: 1.5px solid var(--border-default)
  font-size: 18px; font-weight: 700
  cursor: pointer; transition: var(--transition-fast)

  미체크 (□): background white, border var(--border-default), color transparent
  적합 (✓):   background var(--success), border var(--success), color white
  해당없음(─): background var(--bg-muted), border var(--bg-muted), color var(--text-secondary)
  부적합 (✕): background var(--danger), border var(--danger), color white

본문:
  flex: 1
  항목 텍스트: 15px sans 400, color var(--text-primary), line-height 1.55
  관련 페이지: "→ p.42" — 11px mono, color var(--text-tertiary), margin-top 4px

우측 액션 (hover 시):
  편집 <Pencil /> ghost 버튼 24px
  삭제 <Trash2 /> ghost 버튼 24px, color var(--danger)

부적합 항목: border-left: 3px solid var(--danger)
```

#### 하단 도구
```
배경: var(--bg-elevated)
border-top: 1px solid var(--border-subtle)
padding: 14px
```
- 기본 템플릿 불러오기 버튼 (templateAvailable=true일 때)
- 항목 추가 폼 (+ 항목명 입력 + 관련페이지 입력 + 추가 버튼)

---

### 4.9 NoticesPage `/notices`

#### 헤더
```
display: flex; justify-content: space-between; align-items: center
h2: "공지사항" — 24px serif 600
관리자(Admin Token 있을 때만): "+ 공지 작성" accent 버튼
```

#### 공지 카드 목록
```
각 카드:
  background: var(--bg-surface)
  border: 1px solid var(--border-subtle)
  border-radius: var(--radius-lg)
  overflow: hidden

헤더 영역 (클릭으로 접기/펼치기):
  padding: 16px
  cursor: pointer
  :hover → background: var(--bg-elevated)

  제목 행:
    공지 제목: 15px sans 600, color var(--text-primary)
    📎 아이콘 (첨부파일 있을 때): <Paperclip /> 14px, color var(--text-tertiary)
  
  메타 행:
    게시자: 12px sans 500, color var(--text-secondary)
    날짜: 12px mono, color var(--text-tertiary)
    화살표: <ChevronDown /> → 펼쳐질 때 rotate(180deg) (transition)

본문 영역 (펼쳐진 상태):
  border-top: 1px solid var(--border-subtle)
  padding: 16px
  
  내용: 14px sans 400, line-height: 1.7, white-space: pre-wrap
  
  첨부파일 링크:
    display: inline-flex; align-items: center; gap: 8px
    padding: 8px 14px
    background: var(--bg-elevated)
    border: 1px solid var(--border-subtle)
    border-radius: var(--radius-sm)
    font-size: 13px; color: var(--text-secondary)
    text-decoration: none
    <Paperclip /> 14px + 파일명 + 파일크기
    :hover → background: var(--bg-muted)
  
  삭제 버튼 (관리자만):
    margin-top: 12px
    color: var(--danger); font-size: 13px
    border: 1px solid var(--danger-muted)
    border-radius: var(--radius-sm); padding: 5px 12px
    background: transparent
    :hover → background: var(--danger-muted)
```

#### NoticePopup (공지 팝업)

```
overlay:
  position: fixed; inset: 0; z-index: 1000
  background: var(--overlay)
  display: flex; align-items: center; justify-content: center
  padding: 20px

카드:
  background: var(--bg-surface)
  border-radius: var(--radius-xl)
  padding: 28px 24px 24px
  max-width: 440px; width: 100%
  box-shadow: var(--shadow-lg)
  max-height: 80vh; overflow-y: auto

상단 행:
  "📢 공지사항" 배지: background var(--warning-muted), color var(--warning), 12px sans 700, radius full
  닫기 버튼 X: 우측, ghost 24px

제목: 20px serif 700, color var(--text-primary), margin: 12px 0 8px

메타: 게시자 + 날짜 — 13px sans, color var(--text-secondary), gap 12px

내용: 15px sans 400, line-height 1.7, white-space: pre-wrap

첨부파일: 위와 동일 스타일

확인 버튼: 100% width, accent primary, 14px 패딩, margin-top 20px
```

#### NoticeForm (공지 작성 폼, 관리자)
```
settings-card 스타일 컨테이너

필드:
  제목: input
  내용: textarea (rows=6, resize: vertical)
  게시자: input (currentUser.name 기본값)
  첨부파일: input[type=file] (스타일링된 버튼)
  
파일 업로드 버튼:
  display: block; padding: 10px 16px
  border: 1.5px dashed var(--border-default)
  border-radius: var(--radius-md)
  text-align: center
  color: var(--text-secondary); font-size: 13px
  cursor: pointer
  :hover → border-color var(--accent); color var(--accent)

등록 버튼: accent primary, "공지 등록"
```

---

### 4.10 SettingsPage `/settings`

#### 구조 (카드 스택)
1. **사용자 정보 카드**
2. **Gemini API Key 카드**
3. **Admin Token 카드**
4. **화면 설정 카드**
5. **데이터 관리 카드**

#### 사용자 정보 카드
```
아바타:
  width: 44px; height: 44px; border-radius: var(--radius-full)
  background: var(--accent); color: var(--text-inverse)
  font-size: 20px; font-weight: 700; font-family: var(--font-serif)
  display: flex; align-items: center; justify-content: center
  (이름 첫 글자)

이름: 16px sans 600, color var(--text-primary)
사번: "사번: {sabun}" — 13px mono, color var(--text-secondary)

로그아웃 버튼: 작은 outline 버튼, color var(--danger), border-color var(--danger-muted)
```

#### settings-card 공통 스펙
```
background: var(--bg-surface)
border: 1px solid var(--border-subtle)
border-radius: var(--radius-lg)
padding: 20px

h3: 13px sans 700, color var(--text-secondary), 
     letter-spacing: 0.06em, text-transform: uppercase
     margin-bottom: 14px

setting-row (체크박스 행):
  display: flex; align-items: center; justify-content: space-between
  padding: 10px 0
  border-bottom: 1px solid var(--border-subtle) (마지막 제외)
  
  텍스트 영역:
    strong: 14px sans 600, color var(--text-primary)
    small: 12px sans 400, color var(--text-tertiary), display block
  
  toggle (checkbox):
    width: 44px; height: 24px (토글 스위치 스타일)
    appearance: none; cursor: pointer
    background: var(--bg-muted); border-radius: var(--radius-full)
    :checked → background: var(--accent)
    pseudo-element 흰 원이 슬라이드
```

---

### 4.11 AdminPage `/admin`

```
뒤로 가기: ← 설정
h2: "관리자 문서 관리"

표준지침 상태 카드:
  "문서 N개 · 청크 N개" — 14px mono
  새로고침 버튼: outline 버튼

고급 PDF 파싱 카드:
  pdfplumber 안내 텍스트
  문서명/버전/개정일 인풋
  파일 업로드 버튼 (dashed border style)

인덱싱된 문서 목록:
  각 행: 문서명(15px serif) + 청크수/버전(12px mono) 
  border-bottom 구분
```

---

### 4.12 PdfViewerPage `/pdf-viewer`

```
전체: dark 배경 (유지, 기존 코드 그대로)
toolbar:
  background: #1E1D1A  ← dark 유지
  높이: 56px
  문서명: var(--font-serif), 14px
  페이지 입력: var(--font-mono), tabular-nums

하단 컨트롤:
  이전/다음 버튼: 최소 48×48px (현장 사용성)
  페이지/전체: var(--font-mono) tabular-nums
```

---

## 5. 공통 컴포넌트 카탈로그

### 5.1 Button 변형

| 변형 | 클래스 | 배경 | 텍스트 | 테두리 |
|------|--------|------|--------|--------|
| Primary | `.btn-primary` | var(--accent) | white | none |
| Outline | `.btn-outline` | transparent | var(--text-primary) | 1px border-default |
| Ghost | `.btn-ghost` | transparent | var(--text-secondary) | none |
| Danger | `.btn-danger` | var(--danger) | white | none |
| Danger Outline | `.btn-danger-outline` | transparent | var(--danger) | 1px danger-muted |

**공통 버튼 기본값**
```css
padding: 10px 18px;
border-radius: var(--radius-md);
font-size: 14px; font-weight: 600; font-family: var(--font-sans);
cursor: pointer; border: none;
transition: var(--transition-fast);
min-height: 44px;    /* 터치 타깃 */
```

### 5.2 Card 기본 스펙
```css
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-4);
  box-shadow: var(--shadow-xs);
}
.card:hover {
  border-color: var(--border-default);
  box-shadow: var(--shadow-sm);
}
```

### 5.3 Input / Textarea 기본
```css
.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: 15px; font-family: var(--font-sans);
  background: var(--bg-elevated);
  color: var(--text-primary);
  transition: border-color var(--transition-fast);
}
.form-input:focus {
  outline: none;
  border-color: var(--accent);
  background: var(--bg-surface);
  box-shadow: 0 0 0 3px var(--accent-muted);
}
```

### 5.4 로딩 스피너
```css
.spinner {
  width: 18px; height: 18px;
  border: 2px solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
```

### 5.5 Empty State
```css
.empty-hint {
  text-align: center;
  padding: var(--space-12) var(--space-6);
  color: var(--text-tertiary);
  font-size: 14px; line-height: 1.6;
}
/* 아이콘(lucide) 40px + 텍스트 조합 */
```

### 5.6 Page Header
```css
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: var(--space-4);
}
.page-header h2 {
  font-family: var(--font-serif);
  font-size: 24px; font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  word-break: keep-all;
}
```

### 5.7 Section Stack
```css
.stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
```

---

## 6. 인터랙션 & 애니메이션

### 6.1 페이지 전환
```css
/* 페이지 fade-in */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}
.page-shell > * {
  animation: fadeIn 160ms ease-out;
}
```

### 6.2 체크 항목 토글
```css
/* 체크 버튼 클릭 시 */
@keyframes checkPop {
  0%   { transform: scale(1); }
  40%  { transform: scale(0.88); }
  100% { transform: scale(1); }
}
.check-toggle:active { animation: checkPop 120ms ease; }
```

### 6.3 공지 카드 펼치기/접기
```css
/* ChevronDown 회전 */
.notice-card-header .chevron {
  transition: transform var(--transition-base);
}
.notice-card.expanded .chevron {
  transform: rotate(180deg);
}
```

### 6.4 로그인 버튼 로딩
```css
.login-btn.loading {
  pointer-events: none;
  opacity: 0.7;
}
.login-btn.loading::after {
  content: '';
  display: inline-block;
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-left: 8px;
  vertical-align: -3px;
}
```

### 6.5 팝업 등장
```css
@keyframes popupIn {
  from { opacity: 0; transform: scale(0.95) translateY(8px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}
.notice-popup-card {
  animation: popupIn 200ms cubic-bezier(0.16, 1, 0.3, 1);
}
```

---

## 7. 다크모드

### 7.1 토글 방식
- `document.documentElement.setAttribute('data-theme', 'dark')` / `'light'`
- localStorage에 `'facility-standard:theme'` 저장
- 시스템 설정 감지: `prefers-color-scheme: dark` 초기값 사용

### 7.2 App.js에 추가 필요
```javascript
// App 컴포넌트 useEffect에 추가
useEffect(() => {
  const saved = localStorage.getItem('facility-standard:theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = saved || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', theme);
}, []);
```

### 7.3 SettingsPage에 다크모드 토글 추가
화면 설정 카드에 "다크모드" 토글 추가 (localStorage 연동)

---

## 8. 접근성 (Accessibility)

### 8.1 필수 요구사항
- **WCAG AA**: 모든 텍스트/배경 대비 ≥ 4.5:1 (일반), ≥ 3:1 (큰 텍스트)
- **터치 타깃**: 모든 버튼·링크·토글 최소 **44×44px** (현장 장갑 대응)
- **포커스 링**: `outline: 2px solid var(--accent); outline-offset: 2px`
- **aria-label**: 아이콘 전용 버튼에 반드시 추가
- **color-only 정보 없음**: 상태는 색 + 텍스트/아이콘 병용

### 8.2 체크리스트 토글 접근성
```html
<button
  aria-label={`${item.text} — 현재 상태: ${status}`}
  aria-pressed={status !== '미체크'}
  onClick={cycleStatus}
>
  {STATUS_ICONS[status]}
</button>
```

---

## 9. 구현 체크리스트

### Phase 1: 기반 (토큰·폰트·리셋) — 1일
- [ ] Google Fonts import (Source Serif 4, JetBrains Mono)
- [ ] Pretendard CDN import
- [ ] CSS variables 전체 정의 (light + dark)
- [ ] CSS reset 업데이트 (box-sizing, margin, padding)
- [ ] `font-family: var(--font-sans)` 전역 적용
- [ ] 다크모드 JS 토글 App에 추가
- [ ] `word-break: keep-all` 전역 적용

### Phase 2: 공통 컴포넌트 — 1일
- [ ] `.btn-primary` `.btn-outline` `.btn-ghost` `.btn-danger` 재정의
- [ ] `.card` 기본 스타일
- [ ] `.form-input` `.form-select` `.form-textarea` 재정의
- [ ] `.spinner` (CSS only)
- [ ] `.page-header` 재정의
- [ ] `.stack` gap 값
- [ ] StatusBadge 색상 업데이트
- [ ] BottomNav 새 디자인 (lucide 아이콘 적용)

### Phase 3: LoginPage — 0.5일
- [ ] 카드 중앙 정렬 레이아웃
- [ ] 필드 스타일 (serif label, 포커스 링)
- [ ] 드롭다운 스크롤 스타일
- [ ] 에러 메시지 스타일
- [ ] 버튼 로딩 상태 (disabled + spinner)
- [ ] 기능 검증: 이름+사번 불일치 → 에러 표시, 일치 → 홈 진입

### Phase 4: HomePage — 0.5일
- [ ] serif 타이틀 + 인사말
- [ ] 2×2 카드 그리드 재디자인
- [ ] 법제처 링크 카드 재디자인
- [ ] 빠른 검색 칩 재디자인 (pill 스타일)
- [ ] 기능 검증: 모든 카드 링크 동작, 칩 클릭 → 검색 이동

### Phase 5: SearchPage — 1일
- [ ] sticky 검색 바
- [ ] AI 답변 패널 (serif 본문, 좌측 accent 라인)
- [ ] SearchSection `<details>` 재디자인
- [ ] CompanyResultCard (accent border-left)
- [ ] RagChunkCard (info border-left)
- [ ] KcscCard
- [ ] 기능 검증: 검색 결과 렌더링, PDF 보기 버튼, 각 섹션 접기/펼치기

### Phase 6: ChecklistPages — 1일
- [ ] ChecklistPage 공종 카드 재디자인 (lucide 아이콘, progress)
- [ ] ChecklistDetailPage 진행률 바
- [ ] 체크 토글 버튼 4단계 색상 (기능 유지 필수)
- [ ] 항목 추가/편집 폼
- [ ] 기능 검증: 토글 클릭 → API 호출 → 상태 저장, 템플릿 불러오기

### Phase 7: Site/Notice Pages — 1일
- [ ] SiteListPage 카드 재디자인
- [ ] SiteDetailPage 탭 재디자인
- [ ] DrawingReviewForm / SiteIssueForm 인라인 폼
- [ ] NoticesPage 공지 카드 (접기/펼치기 애니메이션)
- [ ] NoticeForm (관리자 폼)
- [ ] NoticePopup 애니메이션
- [ ] 기능 검증: CRUD 모두 동작, 팝업 확인 후 재표시 안 됨

### Phase 8: Settings/Admin/PDFViewer — 0.5일
- [ ] SettingsPage 사용자 아바타 카드
- [ ] Toggle switch 스타일
- [ ] AdminPage 파일 업로드 버튼 (dashed)
- [ ] PdfViewerPage: 하단 컨트롤 큰 버튼
- [ ] 기능 검증: API 키 저장, 문서 업로드, PDF 렌더링

### Phase 9: QA — 0.5일
- [ ] WCAG 대비 검사 (Chrome 접근성 패널)
- [ ] 모든 라우트 이동 테스트
- [ ] API 통신 테스트 (로그인, 체크리스트, 공지, 검색)
- [ ] 다크모드 전환 시 모든 화면 확인
- [ ] 모바일 (375px, 390px) + 태블릿 (768px) 확인
- [ ] 오프라인 시 에러 메시지 표시 확인

---

## 부록 A: 현재 API 엔드포인트 전체 목록

### 인증
- `GET /api/auth/sites` → 현장 목록 30개
- `POST /api/auth/login` → `{name, sabun, site_name}` → 이름+사번 검증

### 표준 검색
- `GET /api/standards` → 표준 항목 목록 (JSON)
- `POST /api/ask` → AI 답변 (body: `{query, context_chunks}`)

### RAG (문서 검색)
- `GET /api/rag/status` → 문서/청크 수
- `GET /api/rag/documents` → 업로드된 문서 목록
- `POST /api/rag/upload` → 일반 PDF 업로드 (FormData)
- `POST /api/rag/parse-pdf` → 고급 파싱 업로드 (FormData)
- `GET /api/rag/documents/{id}/file` → PDF 파일 다운로드
- `GET /api/rag/search?q=...` → 청크 검색

### 현장이슈
- `GET /api/sites` → 현장 목록
- `POST /api/sites` → 현장 생성
- `GET /api/sites/{id}` → 현장 상세 + 도면검토 + 현장이슈
- `PUT /api/sites/{id}` → 현장 수정
- `DELETE /api/sites/{id}` → 현장 삭제
- `POST /api/drawing-reviews` → 도면검토 추가
- `PUT /api/drawing-reviews/{id}` → 도면검토 수정
- `DELETE /api/drawing-reviews/{id}` → 도면검토 삭제
- `POST /api/site-issues` → 현장이슈 추가
- `PUT /api/site-issues/{id}` → 현장이슈 수정
- `DELETE /api/site-issues/{id}` → 현장이슈 삭제

### 체크리스트
- `GET /api/checklists?site_id=X` → 공종별 진행률 (현장 공유)
- `GET /api/checklists/{trade}?site_id=X` → 공종 상세 (항목+기록)
- `POST /api/checklists/items` → 항목 추가
- `PUT /api/checklists/items/{id}` → 항목 수정
- `DELETE /api/checklists/items/{id}` → 항목 삭제
- `POST /api/checklists/load-template` → 기본 템플릿 불러오기
- `POST /api/checklists/record` → 체크 상태 저장
- `DELETE /api/checklists/record/{id}` → 체크 기록 삭제

### 공지사항
- `GET /api/notices` → 공지 목록 (최신순)
- `POST /api/notices` → 공지 등록 (X-Admin-Token 필요)
- `DELETE /api/notices/{id}` → 공지 삭제 (X-Admin-Token 필요)
- `GET /api/notices/{id}/file` → 첨부파일 다운로드

---

## 부록 B: 화면-컴포넌트 매핑

```
App.jsx
├── LoginPage (진입 로그인)
├── NoticePopup (팝업, 조건부 렌더링)
└── BrowserRouter
    ├── / → HomePage
    │   └── QuickChips
    ├── /search → SearchPage
    │   ├── AiAnswerPanel
    │   ├── SearchSection
    │   │   ├── CompanyResultCard (×N)
    │   │   ├── RagChunkCard (×N)
    │   │   └── KcscCard (×N)
    ├── /item/:id → DetailPage
    ├── /sites → SiteListPage
    ├── /sites/new → SiteFormPage
    ├── /sites/:siteId → SiteDetailPage
    │   ├── StatusBadge
    │   ├── DrawingReviewForm
    │   └── SiteIssueForm
    ├── /checklist → ChecklistPage
    ├── /checklist/:trade → ChecklistDetailPage
    │   └── CheckItem (×N)
    ├── /notices → NoticesPage
    │   └── NoticeForm (관리자만)
    ├── /settings → SettingsPage
    │   ├── GeminiKeyCard
    │   └── AdminTokenCard
    ├── /admin → AdminPage
    └── /pdf-viewer → PdfViewerPage
```

---

## 부록 C: lucide-react 설치 방법

```bash
npm install lucide-react
```

```jsx
// main.jsx 최상단에 추가
import {
  Home, Search, ClipboardList, Bell, Settings,
  Wrench, FileSearch, CheckSquare, Clipboard,
  ArrowLeft, ChevronDown, ChevronRight,
  Sparkles, ExternalLink, Paperclip, Pencil, Trash2,
  Thermometer, Wind, Cog, FlaskConical,
  X, Check
} from 'lucide-react';
```

---

## 부록 D: 핵심 불변 규칙

> 이 규칙을 어기면 앱이 동작하지 않는다.

1. **fetchJson 함수** — 시그니처, URL 경로, 헤더 로직 변경 금지
2. **useStoredState 훅** — localStorage 키 변경 금지
3. **라우트 경로** — `/`, `/search`, `/sites`, `/sites/:siteId`, `/sites/new`, `/checklist`, `/checklist/:trade`, `/notices`, `/settings`, `/admin`, `/pdf-viewer`, `/item/:id` 변경 금지
4. **체크리스트 STATUS_CYCLE** — `['미체크', '적합', '해당없음', '부적합']` 순서 변경 금지
5. **PDF URL 파라미터** — `?url=...&page=...&title=...` 형식 변경 금지
6. **X-User-Id 헤더** — encodeURIComponent(sabun) 형식 유지
7. **X-Admin-Token 헤더** — notices, sites, rag 경로에 자동 포함 유지
8. **readAdminToken()** — 설정에서 저장한 Admin Token을 읽는 함수 유지
9. **로그인 팝업 체크** — `/api/notices` → `lastNoticeId` 비교 로직 유지
10. **PdfViewerPage** — pdfjsLib 코드 전체 유지, 스타일만 변경 가능

---

**문서 끝.**  
이 PRD를 기반으로 `src/App.css` 를 전면 재작성하고, `src/main.jsx`에서는 JSX 구조와 className만 업데이트한다.  
기능 코드(이벤트 핸들러, API 호출, 상태 관리)는 절대 수정하지 않는다.
