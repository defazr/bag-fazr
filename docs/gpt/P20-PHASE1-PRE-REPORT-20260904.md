# P20 — GOOGLE INDEX RECOVERY PILOT / PHASE 1 PRE-REPORT

> **PRE-REPORT ONLY. 코드 수정 0건 / 커밋 0건 / 배포 0건 / GSC 쓰기 동작 0건.**
> 작성일 2026-09-04 · HEAD `a05ebc5` · working tree 무변경
> 선행 문서: `docs/gpt/GPT-HANDOFF-20260903.md` (정본), `docs/gpt/GSC-DIAGNOSIS-20260904.md`
> 이 문서의 모든 수치는 이번 세션에서 **실행해서 얻은 값**이다. 추정은 전부 근거식을 함께 적었다.

> ## ⚠️ 2026-09-04 정정 (구현 후 추가)
>
> **§D-1 · §E · §K2 · §L-1 · §CC-3 의 바이트 예측이 구현 중 반증됐다.**
> 원인: 예측이 **렌더 HTML 만** 계산하고 **RSC payload 증가를 누락**했다. server component 의
> 렌더 결과도 flight payload 에 직렬화되므로 마크업이 두 번 실린다.
> 실측: 렌더 428 B/건 + payload 525 B/건 = **953 B/건**. 예측(399 B/건)의 약 2.4배.
>
> 아래 본문은 **당시 판단 근거를 그대로 보존**하기 위해 수정하지 않는다.
> 정정된 실측값은 **`docs/gpt/P20-PHASE1-COMPLETION-20260904.md` §CC-1 · §CC-4** 를 정본으로 본다.

---

# A. CURRENT STATE

## A-1. Production (변경 없음)

| | |
|---|---|
| store total | 69,292 |
| collection date | 2026-09-04 |
| data checksum | `59617a5e2965712e` |
| routes | 253 (HTML 252 + sitemap) |
| sitemap | 241 URLs |
| 테스트 | PASS 226 / FAIL 0 / exit 0 |

## A-2. GSC 실측 — **Google이 아는 URL은 241개 중 6개뿐이다**

17개 region 페이지를 전수 URL Inspection(READ-ONLY) 한 결과:

| coverageState | 개수 | region |
|---|---|---|
| **Crawled - currently not indexed** | **3** | `seoul` `busan` `gyeonggi` |
| **URL is unknown to Google** | **14** | daegu incheon gwangju daejeon ulsan sejong gangwon chungbuk chungnam jeonbuk jeonnam gyeongbuk gyeongnam jeju |

Google이 이 사이트에서 기록을 가진 URL **전부**:

| URL | lastCrawl | inbound(SSR `<a>`) |
|---|---|---|
| `/` | 2026-08-30 | 250 |
| `/seoul` | 2026-04-30T10:55:04Z | 45 |
| `/gyeonggi` | **2026-04-30T10:55:04Z** (초 단위까지 seoul과 동일) | 35 |
| `/busan` | 2026-04-26T10:30:52Z | 36 |
| `/article/shortage-2026` | 2026-04-27 | **2** |
| `/article/why-no-bags` | 2026-04-29 | **2** |

**6 / 241 = 2.5%.** 나머지 235개는 색인 실패가 아니라 **Google에 존재 자체가 알려지지 않았다.**
크롤은 2026-04-26 ~ 04-30 (sitemap 제출 04-28 전후)에 몰려 있고, 이후 4개월간 홈 1회뿐이다.

## A-3. Region 페이지에는 판매처 데이터가 0건이다 (실측)

17개 region HTML 전수 측정 — `roadAddress` 출현 **전부 0**.

| region | HTML | RSC payload | 가시 텍스트 | 구군 | SSR 링크 | 매장 총계 | `roadAddress` |
|---|---|---|---|---|---|---|---|
| gyeonggi | 70,450 | 39,787 | **1,151자** | 31 | 31 | 15,221 | **0** |
| seoul | 62,361 | 35,057 | **1,094자** | 25 | 25 | 3,054 | **0** |
| busan | 50,076 | 28,046 | **995자** | 16 | 16 | 4,096 | **0** |
| (최소) sejong | 29,922 | 16,425 | 852자 | 1 | 1 | 165 | 0 |

`StoreList` 는 `app/[region]/[district]/page.tsx` 에만 있고 `app/[region]/page.tsx` 에는 없다.
**69,292곳이라는 자산이 Google이 실제로 크롤한 3개 region 페이지에 단 한 건도 들어 있지 않다.**

region 페이지 간 6-word shingle 고유율: gyeonggi 47.8% / seoul 47.3% / busan 39.3% / (최저) sejong 22.3%.

## A-4. district 링크는 이미 정상이다 (가설 하나 제거)

`components/region/DistrictGrid.tsx` 는 `count` 무관하게 전 district 를 링크하고, **script 태그를 제거한 순수 HTML에서도 `<a href>` 가 전부 존재한다**:

```
/busan     전체 href 16개 / script 제외 <a> 16개 / 차집합 0
/gyeonggi  전체 href 31개 / script 제외 <a> 31개 / 차집합 0
```

실제 마크업:
```html
<a class="..." href="/busan/bsbukgu"><div class="min-w-0">
  <span class="font-medium ...">북구</span>
  <span class="block text-sm ...">1곳</span></div>…</a>
```

→ **"링크가 JS 안에 숨어 있어서 Google이 못 본다"는 가설은 폐기된다.** 링크는 4개월 전부터 SSR HTML 에 있었고 Google은 `/busan`·`/gyeonggi` 를 크롤했다. 그런데도 district 들은 unknown 이다.

## A-5. **DistrictGrid 는 이미 매장 수를 노출하고 있다** — 지시서 B안의 전제 정정

`DistrictGrid.tsx:37`:
```tsx
<span className="block text-sm ...">
  {d.count > 0 ? `${d.count}곳` : "판매처 정보 없음"}
</span>
```

지시서 §3 B안("region 페이지에 district별 실제 매장 수 요약을 SSR 노출, 각 항목 district 링크")은
**이미 구현되어 프로덕션에 나가 있다.** 따라서 B안의 한계 가치는 사실상 0이다. 이것이 설계 비교의 출발점을 바꾼다.

---

# B. WHY MANUAL ACTION CLEAN CHANGES THE JUDGMENT

> **출처 구분 (중요).** Search Console API 는 수동 조치·보안 문제를 **노출하지 않는다.**
> 이 두 항목은 **사용자가 UI 에서 확인해 전달한 값**이고, 내가 측정한 값이 아니다.
> 지시서 §0 이 이를 "GSC 실제 측정" 목록에 넣었으나 정확히는 사용자 확인 사항이다.
> 아래 판단은 그 확인이 정확하다는 전제 위에 선다.

## B-1. 제거되는 가설

| 가설 | 제거 근거 |
|---|---|
| 수동 조치(스팸 페널티) | 사용자 확인: 없음 |
| 보안 문제(해킹·멀웨어) | 사용자 확인: 없음 |
| 도메인 단위 페널티 | 형제 서브도메인 실적 — fuel 6클릭/34노출, sangsangpay 2/28, headlines 1/7 (90일). **정상 색인 중** |
| 소유권 미확인 | `https://bag.fazr.co.kr/` **siteOwner** 확인 |
| robots / noindex / canonical 차단 | 크롤된 5개 전부 `robots=ALLOWED` `indexing=INDEXING_ALLOWED` `pageFetch=SUCCESSFUL`, canonical(google)==canonical(user) |
| sitemap 오류 | `errors 0 / warnings 0`, `lastDownloaded 2026-08-24` 정상 |
| **district 링크 미크롤성** | §A-4 — SSR `<a>` 로 전부 존재 |

## B-2. 상대적 가능성이 올라간 가설

기술적 차단이 전부 제거되면 남는 것은 **Google이 크롤은 했으나 색인 가치를 인정하지 않았고, 그 결과 나머지 URL 에 크롤 예산을 배정하지 않았다**는 경로다.

이를 지지하는 실측:
- 크롤된 6개 전부 `Crawled - currently not indexed` (기술 오류 아님, **판단에 의한 보류**)
- 크롤이 04-26~30 에 몰린 뒤 4개월 정지
- Google이 본 3개 region 페이지의 가시 텍스트 **995~1,151자**, 그리고 **판매처 데이터 0건** (§A-3)

## B-3. 단정하지 않는 것

**"품질 문제가 확정됐다"고 쓰지 않는다.** 아래가 미해결이다:

1. Google이 색인을 보류한 사유를 직접 관측할 수단이 없다. `Crawled - currently not indexed` 는 결과이지 사유가 아니다.
2. **외부 백링크 0 관측.** 홈의 유일한 referring 이 내부 URL(`/busan`) 하나다. 신규 서브도메인 + 외부 신호 0 은 콘텐츠 품질과 독립된 크롤 예산 제약 요인이며, **이번 pilot 은 이 변수를 건드리지 않는다.**
3. 콘텐츠를 개선해도 재평가까지 걸리는 시간을 알 수 없다.

---

# C. PILOT TARGET SELECTION

## C-1. 후보는 3개로 강제된다

pilot 은 "변경 전/후 비교"가 성립해야 한다. GSC 기록이 없는 URL(`unknown`)은 baseline 이 없어 비교가 불가능하다.
§A-2 대로 **기록이 있는 region 은 `seoul` `busan` `gyeonggi` 3개뿐**이다. 나머지 14개는 후보가 될 수 없다.

## C-2. 3개 비교

| | gyeonggi | busan | seoul |
|---|---|---|---|
| lastCrawl | 2026-04-30 | 2026-04-26 | 2026-04-30 |
| coverageState | Crawled-not-indexed | Crawled-not-indexed | Crawled-not-indexed |
| district | 31 | 16 | 25 (data file 22) |
| 매장 총계 | **15,221** | 4,096 | 3,054 |
| 가시 텍스트 | 1,151자 | 995자 | 1,094자 |
| shingle 고유율 | **47.8%** | 39.3% | 47.3% |
| 10곳 미만 district | 6 / 31 (19%) | 3 / 16 (19%) | **14 / 25 (56%)** |
| 0곳 district | 0 | 0 | **3** |

**seoul 을 pilot 대상에서 제외한다.** 25개 구군 중 14개가 10곳 미만이고 3개가 0곳이라, "실제 데이터를 보여준다"는 pilot 의 취지에서 보여줄 데이터가 가장 빈약하다. 서울 sparsity 는 핸드오프 §10-9 가 이미 미해결로 기록한 별개 문제이며, pilot 결과에 교란 변수를 더한다.

**결론: 지시서의 `gyeonggi` + `busan` 선택이 데이터로 지지된다.** 다만 **둘 다 바꾸는 것에는 반대한다 — §CC-1 참조.**

---

# D. DESIGN OPTIONS

공통 측정 상수: **store card 1개 = 399 bytes** (실측, 2,889개 카드 / 중앙값 395 / min 356 / max 506).

> **[정정 2026-09-04]** 이 상수 자체는 맞다(렌더 HTML 기준). 그러나 아래 예측은 이 값을
> 그대로 페이지 증가분으로 썼고, **RSC payload 증가분을 더하지 않았다.** 실제 총비용은
> 마크업 형태에 따라 렌더분의 1.8~2.4배다. §D-1 표의 HTML 열은 **하한으로만** 읽을 것.

## D-1. A안 — 대표 판매처 소수 SSR 노출

두 변형을 측정했다.

**A-1 (축소판): 매장 수 상위 6개 district 에서 각 1곳**

| region | 가시 텍스트 | HTML |
|---|---|---|
| gyeonggi | 1,151 → 1,384자 (**+20%**) | 70,450 → 72,844 (+3%) |
| busan | 995 → 1,212자 (**+22%**) | 50,076 → 52,470 (+5%) |

**A-2 (전 district): 모든 district 에서 각 1곳**

| region | 가시 텍스트 | HTML |
|---|---|---|
| gyeonggi | 1,151 → **2,321자 (+102%)** | 70,450 → 82,819 (**+18%**) |
| busan | 995 → **1,595자 (+60%)** | 50,076 → 56,460 (**+13%**) |

## D-2. B안 — district별 매장 수 요약

**이미 구현되어 있다** (§A-5). 한계 가치 ≈ 0.
남은 여지는 정렬 기준뿐이다. 현재 `data/<region>/index.json` 순서(=slug 사전순)로 렌더된다.
매장 수 내림차순 정렬로 바꾸면 상위 구군이 앞에 오지만, **가시 텍스트·고유 텍스트는 1자도 늘지 않는다.**

## D-3. C안 — A+B 혼합

B가 이미 있으므로 C = A + (정렬 변경). 실질적으로 A안이다.

## D-4. 종합 비교

| | A-1 (상위6) | A-2 (전 district) | B (정렬만) |
|---|---|---|---|
| 새로 노출되는 고유 데이터 | 매장명+주소 6건 | **매장명+주소 31/16건** | **0** |
| 가시 텍스트 증가 | +20~22% | **+60~102%** | 0% |
| HTML 증가 | +3~5% | +13~18% | 0% |
| RSC payload 영향 | +약 1KB | +약 5KB(gyeonggi) | 0 |
| district 링크 문맥 강화 | 6개만 | **전 district** | 없음 |
| 사용자 가치 | 낮음(대표 6곳 임의성) | 중간(내 구군 매장 미리보기) | 없음 |
| 구현 위험 | 낮음 | 낮음 | 매우 낮음 |
| rollback | 단일 커밋 revert | 단일 커밋 revert | 단일 커밋 revert |
| 서버 렌더 비용 | district JSON 6개 read | district JSON 31개 read (빌드 시 1회) | 0 |

`getDistrictData()` 가 `lib/data.ts:21` 에 이미 있으므로 데이터 접근 계층 신규 구현은 필요 없다.
빌드 시 추가 파일 read 는 17개 region 합계 **220회**(정적 생성 1회)로, 현행 빌드(253 routes / 803ms 정적 생성)에 유의미한 영향이 없다.

---

# E. RECOMMENDATION

## **A-2 (전 district 대표 판매처 1곳) 을 `/gyeonggi` 단일 region 에만 적용한다.**

근거 (숫자):

1. **B안은 이미 있다.** 새 고유 텍스트를 만드는 방법은 A안뿐이다 (§A-5, §D-2).
2. **A-2 가 A-1 보다 5배 효율적이다.** gyeonggi 기준 가시 텍스트 +102% vs +20%, HTML 비용은 +18% vs +3%. **텍스트 증가/바이트 증가 비율이 A-2 가 유리하다** — A-2 는 1,170자를 12,369 bytes 에, A-1 은 233자를 2,394 bytes 에 얻는다 (자당 10.6 bytes vs 10.3 bytes로 거의 동일한 단가인데, A-2 는 절대량이 5배다).
3. **A-2 는 전 district 링크에 실제 문맥을 붙인다.** 현재 anchor 는 `북구` + `1곳` 뿐이다. 매장명·주소가 링크 옆에 오면 각 district 링크가 고유한 주변 텍스트를 갖는다.
4. **gyeonggi 가 3개 후보 중 최적.** 매장 15,221곳(2위의 3.7배), shingle 고유율 47.8%(최고), 10곳 미만 구군 비율 19%(seoul 56%보다 훨씬 낮음).

## E-1. deterministic 선정 규칙

> **각 district 의 `stores` 배열에서 `name` 오름차순 첫 번째 1곳.**

- 임의 선정이 아니고, 같은 데이터에서 항상 같은 결과가 나온다. 테스트로 고정 가능하다.
- **`stores[0]`(수집 순서)을 쓰지 않는 이유**: 수집 순서는 API 응답 순서에 의존해 재수집마다 바뀔 수 있다. 그러면 데이터가 실질적으로 같아도 region 페이지가 매번 달라져 pilot 측정이 오염된다.
- 매장이 0곳인 district 는 **아무것도 출력하지 않는다** (gyeonggi 에는 해당 없음. 다른 region 확장 시 필요).
- 주소는 `roadAddress || address` — `StoreCard.tsx:4` 의 기존 규칙을 그대로 따른다.

## E-2. 왜 `/busan` 은 **바꾸지 않는가** — 대조군

지시서는 gyeonggi + busan 둘 다를 pilot 으로 지정했다. **여기에 이견이 있다.**

둘 다 바꾸면 이후 관측이 "둘 다 변했다 / 둘 다 안 변했다"로 나올 때 **원인이 변경인지 외부 요인(Google 크롤 주기, 사이트 전체 재평가, 계절성)인지 구분할 수 없다.**

`/gyeonggi` 만 바꾸고 `/busan` 을 그대로 두면:

| 관측 | 해석 |
|---|---|
| gyeonggi 만 recrawl / 상태 변화 | **변경이 원인일 가능성** |
| 둘 다 변화 | 외부 요인. 변경 효과 미확인 |
| 둘 다 무변화 | 변경 효과 없음 또는 관측 기간 부족 |

두 페이지는 같은 사이트·같은 크롤 예산·거의 같은 lastCrawl(04-30 vs 04-26)을 공유하므로 대조군으로 적합하다.
**pilot 의 목적은 배포가 아니라 인과 판정이다. 대조군을 포기하면 이번 실험에서 배울 수 있는 것이 크게 줄어든다.**

`/busan` 은 Phase 1 결과 확인 후 **2차 적용 대상**으로 남긴다.

---

# F. EXPECTED DIFF

**아직 수정하지 않음. 승인 시 예상 변경 목록이다.**

| 파일 | 변경 | 규모(예상) |
|---|---|---|
| `components/region/DistrictGrid.tsx` | 카드 안에 대표 매장 1줄 추가 (`sample?: {name, address}` prop 옵셔널) | +10~15줄 |
| `app/[region]/page.tsx` | pilot region 한정 분기로 대표 매장 조회 후 `DistrictGrid` 에 전달 | +12~18줄 |
| `lib/data.ts` | (선택) `getDistrictSampleStore(regionSlug, districtSlug)` 헬퍼 | +8줄 또는 0줄 |

**단일 커밋. code-only. data 무변경.** (핸드오프 §0-8: code와 data를 한 커밋에 섞지 않는다)

pilot 한정 분기 방식은 `app/[region]/[district]/page.tsx` 의 수원 조건부 강화(P18-A, 커밋 `6eca6a5`) 선례를 따른다 — 다른 region 산출물에 영향 0.

## F-1. 보존 확약 (지시서 §5)

변경하지 않는 것: title · H1 · canonical · robots · metadata · Breadcrumb · region URL · district URL · data schema · P19 collector · integrity gate · sitemap 로직 · `INITIAL_COUNT` · `adjacentDistricts` · `adjacentRegions` · FAQ · JSON-LD · AdSlot 위치.

---

# G. TEST PLAN

1. `python3 scripts/test_collect.py` → **PASS 226 / FAIL 0 / exit 0** (이번 변경은 collector 무관. 회귀 없음 확인용)
2. `npx tsc --noEmit` → errors 0
3. `npx next build` → **253 routes** 유지
4. `find data -type f | sort | xargs shasum -a 256 | shasum -a 256 | cut -c1-16` → **`59617a5e2965712e` 무변경**
5. **before/after 전수 diff** (핸드오프 §3 방법): 변경 파일을 `git stash` 로 되돌려 before 빌드 → 복원 후 after 빌드 → 252개 페이지 정규화 텍스트 비교.
   **기대 blast radius: 정확히 1페이지 (`/gyeonggi`).** 그 외 251개 무변경이면 통과, 아니면 실패로 간주하고 원인 규명.
6. 회귀 0 확인: duplicate title 0 / duplicate H1 0 / canonical 누락 0 (콘텐츠 페이지) / U+FFFD 0 / sitemap 241 URLs / 예상 밖 noindex 0
7. `/gyeonggi` 산출물 실측 대조:
   - 가시 텍스트 1,151 → **2,321자 근처**
   - HTML 70,450 → **82,819 bytes 근처**
   - `roadAddress` 출현 0 → **31**
   - SSR `<a href="/gyeonggi/...">` **31개 유지** (감소 시 실패)
   - canonical `https://bag.fazr.co.kr/gyeonggi` 무변경, H1 무변경, title 무변경
8. **대조군 검증**: `/busan` HTML 바이트·가시 텍스트·링크 수가 **before와 완전 동일**해야 한다.

---

# H. PRODUCTION SMOKE PLAN

배포 후 HTTP 200 및 본문 대조 (핸드오프 §10-10 smoke 방식):

| URL | 확인 |
|---|---|
| `/gyeonggi` | 200 / 대표 매장 31건 노출 / 로컬 빌드와 본문 일치 / 링크 31개 |
| `/busan` | 200 / **변경 없음** (대조군) |
| `/gyeonggi/goyang` | 200 / 1,806곳 표기 / 매장 카드 15개 (INITIAL_COUNT 무변경 확인) |
| `/` `/seoul` | 200 / 무변경 |
| `/gyeonggi/siheung` | 200 / 1곳 (최소 데이터 district 정상 렌더) |

브라우저 콘솔 JS 오류 0. 배포 커밋에 `[skip ci]` 미사용, 최종 HEAD 가 code 커밋 (핸드오프 §0-8).

---

# I. GSC FOLLOW-UP PLAN — **READ-ONLY ONLY**

## I-1. 금지 (지시서 §11 · 메모리 영구 룰)

유효성 검사 재실행 / 색인 요청 / sitemap 재제출 / Indexing API 호출 / 대량 URL 검사 — **전부 금지.**
scope 는 `webmasters.readonly` 유지. 서비스 계정 JSON 은 저장소 밖에 두고 **절대 `git add` 하지 않는다.**

## I-2. 관측 대상과 시점

**baseline 은 이미 고정됐다** (§A-2, 2026-09-04 측정).

| 시점 | 확인 URL | 확인 항목 |
|---|---|---|
| 배포 +7일 | `/gyeonggi` **`/busan`(대조군)** | coverageState, lastCrawlTime |
| 배포 +21일 | 위 2개 + `/gyeonggi/goyang` `/gyeonggi/yongin` `/busan/bsdonggu`(대조) | coverageState 변화, unknown → 발견 이동 여부 |
| 배포 +45일 | 위 + Search Analytics 90일 | impressions 발생 여부 |

**1회 실행 URL Inspection 호출 수 상한: 6.** 이번 전수 스캔(17개)은 pilot 대상 선정을 위한 1회성이었고, 후속 관측은 대조 최소 집합만 본다.

**자동 monitor / 반복 검사 / cron 은 이번에 구현하지 않는다** (지시서 §13).

## I-3. 판정 기준

**A. 즉시 기술 성공** (배포 시점에 판정):
build PASS · canonical 무변경 · title/H1 회귀 0 · `/gyeonggi` 에 실제 고유 데이터 노출 · district 링크 31개 유지 · 페이지 크기 +18% 이내 · JS 오류 0 · smoke 전부 200 · **`/busan` 무변경**

**B. 후속 Google 관측** (시간이 걸리며, 실패해도 코드 결함이 아니다):
`/gyeonggi` recrawl 발생 · coverageState 변화 · gyeonggi 하위 district 가 `unknown` 에서 이탈 · impressions 발생

> **"배포됐다"를 성공으로 정의하지 않는다.** B 는 45일 시점에도 무변화일 수 있고, 그 경우 §CC-4 의 반론이 지지된다.

---

# J. NON-GOALS

이번 Phase 1 에서 **하지 않는 것**:

- `INITIAL_COUNT` 변경 (§L-1 에 분석만)
- `adjacentDistricts` 변경 (§L-2 에 분석만)
- sitemap `lastmod` 수정
- FAQPage 제거/교체, BreadcrumbList·ItemList·LocalBusiness·Organization·WebSite 추가
- SEO용 설명문·광고성 문구 신규 작성 (**목표는 문장 추가가 아니라 실제 데이터 노출**)
- 전국 17개 region 일괄 적용
- URL 구조 변경 / redirect 추가 / canonical 변경 / sitemap 재제출
- `test_collect.py` 수정 (별도 트랙)
- 문서 MISMATCH 정정 (§M)
- P19 재수집 / SAFETY·VALUE 재판정 / threshold 재논쟁

---

# K. RISKS

| # | 위험 | 실측 근거 | 완화 |
|---|---|---|---|
| K1 | **효과가 없을 수 있다** | §CC-4 의 반론. 인과 사슬 3단계 중 2단계가 미검증 | 대조군 설계로 최소한 "효과 없음"을 확정할 수 있게 함. 비용은 1커밋 |
| K2 | 페이지 크기 +18% | 70,450 → 82,819 bytes | 절대값이 83KB 로 사이트 평균(100KB) 미만. district 페이지 최대 538KB 대비 작다 |
| K3 | region ↔ district 매장 중복 | 31곳 / 15,221곳 = **0.2%** | 무시 가능 |
| K4 | 대표 매장 선정이 재수집마다 바뀜 | 수집 순서 의존 시 발생 | `name` 오름차순 고정 (§E-1) |
| K5 | 빌드 시 파일 read 증가 | region 1개당 최대 31회, 전체 220회 | 정적 생성 1회. 현행 253 routes 803ms 대비 무의미 |
| K6 | 0곳 district 에서 렌더 오류 | gyeonggi 최소값 1곳 → 해당 없음 | 그래도 `stores` 빈 배열 가드 필수. 타 region 확장 시 필수 |
| K7 | 대조군 오염 | 다른 커밋이 `/busan` 을 건드리면 실험 무효 | Phase 1 배포 후 관측 종료까지 region 페이지 추가 변경 금지 |
| K8 | 측정 baseline 유실 | GSC 데이터는 시간에 따라 변함 | §A-2 표가 2026-09-04 baseline. 이 문서에 고정됨 |

---

# L. 다음 Phase 를 위한 사전 분석 (이번에 구현하지 않음)

## L-1. `INITIAL_COUNT` 15 → 30 / 50 / 100 — 실측 계산

`components/store/StoreList.tsx:7`. 220개 페이지 전부 **렌더 카드 수 == `min(매장수, 15)`** 임을 확인했다(불일치 0개).
**RSC payload 는 이미 전 매장을 직렬화하므로 `INITIAL_COUNT` 상향은 payload 를 늘리지 않는다.** 증가분은 렌더 HTML 뿐이다.

> **[정정 2026-09-04] 이 문장은 절반만 맞다.** 매장 *데이터* 는 이미 payload 에 있으므로
> 그 부분은 늘지 않는다. 그러나 **렌더된 카드의 마크업(태그·클래스 문자열)도 payload 에
> 직렬화된다.** 따라서 아래 표의 증가율은 **과소평가**이며, 실측 기준 약 2배일 수 있다
> (예: `INITIAL_COUNT=50` 은 +9.7% 가 아니라 **+20% 안팎**일 가능성).
> **Phase 2 착수 전 실측 재계산이 선행 조건이다.** 이 표를 그대로 판단 근거로 쓰지 않는다.

| INITIAL_COUNT | 220페이지 합계 | 증가 | **초기 HTML 노출 매장** |
|---|---|---|---|
| 15 (현재) | 24.64 MB | — | 2,889 / 69,292 = **4.17%** |
| 30 | 25.69 MB | +1.05 MB (**+4.3%**) | 5,517 = **8.0%** |
| 50 | 27.02 MB | +2.38 MB (**+9.7%**) | 8,859 = **12.8%** |
| 100 | 30.12 MB | +5.48 MB (**+22.2%**) | 16,624 = **24.0%** |
| 전체 | 51.13 MB | +26.49 MB (**+107.5%**) | 69,292 = **100%** |

대표 대형 district (현재 → 30 → 50 → 100 → 전체, bytes):

| 페이지 | 매장 | 현재 | 30 | 50 | 100 | 전체 |
|---|---|---|---|---|---|---|
| `/jeonbuk/jeonju` | 1,916 | 537,849 | 543,833 | 551,812 | 571,760 | **1,296,264** |
| `/gyeonggi/goyang` | 1,806 | 499,618 | 505,602 | 513,581 | 533,529 | 1,214,148 |
| `/gyeonggi/hwaseong` | 1,630 | 471,566 | 477,550 | 485,529 | 505,477 | 1,115,879 |

**핵심: 노출률이 선형이 아니다.** 매장 수 분포가 편중돼 있어 100 으로 올려도 노출은 24% 에 그친다.
client hydration 영향: `StoreList` 는 `visibleCount` state 초기값만 바뀌므로 hydration 대상 DOM 이 늘 뿐 로직 변경은 없다. 서버 렌더 비용은 카드 수에 선형.

**Phase 2 판단용 자료. 이번에 수정하지 않는다.**

## L-2. `adjacentDistricts` — 현재 링크 분포와 예상 변화

SSR `<a>` 기준 실측:

- data file 이 있는 district **220개 중 115개(52%)가 inbound 정확히 1개**
  (0곳 페이지 9개를 포함한 229개 기준으로는 **124개**. 두 숫자는 분모 차이일 뿐 모순이 아니다)
- inbound 분포: `{1:115, 2:7, 5:14, 7:12, 9:6, 10:6, 11:6, 14:6, 15:6, 16:6, 18:12, 22:12, 25:5, 26:1, 31:6}`
- 원인: `app/[region]/[district]/page.tsx:116-118` 의 `adjacentDistricts` 가 `count > 0` 필터 후 **정렬 없이 `.slice(0, 6)`** → 각 region 의 **slug 사전순 앞 6개**만 모든 형제에서 반복 링크됨

| region | district | inbound 분포 | adjacent 6 (사전순) |
|---|---|---|---|
| gyeonggi | 31 | `{1:22, 2:2, 7:1, 31:6}` | ansan anseong anyang bucheon dongducheon gapyeong |
| busan | 16 | `{1:8, 2:1, 7:1, 16:6}` | bsbukgu bsdonggu bsgangseo bsjunggu bsnamgu bsseogu |

**Phase 1(A-2) 적용만으로 inbound 링크 수는 변하지 않는다.** DistrictGrid 는 이미 전 district 를 링크하고 있고, A-2 는 그 링크에 **주변 텍스트를 붙일 뿐 링크를 추가하지 않는다.** 예상 변화: gyeonggi 31개 district 의 inbound 수 **불변**, 링크 문맥(anchor 주변 고유 텍스트)만 district당 약 38자 증가.

**Phase 3 후보.** 단 §CC-4 의 반론을 먼저 볼 것.

---

# M. NEXT PHASE CANDIDATES — 우선순위 의견

| 순위 | 항목 | 근거 | 조건 |
|---|---|---|---|
| **1** | Phase 1 결과 관측 (45일) | 다른 모든 판단의 입력 | — |
| **2** | `/busan` 에 A-2 적용 | Phase 1 이 A 판정 통과 시 2차 적용 | Phase 1 관측 종료 후 |
| **3** | ~~`INITIAL_COUNT` 15 → 50~~ **→ 4순위로 강등 (정정 2026-09-04)** | +9.7% 는 payload 누락으로 과소평가됐다. **실측 재계산 선행 필수** | **district 가 실제로 크롤되기 시작한 뒤.** 크롤 안 되는 페이지의 렌더량을 늘리는 것은 측정 불가 |
| **3 (신규)** | sitemap `lastmod` 실제 변경 시각 반영 | 비용이 사실상 0 이고 payload 오차와 무관하다. Google 이 lastmod 를 사이트 단위로 무시하는 상태를 먼저 푸는 편이 낫다 | Phase 1 관측 종료 후 |
| **4** | sitemap `lastmod` 실제 변경 시각 반영 | `app/sitemap.ts:8,17,28` 이 전 URL 동일 빌드 시각. Google이 사이트 단위로 lastmod 를 무시하게 만듦 | Phase 1 관측 종료 후 (지시서 §10 대로 pilot 측정 오염 방지) |
| **5** | `adjacentDistricts` 정렬·확대 | 220개 중 115개 inbound 1 | **§CC-4 반론 검토 후.** 현재 근거가 약하다 |
| **6** | BreadcrumbList JSON-LD | 현재 JSON-LD 는 FAQPage 단독 | 색인이 회복 조짐을 보인 뒤 |
| **7** | FAQ 축자 중복 정리 (`lib/seo.ts:77` `displayName` 오용 포함) | 답변 1,121개 중 497개(44%) 축자 동일, "중구" 5개 페이지 동일 가격 답변 | 6과 함께. **FAQPage 전체 제거는 하지 않는다** |
| **별도 트랙** | **P20-SAFETY-TEST-HARDENING** | §N | 아래 의견 참조 |

## M-1. 테스트 보강 시점에 대한 의견 (지시서 §14 요청)

**권장: Phase 1 배포 직후, 45일 관측 대기 기간에 별도 커밋으로 진행한다.**

근거:
1. **긴급도는 낮다.** 게이트 자체는 직접 실행 감사에서 정상 작동이 확인됐다(경계값 실측 포함). 지금 뚫린 구멍이 아니라 **회귀를 못 잡는 상태**다.
2. **그러나 미루면 위험이 커진다.** 다음 수집(P21)이 오기 전에 닫아야 한다. 수집 직전에 테스트를 건드리는 것이 가장 나쁜 순서다.
3. **Phase 1 관측 기간은 코드 변경이 비어야 하는 시간이 아니다.** SEO pilot 과 파일이 전혀 겹치지 않으므로(`scripts/` vs `app/`·`components/`) 대조군 오염 위험이 0이다.
4. 우선순위: **C positive 테스트 → A → E → F 개별 코드 → 마스킹 2건(`:643`, `:692`) → 항진명제(`:826`) → structural self-test 강화.**
   C 를 먼저 두는 이유는 D 가 같은 구조(정상 경로에서 항상 empty)인데도 직접 주입 테스트를 갖고 있어, C 만 비대칭적으로 비어 있기 때문이다.

---

# N. 문서 MISMATCH (docs-only 정정 후보 — 이번 커밋에 섞지 않음)

1. `GPT-HANDOFF-20260903.md` 1행 제목이 `HEAD 40a4ee9 기준`인데 §1·footer 는 `dc22fe2` 기준. 실제 HEAD 는 `a05ebc5`.
2. 같은 문서 §0-2 의 "**S-prefixed** structural audit" 표현. 실제로 `S.` 접두는 `S.empty` 하나뿐이고 나머지 구조 실패는 `F.*` 로 나온다 (`integrity.py:569-583`). 차단 동작에는 영향 없음.
3. (신규) 데이터 checksum 산출식이 문서에 없다. `find data -type f | sort | xargs shasum -a 256 | shasum -a 256 | cut -c1-16` 를 §1 에 병기해야 한다. `tree_sig()` 방식과 다른 값이 나온다.

---

# CC 이견 및 아이디어

지시서와 다른 판단 4건, 추가 제안 3건.

## CC-1. **`/busan` 을 동시에 바꾸는 것에 반대한다 — 대조군을 남겨야 한다** (가장 강한 이견)

지시서 §4 는 gyeonggi + busan 2개를 pilot 으로 지정했다. 반대한다.

Google 이 기록을 가진 region 은 **3개뿐**이고(§A-2), 그중 seoul 은 데이터 빈약으로 제외된다(§C-2). 남은 2개를 **둘 다 바꾸면 대조군이 0이 된다.**

이 실험의 가장 큰 위험은 "효과가 없는 것"이 아니라 **"효과가 있었는지 알 수 없게 되는 것"** 이다. 4개월간 크롤이 멈춘 사이트에서 어떤 변화가 관측되면, 그것이 우리 변경 때문인지 Google 의 주기적 재평가 때문인지 구분할 수단이 필요하다. `/busan` 은 같은 사이트·같은 크롤 예산·거의 같은 lastCrawl(04-26 vs 04-30)을 가진 **유일한 대조군 후보**다.

`/busan` 적용은 Phase 1 관측이 끝난 뒤 2차로 하면 되고, 그때는 Phase 1 결과라는 정보를 갖고 하게 된다. 비용은 지연뿐이다.

## CC-2. **B안은 이미 구현되어 있다 — 설계 선택지가 실제로는 2개가 아니라 1개다**

지시서 §3 은 A/B/C 3안 비교를 요구했으나, B(`district별 매장 수 + 링크`)는 `DistrictGrid.tsx:37` 에 이미 있고 프로덕션에 나가 있다(§A-5). 따라서 C = A + 정렬변경이고, 실질 선택지는 **"A안을 하느냐, 얼마나 하느냐"** 뿐이다. 이 사실이 지시서 작성 시점에 반영되지 않은 것으로 보인다.

## CC-3. **"더 작은 실험"을 물으셨는데, 오히려 A-1(상위 6개)이 너무 작다고 본다**

지시서 §3 A안 예시는 6~12개다. 측정 결과 상위 6개는 가시 텍스트를 **+20%** 밖에 올리지 못한다(1,151 → 1,384자). Google 이 이 페이지를 색인 가치 없음으로 판정한 상태에서 20% 증가가 판정을 뒤집을 것으로 보기 어렵다.

전 district(31개)는 **+102%** 로 텍스트를 2배 이상으로 만들면서 HTML 비용은 +18%(70KB → 83KB) 에 그친다. **"더 작게"의 축을 페이지 내 변경량이 아니라 적용 region 수로 옮기는 것**(2개 → 1개)이 더 나은 절충이라고 본다. 그래야 변경은 판정 가능할 만큼 크고, 범위는 대조군을 남길 만큼 작다.

## CC-4. **핵심 가설에 대한 반론 — 내부 링크는 이 사이트에서 예측력이 없다**

지시서 §2 의 가설 3단계는 `region 개선 → region 색인 → district 발견` 이다. 2·3단계 모두 미검증인데, **3단계에는 반증에 가까운 실측이 있다.**

| URL | inbound(SSR `<a>`) | Google 상태 |
|---|---|---|
| `/article/shortage-2026` | **2** | **Crawled** |
| `/article/why-no-bags` | **2** | **Crawled** |
| `/gyeonggi/anyang` | **31** | **unknown** |
| `/gyeonggi/ansan` | **31** | **unknown** |
| `/incheon` | **30** | **unknown** |
| `/daegu` | **29** | **unknown** |

**inbound 링크가 15배 많은 페이지가 unknown 이고, 2개뿐인 페이지가 크롤됐다.** 즉 이 사이트에서 Google 의 발견/크롤 선택은 내부 링크 수로 설명되지 않는다.

이것이 함의하는 바:
1. Phase 1 이 region 페이지를 개선해도 **district 발견으로 이어진다는 보장이 없다.** 링크는 이미 4개월간 SSR 로 존재했다(§A-4).
2. 같은 이유로 **`adjacentDistricts` 개선(§L-2, M-5순위)의 기대 효과도 낮다.** 지시서가 이를 Phase 2 후보로 둔 판단에 동의하며, 오히려 **더 낮은 우선순위**를 제안한다.
3. 관측되지 않은 유력 변수는 **외부 백링크 0** 이다. 전 표본에서 referring 이 내부 URL 하나뿐이었다.

**그럼에도 Phase 1 을 지지하는 이유**: 가설이 틀려도 손실이 1커밋이고, region 페이지에 판매처가 0건인 것은 가설과 무관하게 **확정된 결함**이다(§A-3). 그리고 대조군 설계(§CC-1)를 쓰면 "효과 없음"조차 정보가 된다.

## CC-5. (아이디어) region 페이지 store 노출은 과하지 않다 — 단, 단위를 "매장"이 아니라 "district 미리보기"로 볼 것

"region 에 store 까지 보여주는 것이 과한가"라는 물음에 대한 답: **31곳은 과하지 않다.** 15,221곳 중 0.2% 이고, 사용자 관점에서도 "내 구군에 어떤 매장이 있는지" 미리보기는 클릭 전 정보로 자연스럽다. 과한 것은 오히려 **현재 상태 — 판매처 사이트의 region 페이지에 판매처가 0건인 것** 이다.

## CC-6. (아이디어) 진짜 병목은 RSC payload 이며, 이것이 Phase 3 후보다

측정된 구조적 낭비: `/jeonbuk/jeonju` 는 HTML 537,849 bytes 중 payload 약 332KB 가 **렌더되지 않는 JSON** 이다. 1,916곳이 직렬화되어 전송되는데 15곳만 그려진다.

`StoreList` 가 `"use client"` 라서 전 배열이 prop 으로 직렬화되는 것이 원인이다. 검색 입력만 client 로 남기고 목록을 server component 로 옮기면 payload 중복이 사라진다.

**다만 단순 이득이 아니다.** 렌더 카드는 399 bytes/건, payload 는 약 173 bytes/건이므로 **전량 렌더는 payload 제거분보다 비싸다**(jeonju 기준 렌더 764KB vs payload 절감 332KB). 따라서 "payload 제거 + 전량 SSR" 은 페이지를 키운다. 실익이 나오는 조합은 **payload 제거 + 부분 SSR + 나머지는 페이지네이션 URL** 쪽이며, 이는 URL 구조 변경을 수반하므로 지금 판단할 사안이 아니다. **Phase 3 이후 별도 설계 검토 항목으로만 기록한다.**

## CC-7. (아이디어) 측정 방법 개선 — baseline 을 문서가 아니라 스크립트로 고정

이번 baseline(§A-2)은 이 문서의 표로만 남는다. 45일 뒤 비교할 때 같은 방식으로 재측정한다는 보장이 없다.

제안: `scripts/` 가 아닌 **스크래치패드에 baseline JSON 을 덤프**해 두고(측정 시각·URL·coverageState·lastCrawl), 후속 관측 시 diff 하는 방식. 저장소에 넣지 않는 이유는 이것이 collector 안전 경계 밖의 도구이고, `scripts/` 에 들어가면 테스트 게이트·해시 관리 대상이 되기 때문이다. **구현은 Phase 1 승인 후에 하며 지금은 하지 않는다.**

---

*PRE-REPORT 끝. 승인 시 §F 의 diff 를 단일 code-only 커밋으로 구현한다. 승인 전까지 수정하지 않는다.*
