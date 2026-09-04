# GPT 핸드오프 — 2026-09-04 (Production HEAD `9d79168` 기준)

> 이 문서는 **정본**이다. 다음 세션은 커밋 로그를 다시 읽기 전에 이 문서부터 읽는다.
> 이전 핸드오프: `docs/gpt/GPT-HANDOFF-20260426.md` (P17/P17.5)
> 참고 문서: `docs/SESSION_REPORT.md` · `docs/AUDIT-20260903.md` (둘 다 **갱신 지연 상태** — §11 참조)

---

# 0. 다음 세션이 먼저 읽어야 할 영구 규칙

> 아래 8개는 이번 세션에서 실제 사고를 막았거나 실제 사고를 낸 뒤 세운 규칙이다.
> **어기면 production 데이터가 파괴된다.** 편의를 위해 완화하지 않는다.

### 1. Collector fail-closed

수집의 **완전성을 증명하지 못하면 write / delete / promotion을 0건 수행한다.**

- `fetch_all()`은 부분 수집에서 `break` 하지 않고 `CollectionError`를 던진다.
- 종료 조건은 `len(all_items) >= expected_total`(API가 준 `totalCount`)이다.
  요청한 `numOfRows`가 아니라 **첫 응답에서 실측한 page size**를 쓴다.
- 근거: P17.6이 "부분 수집 → 그 결과로 stale 판정 → 대량 삭제" 경로를 심었고,
  실제로 강북구 데이터가 5개월간 오염된 채 라이브였다.

### 2. Single integrity gate

**게이트 전체를 통과하기 전에는 production promotion을 하지 않는다.**

게이트는 `scripts/integrity.py`의 `validate_candidate()` 하나뿐이다.
**named gate는 A–G 7개이고, 별도로 S-prefixed structural audit이 있다.**

**Candidate integrity gate**

| | 검사 | 함수 |
|---|---|---|
| A | API completeness (`raw == totalCount`) | `validate_candidate` 내부 |
| B | stage reconciliation | `check_reconciliation` |
| C | store location integrity (region/district 독립 재도출) | `check_store_locations` |
| D | schema drift | `check_schema_drift` |
| E | contradiction accounting | `check_contradiction_accounting` |
| F | serialized tree reconciliation (`tree_vs_stats` 포함) | `check_tree_counts` |
| G | explicit mutation plan (created/modified/removed/kept) | `diff_trees` |

**A–G 중 하나라도 실패하면:**

```
promotion 0
production preserved
process non-zero
```

**별도 structural audit — S-prefixed checks.**
`audit_tree_structure()`. crash-recovery 경로에서 production / backup tree의 **구조 검증**에만 쓴다.
candidate 게이트가 아니다.

`integrity.py`는 **쓰기 0건**, `__main__` 없음, 순수 모듈이다.

### 3. Rollback-safe promotion

순서는 **candidate → integrity gate → backup → promotion**이다.

- `build_candidate()`는 workspace에만 쓴다. production을 건드리지 않는다.
- `promote_candidate()`는 `data → backup → candidate → data` 순서로 옮기고 실패 시 롤백한다.
- **"atomic directory swap"이라고 표현하지 않는다.** POSIX에 디렉터리 원자 교체는 없다.
  macOS/APFS 실측: `os.rename`과 `os.replace` **둘 다** 비어 있지 않은 대상 디렉터리에
  `ENOTEMPTY(66)`로 실패한다. 따라서 이건 원자 연산이 아니라 **롤백 가능한 다단계 연산**이다.
- SIGKILL·전원 차단·OS 크래시는 Python 예외가 아니므로 rollback이 실행되지 않는다.
  다음 실행 시작 시 **디스크 상태로 판정**한다: `recover_promotion_state()`.

```
data  backup  candidate  판정
────  ──────  ─────────  ───────────────────────────────────────────
 O      X         X      A) 정상
 O      X         O      E) production 확인 후 candidate 정리
 X      O        any     B) backup → data 복구 후 실행 중단
 O      O        any     C) data 구조 감사 PASS면 backup 제거
                            FAIL이면 backup 보존 + fail closed
 X      X        any     D) production 상실. HARD FAIL (사람이 복구)
```

**`.data-backup`을 잔여물로 취급해 무조건 지우지 않는다.** 첫 rename 직후 죽었다면
그것이 **유일하게 남은 production**이다. (이 구멍은 P3-13 커밋 직전에 발견해 막았다.)

### 4. Test gate

**테스트를 실행하는 것만으로는 부족하다. 실패가 non-zero exit로 전파되어야 한다.**

- summary / `sys.exit` 블록은 **반드시 파일 맨 끝**에 있어야 한다.
- 마지막 structural self-test가 **"summary/exit 블록 뒤에 새 check가 추가됐는지"**를 검증한다.
  뒤에 추가되면 스위트가 **실패**해야 한다.
- self-check가 자기 자신을 오탐하지 않도록 marker 문자열은 런타임에 조립한다
  (`_summary_marker = 'print(f"PASS {len(' + 'PASS)} / FAIL'`).
- 보고할 때 **실행된 assertion 수 / PASS-FAIL / process exit code를 각각 분리해서** 쓴다.
- 이 규칙은 실제 사고에서 나왔다. §4 참조.

### 5. Administrative SSOT

**행정구역 매핑을 현재 API sample에서 추론하지 않는다.**

- 정부 공식 행정구역 authoritative data로 **exact-set 검증**한다.
- 예: `scripts/legacy_districts.json`은 인천광역시 토지정보과 CSV를 1차 출처로,
  국토교통부 전국 법정동을 교차검증으로 써서 법정동 집합이 **정확히 일치**함을 기록했다
  (`_verified` 블록). 표본 일치나 부분 일치가 아니다.
- **법정동과 행정동을 구분**한다. 개편 매핑은 법정동 기준이다.

### 6. Identity separation

**collector / storage / canonical identity 와 user-facing display label을 분리한다.**

- `REGIONS.name`, slug, URL, 파일 경로는 **데이터 정체성**이다. 표시 때문에 바꾸지 않는다.
- 표시명은 `lib/regions.ts`의 별도 매핑에서 온다
  (`INCHEON_LEGACY_DISPLAY` / `LEGACY_REGION_DISPLAY`).
- **매장 주소 원문 rewrite 절대 금지.** 주소는 내비게이션용 데이터다.
  제물포구 → 중구, 영종구 → 중구, 서해구·검단구 → 서구,
  전남광주통합특별시 → 광주광역시·전라남도 **전부 금지**.

### 7. Legacy compatibility bucket

**legacy slug가 현재 행정구 하나와 1:1 대응한다고 가정하지 않는다.**

- `/incheon/icjunggu`는 옛 인천 중구 영역이고, 현재 기준으로 **제물포구 + 영종구** 두 구를 덮는다.
- URL/저장 slug는 **legacy 식별자**일 뿐이고 표시 label은 그것과 별개다.
- 개편이 "예정"인지 "이미 시행"인지 혼동하지 않는다. **API 반영 지연 ≠ 미시행.**

### 8. 배포 규칙

- docs/md만 바꾸는 커밋에는 `[skip ci]`를 붙일 수 있다.
- **배포가 필요한 code/data와 함께 push할 때 최종 HEAD를 `[skip ci]`로 두지 않는다.**
- 커밋은 로컬에서 다 만들고 **push는 한 번**만 한다.
- **code와 data를 한 커밋에 섞지 않는다.**
- **이미 push한 커밋은 amend/rebase 하지 않는다.** 오류는 문서에서 정정한다.

---

# 1. 현재 Production 정본

| | |
|---|---|
| HEAD | `9d79168` |
| 배포 확인 | 2026-09-04, push 후 약 60초에 반영 |
| 정적 페이지 | 253 routes (HTML 252 + `sitemap.xml`) |
| 매장 총계 | **69,265건** / 데이터 파일 221개 |
| data checksum | `c6e2934b7173b8b9` (`find data -type f -name '*.json' \| sort \| xargs shasum -a 256 \| shasum -a 256`) |
| `scripts/collect.py` sha256 | `b121e0b6725e6260` (앞 16자) |
| 테스트 | `PASS 120 / FAIL 0`, process exit code 0 |

### Production 완료 항목

| 단계 | 내용 | 커밋 |
|---|---|---|
| P17.7 | collector fail-closed | `d52e11c` `f9672fa` `94b0d11` |
| P17.8 | 전남·광주 통합 + 인천 개편 collector 대응 | `a01e4b9` `54ea10c` |
| P17.9 | legacy 파괴 스크립트 3종 폐기 + test gate 강화 | `d938939` |
| P3-13 | 단일 integrity gate + rollback-safe promotion | `7ec247a` |
| StoreCard factuality | 근거 없는 "영업중" 표시 제거 | `c43a517` |
| Incheon display | 인천 2026 개편 표시 | `70b1e18` |
| Gwangju/Jeonnam display | 전남·광주 통합 표시 | `9d79168` |

---

# 2. 오늘 커밋 (시간순 14건)

| # | 커밋 | 시각 | 무엇을 닫았는가 |
|---|---|---|---|
| 1 | `35206ca` | 09-03 18:06 | 전수 감사 보고서 추가. P0/P1 목록을 문서로 고정해 이후 작업 범위의 기준이 됐다. `[skip ci]` |
| 2 | `eebaf6a` | 09-03 18:06 | **강북구 오염 데이터 12,463행 제거.** 잘못된 지역의 매장이 5개월간 강북구 페이지에 라이브였다. |
| 3 | `eb1f9d4` | 09-03 18:07 | P17.6 핫픽스. og:image 유실(249페이지), 송파 빈 칩, 중복 구군명 29건 title 중복을 한 번에 닫았다. |
| 4 | `6c9f05c` | 09-03 18:16 | 세션 리포트 갱신. `[skip ci]` |
| 5 | `f9672fa` | 09-03 19:50 | API 키 파일을 `.gitignore`에 등록. 키가 커밋·로그·리포트로 새는 경로를 차단. |
| 6 | `d52e11c` | 09-03 19:53 | **collector fail-closed.** 부분 수집 시 `break` 대신 `CollectionError`. P17.6이 심은 "부분 수집 → stale 판정 → 대량 삭제" P0 경로를 막았다. |
| 7 | `94b0d11` | 09-03 20:38 | page size를 요청값이 아니라 **첫 응답 실측값**으로 도출. 직전 커밋이 만든 회귀(요청 1000 vs 실제 100 → 수집 항상 실패)를 닫았다. |
| 8 | `a01e4b9` | 09-03 21:07 | **전남광주통합특별시** 처리. 병합 시도 토큰을 인식하고 하위 구·시군으로 안전 귀속. 미등록 시도는 신규 토큰 / 주소 오류로 분류. |
| 9 | `54ea10c` | 09-03 21:50 | **인천 2026 개편** 처리. 법정동 기준 legacy 라우팅 + `legacy_districts.json` SSOT. 테스트 기록 정정은 §4 참조. |
| 10 | `d938939` | 09-03 22:10 | `classify_all.py` / `reclassify.py` / `reclassify_all.py` **3종 폐기**(744행 삭제). 이들은 게이트 없이 data를 직접 덮어썼다. 재등장 방지 회귀 가드 추가. |
| 11 | `7ec247a` | 09-04 00:19 | **P3-13.** `integrity.py` 신설, 단일 게이트, candidate 트리, rollback-safe promotion, crash recovery 상태 머신. §8 참조. |
| 12 | `c43a517` | 09-04 06:04 | 하드코딩된 "영업중" 배지 제거. 데이터로 뒷받침되지 않는 주장을 UI에서 삭제. §7 참조. |
| 13 | `70b1e18` | 09-04 09:53 | 인천 3개 legacy bucket 표시 확정 + "데이터 갱신일" → "데이터 수집일" 사이트 전체 통일. §6 참조. |
| 14 | `9d79168` | 09-04 10:37 | 전남·광주 통합 표시 확정. region 2개 + district 27개 + 홈 + 인접 칩 4개. §6 참조. |

---

# 3. 검증 방법 메모 (다음 세션이 반복하게 될 것)

- **before/after 전수 diff.** 변경 파일을 `git checkout --` 로 되돌려 before 빌드를 뜨고,
  복원 후 after 빌드를 떠서 252개 페이지의 정규화 텍스트를 비교한다.
  full HTML 해시는 쓰지 않는다 — Next.js buildId가 매 빌드 바뀌어 252/252가 항상 다르게 나온다.
- 정규화: `<script>`/`<style>` 제거 → 태그 제거 → 공백 정리. JSON-LD는 따로 추출한다.
- 이 방법으로 `9d79168`의 blast radius가 **정확히 34페이지**임을 확인했다
  (광주·전남 29 + 홈 1 + `/seoul` `/busan` `/daegu` `/incheon` 4).

---

# 4. P17.8 테스트 기록 정정 (`54ea10c`)

**"실제 테스트 수 50"이라고 쓰지 않는다.** 정확한 기록은 다음과 같다.

| | |
|---|---|
| 당시 화면 summary | `PASS 50 / FAIL 0` |
| **이후 재현한 실제 실행 assertion** | **72** |
| 구성 | summary 이전 **50** + summary 이후 **22** = **72** |
| process exit code | 0 |

**원인.** summary / `sys.exit` 블록이 테스트 파일 **중간**(483행 중 389행)에 있었다.
그 뒤의 22개 assertion은 **실행은 됐지만 summary와 process exit gate에는 반영되지 않았다.**
즉 뒤쪽 22개가 실패했어도 커밋 게이트는 통과했을 것이다.

`d938939`(P17.9)에서 harness 구조를 수정했고, **실패가 non-zero exit로 전파되도록** 보강했다.
이후 summary 블록은 파일 맨 끝에 고정되고, 마지막 structural self-test가 그 위치를 강제한다. → §0-4

**재현 방법 (2026-09-04 실측).** 저장소와 완전히 격리된 사본에서 확인했다.

```
git show 54ea10c:scripts/{collect.py,test_collect.py,legacy_districts.json}
git show 54ea10c:lib/regions.ts
cp -R data <격리사본>/data          # 읽기 전용 사용. 원본 data/ 무변경 확인 완료
python3 scripts/test_collect.py     # → 화면 "PASS 50 / FAIL 0"
# 파일 끝에 print(len(PASS)+len(FAIL)) 한 줄만 덧붙여 재실행 → 72
```

`data/`는 `eebaf6a` 이후 변경 커밋이 0건이므로, 이 재현은 `54ea10c` 당시와 같은 데이터로 돌았다.

**현재(HEAD `9d79168`) 상태:** 997행, summary 블록 991행(파일 끝),
summary 이후 assertion 0개, `PASS 120 / FAIL 0`, process exit code 0.

---

# 5. API A/B 정본

> 출처: 2026-09-03~04 API 조회. 재확인하려면 `scripts/.apikey` (chmod 600, gitignored).
> **키는 어떤 경우에도 대화·로그·커밋·리포트에 남기지 않는다.**

### 총계

| | |
|---|---|
| raw `totalCount` (현재) | **91,116** |
| raw (2026-03 수집) | 90,413 |
| operating (현재) | **72,477** |
| operating (2026-03) | 72,423 |
| 저장된 매장 (production) | 69,265 |

### localCode A/B

| 변형 | `totalCount` |
|---|---|
| `6110000_ALL` (서울) | 91,116 |
| `6260000_ALL` (부산) | 91,116 |
| `6270000_ALL` (대구) | 91,116 |
| 파라미터 생략 | 91,116 |

**4개 변형 모두 `totalCount` 동일, 첫 페이지 응답 byte-identical.**

### 결론

**`localCode`는 현재 API에서 무시되고 있다.** 지역 필터로 동작하지 않는다.
따라서 **서울 sparsity의 원인이 아니다.**

### 서울 현황

- `/seoul/*` 페이지 25개 중 **데이터 파일이 아예 없는 구가 3개**:
  **강북구 · 송파구 · 중랑구** (0곳 안내 페이지로 렌더 중)
- 나머지 22개 구 합계 3,118곳. 그중 **10곳 미만이 11개 구**
  (동작 1, 용산 2, 양천 2, 강동 3, 강서 3, 구로 4, 도봉 4, 서대문 4, 영등포 5, 성동 5, 관악 6)

> **P19 recollection만으로 강북구가 채워지지 않는다.**
> 소스 API 자체가 서울에 대해 희소하다. 이건 수집 방식 문제가 아니라 원본 결측이다.
> 재수집을 "서울 커버리지 해결책"으로 기대하지 않는다.

---

# 6. 2026 행정구역 개편 정본

## 6-1. 인천 (`70b1e18`)

**2026-07-01 시행.** 2군8구 → 2군9구.
중구 → 제물포구 + 영종구 / 동구 → 제물포구 / 서구 → 서해구 + 검단구.

**이미 법적으로 시행 중이다. "예정"이 아니다.** API 반영 지연과 혼동하지 않는다.

### legacy compatibility bucket

| URL | 영역 | 현재 기준 coverage |
|---|---|---|
| `/incheon/icjunggu` | 옛 인천 중구 | **제물포구 + 영종구** |
| `/incheon/icdonggu` | 옛 인천 동구 | 제물포구 |
| `/incheon/icseogu` | 옛 인천 서구 | **서해구 + 검단구** |

### Production 표시

```
제물포구·영종구 (옛 인천 중구)
제물포구 (옛 인천 동구)
서해구·검단구 (옛 인천 서구)
```

- 개편 페이지는 label이 길어 title 공통 suffix(가격·크기·2026)를 뺀다.
- DistrictGrid selector는 2단(주 label + 옛 이름 보조 문구).
- `/incheon` 최상단 전역 공지는 넣지 않았다.
- FAQ 답변은 `scopeLabel`을 쓴다. `longLabel`을 쓰면 "제물포구·영종구에는 82곳"이
  **두 구 전체의 합**으로 오해된다.

### SSOT

`scripts/legacy_districts.json` — old_junggu 44 / old_junggu_yeongjong 8 / old_donggu 7.
1차 출처 인천광역시 토지정보과 CSV, 교차검증 국토교통부 전국 법정동, exact-set 일치 기록(`_verified`).

**StoreCard 주소는 원천 그대로.** 행정명 rewrite 금지.

## 6-2. 광주 / 전남 (`9d79168`)

### 법적 정본

| | |
|---|---|
| 특별법 | 전남광주통합특별시 설치 및 지원에 관한 특별법 |
| 제정 | **2026-03-05** |
| 시행 | **2026-07-01** |
| 법정 약칭 | **광주특별시** (법 제7조) |
| 종전 | 광주광역시 **폐지** / 전라남도 **폐지** |
| 구성 | 5시 5구 17군 |

> 뉴스 요약의 "6월 24일 국회 통과"를 근거로 쓰지 않는다. 위 날짜가 정본이다.

### 구조

하위 27개(광주 5구 + 전남 22시군)는 **구·시군 identity를 그대로 유지**한다.
북구는 여전히 북구고 보성군은 여전히 보성군이다. 이 27개를 묶는 **현재 행정 단위는 없다.**
`/gwangju`와 `/jeonnam`은 통합특별시 안의 옛 영역을 보존하는 **compatibility region**이다.

"광주 지역" 같은 **준행정명을 만들지 않는다.** 법정 약칭 + 폐지된 옛 시도명을 병기한다.

### 표시 label (SSOT: `lib/regions.ts` `LEGACY_REGION_DISPLAY`)

| 종류 | `/gwangju` | `/jeonnam` | 쓰이는 곳 |
|---|---|---|---|
| `longLabel` | 광주특별시 (옛 광주광역시) | 광주특별시 (옛 전라남도) | region title·H1·meta·OG·FAQ |
| `shortLabel` | 광주특별시 (옛 광주) | 광주특별시 (옛 전남) | region breadcrumb |
| `currentLabel` | 광주특별시 | 광주특별시 | 섹션 제목·내부링크 anchor·인접 칩·district 전 surface |
| `legacyLabel` | 옛 광주광역시 | 옛 전라남도 | RegionGrid 카드 보조 문구 |

### Production 실측

- `/gwangju` title 30자 / `/jeonnam` title 29자 (suffix 축약 적용, 현재값보다 짧다)
- H1 26자 / 25자, meta description 65자 / 65자
- region title 중복 0, H1 중복 0 (사이트 전체)
- RegionGrid 3단: `광주특별시 / 옛 광주광역시 / 2524곳`, `광주특별시 / 옛 전라남도 / 6736곳`

### district 27개

- **title / H1 무변경.** 광주 북구, 보성군 그대로. 구·시군 이름이 현재도 유효하기 때문.
- breadcrumb 상위 노드 · FAQ 답변 · 내부링크 anchor · 섹션 제목은 **`currentRegionLabel` = 광주특별시**.
  27/27 전수 확인.

### 판단 근거 2건 (다음 세션이 되돌리지 않도록)

1. **`REGIONS.name`을 바꾸지 않는다.** collector `REGION_NAME_TO_SLUG`와 이름 체계를 공유하고,
   `REGION_SHORT_NAMES`를 바꾸면 중복 구군명 4개(동구·서구·남구·북구)의 title까지 흔들린다.
2. **region FAQ 답변만 병기형을 쓴다.** 이 답변은 개수를 말한다.
   현재명만 쓰면 "광주특별시에는 5개 시/군/구"가 되어 사실과 다르고(전체는 27개),
   `/jeonnam`은 22개라고 해서 두 페이지가 서로 모순된다.
   district FAQ 답변("광주특별시 북구에는 현재 665곳")은 현재명만 쓴다 — 구 이름이 이미 범위를 한정한다.

**StoreCard 주소 rewrite 금지.** production 실측으로 27개 페이지 주소 블록이
배포 전후 바이트 동일임을 확인했다.

---

# 7. StoreCard factuality 정본 (`c43a517`, `70b1e18`)

### 무엇이 문제였나

- 기존 "영업중" 배지는 **하드코딩**이었다. `store.status`를 읽지 않았다.
  모든 매장에 무조건 초록색 "영업중"이 붙었다.
- 저장된 69,265건은 **`SALS_STTS_CD == "01"` 필터 결과**다.
  이건 수집 시점의 인허가 상태이지 **현재 실세계 영업 여부를 증명하지 않는다.**
- `licenseDate`는 `APLY_YMD`, 즉 **신청일(application date)**이다.
  **폐업 판단 근거가 아니다.**

### 조치

- Production에서 **"영업중" 배지 제거.**
- 본문·메타에서 영업 상태를 단정하는 표현 중립화.
- `store.status` 필드 자체는 **유지**한다(데이터는 남기고 주장만 뺀다).
- Footer 면책 문구는 유지.
- **"데이터 갱신일" → "데이터 수집일"** 로 사이트 전체 통일 (홈·시도·구군 전부).

> 수집 로그의 12,718건은 **폐업 건수가 아니다.** 이 숫자를 폐업 근거로 인용하지 않는다.

---

# 8. P3-13 정본 (`7ec247a`)

**단일 integrity gate + rollback-safe promotion.** 1,113 insertions.

### 구성

- **`scripts/integrity.py` (414행, 신설).** 순수 모듈. **쓰기 0건**, `__main__` 없음.
  `collect.py`에서 `importlib.util`로 같은 디렉터리에서 로드한다(`sys.path` 오염 없음).
  구성 요소: `IntegrityReport` · `read_tree` · `check_tree_counts` · `check_store_locations` ·
  `check_reconciliation` · `check_schema_drift` · `check_contradiction_accounting` ·
  `diff_trees` · `audit_tree` · `audit_tree_structure` · `validate_candidate`
- **candidate 트리.** `build_candidate()`는 workspace에만 쓴다. production 무접촉.
- **A–G 게이트.** §0-2 표 참조. `report.ok`가 False면 호출부는 promotion을 하지 않는다.
- **명시적 변경 계획.** `diff_trees()`가 created / modified / removed / kept를 산출한다.
  "무엇이 바뀔지"를 promotion 전에 로그로 남긴다.
- **rollback-safe promotion.** `data → backup → candidate → data`, 실패 시 롤백.
- **APFS 실측.** `os.rename`과 `os.replace` **둘 다** 비어 있지 않은 대상 디렉터리에
  `ENOTEMPTY(66)`. → "atomic swap"이라는 표현을 쓰지 않는 근거.
- **crash recovery 상태 머신 A–E.** `recover_promotion_state()`. §0-3 표 참조.
- **hard crash 테스트.** `os._exit(9)`로 프로세스를 강제 종료해 각 crash window를 재현하고,
  다음 실행이 올바른 상태로 판정·복구하는지 검증한다.
  (`atexit`으로는 exit code를 설정할 수 없다 — `SystemExit`은 "Exception ignored"로 삼켜져 exit 0.)

### 커밋 직전에 막은 P0

`promote_candidate()`가 `.data-backup`을 **무조건 `rmtree`** 하고 있었다.
crash 직후라면 그것이 **유일하게 남은 production**이다.
→ backup이 존재하면 promotion을 **거부**하고, `recover_promotion_state()`가 먼저 판정하도록 고쳤다.

### 상태

- 테스트 **120 assertions PASS / FAIL 0 / exit 0**
- **production data 무변경** (checksum `c6e2934b7173b8b9` 유지)
- **generation manifest / generation ID는 deferred candidate.** 이번에 구현하지 않았다.

---

# 9. AdSense 로컬 검증 메모

**Production에서는 재현되지 않는다. P1 bug로 승격하지 않는다.**

### Production 실측 (2026-09-04, `https://bag.fazr.co.kr/gwangju`)

- HTTP 200, 콘솔 fatal error **0건**
- client error boundary **없음**, 링크 14개 정상 렌더
- AdSense 슬롯 6개 중 4 filled / 1 unfilled — 정상 동작

### 로컬에서만 나타나는 현상

`next start`로 프로덕션 빌드를 띄우고 브라우저로 열면
AdSense가 **localhost origin을 거부(403)** 하고, 그 여파로 페이지가
client error boundary로 넘어간다. 내가 수정하지 않은 페이지(`/seoul/gangnam`)에서도 동일하게 재현된다.

### 검증 주의사항

**로컬에서 SSR/CSS 레이아웃을 검증할 때는 광고 스크립트를 차단해야 한다.**
HTML을 고치지 말고 **CSP 헤더를 덧붙이는 프록시**를 쓴다
(`Content-Security-Policy: script-src 'none'` → SSR HTML + CSS만 렌더).
HTML 문자열을 치환하면 RSC 페이로드가 깨져 오히려 error boundary가 난다.

---

# 10. P19 상태 — **HARD BLOCK**

### 다음 세션의 순서

1. **이 handoff 정본 확인**
2. **P19 SAFETY FINAL JUDGMENT** (collector가 안전한가)
3. **P19 VALUE / NECESSITY JUDGMENT** (지금 재수집할 가치가 있는가)
4. **safety + value 둘 다 GO일 때만** recollect
5. recollection 후 **integrity gate 통과 전 promotion 금지**

### 반드시 지킬 것

> **"collector가 안전해졌다"와 "지금 recollect할 가치가 있다"를 절대 같은 판단으로 취급하지 않는다.**

- 서울 sparsity는 **public API 자체의 희소성**이다.
  P19가 강북구 문제를 해결한다고 **기대하지 않는다.** (§5 참조)
- 현재 production에 **42건의 도로명/지번 위치 모순**이 남아 있다. 자동 수정하지 않았다.

### 판정 시 함께 볼 것 (미결)

인천과 광주는 **P19 이후 성격이 다르다.**

- **인천**: 재수집하면 주소가 제물포구·영종구·서해구·검단구로 바뀐다.
  그러면 `/incheon/icjunggu` 페이지 제목의 구 이름이 **주소에 아예 나오지 않는** 상태가 된다.
- **광주·전남**: 구·시군 이름이 일치하고 상위 시도명만 갱신되므로 **모순이 없다.**
  `/jeonnam/boseong`에 "전남광주통합특별시 보성군" 주소가 나오는 것은 정확한 주소다.

이 둘을 한 판단으로 묶지 않는다.

---

# 11. Deferred (이번에 구현·재판정하지 않는다)

| 항목 | 비고 |
|---|---|
| GSC indexing diagnosis | Google 색인 0 (사용자 보고). canonical은 정상. |
| 0–9 store pages | 전국 33개 (서울 11개 포함) |
| server-rendered store coverage | 페이지당 초기 렌더 매장 수 제한 |
| template similarity | 페이지 간 본문 유사도 |
| search trim bug | P3 이월 |
| 42 road/lot contradictions | 현재 production에 잔존. 자동 수정 안 함. |
| schema drift sensor | 게이트 D는 있으나 상시 센서는 없음 |
| richer API fields | 미사용 필드 활용 |
| BreadcrumbList JSON-LD | **사이트 전체 미구현.** 현재 JSON-LD는 FAQPage뿐이다. |
| `/gwangju` ↔ `/jeonnam` cross-link | 같은 통합특별시인데 서로 링크가 없다 |
| 통합 안내문 | `/gwangju` `/jeonnam` 상단 한 줄 안내 |
| historical exception metadata | 연기군 / 군위군 |
| 홈 가격표 모순 | 20L 490원 vs FAQ 500~1,000원 |
| AdSense 문서/코드 모순 | P3 이월 |
| sitemap lastmod | P3 이월 |
| `docs/AUDIT-20260903.md` 전면 갱신 | 현재 P17.6 시점 내용. **HEAD와 불일치.** |
| `docs/SESSION_REPORT.md` 갱신 | 현재 P18-A 시점 내용. **HEAD와 불일치.** |

---

# 12. GPT에게 요청하는 것

**P19 SAFETY FINAL JUDGMENT 진행 승인.**

이때는 **"코드가 안전한가"만 따로 판정한다.** 재수집 가치 판단은 그다음 단계로 분리한다. → §10
