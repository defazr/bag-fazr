# bag.fazr.co.kr — 프로젝트 전체 보고서

> 최종 업데이트: 2026-03-26
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
| 현재 상태 | 개발+UI+SEO+콘텐츠+광고 전체 완료. 트래픽 확산 + 모니터링 단계 |

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
| 데이터 | 정적 JSON (공공데이터포털 API 1회 수집) |
| 광고 | Google AdSense (활성화 완료) |
| SEO | JSON-LD FAQ, OG/Twitter Card, canonical URL, sitemap.xml |

---

## 3. 데이터

- **출처**: 공공데이터포털 — 행정안전부 자원환경 쓰레기종량제봉투판매업
- **수량**: 전국 69,615곳
- **매칭률**: 99.99% (미매칭 4건, 무시 가능)
- **구조**: 17개 시/도, 229개 시/군/구
- **정적 페이지**: 253개 (홈 + 17 region + 229 district + articles + 404 + sitemap)
- **수집 방식**: Python 스크립트로 API 호출 → JSON 저장 → Next.js에서 직접 import
- **주소 파싱**: normalize + 시/도 우선 매칭 (동명 구 문제 해결: 동구/서구/남구/북구/중구)
- **재분류**: reclassify_all.py로 전체 재분류 완료

### API 정보
- 행정안전부_자원환경_쓰레기종량제봉투판매업
- 일일 한도: 10,000건
- localCode 전국: 6110000_ALL (서울 코드지만 전국 반환)
- 필터: SALS_STTS_CD="01" (영업/정상)

### 0건 구 (API 데이터 없음)
서울 강북구/중랑구/송파구, 울산 울주군, 강원 고성군, 충남 부여군/청양군/당진시

### 종량제 봉투 가격 참고 (인천 기준)

| 구분 | 크기 | 가격 |
|------|------|------|
| 일반용(재사용) | 3L | 90원 |
| | 5L | 130원 |
| | 10L | 250원 |
| | 20L | 490원 |
| | 30L | 740원 |
| | 50L | 1,250원 |
| | 75L | 1,880원 |
| PP마대 | 20L | 2,040원 |
| 음식물(가정) | kg당 130원 / L당 100원 (2L=190원) |
| 음식물(소형음식점) | kg당 190원 / L당 140원 |
| 음식물(다량배출) | kg당 230원 / L당 170원 |

※ 가격은 지자체마다 다름. 위는 인천 기준 참고값.

---

## 4. 파일 구조

```
bag.fazr/
├── app/
│   ├── layout.tsx              # 루트 레이아웃 (metadata, OG, 검색엔진 인증, AdSense <script> in <head>)
│   ├── page.tsx                # 홈 (hero, chips, RegionGrid, articles, price, FAQ, AdSlot x2)
│   ├── not-found.tsx           # 404
│   ├── globals.css             # Tailwind v4 + dark variant + ticker + slide-in animation
│   ├── sitemap.ts              # 동적 sitemap 생성
│   ├── [region]/
│   │   ├── page.tsx            # 시/도 페이지 (DistrictGrid, FAQ, 인접 지역, AdSlot x2)
│   │   └── [district]/
│   │       └── page.tsx        # 구/군/시 페이지 (StoreList, 안내박스, FAQ, 인접지역, AdSlot x2)
│   └── article/
│       ├── shortage-2026/
│       │   └── page.tsx        # 종량제 봉투 대란 이유 총정리
│       └── why-no-bags/
│           └── page.tsx        # 종량제 봉투 왜 없을까? 직접 확인해봤습니다
├── components/
│   ├── layout/
│   │   ├── Header.tsx          # 좌측 "홈" + ThemeToggle + MobileMenu
│   │   ├── Footer.tsx          # 하단 footer
│   │   ├── NoticeBanner.tsx    # 상단 ticker (sticky, dismiss, localStorage)
│   │   ├── MobileMenu.tsx      # 3단 구조 (CTA → 빠른이동 → 정보) + slide-in + ESC
│   │   ├── ThemeToggle.tsx     # 다크/라이트 토글 (system detection + localStorage)
│   │   └── ScrollToTop.tsx     # 스크롤 300px 이후 표시
│   ├── region/
│   │   ├── RegionGrid.tsx      # 시/도 그리드 (홈에서 사용)
│   │   └── DistrictGrid.tsx    # 구/군/시 그리드 (region 페이지에서 사용)
│   ├── store/
│   │   ├── StoreCard.tsx       # 개별 판매처 카드
│   │   └── StoreList.tsx       # "use client" — 검색(200ms debounce) + load-more(15개씩)
│   ├── seo/
│   │   ├── Breadcrumb.tsx      # 빵크럼 네비게이션
│   │   └── FaqSection.tsx      # FAQ 아코디언 + JSON-LD (border-t 분리선 + transition)
│   └── ads/
│       ├── AdSlot.tsx          # AdSense 슬롯 (mount guard + pushed ref, 플랫 컨테이너)
│       └── StickyBottomAd.tsx  # 모바일 하단 광고 (max-h-100px, fluid, sm:hidden)
├── lib/
│   ├── data.ts                 # JSON 데이터 로딩 (getRegionsData, getDistrictData, getRegionIndex)
│   ├── regions.ts              # REGIONS 상수, slug↔name 매핑, getDistrictsByRegion
│   ├── seo.ts                  # generateFaqSchema, getDistrictFaqs, getRegionFaqs
│   └── types.ts                # Store, RegionMeta, RegionIndexEntry 타입
├── public/
│   ├── og-default.jpg          # OG 이미지 (1200x630, 78KB)
│   ├── favicon.ico
│   ├── apple-touch-icon.png
│   ├── ads.txt                 # google.com, pub-7976139023602789, DIRECT, ...
│   └── robots.txt              # User-agent, Sitemap, DaumWebMasterTool
├── data/
│   ├── regions.json            # 17개 시/도 인덱스
│   ├── {region}/index.json     # 각 시/도별 구/군/시 목록
│   ├── {region}/{district}.json # 각 구/군/시별 판매처 데이터
│   └── _unmatched.json         # 미매칭 4건
├── scripts/
│   ├── collect.py              # API 수집
│   └── reclassify_all.py       # 전체 재분류
└── docs/
    ├── BLOG_POST_NAVER.md      # 네이버 블로그 복붙 템플릿
    ├── SESSION_REPORT.md       # Claude용 세션 보고서
    └── gpt/
        └── SESSION_REPORT.md   # 이 문서 (GPT/Claude 공용)
```

---

## 5. 디자인 규칙 (SSOT v1.7 — 절대 준수)

### 카드
```
rounded-xl p-5 border border-gray-200 dark:border-zinc-800
bg-white dark:bg-zinc-900
hover:bg-gray-50 dark:hover:bg-zinc-800 transition duration-200
```

### 버튼
```
rounded-xl border border-gray-200 dark:border-zinc-700
bg-white 또는 bg-gray-50 dark:bg-zinc-800
text-gray-700 dark:text-white
hover:bg-gray-50 또는 hover:bg-gray-100 dark:hover:bg-zinc-700
```

### 텍스트 (다크모드)
| 용도 | 클래스 |
|------|--------|
| 제목 (h1, h2) | dark:text-white |
| 본문 (article) | dark:text-zinc-300 |
| 본문 (일반) | dark:text-zinc-400 |
| 보조 텍스트 | dark:text-zinc-500 |
| body 배경 | dark:bg-zinc-950 |
| 카드 배경 | dark:bg-zinc-900 |
| 테두리 | dark:border-zinc-800 |

### CTA (article 전용)
```
박스: rounded-xl border border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 p-6 shadow-sm
버튼: rounded-xl bg-gray-900 dark:bg-zinc-700 hover:bg-gray-800 dark:hover:bg-zinc-600 text-white
```

### 3-layer 체계 (다크모드)
1. 배경: bg-zinc-950
2. 콘텐츠: bg-transparent
3. 강조 (CTA): bg-zinc-800 → 버튼 bg-zinc-700

### 금지 사항 (중요)
- ❌ `dark:*-gray-*` 사용 금지 → 반드시 `dark:*-zinc-*`
- ❌ `*-blue-*` 사용 금지 → 파란색 전면 제거됨
- ❌ `hover:shadow-md`, `hover:border-blue-*` 금지
- ❌ `bg-zinc-800`을 카드 배경으로 금지 → `bg-zinc-900`이 정답
- ❌ CTA 문구와 실제 연결 페이지 불일치 금지
- ❌ 광고에 fixed/sticky 금지

### 여백
- 섹션 간: `mt-10`
- 버튼 위: `mt-8`
- 카드 내부: `p-5`
- FAQ 컴포넌트: `mt-12 border-t border-gray-200 dark:border-zinc-800 pt-10` (내장)

### Article h2 스타일
```
text-lg font-bold text-gray-900 dark:text-white
border-l-4 border-orange-400 pl-3 mt-10 mb-4
```

---

## 6. 페이지별 구조

### 홈 (/) — 위→아래 순서
1. NoticeBanner — 품절 안내 ticker (sticky top, dismiss 가능)
2. Header — "홈" 링크 + ThemeToggle + MobileMenu
3. Hero — 제목 + 총 판매처 수 + 갱신일 (`mt-10`)
4. 자주 찾는 지역 — 수평 스크롤 chip (강남구, 송파구, 서초구, 수원시, 성남시, 해운대구)
5. 광고: 상단 (8836749083)
6. 지역별 판매처 — RegionGrid 17시도 (`id="regions"`)
7. 종량제 봉투 이슈 — article 2개 카드 (shortage-2026, why-no-bags)
8. 종량제 봉투 가격 — 10L/20L/50L 미리보기 + "판매처 확인하기" CTA (`#regions` 앵커)
9. FAQ — 3문항 + JSON-LD
10. 광고: 하단 (6518541657)
11. Footer
12. StickyBottomAd (모바일만, max-h-100px)

### 시/도 (/[region])
- Breadcrumb → h1 → 광고:상단 → DistrictGrid → FAQ → 인접 지역 pills → 광고:하단

### 구/군/시 (/[region]/[district])
- 데이터 있는 경우: Breadcrumb → h1 → 통합 안내박스(yellow) → StoreList → 광고:리스트아래 → 인접지역 → 안내 콘텐츠 → 함께 많이 찾는 정보 → 다른 지역 → FAQ → 광고:하단 → 신뢰 시그널
- 0건인 경우: Breadcrumb → h1 → 통합 안내박스(yellow, 구매가능장소 포함) → 인접지역 그리드 → FAQ → CTA 버튼

### Article (/article/*)
SSOT v1.6 + v1.7 구조:
1. 공감 도입 → 2. 문제 확대 → 3. 원인 설명 → 4. 해결 방향 → 5. CTA 중간 (href="/") → 6. 현실 팁 → 7. CTA 하단 (href="/") → 8. 정리
- 최소 1200자, 섹션 5개 이상, CTA 최소 2개
- 외부 링크 금지, 뉴스 기사 톤 금지
- FAQ 마지막: "우리 동네 판매처는 어디서 확인할 수 있나요?"
- 본문: dark:text-zinc-300, CTA 박스: dark:bg-zinc-800 shadow-sm, CTA 버튼: dark:bg-zinc-700

### 모바일 메뉴 (MobileMenu)
3단 구조:
1. ① CTA — "종량제 봉투 판매처 확인하기 →" (유일한 `/` 링크)
2. ② 빠른 이동 — 서울, 경기, 부산, 인천
3. ③ 정보 — 왜 봉투가 없을까?, 종량제 봉투 대란 이유
- 슬라이드 인 (200ms), ESC 닫기, backdrop 클릭 닫기

---

## 7. AdSense 설정 (활성화 완료)

| 항목 | 값 |
|------|-----|
| Publisher ID | ca-pub-7976139023602789 |
| Slot 1 (상단) | 8836749083 |
| Slot 2 (리스트 아래) | 7831623329 |
| Slot 3 (하단) | 6518541657 |
| Slot 4 (모바일 하단) | 3611374960 |

### 광고 기술 결정 (중요 — 삽질 기록)
1. `next/script` 사용 금지 → AdSense가 `data-nscript` 속성 거부. `<head>`에 일반 `<script>` 태그 사용
2. `data-full-width-responsive="false"` 필수 → true면 광고가 컨테이너 밖으로 확장
3. 광고 컨테이너: 플랫 (border/padding 없음) → 테두리 넣으면 광고와 안 맞음
4. fixed/sticky 금지 → 콘텐츠 덮음. 일반 흐름(my-10)에 넣기
5. StickyBottomAd: `max-h-[100px] overflow-hidden` + `format="fluid"` → auto면 280px짜리 나옴
6. AdSlot 중복 방지: `mounted` state + `pushed` ref 이중 가드

---

## 8. 검색엔진 등록 상태

| 엔진 | 상태 | 방법 |
|------|------|------|
| Google | 색인 제출 완료 | Search Console sitemap + URL 요청 |
| 네이버 | 메타태그 적용 완료 | `naver-site-verification` in layout.tsx metadata |
| 다음 | robots.txt 적용 완료 | `#DaumWebMasterTool:...` in public/robots.txt |

---

## 9. 커밋 히스토리 (최신→과거)

```
5605af1 Bottom ad: limit height to 100px, use fluid format instead of auto
050244d Ad slots: remove border/padding, flat display only
851ab41 Fix ad overflow: disable full-width-responsive to keep ads inside container
66668c9 Fix AdSense: replace next/script with plain script tag to avoid data-nscript error
0f8823c Ad slots: wrap in card box for content-like appearance
f187f52 P10: fix ad layout — remove fixed/sticky/overflow, ads flow with content
67dcbeb P9: mobile menu UX upgrade — 3-section layout (CTA, quick nav, articles) + slide-in
614c4a2 Enable AdSense: uncomment Script, AdSlot, StickyBottomAd across all pages
1f563df SSOT v1.7: article design polish — CTA emphasis, text contrast, orange bar
cb82aee SSOT compliance: rounded-lg → rounded-xl on cards/inputs/buttons
db161ce Unify all CTA text to '종량제 봉투 판매처 확인하기 →'
eff62d6 Update GPT session report: full stack, design rules, file structure
0ea3395 Fix misleading CTA: '가격 확인' → '판매처 확인'
52e0571 Article h2: add orange left border bar for visual hierarchy
d19e2c4 Fix price CTA: scroll to #regions instead of self-link
f4d4673 Home: add article cards + price teaser block
447bdc5 Add '우리 동네 판매처 확인' FAQ to both articles
c2e9abe Rewrite articles as conversion pages (SSOT v1.6)
383820c Add Naver/Daum site verification
d6dcbb4 Header: change logo text to 홈
eb96d51 OG image, favicon, twitter card metadata (SSOT v1.4)
57c89cd SSOT v1.3 final: zinc unify, blue removal, notice merge, spacing cleanup
2e79eb2 UI cleanup v1.3: unified card/button styling, remove blue accents, merge notice boxes
4dd95ca Dark mode: article pages + 404 page full coverage
3d94369 Update popular districts: population-based selection
8cde49f Quick navigation: popular districts on home + clearer search placeholder
9f4c483 List UX: client-side search + load-more (15 initial, +15 per click)
bf90347 Dark mode polish: unified buttons, text hierarchy, CTA spacing
63fe205 Dark mode tone fix: reduce contrast, cards flush with background
1549017 Dark mode: full card/text/border coverage across all layers
0c39a13 SSOT v1.1: UI/UX overhaul — ticker bar, dark mode, scroll-to-top, hamburger menu
dee3298 Fix AdSlot: prevent duplicate ad creation with mount guard
19c36b2 Comment out AdSense ads temporarily for design work
d61a181 Add trust UX, notice banner, AdSense 4-slot, ads.txt
311f697 Update session reports: Claude memory + GPT folder
15a5103 Add blog-style article for external traffic + Naver blog template
2376f3e CTR + click optimization: hooks, mid-CTA, urgency signals
281fbdb Add shortage article page for traffic activation
4e2ecd2 Add traffic growth optimizations: content blocks, CTR boost, trust signals
863064f Fix data misclassification + SEO Phase 1 optimization
3751c31 Initial release: 종량제 봉투 판매처 찾기 서비스
```

---

## 10. 다음 단계 (우선순위순)

1. **네이버 블로그 게시** — docs/BLOG_POST_NAVER.md 복붙
2. **트래픽 모니터링** — Google Analytics / Search Console 확인
3. **가격 전용 페이지** — 현재 홈에 미리보기만 있음. 지역별 상세 가격표 필요
4. **데이터 갱신** — 현재 1회 수집. 주기적 갱신 구조 검토

---

## 11. 핵심 교훈 / 주의사항

1. **dark:*-gray 금지** — 반드시 dark:*-zinc. 한 곳이라도 gray 쓰면 톤 깨짐
2. **파란색 금지** — blue-* 클래스 절대 사용 안 함. neutral 톤만
3. **AdSense + Next.js** — next/script 사용 금지 (data-nscript 에러). 일반 `<script>` in `<head>` 사용
4. **광고 fixed/sticky 금지** — 콘텐츠 덮음. 일반 흐름에 넣기
5. **data-full-width-responsive="false"** — true면 광고가 컨테이너 밖으로 확장
6. **광고 컨테이너 플랫** — border/padding 넣으면 광고와 안 맞음
7. **StickyBottomAd max-h-100px** — format="auto"면 280px짜리 나옴. fluid + max-h 필수
8. **공공데이터 파싱** — localCode 구 단위 필터 안 됨. 전국 데이터 반환 후 주소 파싱 분류
9. **동명 구 문제** — 동구/서구/남구/북구/중구 → 시/도 먼저 확정 후 구 매칭
10. **CTA 정직** — CTA 문구 = 실제 도착 페이지. 거짓 유도 금지
11. **홈에서 "/" 링크** — 자기 자신이므로 `#regions` 앵커 등으로 대체
12. **Tailwind v4** — `@custom-variant dark` 구문 사용. v3의 `darkMode: 'class'`와 다름
13. **중간 끊긴 작업** — 이어하지 말고 처음부터 다시 적용 (부분 적용은 더 망가뜨림)
14. **GPT 지시서 검증** — GPT가 맥락 잃고 이미 완료된 작업 다시 시키거나 잘못된 변경 지시할 수 있음. 반드시 의견 제시

---

## 12. 작업 스타일 규칙

- **지시서 기반**: 사용자가 구조/지시서를 주고, AI가 실행
- **"해라" = 즉시 실행**: 추가 확인 불필요
- **의견 요청 시**: 근거와 함께 명확한 판단 제시
- **글 작성**: AI가 담당 (사용자는 구조만 제공)
- **새 세션**: 이 문서 첨부 → 지시서 대기
- **커밋**: 작업 완료 후 사용자 확인 받고 push
- **GPT 지시서**: 무조건 의견 제시부터. 맹목적 실행 금지
