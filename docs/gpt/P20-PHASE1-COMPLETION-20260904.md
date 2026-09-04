# P20 — GOOGLE INDEX RECOVERY PILOT / PHASE 1 완료보고

> 작성일 2026-09-04 · code commit **`1f77370`** · deployment **`dpl_3JVSsNHVhfX9RoY7iVYH9879vVB7`** (READY)
> 선행 문서: `GPT-HANDOFF-20260903.md`(정본) · `GSC-DIAGNOSIS-20260904.md` · `P20-PHASE1-PRE-REPORT-20260904.md`
>
> **이 문서는 PRE-REPORT 의 바이트 예측을 정정한다.** PRE-REPORT §D-1 · §E · §K2 · §L-1 · §CC-3 의
> 예측은 구현 중 반증됐다. 해당 항목의 정본은 이 문서 **§CC-1 · §CC-4** 다.
> PRE-REPORT 본문은 당시 판단 근거 보존을 위해 수정하지 않고 정정 주석만 넣었다
> (핸드오프 §0-8: 이미 push 한 커밋은 amend 하지 않고 문서에서 정정한다).

---

# A. START STATE

| | |
|---|---|
| HEAD | `a05ebc5` / origin 일치 |
| working tree | `?? tsconfig.tsbuildinfo` 만 |
| 테스트 | PASS 226 / FAIL 0 / exit 0 |
| data checksum | `59617a5e2965712e` |
| routes / sitemap | 253 / 241 URLs |

---

# B. DOCS COMMIT

**`478e0f4`** — `docs: record P20 indexing diagnosis and pilot plan [skip ci]`
`GSC-DIAGNOSIS-20260904.md` + `P20-PHASE1-PRE-REPORT-20260904.md`. docs-only, code·data 무변경.

---

# C. IMPLEMENTATION

3파일 / **+87 −4**. 신규 파일 0. helper 추상화 없음.

## C-1. `lib/data.ts` — deterministic comparator (exact)

```ts
const SAMPLE_SORT_KEYS: (keyof Store)[] = [
  "name", "roadAddress", "address", "licenseDate", "status",
];

export function getDistrictSampleStore(
  regionSlug: string, districtSlug: string
): Store | null {
  const data = getDistrictData(regionSlug, districtSlug);
  if (!data || data.stores.length === 0) return null;
  const sorted = [...data.stores].sort((a, b) => {
    for (const key of SAMPLE_SORT_KEYS) {
      const av = a[key] ?? "";
      const bv = b[key] ?? "";
      if (av !== bv) return av < bv ? -1 : 1;
    }
    return 0;
  });
  return sorted[0];
}
```

**설계 결정 3건**

| 결정 | 근거 |
|---|---|
| `name` 단독 정렬 사용 안 함 | 동일 상호명이 있으면 수집 순서(API 응답 순서)가 tie-breaker 로 다시 들어와, 재수집마다 대표 매장이 바뀌어 pilot 측정이 오염된다 |
| **`localeCompare` 사용 안 함** | ICU 로케일 데이터에 의존해 Node 버전·플랫폼마다 결과가 달라질 수 있다. 코드포인트 비교(`<`)는 환경 무관하게 결정적이다 |
| `[...data.stores]` 복사 후 정렬 | 원본 배열을 in-place mutate 하지 않는다 |

**결정성 검증 (실측)**

- gyeonggi 31개 구군에서 5개 필드가 **전부 동일한 중복 레코드 0 건** → 동률이 남아도 렌더 결과가 동일하므로 출력은 완전 결정적이다.
- 참고: `name` 단독 동률도 현재 **0/31** 이라 오늘 출력은 단일 키와 같다. 다중 키는 **미래 데이터에 대한 방어**다.
- 새 ID 생성 0 / 해시 생성 0 / 데이터 수정 0.

## C-2. `components/region/DistrictGrid.tsx`

옵셔널 prop `samples?: Record<string, Store>` 추가. 미전달 시 기존 렌더와 동일
(`/busan` `/seoul` 가시 텍스트 완전 일치로 실증 — §H).
0-store 방어: `samples[slug]` 부재 시 아무것도 출력하지 않는다. placeholder·타 구군 대체 없음.

## C-3. `app/[region]/page.tsx`

```ts
const PILOT_SAMPLE_REGIONS = new Set(["gyeonggi"]);
```
pilot 대상이 아니면 `undefined` 를 넘긴다. P18-A 수원 조건부 강화(`6eca6a5`) 선례를 따른다.

## C-4. 보존 확약 이행

title · H1 · canonical · robots · metadata · Breadcrumb · region/district URL · data schema ·
P19 collector · integrity gate · sitemap 로직 · `INITIAL_COUNT` · `adjacentDistricts` ·
`adjacentRegions` · FAQ · JSON-LD · AdSlot — **전부 무변경.**

---

# D. BASELINE

`scratchpad/baseline_20260904.json` (**git add 안 함**). 코드 수정 전 캡처.

| | `/gyeonggi` | `/busan` | `/seoul` |
|---|---|---|---|
| HTML bytes | 70,450 | 50,076 | 62,361 |
| visible chars | 1,151 | 995 | 1,094 |
| district href | 31 | 16 | 25 |
| `roadAddress` 출현 | 0 | 0 | 0 |
| store card | 0 | 0 | 0 |

title · H1 · canonical · HTML sha256 · visible sha256 동봉.

---

# E. TEST

| # | 항목 | 결과 |
|---|---|---|
| 1 | `python3 scripts/test_collect.py` | **PASS 226 / FAIL 0 / exit 0** |
| 2 | `npx tsc --noEmit` | errors 0 |
| 3 | `npx next build` | **253 routes** (HTML 252 + sitemap) |
| 4 | data checksum | **`59617a5e2965712e` 무변경** |
| 5 | sitemap | **241 URLs** |
| 6 | duplicate title / duplicate H1 | 0 / 0 |
| 6 | canonical 누락 | 2 (`_not-found`, `_global-error` — 콘텐츠 페이지 0) |
| 6 | 예상 밖 noindex | 0 (`_not-found` 1건은 의도된 것) |
| 6 | U+FFFD | 0 |

---

# F. BLAST RADIUS

## **정규화 가시 텍스트 기준 정확히 1개 페이지: `gyeonggi.html`**

지시서 §11 이 경고한 "빌드 비결정적 메타데이터를 콘텐츠 변경으로 오판하지 말 것"이 **실제로 발생했다.**
byte diff 로 판정했다면 251개 페이지가 변경된 것으로 오판했을 것이다.

**통제 실험으로 분리했다.** 변경을 `git stash` 하고 원본 소스를 한 번 더 빌드해, 같은 소스의 두 빌드를 비교했다.

| 비교 | byte 다른 페이지 | 정규화 가시 텍스트 다른 페이지 |
|---|---|---|
| **동일 원본 소스 × 2회 빌드** | **252 / 252** | **0 / 252** |
| 통제 빌드 vs 변경본 | — | **1 / 252** (`gyeonggi.html`) |

원인: Next 내부 식별자가 매 빌드 재생성된다. 관측된 diff 구간 77개는 전부
`ua0u0golti` → `rc0e`, `k_u1bNBB` → `eG6o`, `HF91ySuhD8eC` → `EY65gh7hA6uxcz2z` 형태였다.

개별 확인:

| 페이지 | 가시 텍스트 |
|---|---|
| `busan.html` | 동일 (995 → 995자) |
| `seoul.html` | 동일 (1,094 → 1,094자) |
| `index.html` | 동일 (1,007 → 1,007자) |
| `gyeonggi/goyang.html` | 동일 (2,443 → 2,443자) |
| `gyeonggi/siheung.html` | 동일 (1,695 → 1,695자) |

> **다음 세션을 위한 방법 기록:** 이 저장소에서 before/after 산출물 비교는 **반드시 정규화
> 가시 텍스트 또는 semantic HTML 기준**으로 한다. byte·전체 HTML 해시는 항상 100% 다르게 나온다.
> 핸드오프 §3 이 "full HTML 해시는 쓰지 않는다"고 적은 이유가 이것이며, 이번에 통제 실험으로 재확인됐다.

---

# G. GYEONGGI RESULT

| | baseline | after | 판정 |
|---|---|---|---|
| HTML | 70,450 | **84,594** | **+20.1%** — 가드 +25% 이내 |
| 가시 텍스트 | 1,151자 | **2,691자** | **+134%** |
| district 링크 | 31 | **31** | 고유 31 / 중복 0 / **누락 0 / 초과 0** |
| 판매처 예시 | 0 | **31** | 구군 수와 일치 |
| 중첩 `<a>` | 0 | **0** | |
| title / H1 / canonical | — | **전부 동일** | |

렌더 원문 (SSR HTML, `<script>` 제외):

```html
<span class="mt-2 block text-xs text-gray-500 dark:text-zinc-400 leading-snug">판매처 예시: <!-- -->(유한)안산공판장<!-- --> · 경기도 안산시 단원구 선부동 1076-7</span>
```

`<!-- -->` 는 React 의 텍스트 노드 구분자다. 텍스트 자체는 HTML 에 그대로 있어 크롤에 영향이 없다.

---

# H. BUSAN COMPARISON

**무변경 확인.**

| | before | after |
|---|---|---|
| 가시 텍스트 | 995자 | **995자 (동일)** |
| district 링크 | 16 | 16 |
| 판매처 예시 신규 노출 | 0 | **0** |
| title / H1 / canonical | — | 동일 |
| 의도된 content diff | — | **0** |

`/seoul` 도 1,094 → 1,094자로 동일하다. HTML byte 는 `/busan` +227B, `/seoul` +362B 늘었으나
§F 의 통제 실험대로 **빌드 식별자 재생성분이며 콘텐츠 변경이 아니다.**

---

# I. COMMIT

**`1f77370`** — `feat: add Gyeonggi store previews for index recovery pilot`

| | |
|---|---|
| `[skip ci]` | **미사용** |
| data 변경 | 0 |
| scripts 변경 | 0 (`git diff a05ebc5..HEAD -- scripts/ data/` 출력 없음) |
| collector / P19 변경 | 0 |
| push | 1회 |
| 최종 HEAD | **code commit** |
| origin/main | 일치 (`1f77370e06baf7281ae1456224a6315d034c3e40`) |

---

# J. DEPLOYMENT

지시서 §16 이 요청한 3항목 전부 확보했다. **HTTP smoke 대체가 아니라 Vercel API 직접 조회**
(`get_deployment`)로 얻은 값이다.

| | |
|---|---|
| deployment ID | **`dpl_3JVSsNHVhfX9RoY7iVYH9879vVB7`** |
| commit SHA | `1f77370e06baf7281ae1456224a6315d034c3e40` |
| state | **READY** |
| build 소요 | 22초 (`buildingAt` → `ready`) |
| target / region | production / `iad1` |
| alias | `bag.fazr.co.kr` 포함 4개 |
| bundler | turbopack |

참고: 직전 `a05ebc5`(docs `[skip ci]`) 배포는 `CANCELED` 로 남아 있다. Ignored Build Step 이
의도대로 동작한 결과다.

---

# K. PRODUCTION SMOKE

| URL | HTTP | 확인 |
|---|---|---|
| `/` | 200 | 무변경 |
| `/gyeonggi` | 200 | 판매처 예시 31 · district 링크 31 · canonical 정상 |
| `/busan` | 200 | **변경 없음** · 링크 16 · 판매처 예시 0 |
| `/seoul` | 200 | 무변경 · 링크 25 · 판매처 예시 0 |
| `/gyeonggi/goyang` | 200 | **매장 카드 15** (`INITIAL_COUNT` 무변경 확인) |
| `/gyeonggi/siheung` | 200 | 1곳 정상 렌더 |

**live `/gyeonggi` 가시 텍스트 2,691자 = 로컬 빌드와 완전 일치.**

live HTML 이 로컬보다 일괄 +938B 인데, `/gyeonggi` `/busan` `/seoul` 전부 정확히 같은 값이다
→ Vercel 이 주입하는 고정 스크립트이며 콘텐츠 차이가 아니다.

---

# L. FINAL STATE

| | |
|---|---|
| HEAD | **`1f77370`** = origin/main |
| working tree | `?? tsconfig.tsbuildinfo` 만 |
| 테스트 | PASS 226 / FAIL 0 / exit 0 |
| data checksum | `59617a5e2965712e` (무변경) |
| routes / sitemap | 253 / 241 |
| production | `dpl_3JVSsNHVhfX9RoY7iVYH9879vVB7` READY |

---

# M. FOLLOW-UP BASELINE

`scratchpad/followup_baseline_20260904.json` (**git add 안 함**).

| 역할 | URL | 2026-09-04 상태 |
|---|---|---|
| **treatment** | `/gyeonggi` | Crawled - currently not indexed / lastCrawl `2026-04-30T10:55:04Z` |
| **comparison** | `/busan` | Crawled - currently not indexed / lastCrawl `2026-04-26T10:30:52Z` |
| untouched | `/seoul` | Crawled - currently not indexed / lastCrawl `2026-04-30T10:55:04Z` |
| — | `/gyeonggi/suwon` `/gyeonggi/anyang` `/busan/haeundae` | URL is unknown to Google |

사이트 전체: Search Analytics 90일 clicks 0 / impressions 0 · Google 이 아는 URL 6 / sitemap 241 ·
region crawled 3 / unknown 14.

관측 일정: ~~**+7일** `/gyeonggi` `/busan`~~ — **+21일** + `/gyeonggi/goyang` `/gyeonggi/yongin` `/busan/bsdonggu` — **+45일** + Search Analytics.

> **[정정 2026-09-04] +7일 대상은 3 URL 이 정본이다** — `/gyeonggi` `/busan` **`/seoul`**.
> 위 2 URL 은 superseded historical plan. 근거는 이 문서 §CC-5(`/seoul` 이 `/busan` 보다
> 가까운 비교군)이고, 정본 표기는 `GPT-HANDOFF-20260903.md` §13-4 에 있다.

규칙: URL Inspection 1회 **최대 6 URL** · READ-ONLY only · 색인요청 / 유효성검사 / sitemap 재제출 /
Indexing API **전부 금지** · scope `webmasters.readonly` 유지 · 서비스 계정 JSON `git add` 금지.

**배포 직후 GSC 호출 0건** (지시서 §18: baseline 이 이미 존재하므로 재호출 불필요).

---

# CC 이견 및 아이디어

## CC-1. 가드에 걸렸다 — PRE-REPORT 의 측정 오류를 보고한다

**첫 구현(V1)은 +44.7% 로 §12 hard guard(+25%)를 초과했다.** 배포하지 않고 원인을 분해했다.

| /gyeonggi | before | after(V1) | 증가 | 1건당(31 구군) |
|---|---|---|---|---|
| 전체 HTML | 70,450 | 101,929 | **+31,479** | 1,015 B |
| 렌더 HTML | 25,749 | 39,018 | +13,269 | 428 B |
| **RSC payload** | 39,787 | 56,073 | **+16,286** | **525 B** |

**원인: PRE-REPORT §D-1 이 렌더 HTML 만 계산하고 RSC payload 증가를 통째로 누락했다.**
`DistrictGrid` 는 server component 지만 그 **렌더 결과가 flight payload 에도 직렬화**되므로,
추가한 마크업이 **두 번** 실린다. 클래스 문자열이 JSON 이스케이프되면서 payload 쪽이 오히려 더 비싸다.

예측 12,369 B → 실제 31,479 B = **2.5배.** 이건 내 오류이고, PRE-REPORT 의 "+18%" 는 방법 자체가 틀렸다.

## CC-2. 가드를 낮추지 않고 마크업 4종을 전부 빌드해 실측했다

추정으로 맞추지 않았다. 각 변형을 실제로 빌드해서 쟀다.

| 변형 | HTML | 증가율 | 가시 텍스트 | 중립 라벨 | 판정 |
|---|---|---|---|---|---|
| V1 — wrapper + 별도줄 라벨 + name + address (4 span) | 101,929 | +44.7% | 2,598자 | 있음 | **가드 초과** |
| V2 — name + address (2 span), 라벨 없음 | 88,623 | +25.8% | 2,381자 | 없음 | **가드 초과** |
| V3 — 1 span, 라벨 없음 | 83,075 | +17.9% | 2,443자 | 없음 | 통과 |
| **V4 — 1 span, 인라인 라벨 (채택)** | **84,594** | **+20.1%** | **2,691자** | **있음** | **채택** |

**V4 는 V1 보다 바이트가 17% 적으면서 가시 텍스트는 더 많다.** V1 의 비용은 텍스트가 아니라
마크업 오버헤드(4개 span 의 클래스 문자열 × 렌더 + payload)였다.

> **정직하게 적는다.** V3 의 +17.9% 가 PRE-REPORT 예측 +18% 와 거의 일치하는 것은 **우연이다.**
> 예측은 "렌더만 31×399", V3 실측은 "렌더+payload 합계"다. 방법이 맞아서 맞은 값이 아니다.

**가드를 완화하지 않았다.** 핸드오프 §0-4-1("안전 게이트 때문에 깨지면 게이트를 약화하지 않는다")의
정신에 따라, 게이트를 조정하는 대신 변경 자체를 예산 안에 들어오게 만들었다.

## CC-3. UX 손실 1건 — 사람 판단을 요청한다

V4 는 중립 라벨을 지켰지만 **name 과 address 를 한 줄로 합쳤다** (`판매처 예시: 이름 · 주소`).
원래 의도는 `StoreCard` 처럼 이름/주소 2단이었으나 **바이트 예산이 허용하지 않았다.**

`md` 에서 4열 그리드라 카드가 좁고, 긴 주소는 여러 줄로 감긴다. 기능적 문제는 없으나 시각적 밀도가 올라간다.
실제 화면에서 2단이 낫다고 판단되면 V2(+25.8%)를 쓰기 위해 **가드 상향이 필요하다.
임의로 올리지 않았다.**

## CC-4. 같은 측정 오류가 PRE-REPORT §L-1 에도 있다 — Phase 2 전 재계산 필수

§L-1 의 `INITIAL_COUNT` 분석에 동일한 누락이 있다.

- "payload 는 이미 전 매장을 직렬화하므로 상향은 payload 를 늘리지 않는다" → **매장 데이터는** 맞다.
- 그러나 **렌더된 카드의 마크업(태그·클래스)도 payload 에 실린다.** 이 부분이 빠졌다.

따라서 §L-1 표는 **전부 과소평가**다.

| | PRE-REPORT 예측 | 이번 실측 기준 재추정 |
|---|---|---|
| `INITIAL_COUNT` 30 | +4.3% | **+8~9% 가능** |
| `INITIAL_COUNT` 50 | +9.7% | **+20% 안팎 가능** |
| `INITIAL_COUNT` 100 | +22.2% | **+40% 이상 가능** |

**이 값들도 추정이다. Phase 2 착수 전 실제 빌드로 재측정해야 한다.** 추정으로 진행하면 같은 실수를 반복한다.

## CC-5. comparison URL 의 한계 — 지시서 §19 표현을 채택했고, 두 가지를 덧붙인다

`/busan` 을 control 이 아니라 **comparison URL** 로 표기했다. 무작위 배정이 아니고 Google 크롤
스케줄링이 비결정적이라는 지적이 맞다. 추가 한계 2건:

1. **`/seoul` 도 손대지 않았으므로 comparison 이 사실상 2개다.** 셋 다 변하면 "사이트 전체 재평가"
   해석이 강해지고, gyeonggi 만 변하면 신호가 조금 더 강해진다. 관측 시 seoul 을 포함하는 편이
   이득이다 (추가 비용 1 URL, 6 URL 상한 내).
2. **`/gyeonggi` 와 `/seoul` 은 lastCrawl 이 초 단위까지 동일**(`2026-04-30T10:55:04Z`)하다.
   같은 크롤 배치에 묶였다는 뜻이고, **`/busan`(04-26)보다 `/seoul` 이 더 가까운 비교군일 수 있다.**

## CC-6. Google 가설에 대한 반증은 그대로 유효하다

PRE-REPORT §CC-4 의 반론(내부 링크 31개인 `/gyeonggi/anyang` 이 unknown, 2개인 기사가 crawled)은
이번 구현으로 **전혀 해소되지 않았다.** 이번 변경은 링크를 1개도 추가하지 않았고 문맥만 붙였다.
그건 의도한 대로다.

함의를 다시 적어둔다: **Phase 1 이 실패해도 그것은 "콘텐츠가 부족하다"의 반증이 아니라
"region 페이지 콘텐츠만으로는 부족하다"의 증거일 뿐이다.** 미관측 변수인 **외부 백링크 0**
(전 표본에서 referring 이 내부 URL 하나뿐)은 이번에도 건드리지 않았다. 45일 뒤 무변화라면
그때 다뤄야 할 후보라고 본다.

## CC-7. 다음 Phase 우선순위 변경 의견

CC-4 때문에 PRE-REPORT §M 의 순위를 조정한다.

| | PRE-REPORT | **수정 제안** | 근거 |
|---|---|---|---|
| 3순위 | `INITIAL_COUNT` 15→50 | **sitemap `lastmod`** | 비용이 사실상 0 이고 payload 오차와 무관하다. Google 이 lastmod 를 사이트 단위로 무시하는 상태를 먼저 푸는 편이 낫다 |
| 4순위 | sitemap `lastmod` | **`INITIAL_COUNT`** | **실측 재계산이 선행 조건.** 그리고 district 가 여전히 unknown 이면 측정 자체가 불가능하다 |

`adjacentDistricts` 는 PRE-REPORT §CC-4 의 반증 때문에 **더 낮은 우선순위**를 유지한다.

**P20-SAFETY-TEST-HARDENING 시점**은 PRE-REPORT §M-1 의견 그대로다 — **지금 45일 관측 대기 기간에 착수.**
파일이 `scripts/` 로 `app/`·`components/` 와 겹치지 않아 comparison 오염 위험이 0이다.
순서: **C → A → E → F 개별 코드 → 마스킹 2건(`:643` `:692`) → 항진명제(`:826`) → structural self-test.**

---

*Phase 1 종료. 다음 행동은 45일 관측이며, 그 전까지 region 페이지를 추가로 변경하지 않는다
(comparison 오염 방지 — PRE-REPORT §K7).*
