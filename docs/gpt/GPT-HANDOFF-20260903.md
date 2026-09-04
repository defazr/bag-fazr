# GPT 핸드오프 — bag.fazr.co.kr 정본

> **리비전 표기 규약.** 이 프로젝트는 세 가지가 서로 다를 수 있으므로 `HEAD` 한 단어로 뭉뚱그리지 않는다.
>
> | 용어 | 뜻 | 2026-09-04 현재 |
> |---|---|---|
> | **repository HEAD** | git 이력의 최신 커밋. docs-only 커밋도 포함된다 | **값을 적지 않는다** — `git rev-parse --short HEAD` 로 확인 |
> | **production revision** | 실제로 배포되어 라이브를 서빙하는 커밋 | `befe834` (`dpl_GvogSRHiaFRkM5QWRMMhwsfj26Pc`, READY) |
> | **canonical data revision** | production `data/` 를 마지막으로 바꾼 커밋 | `dc22fe2` (P19 재수집) |
>
> 셋이 같아 보이는 시점도 있지만 일치를 전제하지 않는다. docs-only 커밋은 repository HEAD 만 올리고
> production revision 을 바꾸지 않는다 (§0-8).
>
> **repository HEAD 는 이 문서에 값으로 적지 않는다.** 자기참조이기 때문이다 — 값을 적어 넣는
> 그 커밋이 곧 HEAD 를 바꾸므로 기록하는 순간 낡는다. 나머지 둘은 docs-only 커밋으로 바뀌지
> 않으므로 고정값으로 적어도 안전하다.

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
**named gate는 A–G 7개이고, 별도로 structural audit(`audit_tree_structure()`)이 있다.**

> **[정정 2026-09-04]** 이전 판은 이를 "S-prefixed structural audit" 이라고 적었으나 사실과 다르다.
> `S.` 접두 코드는 **`S.empty` 하나뿐**(`integrity.py:580`)이고, 나머지 구조 실패는
> `check_tree_counts()` 에 위임되어 **`F.*` 접두**로 나온다. 실측:
> 빈 디렉터리 → `['S.empty']` / count 불일치 트리 → `['F.file_selfcount','F.index_vs_file', …]`.
> **차단 동작에는 영향이 없다** — `recover_promotion_state()` 는 접두사가 아니라
> `report.ok`(= `failures` 유무)만 본다 (`collect.py:1007`).

**Candidate integrity gate**

| | 검사 | 함수 |
|---|---|---|
| A | API completeness (`raw == totalCount`) | `validate_candidate` 내부 |
| B | stage reconciliation | `check_reconciliation` |
| C | store location integrity (region/district 독립 재도출) | `check_store_locations` |
| D | schema drift | `check_schema_drift` |
| E | contradiction accounting | `check_contradiction_accounting` |
| F | serialized tree reconciliation (`tree_vs_stats` 포함) | `check_tree_counts` |
| G | explicit mutation plan + **catastrophic-drop guard** | `diff_trees` + `check_drop_guard` |

**G 하위 실패 코드 6개** (전부 `report.fail`. 임계값 근거는 §10-6):

| 코드 | 조건 |
|---|---|
| `G.total_wipe` | production > 0 AND candidate == 0 |
| `G.national_drop` | 전국 손실률 >= 25% (절대량 하한 **없음**) |
| `G.region_drop` | 시도 손실 >= 30건 AND >= 10% |
| `G.district_drop` | (구군 손실 >= 100건 AND >= 10%) OR >= 500건 |
| `G.district_extinction` | production >= 20건인 구군이 0 이 됨 |
| `G.mass_drop` | material-drop(>=20건 AND >=5%) 구군 >= 15개 OR 합계 >= 2,000건 |

**A–G 중 하나라도 실패하면:**

```
promotion 0
production preserved
process non-zero
```

**별도 structural audit — `audit_tree_structure()`.** (§0-2 정정 참조: `S.` 접두는 `S.empty` 하나뿐이고 나머지는 `F.*` 로 나온다)
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
- **테스트가 있다는 사실은 안전의 증거가 아니다. 그 테스트가 무엇을 단언하는지를 본다.**
  실제로 테스트 [4]가 `totalCount=0` 을 정상 완결로 단언하며 전멸 경로를 보증하고
  있었고, 스위트는 그 상태로 PASS 였다. → §10-1
- 이 규칙은 실제 사고에서 나왔다. §4 참조.

### 4-1. 안전 게이트 vs 테스트 fixture

**안전 게이트 때문에 기존 테스트가 깨지면 안전 게이트를 약화하지 않는다.**
테스트가 본래 검증하려던 목적을 유지하도록 **fixture 를 수정**하고,
그 fixture 에 **왜 safety gate 대상이 아닌지 주석으로 남긴다.**

**어떤 안전 규칙을 완화하는 근거로 "다른 계층이 이미 커버한다"고 주장하려면,
실제 현재 상수와 fixture 에 대입해 그 주장을 먼저 검증한다.
추측으로 cross-layer coverage 를 주장하지 않는다.**

> 실패 사례 (2026-09-04, FIX-2A 로 정정). 급감 가드 도입 후 promotion mechanics
> 테스트(production 3건 → candidate 1건)가 전국 게이트에 걸리자, 게이트에
> 절대량 하한 1,000건을 넣어 통과시켰다. 근거로 "그 구간은 시도·구군 게이트가
> 본다"고 적었으나 **상수와 대조하지 않은 추측이었다.** 3 → 1 은
> R1(>=30건)·D1(>=100건)·D2(>=20건)·AGG(>=20건) 어디에도 걸리지 않는다.
> 즉 전국 66.7% 붕괴가 통과하는 구멍을 스스로 만든 것이다.
> 정정: 하한을 제거하고 fixture(`GOOD3`)를 고쳤다.

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

> **[전면 개정 2026-09-04]** 이전 판은 배포 제어를 `[skip ci]` 로 설명했다. **틀렸다.**
> 이 프로젝트에서 배포 여부를 결정하는 것은 오직 Vercel **Ignored Build Step** 의 exit code 다.
> 실증: `befe834` 는 커밋 메시지에 `[skip ci]` 를 달았는데도 production 배포가 발생했다
> (`dpl_GvogSRHiaFRkM5QWRMMhwsfj26Pc`, READY). 반대로 docs-only 커밋이 CANCELED 된 것은
> `[skip ci]` 때문이 아니라 ignore 명령이 exit 0 을 반환했기 때문이다.

**현재 Ignored Build Step (2026-09-04 개정):**

```
git diff --quiet HEAD^ HEAD -- ':!*.md' ':!docs/' ':!scripts/'
```

exit 0 = 빌드 건너뜀 / exit 1 = 빌드 진행 / exit 128(`HEAD^` 없음) = 빌드 진행(fail-open).

- **`[skip ci]` 를 배포 제어 수단으로 쓰지 않는다.** 이 프로젝트에서 아무 효과가 없다.
- **한 push 에 여러 커밋을 담을 때, 최종 HEAD 가 `docs/`·`*.md`·`scripts/` 만 바꾸는 커밋이면 안 된다.**
  Ignored Build Step 은 `HEAD^..HEAD`, 즉 **최종 커밋 하나만** 판정한다. 앞선 커밋의 code/data
  변경이 배포되지 않은 채 남는다. (실측 확인: 마지막이 docs-only 면 직전 `app/` 변경이 skip 된다.)
- 커밋은 로컬에서 다 만들고 **push는 한 번**만 한다 — 단 위 규칙을 함께 지킨다.
- **code와 data를 한 커밋에 섞지 않는다.**
- **이미 push한 커밋은 amend/rebase 하지 않는다.** 오류는 문서에서 정정한다.
- **`scripts/` 에 `.ts`/`.tsx`/`.js` 를 두지 않는다.** 현재 `scripts/` 는 `.py` 3개 + `.json` 1개라
  production build input 이 아님이 감사됐고(§13-2), 그 전제 위에서 배포 제외 대상이다.

**merge commit 은 안전하다.** `HEAD^` 는 첫 부모(main)이므로 feature 브랜치 변경이 diff 에 전부 들어와
빌드가 진행된다. 실측 확인.

---

# 1. 현재 Production 정본

| | |
|---|---|
| **repository HEAD** | `git rev-parse --short HEAD` 로 확인 (§ 상단 규약 참조) |
| **production revision** | `befe834` (`dpl_GvogSRHiaFRkM5QWRMMhwsfj26Pc`, READY) |
| **canonical data revision** | `dc22fe2` (2026-09-04, P19 recollection) |
| origin/main | repository HEAD 와 일치 |
| git status | untracked `tsconfig.tsbuildinfo` 만 |
| 정적 페이지 | 253 routes (HTML 252 + `sitemap.xml`) |
| sitemap | **241 URLs**, 생성 안 된 페이지 0 |
| 매장 총계 | **69,292건** |
| 데이터 파일 | JSON **239개** / district data file **220개** / region index 17 |
| **데이터 수집일** | **2026-09-04** (사용자 노출 **238 페이지**) |
| data checksum | **`59617a5e2965712e`** |
| 테스트 | **`PASS 264 / FAIL 0`, process exit code 0** |

**테스트 계측은 세 숫자를 분리해서 읽는다** (§0-4). 2026-09-04 실측:

| | |
|---|---|
| 실행된 assertion | **264** (`sys.setprofile` 로 `check()` 진입 계수) |
| summary 반영 | **264** |
| exit 판정 대상 | **264** |

세 숫자가 일치하고 요약 블록 이후 실행문은 0이다. 런타임 게이트가 이 일치를 강제한다
(불일치 시 `atexit` 에서 exit 1).

**data checksum 산출식** (문서에 없어 2026-09-04 에 특정함):

```
find data -type f | sort | xargs shasum -a 256 | shasum -a 256 | cut -c1-16
```

`test_collect.py` 의 `tree_sig()`(relpath+content 를 sha256 에 누적)로는 **재현되지 않는다.**
두 방식이 공존하므로 checksum 을 비교할 때 어느 쪽인지 먼저 확인한다.

**파일 해시** (2026-09-04 실측)

```
collect.py       cc944e916f8de7e1df6f6c0b501a5f48800dc46cafeb70a94557846d8650d066
integrity.py     1a850a28a5bc663044d571e816f81f01b0b915561fb169d650575be2dc5de4ae
test_collect.py  4a6bd538cbc2d2e6312f9f4448f5779355b8bd9332b1217525bfd37a64084294
data checksum    59617a5e2965712e   (P19 이전: c6e2934b7173b8b9)
```

`collect.py` / `integrity.py` 는 `40a4ee9` 이후 무변경이다. `test_collect.py` 는
P20-SAFETY-TEST-HARDENING(`befe834`)에서 바뀌었다 — 게이트 로직은 건드리지 않았다 (§13-1).


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
| P19 SAFETY FIX-1 | 빈 응답·오류 봉투 promotion 차단 | `8f2b6ee` |
| P19 계측 | 구군별 손실 원인 분해 (`district_stats`) | `b10ac51` |
| P19 급감 가드 | G 확장 — catastrophic-drop guard | `40a4ee9` |
| **P19 recollection** | **전국 재수집 + promotion 완료 (CLOSED)** | **`dc22fe2`** |

---

# 2. 커밋 (시간순 21건)

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
| 15 | `12bb09e` | 09-04 11:5x | 직전 정본 문서 마감. `[skip ci]` |
| 16 | `8f2b6ee` | 09-04 12:0x | **P19 SAFETY FIX-1.** `totalCount=0` 을 완결로 인정하지 않고, API 오류 봉투를 차단하고, `G.total_wipe` 로 전면 삭제를 막았다. 실증했던 전멸 경로를 닫는다. §10-1, §10-2 |
| 17 | `b10ac51` | 09-04 13:4x | 구군별 손실 원인 계측. `district_stats` 5칸을 stats 에 추가. 수집 결과·candidate serialization 변화 0 을 69,265건 실규모로 증명. §10-4 |
| 18 | `40a4ee9` | 09-04 16:xx | **catastrophic-drop guard.** G 를 실제 차단 게이트로 확장. N1/N2/R1/D1/D2/AGG. §10-5, §10-6 |
| 19 | `c845430` | 09-04 17:xx | 정본을 `40a4ee9` 기준으로 갱신. `[skip ci]` |
| 20 | `6432324` | 09-04 17:xx | SAFETY=GO / VALUE=GO / NECESSITY=MEDIUM 판정 기록. `[skip ci]` |
| 21 | **`dc22fe2`** | **09-04 18:13** | **P19 전국 재수집.** 912 calls / A~G PASS / promotion 성공. 69,265 → 69,292. data-only. §10-10 |

> 커밋 번호 15~18 은 `docs/` 또는 `scripts/` 만 건드렸다. 사이트 산출물(253 pages)은
> `9d79168` 이후 변하지 않았고 production `data/` 도 무변경이다.

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
- 저장된 매장(2026-09-04 기준 **69,292건**)은 **`SALS_STTS_CD == "01"` 필터 결과**다.
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

# 10. P19 SAFETY 워크스트림 — **판정 완료 (SAFETY GO / VALUE GO)**

> 이 절이 다음 세션의 출발점이다. **최종 판정과 다음 단계는 §10-9 에 있다.**
> 10-1 ~ 10-8 은 그 판정의 근거이며, 재측정은 필요 없다.

## 10-1. 최초 SAFETY 판정 = **STOP** (실증)

기존 게이트가 막지 못한 것을 격리 환경에서 **실제로 재현했다.**

API 가 형식상 정상인 빈 응답(`totalCount=0`)을 주면:

```
fetch_all  → "완결성 검증 통과: 0 == totalCount 0"   (예외 없음)
게이트 A~G → failures=0                              (빈 트리도 자기일관적)
promotion  → 실행됨. 매장 10건 → 0건
```

실 데이터라면 69,265 → 0 이고, **크래시가 아니라 exit 0 으로 끝나는 조용한 전멸**이다.
쿼터 초과 응답(`resultCode=22`)도 body 가 `items=[] / totalCount=0` 이라 같은 경로를 탔다.
당시 응답 header 는 **아예 검증하지 않았다.**

> 더 불편한 사실: 테스트 [4]가 이 동작을 `"totalCount=0은 완결로 인정"` 으로
> **단언하고 있었다.** 스위트는 PASS 120 / FAIL 0 이면서 전멸 경로를 보증했다.
> → 영구 규칙 §0-4 에 반영.

## 10-2. FIX-1 (`8f2b6ee`) — 무엇을 닫았나

3층 구조. 다만 **실측으로 확인한 각 층의 실제 기여도**는 다음과 같다.

| 층 | 내용 | 실제 기여 |
|---|---|---|
| 1 | API 오류 봉투 / `resultCode` 검증 | **주로 진단**. `OpenAPI_ServiceResponse` 와 top-level `cmmMsgHeader` 는 수정 전에도 `data["response"]` KeyError 로 이미 막혔다(사유가 "응답 파싱 실패" 였을 뿐). 새로 막은 것은 `response.header` 오류 코드 케이스 |
| 2 | `expected_total <= 0` fail closed | **실제 차단** |
| 3 | `G.total_wipe` | **실제 차단** |

`resultCode` 는 정수로 읽히고 0 이 아닐 때만 오류로 본다. 판정 불가한 문자열은
경고만 남기고 통과시킨다 — 근거 없이 조이면 이 API 가 header 를 다른 형태로
보낼 때 수집이 **100% 실패**한다. 이 판단은 §10-3 실측으로 옳았음이 확인됐다.

**남아 있던 구멍:** `G.total_wipe` 는 candidate 가 **정확히 0** 일 때만 발화한다.
candidate 1건 / 10건 / 100건 같은 자기일관적 near-total drop 은 그대로 통과했다.
→ **당시** P19 HARD BLOCK 유지 사유였다. 이 구멍은 `40a4ee9` 에서 닫혔다(§10-6).

## 10-3. SAFETY dry-run 2회 (promotion 불가 3중 차단)

**차단 방식** — 한 층이 뚫려도 나머지가 막는다.

```
Layer A  classify_and_save(complete=False)     promote_candidate 미도달
Layer B  data_dir = TEMP 사본                   repo data/ 가 인자에 없음
Layer C  스파이                                  promote_candidate 호출 시 SafetyIncident,
                                                repo 경로 rename/rmtree/remove 차단
```

실 fetch 전에 **스파이 자체를 fixture 로 검증**했다 (2회 모두 PASS 14 / FAIL 0).
과차단 여부까지 봤다 — TEMP 내부 mutation 은 정상 허용되어야 dry-run 이 성립한다.

**두 실행 결과가 완전히 동일했다.**

| | dry-run #1 | dry-run #2 |
|---|---|---|
| API calls | 912 | 912 |
| elapsed | 515.9s | 502.9s |
| raw totalCount | 91,120 | 91,120 |
| active | 72,480 | 72,480 |
| unmatched | 14 | 14 |
| dedupe input | 72,466 | 72,466 |
| duplicates removed | 3,132 | 3,132 |
| verified input | 69,334 | 69,334 |
| contradictions | 42 | 42 |
| final | 69,292 | 69,292 |
| candidate fingerprint | `ec0731218421da99` | `ec0731218421da99` |
| A–G | PASS | PASS |
| promote_candidate 호출 | **0** | **0** |
| repo 대상 rename/delete | **0 / 0** | **0 / 0** |
| production checksum | 무변경 | 무변경 |

production 69,265 → candidate 69,292 (**+27 / +0.04%**).
plan: 생성 0 / 변경 142 / 제거 1 / 유지 97. 제거 파일은 `gyeongnam/tongyeong.json` 하나.

### API header 정본 (2회 × 912페이지 = 1,824 관측)

```
top[response] response[body,header] header[resultCode,resultMsg]
resultCode='0'  resultMsg='정상'
```

**단일 지문. 다른 shape·code 0건. gateway 오류 봉투 0건.**

> **`resultCode` 는 `"00"` 이 아니라 `"0"` 이다.**
> FIX-1 이 성공 집합을 `{"00","0","0000"}` 로 넓게 잡고 정수 fallback 을 둔 덕에 통과했다.
> `"00만 성공"` 으로 하드코딩했다면 **1페이지에서 수집이 전부 실패했다.**
> 향후 조일 때도 관측된 `"0"` 을 넘어 좁히지 않는다.

### API 쿼터 (다음 세션이 꼭 알아야 할 것)

| | |
|---|---|
| 전국 1회 수집 | **912 calls** (91,120건 ÷ 페이지 100건) |
| 일일 한도 | **10,000** (2026-03 로그 `Total API calls so far: 905/10000`) |
| 2026-09-04 소모 | 1,824 (18.2%) — 쿼터 오류 0건, HTTP 503 재시도 1회씩 복구 |

**쿼터에 걸리면 그 실행의 수확은 0이다.** FIX-1 이 부분 수집을 남기지 않기 때문이다.
따라서 실제 P19 는 **하루 한 번, 쿼터가 넉넉할 때** 돌린다. 실패해도 같은 날 재시도하지 않는다.
응답에 잔여 쿼터 정보는 없다(header 는 `resultCode`/`resultMsg` 2개뿐).

## 10-4. 계측 (`b10ac51`) 과 229개 교차검증

`stats["district_stats"]` — 키 `"{region_slug}/{district_slug}"`, 값 5개 정수:
`classified_before_dedupe` / `duplicates_removed` / `after_dedupe` /
`contradictions_removed` / `final`. **매장 0건 구군 포함 229개 전부** 존재한다
(빠지면 전멸 구군이 집계에서 사라진다).

- 격리 수는 반드시 `stores = verified` **재할당 전**에 잰다. 뒤에서 재면 항상 0 으로 굳는다.
- `unmatched` 는 구군 귀속이 불가능하다(분류 실패로 `district_slug` 가 없다).
  억지로 배분하지 않고 전국 회계에만 둔다. 구군 사슬은 raw 가 아니라 **classified 에서 시작**한다.
- 수집 결과 변화 0 을 **실규모로 증명**했다: production 69,265건을 API item 으로 복원해
  계측 전(HEAD)과 계측 후에 넣었더니 candidate tree sha256 이 `804bc5b07794b0c9…` 로
  **완전히 동일**(238 파일, stats 정수 전부 동일, A~G note 목록 동일).

### 교차검증 결과 (dry-run #2)

| 검사 | 결과 |
|---|---|
| 구군 항등식 `classified = duplicates + after_dedupe` | 불일치 **0/229** |
| 구군 항등식 `after_dedupe = contradictions + final` | 불일치 **0/229** |
| 전국 합계 5종 vs `stats` | 72,466 / 3,132 / 69,334 / 42 / 69,292 **전부 일치** |
| raw 주소 **독립** 집계 vs `classified_before_dedupe` | **229/229 일치, 불일치 0** |
| 독립 집계 미귀속 잔차 | **14** = historical 11 + malformed 3 + merged unresolved 0 = `unmatched_total` |

독립 집계는 드라이버가 `normalize_region` / `extract_district` / `resolve_merged_sido` /
`resolve_legacy_district` 를 재사용해 `build_candidate` 분기 순서를 그대로 따른 것이다.
**진실로 간주하지 않고 대조 대상으로만 썼고, 전량 일치했으므로 원인 분해를 근거로 쓸 수 있다.**

## 10-5. 원인 분해 결과

229개 구군: **감소 38 / 증가 52 / 동일 139.**
감소 38개의 원인: **dedupe 주도 19 / contradiction 주도 10 / source·API 감소 후보 6 / 복합 3.**

> **해석 순서 주의.** production 은 2026-03 수집의 *최종* 산출물(그때의 dedupe·격리를 이미 거침)이고
> 오늘 raw 는 dedupe *이전* 값이다. 그래서 `raw - production` 을 "순수 source delta" 라고 부르지 않는다.
> 3월의 구군별 원장이 없으므로 이 값은 **상한 추정**이며, 음수로 나오면 실제 원천 감소는 그보다 크다.
> 표현은 **"source/API change candidate"** 또는 **"internal loss 로 설명되지 않는 변화"** 를 쓴다.

| district | production | raw | dedupe | contra | final | delta | 판정 |
|---|---|---|---|---|---|---|---|
| `jeonnam/gangjin` | 117 | 87 | 2 | 0 | 85 | -32 / -27.35% | source/API 감소 후보 |
| `busan/bsjunggu` | 356 | 304 | 14 | 0 | 290 | -66 / -18.54% | source/API 감소 후보 |
| `seoul/mapo` | 602 | 537 | 1 | 0 | 536 | -66 / -10.96% | source/API 감소 후보 (거의 순수) |
| `gyeonggi/hwaseong` | 1,738 | 1,657 | 26 | 1 | 1,630 | -108 / -6.21% | source 주도, 최대 절대 감소 |
| `gyeongnam/tongyeong` | 1 | **1** | 0 | **1** | **0** | -1 / -100% | **원천 소멸 아님** |

**통영이 설계를 바꿨다.** 원천에는 1건이 그대로 있는데(매장명 `도매유통`,
도로명 경상남도 / 지번 전라남도) 저장 직전 격리에 걸려 0 이 됐다.
즉 **"district 전멸이면 무조건 BLOCK"** 은 잘못된 설계다. 최소 규모 조건이 필요하다.

### 시도 단위 정상 변동 (2회 재현)

범위 **-2.05% ~ +1.52%**. 10% 이상 감소한 시도 **0개**.
Seoul 3,118→3,054 (-2.05%) / Gwangju 2,524→2,478 (-1.82%) / Busan 4,164→4,096 (-1.63%) /
Jeonnam 6,736→6,703 (-0.49%) / Incheon 1,145→1,143 (-0.17%) / Jeonbuk +1.52% / Gangwon +1.44%.

> 두 dry-run 은 **같은 날 같은 API 스냅샷**이다. 시계열로 과장하지 않는다.

### 전국 총계 게이트만으로는 불가능하다는 근거

| 사고 | 전국 영향 |
|---|---|
| 서울(3,118건) 전체 소실 | **-4.37%** |
| 제주 -90% | **-1.03%** |
| 세종(165건) 전멸 | **-0.20%** |
| 최대 구군 전주(1,880건) 전멸 | **-2.73%** |

## 10-6. 최종 catastrophic-drop guard (`40a4ee9`)

**A–G 구조 유지. 새 H 없음.** G 를 production↔candidate mutation/drop safety gate 로 확장.
코드 위치: `integrity.py` `check_drop_guard()`, 임계값은 파일 상단 상수 블록.
비교는 **production/candidate 키 합집합**으로 한다(교집합만 보면 사라진 시도·구군을 놓친다).

| 코드 | 조건 | 임계값 근거 (2026-09-04 실측) |
|---|---|---|
| `G.total_wipe` | prod > 0 AND cand == 0 | FIX-1 에서 유지 |
| `G.national_drop` | 전국 손실률 >= **25%** | 정상 +0.04%. **절대량 하한 없음** — §0-4-1 참조 |
| `G.region_drop` | 손실 >= **30건** AND >= **10%** | 정상 최악 서울 -2.05% / -64건 (2회). 비율은 5배. 절대 조건은 세종(165건) 소량 변동 제외용 |
| `G.district_drop` | (손실 >= **100건** AND >= **10%**) OR >= **500건** | 정상에서 손실>=100 인 최대 비율 = 화성 -6.21%. 비율>=10% 인 최대 절대 = -66건. 교차 조건이라 정상 표본 침범 0 |
| `G.district_extinction` | production >= **20건** 이 0 이 됨 | 정상 전멸은 통영 prod=1. prod<10 구군이 41개(합계 99건) |
| `G.mass_drop` | material(>=**20건** AND >=**5%**) 구군 >= **15개** OR 합계 >= **2,000건** | 정상 material 5개 / 합계 320건 |

**D1 이 왜 저 형태인가.** 초안은 `(>=50% AND >=150건) OR >=500건` 이었는데
`300 → 160 (-140 / -46.7%)` 같은 단일 구군 붕괴를 놓쳤다. 실측에 더 깔끔한 경계가 있었다:
손실>=100건 사례의 최대 비율이 -6.21%, 비율>=10% 사례의 최대 절대가 -66건이라
**(>=100건 AND >=10%)** 는 정상 candidate 를 하나도 막지 않으면서 그 빈 구간을 덮는다.

**N2 에 절대량 하한이 없는 이유.** §0-4-1 의 실패 사례 그대로다. `3 → 1` 은
다른 어떤 층에도 걸리지 않으므로 전국 비율 fail-safe 를 약화하면 안 된다.
테스트가 `3 → 1` 이 `G.national_drop` **단독**으로 BLOCK 됨을 고정한다.

### 원인 분해는 BLOCK 면제에 쓰지 않는다 (영구 결정)

`district_stats` 는 **진단 전용**이다. "dedupe 때문이므로 PASS", "contradiction 때문이므로 PASS"
같은 예외를 두지 않는다. **dedupe 나 `verify_store_location` 자체가 회귀한 사고를 놓치기 때문이다.**

> S12 로 증명: 감소분 100% 를 dedupe 로 귀속시킨 `district_stats` 를 넘겨도
> `G.national_drop` / `G.region_drop` / `G.district_drop` 이 그대로 발화한다.
> 반대로 구군 게이트를 source 성분 기준으로 만들었다면(안 B), raw 가 정상인
> dedupe 회귀 사고에서 **한 건도 발화하지 않는다**(오늘 데이터에서 raw >= prod×0.9 인 구군 225/229).

**WARN 등급은 만들지 않는다.** `IntegrityReport.ok` 는 `failures` 만 보고,
`classify_and_save` 는 `report.ok is False` 일 때만 `CollectionError` 를 던진다.
즉 `note` 로 두면 promotion 이 그대로 진행된다 — 로그만 남기는 경고는 안전장치가 아니다.

## 10-7. fixture matrix (전부 테스트로 고정, 당시 `PASS 226 / FAIL 0 / exit 0`)

> **[주의]** 이 절의 `PASS 226` 은 **P19 당시(2026-09-04) 값**이다. 현재 baseline 은
> **`PASS 264 / FAIL 0 / exit 0`** 이다 (§1, §13-1). 아래 §10 전체가 P19 시점 기록이며,
> 현재 상태를 읽으려면 §1 과 §12·§13 을 본다.

| | 시나리오 | 기대 | 발화 |
|---|---|---|---|
| S1 | **2026-09-04 실측 229개 구군 그대로** (69,265→69,292) | PASS | — |
| S2 | 전체 0 | BLOCK | 6개 전부 |
| S3 | 전체 1 | BLOCK | national/region/district (total_wipe 는 미발화) |
| S4 | 서울 전체 소실 | BLOCK | region_drop |
| S5 | 경기 -30% | BLOCK | region_drop |
| S6 | 최대 구군(전주) 전멸 | BLOCK | district_drop + extinction |
| S7/S13 | 통영 1→0 (contradiction) | **PASS** | — |
| S8 | 강진 117→85 | **PASS** | — |
| S9 | 마포 602→536 | **PASS** | — |
| S10 | 화성 1738→1630 | **PASS** | — |
| S11 | 상위 50개 각 -8% | BLOCK | **mass_drop 단독** |
| S12 | dedupe 회귀 90% 소실 (raw 정상) | BLOCK | national/region/district |
| S14 | 제주 -90% | BLOCK | region_drop |
| S15 | 300→160 (-140 / -46.7%) | BLOCK | district_drop |
| S16 | -500건 / 비율 <10% | BLOCK | district_drop |
| S17 | -99건 / 20% | PASS | — |
| S18 | -100건 / 9.99% | PASS | — |
| S19 | -100건 / 10.00% | BLOCK | district_drop |
| S20 | 시도 -29건 / 50% | PASS | — |
| S21 | 시도 -30건 / 10.00% | BLOCK | region_drop |
| S22 | material 14개 / 1,999건 | PASS | — |
| S23 | material 15개 / 1,950건 | BLOCK | mass_drop |
| S24 | material 14개 / 2,000건 | BLOCK | mass_drop |
| N2-A | production 3 → 1 (-66.67%) | BLOCK | **national_drop 단독** |
| N2-B | 4 → 3 (정확히 -25%) | BLOCK | national_drop |
| N2-C | 10,000 → 7,501 (-24.99%) | PASS(N2) | — |
| N2-D | 10,000 → 7,500 (-25.00%) | BLOCK | national_drop |
| N2-E | bootstrap 0 → 양수 | PASS | — |

경계 테스트: AGG 4.99% vs 5.00%, D2 prod=19 vs 20 도 고정. **임계값 이상이면 발화**로 확정.

> S1 이 가장 중요하다. 우리가 가진 **유일한 정상 표본**이므로 여기서 발화하면
> 정상 수집이 매번 막힌다. 여유는 R1 이 가장 빡빡해 7.95%p.

## 10-8. 남은 위험 (SAFETY 최종 판정에서 판단할 것)

1. **임계값의 근거가 사실상 한 점이다.** 2회 측정했지만 같은 날 같은 API 스냅샷이다.
   계절·주기 변동으로 시도 감소가 -10% 를 넘는 날이 있으면 오탐이 난다.
   다만 그 경우 promotion 이 막힐 뿐 데이터는 안전하고, 사람이 조정하면 된다.
2. **D1 의 사각지대.** 300건 구군이 160건이 되면 잡지만, 예컨대 1,000건이 910건이
   되는 경우(-90건 / -9%)는 통과한다. AGG 로 일부만 커버된다.
3. **AGG 의 사각지대.** 14개 구군이 각 100건씩 1,400건을 잃으면 통과한다.
4. **오류 시 `resultCode` 를 아직 모른다.** 2회 다 정상 응답만 받았다.
5. **인천 서해구·검단구가 원천에 0건이다.** 개편이 API 에 반영되는 시점과 그때의
   delta 크기를 모른다. 반영되면 게이트가 발화할 수 있고, 그건 정상 발화다.
6. **production 의 42건 위치 모순.** 재수집하면 격리되어 사라진다(설명 가능한 감소).

## 10-9. 최종 판정 (2026-09-04 확정)

| | |
|---|---|
| **P19 SAFETY** | **GO** |
| **P19 VALUE** | **GO** |
| **NECESSITY** | **MEDIUM** |
| **P19 PRODUCTION RECOLLECTION** | **COMPLETED** |
| **P19** | **CLOSED** |

실행일 **2026-09-04**, data commit **`dc22fe2260188ac268a25995db20f36bfe97e7fe`**.

> **다음 세션은 SAFETY 도 VALUE 도 다시 판정하지 않고, P19 recollection 을 다시 실행하지 않는다.**

### SAFETY = GO 근거 (요약)

- 최초 STOP 을 만든 `totalCount=0` silent wipe 경로 폐쇄 (§10-1, §10-2)
- near-total drop 도 `G.national_drop` 으로 폐쇄. 절대량 하한이 없어 `3 → 1` 도 막힌다
- 시도 / 구군 / 전멸 / 분산 손실 각각에 가드 존재 (§10-6)
- dedupe·contradiction 은 **면제 사유가 아니라 diagnostic only.** S12 로 고정
- S1–S24 + N2 경계 전부 PASS (`PASS 226 / FAIL 0 / exit 0`)
- §10-8 의 남은 threshold blind spot 은 **탐지 한계**이지 열린 silent catastrophic path 가 아니다

### VALUE = GO 근거

**`+27` 순증 자체는 이유가 아니다.** 실제 이동은 **759건 = production 의 약 1.10%** 다
(감소 38 districts / -366, 증가 52 districts / +393, 동일 139).

- **노후도**: 직전 수집일 `2026-03-27`, 판정일 기준 **161일**. 사용자에게 직접 노출됐다.
- **품질**: contradiction **42건** quarantine. 자동 주소 수정이 아니다.
- **신규 반영**: 증가 393건은 당시 사이트에 없던 매장이다 (Namyangju +95 / Jeonju +36 / Wonju +25 등)
- 실행 비용 낮음 (912 calls / 약 9분 / 쿼터 9.1%), 실패해도 production 보존
- **기다릴 구체적 이점이 없었다**

알고 있는 한계이며 **VALUE STOP 사유로 보지 않은 것**: 서울 sparsity 미해결
(Gangbuk / Songpa / Jungnang 은 source 자체가 0건 — **VALUE GO 의 근거로 서울 해결을 쓰지 않았다**),
일부 district 감소, Tongyeong 0건, 인천 source lag.
**SEO 는 판정 근거에서 제외했다. SEO effect = UNKNOWN.**

### Tongyeong 정책 결정 (선례)

`gyeongnam/tongyeong` — production 1 / raw 1 / dedupe 0 / **contradiction 1** / candidate 0.
매장명 `도매유통`. 도로명은 경상남도, 지번은 전라남도로 **지역 identity 를 검증할 수 없다.**
**source disappearance 가 아니라 quarantine 에 따른 의도된 품질 변화다.**

> **정책: 검증 불가능한 1건을 coverage 를 위해 유지하는 것보다 정직한 0건을 우선한다.**

단, **"모든 contradiction 은 항상 삭제가 정답"** 이라는 뜻이 아니다.
**독립 검증이 불가능할 때** 임의 rewrite/relocation 하지 않고 **quarantine** 한다는 뜻이다.

---

## 10-10. 실행 결과 (2026-09-04, `dc22fe2`)

**preflight**: HEAD/origin `6432324` 일치, 예상 외 working-tree 변경 0,
`PASS 226 / FAIL 0 / exit 0`, pre checksum `c6e2934b7173b8b9`, recovery state **A.normal**
(`.data-backup` / `.data-candidate` 둘 다 없음).

### API

| | |
|---|---|
| API calls | **912** |
| elapsed | **8분 58초** (18:04:12 → 18:13:10) |
| expected_total / fetched | **91,120 / 91,120** (완결성 검증 통과) |
| page size | 100 (실측) |
| retry | **0회** |

> header fingerprint 는 production collector 에 계측이 없어 별도 수집하지 않았다.
> 다만 `detect_api_error()` 가 912 페이지 전부에서 한 번도 발화하지 않았다 —
> gateway 오류 봉투 0건이고 오류 `resultCode` 도 관측되지 않았다는 뜻이다.

### pipeline

```
raw 91,120 → active 72,480 → unmatched 14 → dedupe input 72,466
  → duplicates removed 3,132 → verified input 69,334
  → contradictions 42 → final 69,292
```

unmatched 14 = malformed 3 + historical 11 (경상북도 군위군 1 / 충청남도 연기군 10).
**dry-run 2회와 여덟 개 수치가 전부 동일했다.**

### integrity — A~G 전부 PASS (`failures=0 notes=11`)

`G.total_wipe` / `G.national_drop` / `G.region_drop` / `G.district_drop` /
`G.district_extinction` / `G.mass_drop` — **failure count 전부 0**.
`G.mass_drop` 은 material-drop 5개 / 합계 320건으로 기준(15개 또는 2,000건) 미달 note.

### mutation plan

| | |
|---|---|
| store total | 69,265 → **69,292** (**+27 / +0.04%**) |
| 감소 | 38 districts / **-366** |
| 증가 | 52 districts / **+393** |
| 동일 | 139 districts |
| **gross movement** | **759건 (production 의 약 1.10%)** |
| plan | created 0 / modified 142 / removed 1 / kept 97 |
| removed | `gyeongnam/tongyeong.json` (production 1건) |

### promotion

성공. **rollback 0회.** `.data-backup` / `.data-candidate` 둘 다 없음.
checksum `c6e2934b7173b8b9` → **`59617a5e2965712e`**.
**"atomic swap" 이 아니라 rollback-safe multi-step promotion 이다.**

### postcheck (commit 전 전부 통과)

- 테스트 **`PASS 226 / FAIL 0` / process exit 0**
  — 별도 execution/structure 계측: PASS·FAIL 출력 라인 **244개**. 두 숫자를 혼동하지 않는다
- TypeScript errors 0 / `next build` success / **253 routes**
- duplicate title 0 / duplicate H1 0 / canonical 누락 0 / U+FFFD 0 / 예상 밖 noindex 0
- sitemap **241 URLs**, 생성 안 된 페이지 0
  (P19 이전 242 → 통영 data file 제거로 241. 구조 회귀 아님)
- 사용자 노출 수집일: 옛 날짜 `2026-03-27` 잔존 **0건**, `2026-09-04` **238 페이지**
  (이전 239 → 통영 data file 제거 영향으로 238)

### 0-store district 9개

부여 · 청양 · 당진 · 강원 고성 · **통영** · 강북 · 중랑 · 송파 · 울주.
전부 404 가 아니라 **0곳 안내 정적 페이지**로 정상 생성되며 대안 안내(편의점·마트·주민센터)를 갖췄다.
Tongyeong 은 §10-9 정책대로 contradiction quarantine 에 따른 의도된 1→0 변화다.

### deployment / smoke

data commit `dc22fe2`, `[skip ci]` 미사용, origin/main 일치, 최종 HEAD 가 data commit.
deployment triggered 및 live 반영 확인. **deployment ID / production revision 은 미확보**
— HTTP live smoke 로 확인했으므로 이를 실패로 쓰지 않는다.

smoke 9 URL 전부 **200**: `/` · `/seoul` · `/gyeongnam` · `/seoul/mapo` ·
`/gyeonggi/hwaseong` · `/busan/bsjunggu` · `/jeonnam/gangjin` ·
`/gyeongnam/tongyeong` · `/seoul/gangbuk`.
라이브 본문이 로컬 빌드와 일치했다 — Seoul 3,054 / Mapo 536 / Hwaseong 1,630 /
Busan Jung-gu 290 / Gangjin 85.

---

# 11. Deferred (이번에 구현·재판정하지 않는다)

| 항목 | 비고 |
|---|---|
| ~~GSC indexing diagnosis~~ | **2026-09-04 완료.** `GSC-DIAGNOSIS-20260904.md`. 색인 0 확정(90일 노출 0), Google 이 아는 URL 은 241개 중 6개뿐 |
| 0–9 store pages | 전국 33개 (서울 11개 포함) |
| server-rendered store coverage | 페이지당 초기 렌더 매장 수 제한 |
| template similarity | 페이지 간 본문 유사도 |
| search trim bug | P3 이월 |
| ~~42 road/lot contradictions~~ | **2026-09-04 P19 에서 42건 quarantine 완료** (`dc22fe2`). contradiction 정책 자체는 유지 — §10-9 |
| schema drift sensor | 게이트 D는 있으나 상시 센서는 없음. D 는 정상 경로에서 항상 empty 를 받는다(drift preflight 가 workspace write 이전에 먼저 막기 때문). 판정 로직이 살아 있음은 직접 주입 테스트로 증명돼 있다 |
| 감소율 threshold 정밀화 | D1 사각지대(1,000→910), AGG 사각지대(14개×100건). 관측이 쌓이면 재검토 |
| API 오류 시 `resultCode` 확정 | 정상값 `"0"` 만 관측. 오류 코드 미관측이라 header 검증을 더 조이지 못함 |
| `tsconfig.tsbuildinfo` | 빌드 산출물. 다음 코드 커밋 때 `.gitignore` 후보 |
| `lib/regions.ts` 고령군 중복 | 경상북도 고령군이 동일 내용으로 2회 정의. 현재 무해(값이 같아 dict 병합에서 흡수) |
| richer API fields | 미사용 필드 활용 |
| BreadcrumbList JSON-LD | **사이트 전체 미구현.** 현재 JSON-LD는 FAQPage뿐이다. |
| `/gwangju` ↔ `/jeonnam` cross-link | 같은 통합특별시인데 서로 링크가 없다 |
| 통합 안내문 | `/gwangju` `/jeonnam` 상단 한 줄 안내 |
| historical exception metadata | 연기군 / 군위군 |
| 홈 가격표 모순 | 20L 490원 vs FAQ 500~1,000원 |
| AdSense 문서/코드 모순 | P3 이월 |
| sitemap lastmod | P3 이월 |
| `docs/AUDIT-20260903.md` | P17.6 시점 감사 기록. **이미 stale 배너가 있고 이 문서를 정본으로 가리킨다.** 전면 갱신 불필요 — 역사 기록으로 보존 |
| `docs/SESSION_REPORT.md` | P18-A 시점 기록. **이미 stale 배너 있음.** 역사 기록으로 보존 |
| `docs/gpt/SESSION_REPORT.md` | 2026-04-26 시점. 2026-09-04 에 stale 배너 추가함 |
| **A 게이트 침묵 경로** | `expected_total is None` 이면 fail 도 note 도 없이 침묵한다 (`integrity.py:609`). 출하 경로(`main()`)는 항상 값을 넘기므로 현재 무해하나, `classify_and_save` 기본값이 `None` 이라 **새 호출자가 생기면 A 가 조용히 꺼진다.** 다음 collector 변경 때 기본값 제거를 검토한다. 이번에 semantics 를 바꾸지 않았다 |
| `audit_tree()` production 미호출 | 유일한 호출자가 `test_collect.py`. 죽은 코드인지 의도된 도구인지 문서에 없다 |
| sitemap `lastmod` | `app/sitemap.ts:8,17,28` 이 전부 `new Date()`. **아무 production build 나 241개 lastmod 를 동시에 갱신한다.** P20 관측 종료 후 최우선 후보 |
| `app/` 아래 `.md` 와 ignore 규칙 | `':!*.md'` 는 git pathspec 상 **모든 위치**의 `.md` 를 제외한다(`app/x/README.md` 포함). 현재 노출도 0(모든 `.md` 11개가 `docs/` 아래, MDX 참조 0)이나 나중에 MDX 도입 시 조용히 skip 된다 |

---

# 12. 현재 위치

| | |
|---|---|
| **P19** | **CLOSED** (§10-9, §10-10) |
| **P20 Phase 1** | **DEPLOYED / TECHNICAL PASS / OBSERVATION ACTIVE / FREEZE** |
| **P20-SAFETY-TEST-HARDENING** | **CLOSED** (§13-1) |
| **P20 build-trigger hardening** | **CLOSED** (§13-2) |

다음 세션이 하지 말아야 할 것:

- SAFETY 재판정 / VALUE 재판정 (2026-09-04 종료)
- **P19 recollection 재실행**
- threshold 재논쟁 — 새 실측이나 실제 사고 근거 없이는 하지 않는다
- **관측 종료 전 `app/` `components/` `lib/` `data/` `public/` 변경** (§13-5)

**지금 가장 중요한 것은 무언가를 더 고치는 것이 아니라 변수를 더 넣지 않는 것이다.**
+7일 관측 시점까지 문서 외에는 건드리지 않는다.

---

# 13. P20 — Google 색인 회복 (진행 중)

> 상세는 별도 문서에 있다. 여기서는 **상태와 금지사항만** 고정한다. 내용을 중복하지 않는다.
> - `docs/gpt/GSC-DIAGNOSIS-20260904.md` — 색인 진단 + 세션 감사 3건
> - `docs/gpt/P20-PHASE1-PRE-REPORT-20260904.md` — 설계 판단 (**바이트 예측은 반증됨**)
> - `docs/gpt/P20-PHASE1-COMPLETION-20260904.md` — 구현·배포 결과 + 예측 정정 (해당 항목 정본)

## 13-1. P20-SAFETY-TEST-HARDENING (`befe834`) — CLOSED

**게이트 정책 변경 0.** 테스트가 각 규칙의 발화를 실제로 증명하도록만 바꿨다.

- **C positive wiring** — `C.location_mismatch`(store 주소만 변경, 건수 불변) / `C.no_names`
- **`A.api_completeness`** — `expected_total` 주입 + negative 대조군
- **`E.count_vs_records`** — `contradiction_records` 만 늘린다. 선언값을 바꾸면 `B.stage3`·`B.closure` 가 함께 터져 E 를 가린다
- **F 13개 코드** — 합성 트리를 `check_tree_counts` 에 직접 넣어 exact-set 단언. 이전에는 접두사 검사 하나뿐이라 `F.missing_file` 이 죽고 `F.index_selfsum` 만 살아 있어도 통과했다
- **masking fixture 2건** — `[P3-13] 1`(`G.national_drop` 이 대신 막음) / `[P3-13] 3`(`G.total_wipe` 가 대신 막음). 둘 다 **변이 제거 시 promotion 까지 감**을 실제로 확인
- **항진명제 제거** — `issubclass(CollectionError, Exception)` 은 클래스 정의만으로 항상 참이었다
- **runtime structural self-test** — 리터럴 `check(` 스캔은 `chk = check` / `check (` / `globals()["check"]` 로 우회되고 요약 앞 `sys.exit(0)` 을 못 잡았다. 실행 횟수를 요약 시점과 `atexit` 시점에 비교하는 게이트로 교체. 격리 트리 실측: 우회 3형태 전부 exit 1, 대조군 exit 0
- **fixture 정합성** — 테스트 10 주석의 `5 -> 1 = -80%` → 실제값 `3 -> 1 = -66.7%` 로 정정하고 시도·구군 층 침묵 사유(R1·D1·D2·AGG 임계값 미달) 명시. S22/S24 의 pad 중복 append 제거(판정 불변)

## 13-2. Vercel build-trigger hardening — CLOSED

**문제.** `scripts/` 파일 하나만 바꿔도 production 이 재배포되고, `app/sitemap.ts` 의 `new Date()` 때문에 241개 lastmod 가 전부 새로 찍혔다.

**감사 — `scripts/` 는 production build input 이 아니다.** `package.json` 에 prebuild/postbuild 없음, `next.config.ts` 빈 설정, `app`/`components`/`lib` 에서 참조 0건, `scripts/legacy_districts.json` 을 TS 가 읽지 않음, tsconfig include 는 `**/*.ts|tsx` 인데 `scripts/` 는 `.py`+`.json` 뿐, 빌드의 파일 접근 지점은 `lib/data.ts` → `data/` 하나뿐.

**변경.** Ignored Build Step: `':!*.md' ':!docs/'` → **`':!*.md' ':!docs/' ':!scripts/'`**

**truth table 13/13 실측 일치.** scripts-only → skip / docs-only → skip / docs+scripts → skip / `app`·`components`·`lib`·`data`·`public`·`package.json` → build / **app+scripts 혼합 → build**. merge commit → build(안전, 첫 부모가 main). 최초 커밋(`HEAD^` 없음) → exit 128 → build(fail-open).

**설정 저장 자체는 배포를 만들지 않는다.** 저장(12:19:26Z) 후 새 deployment 0, production revision `befe834` 유지, sitemap lastmod 재갱신 0 — 전부 실측 확인.

**롤백 명령:** `git diff --quiet HEAD^ HEAD -- ':!*.md' ':!docs/'`

## 13-3. accidental deployment 기록 (`befe834`)

scripts-only 커밋에 `[skip ci]` 를 붙였으나 **production 배포가 발생했다** (`dpl_GvogSRHiaFRkM5QWRMMhwsfj26Pc`, READY).

**원인.** 이 프로젝트에서 `[skip ci]` 는 배포 제어 수단이 아니다. Ignored Build Step 의 exit code 가 실제 결정자다 (§0-8).

**영향.** application content 는 의미상 동일 — `/gyeonggi` **2,691자** / `/busan` **995자** / sitemap **241 URLs** 전부 유지. **바뀐 것은 241개 lastmod 가 같은 날 안에서 한 번 재갱신된 것뿐**(빌드 11:47:48Z → lastmod 11:47:59Z).

**revert 하지 않은 이유.** revert 자체가 또 build 를 일으켜 lastmod 를 다시 흔든다. 현 상태 유지가 최선이다.

## 13-4. P20 Phase 1 관측 상태

| 역할 | URL | 2026-09-04 baseline |
|---|---|---|
| **treatment** | `/gyeonggi` | Crawled - currently not indexed / lastCrawl `2026-04-30T10:55:04Z` |
| **comparison** | `/busan` | Crawled - currently not indexed / lastCrawl `2026-04-26T10:30:52Z` |
| **comparison** | `/seoul` | Crawled - currently not indexed / lastCrawl `2026-04-30T10:55:04Z` |
| — | `/gyeonggi/suwon` `/gyeonggi/anyang` `/busan/haeundae` 등 district 표본 | **URL is unknown to Google** |

Search Analytics 90일: **clicks 0 / impressions 0.**

> `/busan` 을 **control 이라고 쓰지 않는다.** 무작위 배정이 아니고 Google 크롤 스케줄링은 비결정적이다. **comparison URL** 로 표기한다.

**관측 일정** — **+7일(2026-09-11)** `/gyeonggi` `/busan` `/seoul` — **+21일(9/25)** 위 3개 + district 표본 — **+45일(10/19)** 위 + Search Analytics.

> **+7일 대상은 3 URL 이 정본이다.** `P20-PHASE1-PRE-REPORT-20260904.md` §I-2 와
> `P20-PHASE1-COMPLETION-20260904.md` §M 에는 2 URL(`/gyeonggi` `/busan`)로 적혀 있으나
> **superseded historical plan** 이다. `/seoul` 을 넣는 근거는 COMPLETION §CC-5 다 —
> `/gyeonggi` 와 `/seoul` 은 lastCrawl 이 **초 단위까지 동일**(같은 크롤 배치)이라
> `/busan`(04-26)보다 가까운 비교군이고, 셋 다 변하면 "사이트 전체 재평가" 해석이 가능해진다.
> 추가 비용은 1 URL 이고 6 URL 상한 안이다.

## 13-4-1. 관측 재현 코드 (READ-ONLY)

> **이 코드블록이 정본이다.** 이전 판은 `<scratchpad>/gsc_diag.py` 를 가리켰으나
> 스크래치패드는 세션 스코프라 새 세션에서 사라진다. 저장소에 실행 파일로 추가하지 않는다 —
> `scripts/` 에 `.py` 를 넣으면 P17.9 entrypoint 재등장 방지 가드에 걸린다.
> **필요할 때 이 블록을 세션 스크래치패드에 복사해 쓰고 저장소에 커밋하지 않는다.**

**실행 전 preflight (API 호출 0):** `git rev-parse --short HEAD` 와 `git status --porcelain` 으로
P20 배포(`befe834`) 이후 production build 가 0건인지 먼저 확인한다. build 가 있었다면
241개 lastmod 가 갱신됐다는 뜻이고 관측 해석이 달라진다.

```python
#!/usr/bin/env python3
"""P20 관측 — GSC READ-ONLY. 의존성 0 (openssl + 표준 라이브러리).

사용: python3 observe.py <service-account-key.json>
     또는  GSC_KEY=<경로> python3 observe.py

이 스크립트는 URL Inspection(index:inspect) 조회만 한다.
색인 요청 / 유효성 검사 / sitemap 재제출 / Indexing API 는 참조조차 하지 않는다.
서비스 계정 키는 저장소 밖에 두고 절대 git add 하지 않는다.
"""
import base64, json, os, subprocess, sys, tempfile, time
import urllib.error, urllib.parse, urllib.request

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
TOKEN_URI = "https://oauth2.googleapis.com/token"
INSPECT = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
SITE = "https://bag.fazr.co.kr/"
TARGETS = ["/gyeonggi", "/busan", "/seoul"]          # +7일 정본 3개
BASELINE = {                                          # 2026-09-04 고정값
    "/gyeonggi": ("Crawled - currently not indexed", "2026-04-30T10:55:04Z"),
    "/busan":    ("Crawled - currently not indexed", "2026-04-26T10:30:52Z"),
    "/seoul":    ("Crawled - currently not indexed", "2026-04-30T10:55:04Z"),
}

def b64u(raw): return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

def get_token(key):
    now = int(time.time())
    head = b64u(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = b64u(json.dumps({"iss": key["client_email"], "scope": SCOPE,
                             "aud": TOKEN_URI, "iat": now, "exp": now + 3600}).encode())
    signing_input = f"{head}.{claim}".encode()
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as f:
        f.write(key["private_key"]); pem = f.name
    os.chmod(pem, 0o600)
    try:
        p = subprocess.run(["openssl", "dgst", "-sha256", "-sign", pem, "-binary"],
                           input=signing_input, capture_output=True)
        if p.returncode != 0:
            raise SystemExit(f"openssl 서명 실패: {p.stderr.decode()[:300]}")
        jwt = signing_input.decode() + "." + b64u(p.stdout)
    finally:
        os.unlink(pem)
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(TOKEN_URI, data=body)) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        raise SystemExit(f"토큰 교환 실패 {e.code}: {e.read().decode()[:400]}")

def inspect(token, path):
    req = urllib.request.Request(
        INSPECT,
        data=json.dumps({"inspectionUrl": SITE.rstrip("/") + path, "siteUrl": SITE}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)["inspectionResult"]["indexStatusResult"]
    except urllib.error.HTTPError as e:
        return {"_error": f"{e.code} {e.read().decode()[:200]}"}

def main():
    kp = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GSC_KEY")
    if not kp:
        raise SystemExit(__doc__)
    token = get_token(json.load(open(kp)))
    print(f"{'URL':<12}{'coverageState':<36}{'lastCrawlTime':<24}변화")
    print("-" * 88)
    for path in TARGETS:
        r = inspect(token, path)
        if "_error" in r:
            print(f"{path:<12}ERROR {r['_error']}"); continue
        cov, last = r.get("coverageState"), r.get("lastCrawlTime")
        b_cov, b_last = BASELINE[path]
        d = []
        if cov != b_cov: d.append(f"coverage {b_cov!r} → {cov!r}")
        if last != b_last: d.append(f"lastCrawl {b_last} → {last}")
        print(f"{path:<12}{str(cov):<36}{str(last):<24}{' / '.join(d) if d else '변화 없음'}")

if __name__ == "__main__":
    main()
```

**서비스 계정 키는 저장소 밖**(`~/Downloads/claude-seo-*.json`)에 두고 **절대 `git add` 하지 않는다.**
`python3 observe.py <key.json>` 또는 `GSC_KEY=<경로> python3 observe.py`.
의존성 0 — `openssl` 로 RS256 서명하고 표준 라이브러리로 호출한다.

**검증 상태 (2026-09-04):** 구문 OK · 금지 엔드포인트 참조 0(`indexing.googleapis` / `urlNotifications` /
`sitemaps` / `searchAnalytics` / PUT / DELETE) · scope `webmasters.readonly` 고정 ·
키 하드코딩 없음 · **openssl 서명 경로 실증**(exit 0, 서명 256 bytes, JWT 3세그먼트, claim.scope 확인).
네트워크 구간(토큰 교환·Inspection)은 FREEZE 중이라 실행하지 않았다 — 그 부분은
2026-09-04 에 실제로 동작한 `gsc_diag.py` 와 동일한 코드다.

**GSC 규칙:** READ-ONLY only. URL Inspection 1회 **최대 6 URL**. 색인 요청 / 유효성 검사 / sitemap 재제출 / Indexing API / 대량 Inspection **전부 금지**. scope `webmasters.readonly` 유지. 서비스 계정 JSON `git add` 금지.

## 13-5. FREEZE 규칙

관측 종료 전까지 `app/` `components/` `lib/` `data/` `public/` 를 바꾸지 않는다.
특히 region · district · sitemap · metadata · `INITIAL_COUNT` · `adjacentDistricts` · schema/FAQ 를 열지 않는다.

**디렉터리 목록만 보고 판단하지 않는다. 루트 레벨 tracked 파일도 전부 금지다.**
`.gitignore` · `package.json` · `next.config.ts` · `tsconfig.json` · `postcss.config.mjs` 등은
Ignored Build Step 의 세 pathspec(`':!*.md'` `':!docs/'` `':!scripts/'`) 어디에도 걸리지 않아
**변경 시 production build 를 일으킨다.**

실측 확인: 과거 `.gitignore` 만 바꾼 커밋 `f9672fa` 에 현재 ignore 명령을 대입하면
`exit 1 (BUILD)` 이다. 특히 `.gitignore` 에 `tsconfig.tsbuildinfo` 를 추가하는 것은
빌드 산출물 위생 작업이라 가장 무해해 보이지만 **관측을 통째로 오염시킨다.**
(`tsconfig.tsbuildinfo` 는 애초에 git 에 추적되지 않으므로 실익도 0이다.)

**이유:** production build 가 한 번이라도 발생하면 `app/sitemap.ts` 의 `new Date()` 때문에 241개 lastmod 가 다시 갱신된다. `lib/regions.ts` 고령군 중복 정의처럼 사소해 보이는 수정도 포함이다.

## 13-6. 관측 종료 후 후보 (우선순위는 관측 결과로 재판정)

1. **sitemap `lastmod`** 를 실제 변경 시각 기반으로 수정
2. **`INITIAL_COUNT`** — **PRE-REPORT §L-1 의 바이트 계산은 폐기하고 참고하지 않는다.** RSC payload 증가를 누락해 과소평가다. 실측 재계산이 선행 조건
3. `adjacentDistricts` — 내부 링크 수가 이 사이트에서 예측력이 없다는 반증이 있어 우선순위 낮음
4. schema / FAQ 정리
5. 외부 backlink 신호 검토 — 전 표본에서 referring 이 내부 URL 하나뿐이었다

---

*이 문서는 repository HEAD 기준 정본이다. P19 완료(2026-09-04), P20 Phase 1 배포·관측 개시, 테스트 하드닝, 배포 트리거 하드닝을 반영해 갱신됐다.*
