# bag.fazr.co.kr 세션 보고서

> 새 Claude/GPT 세션에서 컨텍스트 파악용. 이 문서만 읽으면 바로 이어갈 수 있도록 작성.
> 최종 업데이트: 2026-05-11

## 현재 상태: P18-A 완료, P18-B 대기

사이트 라이브: https://bag.fazr.co.kr
데이터: 전국 69,265곳 (2026-03-27 수집) | 페이지: 253개 | Article: 3개
색인 상황: GSC 색인 회복 대기 중
Vercel Ignored Build Step: `git diff --quiet HEAD^ HEAD -- ':!*.md' ':!docs/'` 설정 완료

---

## 완료된 Phase

| Phase | 내용 | 상태 |
|---|---|---|
| P1~P11 | 데이터/SEO/CTR/콘텐츠/광고/검색UX/내부링크/허브 | 완료 |
| P17 | where-to-buy 허브 페이지 + 양방향 내부링크 | 완료 |
| P17.5 | 홈 카드 3개 확장 + 햄버거 메뉴 | 완료 |
| **P18-A** | **수원 페이지 강화** (조건부 콘텐츠 + FAQ 8개 + 내부링크) | **완료 (5/11)** |

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

### 핵심 원칙
**"새 페이지 늘리지 말고, 터진 페이지 더 깊게."**

---

## 다음 작업 계획 (P18-B ~ P19)

### 일정

```
5/11 --- P18-A 완료 (수원 강화) ✅
5/12 --- 휴식 / 배포 상태 확인만
5/13 --- P19 사전조사 (읽기 전용, API totalCount만 확인)
5/14 --- P18-B 서초
5/15 --- P18-B 성남
5/16 --- P18-B 대구
5/17 --- P18-B 해운대 + 중간 데이터 체크
5/18 --- P18-B 인천
5/19 --- P18-C 검토 / 결정
5/20~22 - P18-C (가격 가이드 article)
5/23 --- P18 시리즈 데이터 체크
5/24~26 - P19 본실행 (데이터 재수집)
```

### P18-B: TOP 5 지역 페이지 보강

| 순서 | 페이지 | 네이버 클릭 | GA4 조회 |
|------|--------|------------|---------|
| 1 | /seoul/seocho | 113 | 142 |
| 2 | /gyeonggi/seongnam | 109 | 132 |
| 3 | /daegu | 62 | 105 |
| 4 | /busan/haeundae | 46 | 64 |
| 5 | /incheon | 45 | 66 |

각 페이지 작업 범위 (수원보다 가볍게):
- 상단 이용 안내 박스 (3~4줄)
- 매장 유형별 구매 팁
- FAQ 2~3개
- /article/where-to-buy 내부링크
- 구별 분류는 생략 (수원만 4구라 특별했음)

작업 방식: 하루 1개, 조건부 분기, 빌드 테스트, 영향 확인 후 커밋.

### P18-C: /article/price 생성 (조건부)

- 가격표 아님. 가격 확인 가이드.
- 가격 직접 기재 절대 금지 (DB 없음)
- P18-A,B 효과 확인 후 결정

### P19: 데이터 재수집 (별도)

- collect.py v2 실행 (전국 재수집)
- 코드 변경 0, 데이터만 단일 커밋
- 5/13 사전조사: API totalCount 현재값 vs 기존 69,265 비교
- 조건: 변화 5% 미만이면 보류, 10%+ 이면 우선 실행

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
docs/  SESSION_REPORT.md, BLOG_POST_NAVER.md, gpt/
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
3. AdSense: layout.tsx에 일반 `<script>` 태그 (next/script 금지)
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
