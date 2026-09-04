# bag.fazr.co.kr 세션 보고서

> ⚠️ 이 문서는 당시 세션 상태 기록입니다.
> 현재 Production 상태와 다음 작업 순서의 정본은
> `docs/gpt/GPT-HANDOFF-20260903.md` 를 따릅니다.

> 새 Claude/GPT 세션에서 컨텍스트 파악용. 이 문서만 읽으면 바로 이어갈 수 있도록 작성.
> 최종 업데이트: 2026-09-03

## 현재 상태: P17.6 HOTFIX Production 완료 / 다음은 P3-13

사이트 라이브: https://bag.fazr.co.kr
데이터: 전국 69,265곳 (2026-03-27 수집, **160일 경과**) | 페이지: 253개 | Article: 3개
색인 상황: GSC 색인 회복 대기 중
Production commit: **`eb1f9d4`** (2026-09-03 배포 완료, 라이브 검증 통과)
Vercel Ignored Build Step: `git diff --quiet HEAD^ HEAD -- ':!*.md' ':!docs/'` 설정 완료

**감사 정본: `docs/AUDIT-20260903.md`** — 전수 감사 원문 + FIXED 4건 / DEFERRED(P2) 7건 / DEFERRED(P3) 13건.
다음 세션은 이 문서를 반드시 함께 읽을 것.

> ⚠️ 2026-05-11 ~ 2026-09-03 사이 작업 없음. 당시 계획된 5/12~5/26 일정(P18-B 5개 지역,
> P18-C, P19)은 **전부 미실행**이며, 그 일정표는 폐기됐다. 아래 "다음 작업 계획"이 최신이다.

---

## 완료된 Phase

| Phase | 내용 | 상태 |
|---|---|---|
| P1~P11 | 데이터/SEO/CTR/콘텐츠/광고/검색UX/내부링크/허브 | 완료 |
| P17 | where-to-buy 허브 페이지 + 양방향 내부링크 | 완료 |
| P17.5 | 홈 카드 3개 확장 + 햄버거 메뉴 | 완료 |
| **P18-A** | **수원 페이지 강화** (조건부 콘텐츠 + FAQ 8개 + 내부링크) | **완료 (5/11)** |
| **P17.6** | **HOTFIX** — 강북구 오염 제거 + OG 복구 + 중복명 보간 + 칩 교체 | **Production 완료 (9/3)** |

### P18-A 작업 상세 (커밋: 6eca6a5)
- 파일: `app/[region]/[district]/page.tsx` (+101줄)
- 모든 변경: `region === "gyeonggi" && district === "suwon"` 조건부 분기
- 추가된 섹션:
  1. 상단 이용 안내 박스 (4구 안내 + 매장 유형 팁)
  2. "수원시 구별로 찾는 법" (장안구/권선구/영통구/팔달구)
  3. "매장 유형별 구매 팁" (편의점/대형마트/동네슈퍼)
  4. 수원 전용 FAQ 3개 (기존 5 + 신규 3 = 8개)
  5. "함께 많이 찾는 정보" 첫 번째 카드 → /article/where-to-buy
- 검증 완료: 수원 정상 / 성남·강남 영향 없음

### P17.6 HOTFIX 작업 상세 (커밋: `eb1f9d4` / 데이터 `eebaf6a` / 문서 `35206ca`)

전수 감사에서 나온 P0/P1만 범위로 고정. P2·P3는 손대지 않음.

**① 강북구 오염 제거 + 재발 방지 3종**

`data/seoul/gangbuk.json`이 "강북구" 이름으로 **대구 북구 948 / 광주 북구 722 / 울산 북구 108 / 부산 북구 1 = 1,779곳**을 서비스하고 있었다. 서울 주소는 0건. 5개월간 라이브.

원인은 v1 `collect.py`(`3751c31`)의 부분 매칭 fallback. 지역 정보 없이 구 이름만 매칭해서 `"북구"`가 서울 맵의 `"강북구"`에 흡수됐다(재현 확인: 남구→강남구, 동구→강동구, 서구→강서구도 동일). v2(`ae1b916`)가 지역 스코프를 확정해 분류는 고쳤으나, **저장부에 stale 파일 삭제가 없어** 2026-03-27 교정 실행 이후에도 고아 파일이 남았다.

- `data/seoul/gangbuk.json` 삭제 (12,463줄)
- `scripts/collect.py` — 부분 매칭 fallback 제거 (실패 시 `_unmatched.json` + WARN)
- `scripts/collect.py` — `count == 0`이면 기존 `{slug}.json` 삭제
- `scripts/collect.py` — 저장 직전 지역 일치 검증, 불일치 매장은 기록 거부 + ERROR

fallback 제거 전 현행 69,265건으로 신·구 로직 diff: **unmatched 증가 0, 매칭 변경 0**.
총계 변화 없음 — 사이트 표기 69,265(서울 3,118)가 정확한 값이었다.

**② OG metadata 전 페이지 복구**

Next.js는 `metadata`의 `openGraph` 객체를 **얕게 덮어쓴다.** 하위 페이지가 `{title, description}`만 선언해 layout의 `images/url/siteName/locale/type`이 249개 페이지에서 소실돼 있었다(카카오/네이버 공유 시 썸네일 없음).

`lib/seo.ts`에 `buildOpenGraph(title, description, path)` 단일 생성기를 두고 **root layout 포함 모든 선언부가 이 함수를 거치게** 했다. 파일별 값 복사가 없어 드리프트 불가.

**③ 중복 district 7개 이름 / 29개 페이지 선택 보간**

```
중구 ×6  동구 ×6  서구 ×5  남구 ×4  북구 ×4  강서구 ×2  고성군 ×2
유니크 200개는 미변경
```

`lib/regions.ts`의 `getDistrictDisplayName(regionSlug, districtName)`을 title·H1·FAQ가 공유.
229개 일괄 변경을 피한 이유: 색인 회복 대기 중 대규모 시그널 변경 회피 + "모든 지역 일괄 수정 금지" 룰 준수.
중복 판정은 `regionSlug+slug` 선(先)중복제거를 거쳐, `lib/regions.ts`의 고령군 중복 등록(P3-6)이 오탐을 만들지 않는다.

**④ 홈 "자주 찾는 지역" 칩: 송파구 → 마포구(602곳)**

송파구는 `data/seoul/songpa.json` 부재로 "판매처 없음" 페이지로 연결됐다.

**회귀 검증 (빌드 산출물 전수 + Production 라이브)**

```
중복 title 0 · 중복 H1 0 · 중복 FAQ Question.name 0 · 강북구 오염 주소 0
stale/불일치 JSON 0 · og:image 251/251 · canonical 250 유지 · sitemap 404 0
tsc 0 · build 253 pages · 코드 U+FFFD 0 · SSOT 위반 0
Production: /seoul/gangbuk 타 지역 주소 0건, HTML 315,796 → 31,390 bytes
```

---

## 합의된 영구 룰

### Google 쪽
- GSC 유효성 검사 재실행 영구 금지
- 대량 색인 요청 금지
- 사이트 구조 흔들기 금지
- 기본 자세: 건드리지 말고 회복 대기

### 콘텐츠 쪽
- 새 페이지 막 늘리기 금지
- 재고 페이지 생성 금지 (실시간 데이터 없음)
- 모든 지역 일괄 수정 금지
- 추측성/단정형 사실 주장 절대 금지 (검증 후 작성)
- 코드 + 데이터 동시 커밋 금지
- 한 번에 여러 페이지 동시 작업 금지

### 커밋/배포 쪽
- docs/md 파일만 커밋 시 `[skip ci]` 붙이기
- **배포가 필요한 변경과 함께 push할 때 `[skip ci]` 커밋을 HEAD로 두지 않는다.**
  실제 배포를 유발하는 코드/데이터 커밋을 최종 HEAD로 둔다.
  근거: `d2de90f`("Update session report ... [skip ci]")가 HEAD였을 때 해당 Production
  배포가 **CANCELED**로 남았다. P17.6은 docs → data → code 순으로 커밋해
  `fix:` 커밋을 HEAD로 두고 한 번에 push, 배포 1건 정상 생성을 확인했다.
- 여러 커밋은 로컬에서 전부 만든 뒤 한 번에 push (Production이 중간 상태를 보지 않게)

### 핵심 원칙
**"새 페이지 늘리지 말고, 터진 페이지 더 깊게."**

---

## 다음 작업 계획

> 2026-05-11자 5/12~5/26 일정표는 폐기됐다(미실행). 아래가 최신 우선순위다.

### 우선순위

```
1순위  P3-13  데이터 무결성 체크 스크립트 (재수집 전 필수)
2순위         현재 데이터 변화폭 확인 (API totalCount vs 69,265, 읽기 전용)
3순위         위 결과로 P19 / P18-B 순서 결정
보류          P18-B, P18-C, P19 즉시 실행 금지
```

### 1순위 — P3-13: 데이터 무결성 체크

`index.json[].count` vs `{slug}.json.totalCount` 대조 + 매장 주소의 시/도 일치 검증. 약 30줄.

**왜 이게 먼저인가.** 이번 사고는 "수집 로직은 고쳐졌는데 stale 파일이 남아 5개월간 살아있던" 유형이다. P17.6으로 원인은 막았지만, P19 재수집은 데이터 전량이 교체되는 작업이라 검증기 없이 돌리면 같은 부류의 사고를 또 몇 달 뒤에 발견하게 된다. 이 체크 하나면 강북구 오염은 5개월 전에 잡혔다.

부수 확인 필요: `collect.py`에 stale 삭제가 들어갔으므로, 다음 재수집 때 무데이터 구군의 기존 파일이 자동 삭제된다. 의도대로 동작하는지 볼 수단이 이 검증기다.

### 2순위 — 현재 데이터 변화폭 확인 (읽기 전용)

API totalCount 현재값 vs 기존 69,265 비교. 코드/데이터 변경 없음.
데이터는 2026-03-27 수집분으로 **160일 경과** 상태다.

### 3순위 — P19 / P18-B 순서 결정

- 변화 10%+ → **P19(재수집) 우선**
- 변화 5% 미만 → P19 보류, P18-B 재검토

### P18-B (보류) — 지역 페이지 보강

기존 TOP5 순서(서초 113 / 성남 109 / 대구 62 / 해운대 46 / 인천 45)는 **2026-05 시점 지표**다.
4개월 경과했으므로 **보강 대상 선정 전 현재 GSC/GA4 수치를 다시 볼 것.** 옛 순서를 그대로 쓰지 말 것.

각 페이지 작업 범위 (수원보다 가볍게): 상단 이용 안내 박스 3~4줄, 매장 유형별 구매 팁, FAQ 2~3개,
`/article/where-to-buy` 내부링크. 구별 분류는 생략(수원만 4구라 특별했음).
작업 방식: 하루 1개, 조건부 분기, 빌드 테스트, 영향 확인 후 커밋.

### P18-C (보류) — `/article/price`

가격표 아님, 가격 확인 가이드. 가격 직접 기재 절대 금지 (DB 없음).
**선결 조건:** P2-1(홈 가격표 490원 vs FAQ 500~1,000원 모순) 정리가 먼저다.

### P19 (보류) — 데이터 재수집

`collect.py` 실행(전국 재수집). 코드 변경 0, 데이터만 단일 커밋.
**선결 조건: P3-13 검증기 존재.**

### 이번 핫픽스에서 하지 않은 것

- **GSC 수동 색인 요청 안 함.** title/H1이 바뀐 29개는 저트래픽 중복명 페이지고,
  `/seoul/gangbuk`은 오히려 색인에서 빠지는 게 맞다. "건드리지 말고 회복 대기" 룰 유지.
  자연 재크롤 대기.
- P2 7건 / P3 13건 전부 미착수 (`docs/AUDIT-20260903.md` 참조)

---

## 프로젝트 구조

```
app/
  page.tsx                          # 홈 (카드 3개: where-to-buy, shortage, why-no-bags)
  [region]/page.tsx                 # 시도 (+ where-to-buy 역방향 링크)
  [region]/[district]/page.tsx      # 구군시 (핵심, P18-A 수원 조건부 콘텐츠 포함)
  article/where-to-buy/page.tsx     # 쓰레기봉투 파는곳 총정리 (SEO 허브)
  article/shortage-2026/page.tsx    # 대란 이유 (SEO 진입)
  article/why-no-bags/page.tsx      # 블로그 톤 (외부 공유)
  layout.tsx                        # AdSense + GA4 <script> in <head>
  globals.css                       # ticker + slide-in animation
  sitemap.ts, not-found.tsx
lib/   regions.ts, data.ts, seo.ts, types.ts
components/
  store/   StoreCard, StoreList (alias 검색)
  region/  RegionGrid, DistrictGrid (화살표 CTR)
  seo/     Breadcrumb, FaqSection
  article/ RegionLinks (6개 지역 chip, SEO 내부링크)
  layout/  Header, Footer, NoticeBanner, MobileMenu, ThemeToggle, ScrollToTop
  ads/     AdSlot, StickyBottomAd
data/  regions.json, {region}/, _unmatched.json
scripts/  collect.py (v2: 1회 수집 + 주소 파싱 + 세종 예외 + dedupe)
docs/  SESSION_REPORT.md, AUDIT-20260903.md (감사 정본), BLOG_POST_NAVER.md, gpt/
```

## 내부링크 구조

```
홈 → where-to-buy(카드1), shortage(카드2), why-no-bags(카드3)
햄버거 → where-to-buy(정보1), why-no-bags(정보2), shortage(정보3)
where-to-buy → 17개 시/도(허브), shortage(인라인), why-no-bags(인라인)
shortage → where-to-buy(인라인), 서울/경기/부산
why-no-bags → where-to-buy(인라인), 서울/경기/부산
17개 시/도 → where-to-buy(역방향링크)
수원 district → where-to-buy(함께 찾는 정보 카드) [P18-A 신규]
```

## 핵심 기술 결정

1. 주소 파싱 기반 분류 (API localCode 사용 안 함)
2. 세종 특수 처리 (구 없음 → sejongsi 직접 매핑)
3. ~~AdSense: layout.tsx에 일반 `<script>` 태그 (next/script 금지)~~
   ⚠️ **이 항목은 현재 코드와 반대다.** `85d71ff`가 `<Script strategy="afterInteractive">`(next/script)로
   바꿨고, 그 결과 서버 HTML에 AdSense 로더 `<script>`와 `<ins class="adsbygoogle">`가 **0개**다
   (라이브 실측). 문서와 코드 중 어느 쪽이 정본인지 미결 — P3-2로 이월. **판단 전까지 이 항목을
   근거로 코드를 고치지 말 것.**
4. 광고 컨테이너: fixed/sticky 금지 → 일반 흐름
5. data-full-width-responsive="false" 필수
6. 검색: alias 매핑 (CU→씨유, GS→GS25 등)
7. Article 인라인 링크: font-medium underline underline-offset-2 (blue 금지)
8. where-to-buy = 허브 (17개 시/도 + 3개 article 양방향)
9. P18-B/C 조건부 분기: `region === "xxx" && district === "yyy"` 패턴

## 디자인 규칙 (SSOT v1.7)

- dark:*-gray 금지 → 반드시 dark:*-zinc
- 파란색(*-blue-*) 전면 금지
- 카드: rounded-xl, p-5, border border-gray-200 dark:border-zinc-800, bg-white dark:bg-zinc-900
- CTA: shadow-sm, dark:border-zinc-700, dark:bg-zinc-800
- Article h2: border-l-4 border-orange-400 pl-3 mt-10 mb-4
- District h2: text-lg font-bold text-gray-900 dark:text-white (border-l 없음)
- 본문: text-sm text-gray-600 dark:text-zinc-400 leading-relaxed
- 인라인 링크: font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition

## AdSense 설정

| 위치 | Slot ID | 페이지 |
|------|---------|--------|
| 리스트 아래 | 8836749083 | 홈, region |
| 리스트 아래 | 7831623329 | district |
| 하단 | 6518541657 | 홈, region, district |
| 모바일 하단 | 3611374960 | 전체 (StickyBottomAd, sm:hidden) |

## 사용자 작업 스타일

- 지시서 기반 작업 (새 세션 = "지시서 대기합니다")
- 결과 중심, 간결한 답변
- "해라" = 즉시 실행, 추가 확인 불필요
- 의견 물으면 근거와 함께 명확한 판단 제시
- GPT 지시서 오면 반드시 의견 제시 먼저 (맹목적 실행 금지)
- 중간 끊긴 작업은 이어하지 말고 처음부터 다시
- 메모리/보고서 저장 시 확인 요청
- 추측성/단정형 사실 주장 절대 금지 (검증 후 작성)
- 사실관계 콘텐츠는 웹 검색 후 작성
- docs/md 파일만 커밋 시 [skip ci] 붙이기 (Vercel Ignored Build Step도 설정 완료)
- 수동적 수행 금지 — 이견·의견·아이디어를 항상 함께 제시할 것

---

## CC 이견 및 아이디어 (2026-09-03)

**1. 다음 액션은 P18-B가 아니라 P3-13(무결성 체크)이다.**
이번 사고는 코드 버그가 아니라 **파일이 지워지지 않아서** 5개월간 살아남은 유형이다. P17.6으로 원인은 막았지만, P19 재수집은 데이터 전량이 교체되는 작업이라 검증기가 있는 상태에서 돌려야 안전하다. 30줄이면 되고, CI에 걸면 다음 사고를 자동으로 잡는다. (사용자 동의 완료)

**2. P18-B의 옛 TOP5 순서를 그대로 쓰지 말 것.**
서초·성남·대구·해운대·인천 순위는 2026-05 시점 지표다. 4개월 경과했고 그 사이 강북구 오염 페이지가 계속 서비스됐다. 보강 대상 선정 전에 현재 GSC/GA4를 다시 볼 것.

**3. P2 착수 시 홈 가격표(P2-1)가 최우선이다.**
단순 룰 위반이 아니라 **사이트 내부에서 숫자가 서로 다르다** — 홈은 20L 490원, `lib/seo.ts`는 약 500~1,000원. 후자는 238개 페이지에 FAQ 구조화 데이터로 발행 중이다. 홈과 구군 페이지를 연달아 보면 바로 드러난다.

**4. P3-2(AdSense)는 "고칠지"가 아니라 "무엇을 정본으로 할지"의 문제다.**
핵심 기술 결정 #3과 `85d71ff`가 정반대다. 어느 쪽이 맞는지는 당시 AdSense 승인/게재 상황을 아는 쪽이 판단해야 한다. 코드를 되돌리든 문서를 고치든 **둘 중 하나는 반드시 정리**해야 같은 혼선이 반복되지 않는다.

**5. 관찰 제안 — GSC에서 `/seoul/gangbuk` URL 하나만 조회.**
이 페이지가 과거 색인됐다면 "강북구" 제목으로 대구/광주 매장을 5개월간 노출한 셈이다. 노출/클릭 추이를 보면 오염이 색인 정체에 기여했는지 단서가 나온다. **URL 검사 조회만** 하면 되므로 "유효성 검사 재실행 금지" 룰과 충돌하지 않는다.

**6. `_unmatched.json`의 연기군 10건.**
`충청남도 연기군 …` 주소 10건이 미분류로 남아 있다. 연기군은 2012년 세종시로 편입된 옛 지명이라 세종 데이터로 회수 가능하다. `_unmatched.json`은 `app/`·`lib/`에서 읽지 않으므로 렌더 버그는 아니고 미출고 데이터 손실이다. P19 때 매핑 한 줄로 처리된다.
