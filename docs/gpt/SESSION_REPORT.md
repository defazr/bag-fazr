# bag.fazr.co.kr — 프로젝트 전체 보고서

> 최종 업데이트: 2026-03-28
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
| 현재 상태 | 개발+UI+SEO+콘텐츠+광고+데이터품질+검색UX 전체 완료. 운영 단계 |

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
- **정적 페이지**: 252개
- **수집 방식**: collect.py v2 — 1회 전국 수집 → 주소 파싱 분류 → dedupe
- **주소 파싱**: normalize + 시/도 우선 매칭 (동명 구 문제 해결)
- **세종 처리**: 구 없음 → "세종시"(sejongsi)로 직접 매핑

### API 정보
- 행정안전부_자원환경_쓰레기종량제봉투판매업
- 일일 한도: 10,000건
- localCode: 6110000_ALL (전국 반환)
- 필터: SALS_STTS_CD="01" (영업/정상)
- API 콜: 905회 (1회 수집 구조)

### collect.py v2 주요 변경 (2026-03-28)
- 기존: 17개 시/도별 localCode 호출 (각각 전국 반환 → 중복 17배) → 15,385+ API 콜
- 변경: 1회 전국 수집 + 주소 파싱 분류 → 905 API 콜 (94% 절감)
- 세종 예외: extract_district()에서 세종특별자치시 → "세종시" 직접 반환
- dedupe: name + address 기준 중복 제거

### 0건 구 (API 데이터 없음 — 수정 불가)
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
│   ├── layout.tsx              # 루트 레이아웃 (metadata, OG, AdSense + GA4 <script> in <head>)
│   ├── page.tsx                # 홈 (hero, chips, RegionGrid, articles, price, FAQ, AdSlot x2)
│   ├── not-found.tsx           # 404
│   ├── globals.css             # Tailwind v4 + dark variant + ticker + slide-in animation
│   ├── sitemap.ts              # 동적 sitemap 생성
│   ├── [region]/
│   │   ├── page.tsx            # 시/도 (신뢰문구, DistrictGrid, AdSlot 리스트아래, FAQ)
│   │   └── [district]/
│   │       └── page.tsx        # 구/군/시 (신뢰문구, StoreList alias검색, AdSlot x2)
│   └── article/
│       ├── shortage-2026/page.tsx  # 종량제 봉투 대란 이유 총정리
│       └── why-no-bags/page.tsx    # 종량제 봉투 왜 없을까?
├── components/
│   ├── layout/
│   │   ├── Header.tsx          # 좌측 "홈" + ThemeToggle + MobileMenu
│   │   ├── Footer.tsx
│   │   ├── NoticeBanner.tsx    # 상단 ticker (sticky, dismiss)
│   │   ├── MobileMenu.tsx      # 3단 구조 (CTA → 빠른이동 → 정보) + slide-in + ESC
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
│   └── ads/
│       ├── AdSlot.tsx          # AdSense 슬롯 (플랫, full-width-responsive=false)
│       └── StickyBottomAd.tsx  # 모바일 하단 (max-h-100px, fluid, sm:hidden)
├── lib/
│   ├── data.ts                 # JSON 데이터 로딩
│   ├── regions.ts              # REGIONS 상수, slug↔name 매핑
│   ├── seo.ts                  # FAQ 생성, JSON-LD schema
│   └── types.ts                # Store, RegionMeta, RegionIndexEntry
├── public/
│   ├── og-default.jpg, favicon.ico, apple-touch-icon.png
│   ├── ads.txt, robots.txt
├── data/
│   ├── regions.json            # 17개 시/도 인덱스
│   ├── {region}/index.json     # 각 시/도별 구/군/시 목록
│   ├── {region}/{district}.json # 각 구/군/시별 판매처 데이터
│   └── _unmatched.json         # 미매칭 14건
├── scripts/
│   └── collect.py              # v2: 1회 수집 + 주소 파싱 + 세종 예외 + dedupe
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

---

## 6. 페이지별 구조

### 홈 (/) — 위→아래 순서
1. NoticeBanner — 품절 안내 ticker
2. Header — "홈" + ThemeToggle + MobileMenu
3. Hero — 제목 + 총 판매처 수 + 갱신일
4. 자주 찾는 지역 — 수평 스크롤 chip
5. 지역별 판매처 — RegionGrid 17시도
6. 광고: 리스트 아래 (8836749083)
7. 종량제 봉투 이슈 — article 2개 카드
8. 종량제 봉투 가격 — 미리보기 + CTA
9. FAQ — 3문항 + JSON-LD
10. 광고: 하단 (6518541657)
11. Footer + StickyBottomAd (모바일만)

### 시/도 (/[region])
- Breadcrumb → h1 + 신뢰문구 → DistrictGrid(화살표) → 광고:리스트아래 → FAQ → 인접 지역 → 광고:하단

### 구/군/시 (/[region]/[district])
- 데이터 있음: Breadcrumb → h1 + 신뢰문구 → 안내박스(yellow) → StoreList(alias검색) → 광고 → 인접지역 → 안내콘텐츠 → FAQ → 신뢰시그널 → 광고:하단
- 0건: Breadcrumb → h1 → 안내박스("판매처 정보 없음") → 인접지역 → FAQ → CTA

### Article (/article/*)
- 8섹션: 공감→문제→원인→해결→CTA중간→팁→CTA하단→정리
- CTA 2개 (모두 "/" 연결), 최소 1200자

---

## 7. AdSense 설정 (활성화 완료)

| 항목 | 값 |
|------|-----|
| Publisher ID | ca-pub-7976139023602789 |
| Slot 1 (리스트 아래) | 8836749083 |
| Slot 2 (리스트 아래) | 7831623329 |
| Slot 3 (하단) | 6518541657 |
| Slot 4 (모바일 하단) | 3611374960 |

### 광고 기술 결정 (삽질 기록)
1. `next/script` 사용 금지 → `data-nscript` 속성 거부. `<head>`에 일반 `<script>` 태그
2. `data-full-width-responsive="false"` 필수 → true면 컨테이너 밖 확장
3. 광고 컨테이너: 플랫 (border/padding 없음)
4. fixed/sticky 금지 → 콘텐츠 덮음
5. StickyBottomAd: `max-h-[100px] overflow-hidden` + `format="fluid"`
6. AdSlot 중복 방지: `mounted` state + `pushed` ref 이중 가드
7. 광고 위치: 리스트(RegionGrid/DistrictGrid) 아래 (제목 바로 아래 ❌)

---

## 8. 검색엔진 등록 상태

| 엔진 | 상태 | 방법 |
|------|------|------|
| Google | 색인 제출 완료 | Search Console sitemap + URL 요청 |
| 네이버 | 메타태그 적용 완료 | `naver-site-verification` in layout.tsx |
| 다음 | robots.txt 적용 완료 | `#DaumWebMasterTool` in robots.txt |

---

## 9. 커밋 히스토리 (최신→과거, 주요)

```
0dc9e3d P14: District card CTR improvement with arrow and hover
36ed6a8 P13: trust message, search alias, ad placement, remove 준비중
ae1b916 Rewrite collect.py v2: single-fetch + Sejong fix (69,265 stores)
2baef6d Add GA4 tracking (G-WTTDTMNTWQ)
0ee3304 Update session reports
5605af1 Bottom ad: limit height to 100px, fluid format
050244d Ad slots: flat display only
851ab41 Fix ad overflow: disable full-width-responsive
66668c9 Fix AdSense: plain script tag (no next/script)
f187f52 P10: fix ad layout — remove fixed/sticky
67dcbeb P9: mobile menu UX upgrade — 3-section layout
614c4a2 Enable AdSense across all pages
1f563df SSOT v1.7: article design polish
... (이전 커밋 생략)
3751c31 Initial release
```

---

## 10. 다음 단계 (우선순위순)

1. **네이버 블로그 게시** — docs/BLOG_POST_NAVER.md 복붙
2. **트래픽 모니터링** — GA4 + Search Console 확인
3. **가격 전용 페이지** — 지역별 상세 가격표
4. **데이터 갱신** — 주기적 갱신 구조 검토

---

## 11. 핵심 교훈 / 주의사항

1. **dark:*-gray 금지** — 반드시 dark:*-zinc
2. **파란색 금지** — blue-* 절대 사용 안 함
3. **AdSense + Next.js** — next/script 금지, 일반 `<script>` in `<head>`
4. **광고 fixed/sticky 금지** — 일반 흐름에 넣기
5. **data-full-width-responsive="false"** — true면 컨테이너 밖 확장
6. **광고 위치** — 리스트 아래 (제목 바로 아래 ❌)
7. **StickyBottomAd max-h-100px** — format="fluid" 필수
8. **공공데이터 파싱** — localCode 구 단위 필터 안 됨. 전국 1회 수집 + 주소 파싱
9. **세종 특수 처리** — 구 없음, sejongsi로 직접 매핑
10. **동명 구 문제** — 동구/서구/남구/북구/중구 → 시/도 먼저 확정 후 구 매칭
11. **검색 alias** — CU/GS 등 영문 브랜드 한글 alias 필수
12. **"준비중" 금지** — "판매처 정보 없음" 사용
13. **신뢰 문구** — "공공데이터 기준이며 일부 지역은 실제와 차이" 항상 표시
14. **CTA 정직** — CTA 문구 = 실제 도착 페이지
15. **중간 끊긴 작업** — 이어하지 말고 처음부터 다시 적용
16. **GPT 지시서 검증** — 맥락 잃은 GPT 지시 반드시 의견 제시

---

## 12. 작업 스타일 규칙

- **지시서 기반**: 사용자가 구조/지시서를 주고, AI가 실행
- **"해라" = 즉시 실행**: 추가 확인 불필요
- **의견 요청 시**: 근거와 함께 명확한 판단 제시
- **새 세션**: 이 문서 첨부 → 지시서 대기
- **커밋**: 작업 완료 후 사용자 확인 받고 push
- **GPT 지시서**: 무조건 의견 제시부터. 맹목적 실행 금지
- **검토만**: 사용자가 "검토만"이라고 하면 수정하지 말고 의견만 제시
