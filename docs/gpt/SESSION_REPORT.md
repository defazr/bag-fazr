# bag.fazr.co.kr — 프로젝트 전체 보고서

> 최종 업데이트: 2026-04-26
> 이 문서는 새 세션(GPT/Claude)에서 프로젝트 컨텍스트를 완전히 복원하기 위한 것입니다.
> 이 파일을 새 세션에 첨부하면 됩니다.

---

## 1. 프로젝트 개요

| 항목 | 값 |
|------|-----|
| 서비스명 | 종량제 봉투 판매처 찾기 |
| URL | https://bag.fazr.co.kr |
| GitHub | https://github.com/defazr/bag-fazr |
| 목적 | 전국 종량제 봉투 판매처를 지역별로 검색할 수 있는 SEO 기반 서비스 |
| 배경 | 2026 나프타 공급 위기 → 종량제 봉투 품귀 → 검색 수요 급증 |
| 수익 모델 | AdSense (SEO 트래픽 기반) |
| 현재 상태 | P17.5 완료. 허브 article + 양방향 내부링크 + 홈/메뉴 동선 완성. 색인 확장 대기. |

---

## 2. 기술 스택

| 기술 | 상세 |
|------|------|
| 프레임워크 | Next.js 14 (App Router) |
| 스타일 | TailwindCSS v4 |
| 다크모드 | class 기반 (`@custom-variant dark (&:where(.dark, .dark *))`) |
| 렌더링 | ISR (revalidate=86400, 24시간) |
| 배포 | Vercel (자동 배포, main push 시) |
| 도메인 | 가비아 (bag.fazr.co.kr) |
| 데이터 | 정적 JSON (공공데이터 1회 수집 → 주소 파싱 분류) |
| 광고 | Google AdSense (활성화 완료) |
| 분석 | GA4 (G-WTTDTMNTWQ) |
| SEO | JSON-LD FAQ, OG/Twitter Card, canonical URL, sitemap.xml |

---

## 3. 데이터

- **출처**: 공공데이터포털 — 행정안전부 자원환경 쓰레기종량제봉투판매업
- **수량**: 전국 69,265곳 (dedupe 후)
- **미매칭**: 14건 (연기군/주소깨짐/군위 — 무시 가능)
- **구조**: 17개 시/도, 229개 시/군/구
- **정적 페이지**: 253개
- **Article**: 3개 (shortage-2026, why-no-bags, where-to-buy)
- **수집 방식**: collect.py v2 — 1회 전국 수집 → 주소 파싱 분류 → dedupe

### 0건 구 (API 데이터 없음 — 수정 불가)
서울 강북구/중랑구/송파구, 울산 울주군, 강원 고성군, 충남 부여군/청양군/당진시

---

## 4. 파일 구조

```
bag.fazr/
├── app/
│   ├── layout.tsx              # 루트 레이아웃 (metadata, OG, AdSense + GA4 <script> in <head>)
│   ├── page.tsx                # 홈 (hero, chips, RegionGrid, 가이드카드3개, price, FAQ, AdSlot x2)
│   ├── not-found.tsx           # 404
│   ├── globals.css             # Tailwind v4 + dark variant + ticker + slide-in animation
│   ├── sitemap.ts              # 동적 sitemap 생성 (article 3개 수동)
│   ├── [region]/
│   │   ├── page.tsx            # 시/도 (신뢰문구, DistrictGrid, where-to-buy 역방향링크, FAQ)
│   │   └── [district]/
│   │       └── page.tsx        # 구/군/시 (신뢰문구, StoreList alias검색, AdSlot x2)
│   └── article/
│       ├── where-to-buy/page.tsx   # 쓰레기봉투 파는곳 총정리 (SEO 허브, P17)
│       ├── shortage-2026/page.tsx   # 종량제 봉투 대란 이유 총정리
│       └── why-no-bags/page.tsx     # 종량제 봉투 왜 없을까?
├── components/
│   ├── layout/
│   │   ├── Header.tsx          # 좌측 "홈" + ThemeToggle + MobileMenu
│   │   ├── Footer.tsx
│   │   ├── NoticeBanner.tsx    # 상단 ticker (sticky, dismiss)
│   │   ├── MobileMenu.tsx      # 3단 구조 (CTA → 빠른이동 → 정보3개) + slide-in + ESC
│   │   ├── ThemeToggle.tsx     # 다크/라이트 토글
│   │   └── ScrollToTop.tsx
│   ├── region/
│   │   ├── RegionGrid.tsx      # 시/도 그리드 (홈)
│   │   └── DistrictGrid.tsx    # 구/군/시 그리드 (화살표→ + group hover)
│   ├── store/
│   │   ├── StoreCard.tsx       # 개별 판매처 카드
│   │   └── StoreList.tsx       # alias 검색(CU/GS등) + debounce + load-more
│   ├── seo/
│   │   ├── Breadcrumb.tsx
│   │   └── FaqSection.tsx      # FAQ 아코디언 + JSON-LD
│   ├── article/
│   │   └── RegionLinks.tsx     # 6개 지역 chip 링크 (SEO 내부링크)
│   └── ads/
│       ├── AdSlot.tsx          # AdSense 슬롯 (플랫, full-width-responsive=false)
│       └── StickyBottomAd.tsx  # 모바일 하단 (max-h-100px, fluid, sm:hidden)
├── lib/
│   ├── data.ts, regions.ts, seo.ts, types.ts
├── data/
│   ├── regions.json, {region}/, _unmatched.json
├── scripts/
│   └── collect.py              # v2: 1회 수집 + 주소 파싱 + 세종 예외 + dedupe
└── docs/
    ├── BLOG_POST_NAVER.md, SESSION_REPORT.md
    └── gpt/  SESSION_REPORT.md, GPT-HANDOFF-*.md
```

---

## 5. 디자인 규칙 (SSOT v1.7 — 절대 준수)

### 금지 사항 (중요)
- `dark:*-gray-*` 사용 금지 → 반드시 `dark:*-zinc-*`
- `*-blue-*` 사용 금지 → 파란색 전면 제거됨
- `hover:shadow-md`, `hover:border-blue-*` 금지
- `bg-zinc-800`을 카드 배경으로 금지 → `bg-zinc-900`이 정답
- 광고에 fixed/sticky 금지

### 카드
```
rounded-xl p-5 border border-gray-200 dark:border-zinc-800
bg-white dark:bg-zinc-900
hover:bg-gray-50 dark:hover:bg-zinc-800 transition duration-200
```

### CTA (article 전용)
```
박스: rounded-xl border border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 p-6 shadow-sm
버튼: rounded-xl bg-gray-900 dark:bg-zinc-700 hover:bg-gray-800 dark:hover:bg-zinc-600 text-white
```

### Article h2
```
text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4
```

### 인라인 링크 (article 본문)
```
font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition
```

---

## 6. 페이지별 구조

### 홈 (/) — 위→아래 순서
1. NoticeBanner — 품절 안내 ticker
2. Header — "홈" + ThemeToggle + MobileMenu
3. Hero — 제목 + 총 판매처 수 + 갱신일
4. 자주 찾는 지역 — 수평 스크롤 chip
5. 지역별 판매처 — RegionGrid 17시도
6. 광고: 리스트 아래 (8836749083)
7. **종량제 봉투 가이드 — article 카드 3개** (where-to-buy → shortage → why-no-bags)
8. 종량제 봉투 가격 — 미리보기 + CTA
9. FAQ — 3문항 + JSON-LD
10. 광고: 하단 (6518541657)
11. Footer + StickyBottomAd (모바일만)

### 시/도 (/[region])
- Breadcrumb → h1+신뢰문구 → DistrictGrid → 광고:리스트아래 → **where-to-buy 역방향링크** → FAQ → 인접지역 → 광고:하단

### Article (/article/where-to-buy) — 허브
- Breadcrumb → h1 → 즉시클릭(서울/경기/부산) → 도입부(→shortage링크) → **17개 시/도 허브** → CTA중간 → 파는곳종류 → 편의점 → 가격/사이즈 → 구매팁(→why-no-bags링크) → CTA하단 → RegionLinks → 정리 → FAQ → 신뢰시그널

### Article (/article/shortage-2026, why-no-bags)
- 기존 구조 + P16 인라인 링크(서울/경기/부산) + **P17 where-to-buy 인라인 링크**

---

## 7. 내부링크 구조 (P17.5 후 — 완성)

```
홈 → where-to-buy(카드1), shortage(카드2), why-no-bags(카드3)
햄버거 → where-to-buy(정보1), why-no-bags(정보2), shortage(정보3)
where-to-buy → 17개 시/도(허브), shortage(인라인), why-no-bags(인라인)
shortage → where-to-buy(인라인), 서울/경기/부산(P16)
why-no-bags → where-to-buy(인라인), 서울/경기/부산(P16)
17개 시/도 → where-to-buy(역방향링크)
```

---

## 8. 커밋 히스토리 (최신→과거, 주요)

```
5215934 Fix: shortage-2026 한글 깨짐 복구
ae09f66 P17.5: 홈 카드 3개 확장 + 햄버거 메뉴 where-to-buy 추가
8e47352 P17: where-to-buy 허브 페이지 + 양방향 내부링크 구축
615e669 P16: Crawl priority boost - reorder regions + inline article links
70cc412 P15: Add region internal links to articles for SEO crawl path
0dc9e3d P14: District card CTR improvement with arrow and hover
36ed6a8 P13: trust message, search alias, ad placement, remove 준비중
ae1b916 Rewrite collect.py v2: single-fetch + Sejong fix (69,265 stores)
... (이전 커밋 생략)
```

---

## 9. 다음 단계 (우선순위순)

1. **GSC 수동 색인 요청 5건** — /, /article/where-to-buy, /seoul, /gyeonggi, /busan
2. **4/29 체크포인트** — 색인 8→10+ 확인
3. **P18 방향 결정** — price 페이지 (MO 22,200) 유력
4. 네이버 블로그 게시 — docs/BLOG_POST_NAVER.md
5. 데이터 갱신 구조 검토

---

## 10. 핵심 교훈 / 주의사항

1~17번은 이전 보고서와 동일 (dark:zinc, blue 금지, AdSense 등)

18. **Edit tool 한글 바이트 손상** — Edit 시 한글 문자열이 깨질 수 있음. 커밋 전 반드시 확인.
19. **where-to-buy = SEO 허브** — 17개 시/도 전부 링크 포함. 다른 article과 양방향 연결.
20. **docs/md 커밋 시 [skip ci]** — 문서 변경은 빌드 불필요.

---

## 11. 작업 스타일 규칙

- **지시서 기반**: 사용자가 구조/지시서를 주고, AI가 실행
- **"해라" = 즉시 실행**: 추가 확인 불필요
- **의견 요청 시**: 근거와 함께 명확한 판단 제시
- **새 세션**: 이 문서 첨부 → 지시서 대기
- **커밋**: 작업 완료 후 사용자 확인 받고 push
- **GPT 지시서**: 무조건 의견 제시부터. 맹목적 실행 금지
- **검토만**: 사용자가 "검토만"이라고 하면 수정하지 말고 의견만 제시
- **docs/md 커밋**: 메시지에 [skip ci] 붙이기
