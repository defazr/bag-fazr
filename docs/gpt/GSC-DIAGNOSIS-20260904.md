# GSC 색인 진단 + 세션 감사 보고서 — 2026-09-04

> 대상: GPT 검증
> 저장소 HEAD: `a05ebc5` / origin/main 일치 / working tree 변경 없음(`?? tsconfig.tsbuildinfo`만)
> 정본 핸드오프: `docs/gpt/GPT-HANDOFF-20260903.md` (이 문서는 그것을 대체하지 않고 **보완**한다)
> 이 문서에 쓴 수치는 전부 이번 세션에서 **실행해서 얻은 값**이다. 추정치는 명시적으로 HYPOTHESIS 로 표시했다.

---

# 0. 이 문서가 답하는 것

1. 핸드오프 `GPT-HANDOFF-20260903.md` 의 주장이 실제 저장소와 일치하는가 → **§1**
2. 문서가 주장하는 안전장치가 코드에 실제로 있는가 → **§2**
3. 그 안전장치를 지키는 테스트가 실제로 그것을 단언하는가 → **§3**
4. Google 색인 0 의 원인은 무엇인가 → **§4(로컬)** + **§5(GSC 실측, 신규)**
5. 무엇을 해야 하는가 / GPT 판단이 필요한 지점 → **§6, §7**

§5 는 이번에 처음 얻은 데이터다. 이전 세션은 GSC 접근이 없어 §11 Deferred 로 남겨뒀다.

---

# 1. 핸드오프 정본 검증 — 전 항목 재현 성공

`GPT-HANDOFF-20260903.md` §1 의 주장을 전부 실측 대조했다.

| 항목 | 문서 | 실측 | |
|---|---|---|---|
| HEAD / origin/main | 일치 | `a05ebc5` 양쪽 동일 | OK |
| recovery state | A.normal | `.data-backup`/`.data-candidate` 부재 | OK |
| 매장 총계 | 69,292 | 69,292 (`regions.json` totalCount == district 파일 합계) | OK |
| 데이터 수집일 | 2026-09-04 | `updatedAt: 2026-09-04` | OK |
| JSON 파일 | 239 / district 220 / index 17 | 동일 | OK |
| data checksum | `59617a5e2965712e` | 동일 | OK |
| script 3종 SHA256 | 문서 기재값 | 3개 전부 일치 | OK |
| 테스트 | PASS 226 / FAIL 0 / exit 0 | 동일 | OK |
| TypeScript | errors 0 | `tsc --noEmit` exit 0 | OK |
| 빌드 | 253 routes | 253/253 (HTML 252 + sitemap) | OK |
| sitemap | 241 URLs, 미생성 0 | 241 / 미생성 0 | OK |
| 수집일 노출 | 238 페이지 | 238 | OK |
| duplicate title / H1 | 0 / 0 | 0 / 0 | OK |
| U+FFFD | 0 | 0 | OK |
| `gyeongnam/tongyeong.json` | 제거됨 | 부재 | OK |

**checksum 산출식** (문서에 없어 이번에 특정함 — 다음 세션은 이 명령을 쓴다):

```
find data -type f | sort | xargs shasum -a 256 | shasum -a 256 | cut -c1-16
```

`test_collect.py` 의 `tree_sig()`(relpath+content 를 sha256 에 누적) 로는 재현되지 않는다. 두 방식이 공존하므로 **문서에 산출식을 함께 적어야 한다.**

## 1-1. 확인 과정에서 걸렸다가 해소된 것

| 관측 | 판정 |
|---|---|
| HTML 6개에 옛 날짜 `2026-03-27` 잔존 | **회귀 아님.** 전부 매장의 `licenseDate`(인허가일자) 값. `데이터 수집일` 라벨은 6개 모두 `2026-09-04` |
| canonical 누락 2건 | **회귀 아님.** `_not-found.html` / `_global-error.html` 뿐. 콘텐츠 페이지 기준 0 |

## 1-2. 문서 표기 오류 2건 (내용 아님)

1. **1행 제목이 `HEAD 40a4ee9 기준`인데 §1 과 마지막 줄은 `dc22fe2` 기준.** §1·footer 갱신 시 제목만 남았다.
2. **§0-2 의 "S-prefixed structural audit" 서술이 실제와 다르다.** → §2-6

---

# 2. 감사 A — 안전장치 문서주장 ↔ 코드실제

방법: `integrity.py` / `collect.py` 를 읽고, **합성 입력으로 게이트를 직접 호출해 경계를 실측**했다. 대조 대상 파일 해시가 문서 §1 기재값과 일치하므로 문서가 서술하는 그 코드가 맞다.

## 2-1. A~G 게이트 7개 — 전부 존재 · 무조건 호출 · fail 로 승격

| 게이트 | 정의 | 호출 | 실패 코드 |
|---|---|---|---|
| A | `integrity.py:608-616` | `:611` | `A.api_completeness` |
| B | `integrity.py:284` | `:619` | `B.stage1/stage2/stage3/closure/unmatched_reasons` |
| C | `integrity.py:253` | `:620` | `C.no_names`, `C.location_mismatch` |
| D | `integrity.py:332` | `:621` | `D.unknown_province`, `D.unknown_district` |
| E | `integrity.py:347` | `:622` | `E.count_vs_records` |
| F | `integrity.py:166` | `:623`, `:625-629` | `F.*` 9종 + `F.tree_vs_stats` |
| G | `integrity.py:408`, `:458` | `:631`, `:632` | `G.*` 6종 |

`IntegrityReport.ok` 는 `not self.failures` (`integrity.py:87-88`) — `notes` 는 판정에 영향이 없다. **실패를 note 로 강등하는 경로 0건.**

## 2-2. G 하위 6코드 — 임계값 런타임 실측

상수 `integrity.py:38-65`. 실측값 `0.25 / 0.10·30 / 100·0.10·500 / 20 / 20·0.05·15·2000` — 문서 §0-2 표와 전부 일치.

**§0-4-1 이 기록한 "절대량 하한 1,000건 제거" — 코드에서 확인.** 모듈 전체에 `NATIONAL_*` 상수는 `NATIONAL_DROP_RATIO` 하나뿐이고 `:483` 조건에 `n_loss` 항이 없다.

경계 실측 (전부 문서 §10-7 fixture 와 일치):

```
3 → 1 (-66.67%)         BLOCK G.national_drop 단독   ← 하한 제거 증명
4 → 3 (정확히 -25%)      BLOCK
10000 → 7501 (24.99%)   PASS      10000 → 7500 (25.00%)  BLOCK
구군 -99/20%   PASS     -100/9.98% PASS   -100/10.00% BLOCK
구군 -499/8.3% PASS     -500/8.3%  BLOCK
시도 -29/50%   PASS     -30/10.00% BLOCK
전멸 prod=19   PASS     prod=20    BLOCK
AGG 14개/1988  PASS     15개/1950  BLOCK   14개/2002 BLOCK
material 비율  4.99% 제외 / 5.00% 포함
bootstrap 0 → 500       PASS (`_loss` 가 prod<=0 제외, `:403`)
```

시도·구군 순회는 문서대로 **합집합**이다: `set(pr)|set(cr)` (`:494`), `set(pd)|set(cd)` (`:508`).

## 2-3. 게이트 실패 시 promotion 0건 — 실제 파이프라인 실행으로 확인

```
prod 1000 → cand 1000   PROMOTED      production 1000 → 1000
prod 1000 → cand 60     BLOCKED(3건)  production 1000 유지, backup 없음, candidate 정리
prod 1000 → cand 1      BLOCKED(3건)  production 1000 유지, backup 없음, candidate 정리
```

첫 줄이 승격되므로 "항상 실패하는 게이트"가 아니라 실제 차단이다.

우회 경로 없음: `collect.py:1108-1112` 가 `promote_candidate()` 호출부(`:1125`)보다 먼저 raise 한다. `classify_and_save` 의 유일한 호출자는 `main()`(`:1175`), `argparse` 는 `--key` 하나뿐(`:1135`), `--force`/환경변수/resume 없음, `.github/workflows` 자체가 없음. `finally`(`:1128-1130`)는 workspace 만 정리하고 `data_dir`·backup 은 건드리지 않는다.

## 2-4. Collector fail-closed — 4개 주장 전부 확인

| 문서 주장 | 코드 |
|---|---|
| 부분 수집에서 `break` 대신 `CollectionError` | `:245` `:254` `:268` `:300` `:314` `:321` `:324` |
| 종료 조건 `len(all_items) >= expected_total` | `:309` |
| page size = 첫 응답 실측값 | `:290` → `:291` |
| `totalCount=0` 을 완결로 인정 안 함 | `:280-285` |

`fetch_all` 내 `break` 는 2개뿐이고 둘 다 부분 수집을 반환할 수 없다 — `:310` 은 완결 조건, `:304` 는 루프 종료 후 `:323` 의 건수 검사에 걸린다. `:290` 의 `else NUM_OF_ROWS` fallback 도 도달 즉시 `:297-303` 에서 raise 된다.

## 2-5. Rollback-safe promotion + crash recovery — 실행으로 확인

`promote_candidate()` (`collect.py:1032-1073`): `rename(data→backup)`(`:1061`) → `rename(workspace→data)`(`:1064`) → 성공 시에만 `rmtree(backup)`(`:1073`). `except BaseException`(`:1065-1070`)이 롤백 후 re-raise.

**`.data-backup` 무조건 삭제 경로 없음.** 삭제 지점 2곳 모두 조건부다 — `:1012`(recovery C 에서 구조감사 PASS 일 때만), `:1073`(두 번째 rename 성공 후). 추가로 `:1053-1057` 이 backup 선존재 시 promotion 자체를 거부한다.

`recover_promotion_state()` 7개 조합 실행:

```
data O  backup X  cand X   → A.normal
data O  backup X  cand O   → E.candidate_cleaned   (backup 무접촉)
data X  backup O  cand any → CollectionError (B)   backup→data 복구 후 중단
data O  backup O  감사 PASS → C.backup_cleaned
data O  backup O  감사 FAIL → CollectionError      backup 보존 확인
data X  backup X           → CollectionError (D)   아무것도 건드리지 않음
```

## 2-6. MISMATCH 1건 (표기, 안전 영향 없음)

문서 §0-2 는 "별도 **S-prefixed** structural audit"이라 쓰지만, `audit_tree_structure()`(`integrity.py:569-583`)가 내는 `S.` 접두 코드는 **`S.empty` 하나뿐**(`:580`)이고 나머지 구조 실패는 `check_tree_counts()`(`:582`)에 위임되어 **`F.` 접두**로 나온다. 실측:

```
빈 디렉터리       → ['S.empty']
count 불일치 트리 → ['F.file_selfcount','F.index_vs_file','F.index_vs_files',
                     'F.regions_vs_index','F.regions_total']
```

`recover_promotion_state()` 는 접두사가 아니라 `report.ok` 만 보므로(`collect.py:1007`) **차단 동작에는 영향이 없다.** 문서 표기만 정정하면 된다.

## 2-7. 사실 기록 (MISMATCH 아님)

1. **게이트 A 는 조건부 평가.** `integrity.py:609` 가 `raw`/`expected_total` 이 모두 non-None 일 때만 동작하고, `expected_total is None` 이면 fail 도 note 도 없이 침묵한다. 다만 `main()` 은 `fetch_all` 반환값을 항상 넘기므로(`collect.py:1176`) 출하 경로에서는 항상 활성. **`None` 기본값(`:1081`)은 침묵 경로를 남겨두는 설계다.**
2. **게이트 D 의 입력은 파이프라인에서 상수 `{}`.** `build_candidate` 가 하드코딩 빈 dict 를 반환한다(`collect.py:935-936`). 실제 차단은 preflight — `:667`(미등록 시도), `:735`(미등록 구군)에서 workspace write 이전에 raise. 문서 §11 의 "D 는 정상 경로에서 항상 empty 를 받는다"와 정합.
3. **`audit_tree()`(`integrity.py:586`)는 프로덕션 코드에서 미호출.** 유일한 호출자는 `test_collect.py:818`.

---

# 3. 감사 B — 테스트 정직성

> 배경: 이 저장소는 **"테스트가 있다는 사실이 안전의 증거가 아니었다"** 를 두 번 겪었다(§4 의 summary 위치 사고, §10-1 의 `totalCount=0` 정상 단언). 따라서 `PASS 226` 은 그 자체로 아무것도 증명하지 않는다.

## 3-1. 숫자 3종 — 문서 주장 그대로

| 구분 | 값 | 근거 |
|---|---|---|
| 실행 assertion | **226** | `sys.setprofile` 로 `check()` 진입 계수. static call site 181개 중 179개 실행 + 루프 11개 지점 |
| summary 반영 | **226** | `PASS/FAIL` 은 34행 1회 초기화, 38행 무조건 append, 다른 append/재초기화 0 |
| exit code 반영 | **226** | summary 블록 1695–1701행 = 파일 총 1701행의 맨 끝. 뒤에 실행문 0개 |

`assert` 문 0개, `except: pass` 형태 삼킴 0개. **§4 의 사고(50 vs 72)는 닫혔다.**

## 3-2. structural self-test — 부분 CONFIRMED

작동 확인: marker 런타임 조립(1679행)이 자기 오탐을 막고(파일 내 literal 출현 1곳), marker 소실 시 fail-closed, 파일 끝에 `check(...)` 추가 시 FAIL.

**우회 불가능하지는 않다.** 리터럴 `check(` 부분문자열 스캔이라 다음 3형태는 요약 블록 뒤에 놓여도 통과한다(전부 유효한 Python, 재현 확인):

```python
chk = check ; chk("x", True)
check ("x", True)
globals()["check"]("x", True)
```

또한 **위치만 강제하고 도달 가능성은 보지 않는다.** 요약 블록 *앞*에 `sys.exit(0)` 이 삽입되면 이후 assertion 과 self-test 가 실행되지 않고 exit 0 으로 끝나는데, 이를 잡는 검사가 없다.

**부수 사실: exit code 를 소비하는 자동 게이트가 없다.** `.github/` 없음, 활성 git hook 없음, `npm test` 없음. 커밋 게이트는 사람 또는 에이전트의 수동 실행뿐이다.

## 3-3. 게이트별 positive 테스트 커버리지

| 게이트 | positive | 판정 |
|---|---|---|
| **G** 6코드 | positive·negative 양방향 전부 (경계 대조군 포함) | 충실 |
| **D** | 직접 주입 positive 2 + negative 1 (`:1145-1158`) | 충실 |
| **B** | `"B." in raised` 구분 (`:747`) | 있음 |
| **A** `api_completeness` | **0개** (코드명 출현 0회) | 구멍 |
| **C** `location_mismatch`/`no_names` | **0개** (코드명 출현 0회) | 구멍 |
| **E** `count_vs_records` | **0개** (fixture 가 두 값을 0으로 맞춰 미발화) | 구멍 |
| **F** 12코드 | 접두사 `"F." in` 1건뿐, 개별 코드명 고정 0 | 구멍 |

**A·C·E 와 F 대부분이 죽어도 스위트는 초록색이다.** D 는 같은 상황(정상 경로에서 항상 empty)인데도 직접 주입 테스트를 갖고 있다. **C 에 동등물이 없는 것이 대비로 드러난다.**

`[6~8]`, `H~J`(188–451행)는 `verify_store_location` **함수**만 시험하고, `check_store_locations` 가 report 에 실패를 싣는 **배선**은 시험하지 않는다.

## 3-4. 통과하지만 엉뚱한 이유로 통과하는 테스트 2건

주입/변이를 제거하고 실행해서 확인했다.

**`test_collect.py:643-645`** — `make_prod(n=3)` + `GOOD`(1건). 주입한 `TEST.injected` 없이도:
```
raised: G.national_drop: 전국 prod=3 cand=1 loss=2 (66.67%) >= 25%
promote called: False
```
세 단언이 주입 기여 없이 전부 성립. → *임의의 미지 실패 코드가 promotion 을 차단한다* 는 보증되지 않는다.

**`test_collect.py:692`** "candidate 파일 누락 → FAIL" — 변이 미적용 시에도 `G.national_drop` 단독으로 raise. → **`F.missing_file` 계열 탐지가 통째로 죽어도 PASS.** 바로 옆 670행은 `"F." in raised`, 747행은 `"B." in`으로 구분하는데 692행만 구분자가 없다.

## 3-5. 항진명제 1건

`test_collect.py:826`:
```python
check("9) 게이트 실패는 CollectionError로만 표현된다 (silent pass 없음)",
      issubclass(collect.CollectionError, Exception))
```
`CollectionError(RuntimeError)` (`collect.py:135`) 이므로 클래스 정의만으로 항상 참. 모든 게이트가 조용히 통과하도록 바뀌어도 PASS. (실제 exit-code 전파 보증은 `:1160-1216` 자식 프로세스 3시나리오가 별도로 한다. 보증 자체는 있고 826행만 무의미하다.)

## 3-6. fixture 2건

**`:806-816` 테스트 10** — production `busan`(3건) → candidate `seoul`(GOOD3 3건). 전국 0% 이지만 **부산 시도가 통째로 소멸하는 것을 "promotion 성공"으로 단언**한다. 게이트 침묵 이유는 R1(`>=30건`)·D2(`>=20건`) 미달. §0-4-1 이 요구하는 "왜 safety gate 대상이 아닌지" 주석은 **전국 층만** 설명하고 시도·구군 층 침묵은 설명하지 않는다.
같은 주석의 `"GOOD(1건)이면 5 → 1 = -80%"` 도 fixture 와 불일치 — `n=3` 이므로 실제로는 3 → 1 = -66.7%.

**`:1599-1604` S22/S24** — `mass()`(`:1593-1598`)가 이미 붙인 `("pad/d", 400000, 400000)` 을 한 번 더 append 한다. dict comprehension 인 `prod_districts`/`cand_districts` 는 400,000 으로 합쳐지고 루프 누적인 `prod_regions`/`cand_regions` 는 800,000 이 된다. **판정 영향 없음**(prod·cand 동시 2배라 감소 0). 다만 정합한 트리를 나타내지 않는다.

## 3-7. CONFIRMED

- §0-4 "summary 블록 파일 맨 끝, 이후 assertion 0개" — 사실
- §10-1 사고 폐쇄 — 사실. `:137-150` 이 이제 `raised is not None` + `data/` 무변경을 단언
- §0-4-1 GOOD3 fixture 정정 — 사실(`:611-621`). 단 GOOD3 는 게이트가 **테스트를 막던** 곳에만 적용됐고, 게이트가 **테스트를 가려주던** 곳(§3-4)에는 적용되지 않았다
- exit code 전파 — `:1160-1216` 자식 프로세스 3시나리오에서 `rc != 0` + production 무변경 단언
- G 6코드 양방향 커버리지 — S1 은 2026-09-04 실측 229개 구군 전체를 오탐 0으로 고정하는 negative 대조군, S12 는 손실 원인이 100% dedupe 여도 면제되지 않음을 단언(면제 로직 회귀 방지)

---

# 4. 감사 C — 로컬 색인 저해 요인

대상: `.next/server/app` 의 252개 HTML + `sitemap.xml.body` + `prerender-manifest.json`, 소스 `app/` `lib/` `components/`.

## 4-1. 기술적 차단 없음 (CONFIRMED CLEAN)

| 항목 | 측정 |
|---|---|
| `public/robots.txt` | `User-agent: * / Allow: /` + sitemap 선언. 차단 0 |
| noindex | 252개 중 `_not-found` **1개뿐** |
| X-Robots-Tag | `vercel.json` **파일 없음**. `next.config.ts` 는 빈 설정 4줄. middleware 없음. `headers()`/`redirects()` 0건 |
| canonical | 콘텐츠 250개 전부 존재, **자기URL 불일치 0 · 충돌 0 · 전부 https · trailing slash 0** |
| title / description | 중복 **0** / 중복 **0** |
| H1 | 252개 전부 정확히 1개 |
| 고아 페이지 | **0개**, 홈 기준 최대 깊이 **2** |

## 4-2. H1 — 얇음 + 준중복

6-word shingle 로 90% 이상 페이지 공통 텍스트(=템플릿)를 제외한 결과:

- 전체 가시 텍스트 중앙값 2,059자 → **템플릿 제외 중앙값 615자** (본문의 **약 70%가 보일러플레이트**)
- 고유 텍스트 500자 미만 **34개 / 229 (15%)**, 300자 미만 12개
- 최하위 6개 **101~103자**: `/chungnam/buyeo` `/chungnam/cheongyang` `/chungnam/dangjin` `/seoul/gangbuk` `/seoul/jungnang` `/seoul/songpa`

difflib SequenceMatcher 문자 단위 유사도:

- **0곳 페이지 9개**: 36쌍 전부 ≥0.875, 중앙값 0.892, 최대 **0.981**
- **1~9곳 페이지 26개**: 325쌍 중 **305쌍(94%) ≥0.85**, 임계 0.90 에서 26개 전부가 **단일 군집**
- 최고: `/gyeonggi/icheon`↔`/gyeonggi/siheung` **0.9701**, `/gyeongnam/hapcheon`↔`/gyeongnam/miryang` **0.9695**
- **대조군: 매장 많은 상위 60개도 쌍별 중앙값 0.739 / p90 0.796**

근거 파일: `app/[region]/[district]/page.tsx:121-214`(0곳 분기, 지역명만 치환), `:398-419`(전 페이지 공통 3문단), `:216-221` + `lib/seo.ts:58-92`(FAQ)

0~9곳 페이지 = **41개**(0곳 9 + 1~9곳 32), 서울 14개. 문서 §11 의 "전국 33개(서울 11개)"는 1~9곳만 센 P19 이전 값이고, 통영 1→0 으로 현재 32개. **서울 11개는 완전 일치.**

## 4-3. H2 — 초기 HTML 매장 노출률 4.17% (H1 의 기계적 원인)

`components/store/StoreList.tsx:7` — `const INITIAL_COUNT = 15;`

- 69,292곳 중 **초기 HTML 렌더 = 2,889개 (4.17%)**
- 15곳 초과 페이지 179개: 69,088곳 중 렌더 2,685곳(**3.9%**)
- 최악: `/jeonbuk/jeonju` **1,916곳 중 15곳(0.8%)**, `/gyeonggi/goyang` 1,806 중 15, `/gyeonggi/yongin` 1,680 중 15

**그런데 데이터는 전량 전송된다.** `StoreList` 가 `"use client"` 이고 `stores` 배열 전체를 prop 으로 받으므로 RSC flight payload 에 전 매장이 직렬화된다:

| 페이지 | HTML | flight payload | payload 내 매장 객체 | 렌더 카드 |
|---|---|---|---|---|
| `/jeonbuk/jeonju` | 351 KB | **332 KB** | 1,916 | 15 |
| `/seoul/mapo` | 126 KB | 107 KB | 536 | 15 |

252개 HTML 합계 24.7 MB, 평균 100 KB. **바이트의 94% 가 렌더되지 않는 JSON 이고, 사이트 유일의 차별화 자산은 텍스트로 96% 안 보인다.** Googlebot 이 JS 를 실행해도 "더 보기"를 클릭하지 않으므로 15개가 상한이다.

## 4-4. H3 — sitemap lastmod 전 URL 동일

`app/sitemap.ts:8,17,28` 세 곳 모두 `lastModified: new Date()`.
`sitemap.xml.body`: `<loc>` 241 / `<lastmod>` 241, **값 전부 `2026-09-04T10:03:31.524Z` 동일**.
`prerender-manifest.json` 의 `/sitemap.xml` → `initialRevalidateSeconds: false` (완전 정적) = **빌드 시각 고정, 배포마다 241개 통째 갱신**.

## 4-5. H4 — sitemap 미포함 11개의 정체

| 분류 | 항목 |
|---|---|
| 라우트 아님 (2) | `_global-error`, `_not-found` |
| 홈 (1) | sitemap 에 `https://bag.fazr.co.kr` 로 존재. 표기 차이, 누락 아님 |
| **0곳 district (9)** | `chungnam/buyeo` `chungnam/cheongyang` `chungnam/dangjin` `gangwon/gwgoseong` `gyeongnam/tongyeong` `seoul/gangbuk` `seoul/jungnang` `seoul/songpa` `ulsan/ulju` |

원인: `app/sitemap.ts:25` `if (d.count > 0)`.
**모순**: `components/region/DistrictGrid.tsx:16-24` 는 count 무관하게 전부 링크한다(`:37` 에서 표시만 다름). 9개 전부 inbound=1, depth=2. **sitemap 에서만 뺐지 크롤 경로는 열려 있다.**

## 4-6. H5 — district 54% 가 inbound 링크 1개

- 고아 0, 최대 깊이 2 (구조 자체는 건강)
- 그러나 **229개 중 124개(54%)가 inbound 정확히 1개** = 자기 region 페이지에서만
- 원인: `app/[region]/[district]/page.tsx:116-118` — `adjacentDistricts` 가 `count > 0` 필터 후 **정렬 기준 없이 `.slice(0, 6)`**. 각 region 앞 6개만 모든 형제에서 반복 링크
- 분포 극단: inbound 1개(124 페이지) ↔ 31개(6 페이지)
- 기사도 편중: `/article/where-to-buy` 21 vs `/article/why-no-bags` 2, `/article/shortage-2026` 2

## 4-7. H6 — JSON-LD FAQPage 단독 + 44% 축자 중복

- 250개 콘텐츠 페이지의 JSON-LD 타입 = **`FAQPage` 하나뿐**. `BreadcrumbList`/`LocalBusiness`/`ItemList`/`Organization`/`WebSite` **0건**
- `components/seo/Breadcrumb.tsx` 는 시각적 breadcrumb 만 렌더, 스키마 미출력
- FAQ 답변 슬롯 1,121개 중 **497개(44%) 가 다른 페이지와 축자 동일**. 2개 질문은 **220개 페이지에서 질문·답변 완전 동일** (`lib/seo.ts:83-90`)
- `lib/seo.ts:77` 이 `displayName` 이 아닌 `districtName` 을 써서 **"중구" 5개 페이지에 같은 가격 답변** 출력
- FAQ 리치결과는 2023-08 부터 정부·보건 외 미표시 → **SERP 이득 0**

## 4-8. 부수 관측 (색인 영향 낮음)

- ISR: 247개 라우트 `revalidate 86400` / `expire 31536000`. 정상
- title 251개 중 **49개가 35자 초과** (최장 39자) — CTR 문제이지 색인 문제 아님
- description 250개 중 **246개가 70자 미만** (중앙값 64자) — Google 자체 스니펫 대체 가능
- `app/layout.tsx:27-31` 에 `naver-site-verification` 은 있으나 **google-site-verification meta 없음** (DNS/기타 방식일 수 있음 → §5 에서 소유권 확인됨)

---

# 5. GSC 실측 — **이번 세션 신규**

방법: 서비스 계정 `claude-seo@<project>.iam.gserviceaccount.com` (서치콘솔 `bag.fazr.co.kr` **siteOwner**).
scope 는 **`webmasters.readonly` 고정**. Indexing API 미참조. URL Inspection 은 `index:inspect`(상태 조회)만 사용. **색인 요청·유효성 검사 재실행 0건.**
키 파일은 저장소 밖에 있고 커밋되지 않는다.

## 5-1. 속성 상태 — 정상

```
sc-domain:fazr.co.kr        siteOwner
https://fazr.co.kr/         siteOwner
https://bag.fazr.co.kr/     siteOwner      ← 대상
https://howcheck.com/       siteFullUser
```

**소유권 확인 문제 없음.** URL 접두어 속성이며 형식도 `https://bag.fazr.co.kr/` 로 정확하다. (§4-8 의 google-site-verification meta 부재는 다른 방식으로 확인됐다는 뜻이다.)

## 5-2. Search Analytics — 진짜 0

기간 2026-06-06 ~ 2026-09-04 (90일):

```
dimension=date   rows=15,  전 행 clicks=0 impressions=0
dimension=page   rows=0
dimension=query  rows=0
```

**`site:` 연산자 오독이 아니다. 90일간 노출 0 · 클릭 0 이 API 로 확정됐다.**

## 5-3. Sitemap — 제출·다운로드 정상, 오류 0

```
https://bag.fazr.co.kr/sitemap.xml
  lastSubmitted  2026-04-28T11:02:03Z
  lastDownloaded 2026-08-24T02:22:17Z
  isPending False   errors 0   warnings 0
  type=web  submitted=242  indexed=0
```

**두 가지 주의:**

1. `submitted=242` 는 **P19 이전 값**이다(현재 sitemap 은 241). `lastDownloaded` 가 2026-08-24 로 **P19 배포(09-04) 이전**이므로 Google 은 아직 새 sitemap 을 받지 않았다.
2. **`indexed=0` 을 근거로 쓰면 안 된다.** 이 필드는 형제 sitemap 전부(fuel 1607, fazr 688, dust 226, support 110 …)에서 0 으로 나오는데, 그중 `fuel.fazr.co.kr` 는 실제로 90일 6클릭·34노출을 받고 있다. **즉 `indexed` 는 이 API 에서 신뢰할 수 없는 값이다.** (§5-5 참조)

## 5-4. URL Inspection — 13개 표본, 상태 조회 전용

| URL | coverageState | lastCrawl |
|---|---|---|
| `/` | **Crawled - currently not indexed** | 2026-08-30 |
| `/busan` | **Crawled - currently not indexed** | 2026-04-26 |
| `/gyeonggi` | **Crawled - currently not indexed** | 2026-04-30 |
| `/article/shortage-2026` | **Crawled - currently not indexed** | 2026-04-27 |
| `/article/why-no-bags` | **Crawled - currently not indexed** | 2026-04-29 |
| `/jeonnam` | **URL is unknown to Google** | — |
| `/gyeonggi/suwon` | **URL is unknown to Google** | — |
| `/seoul/seocho` | **URL is unknown to Google** | — |
| `/busan/haeundae` | **URL is unknown to Google** | — |
| `/jeonnam/gangjin` | **URL is unknown to Google** | — |
| `/seoul/gangbuk` | **URL is unknown to Google** | — |
| `/gyeongnam/tongyeong` | **URL is unknown to Google** | — |
| `/sitemap.xml` | URL is unknown to Google | — (sitemap 은 페이지로 색인되지 않음, 정상) |

집계: **Crawled-not-indexed 5 / unknown 8**

크롤된 5개는 전부 `robots=ALLOWED`, `indexing=INDEXING_ALLOWED`, `pageFetch=SUCCESSFUL`, `crawledAs=MOBILE`, **canonical(google) == canonical(user)**.

**결정적 관측 3가지:**

1. **크롤 시각이 2026-04-26 ~ 04-30 에 몰려 있다.** 그 이후는 홈 1회(08-30)뿐. **4개월간 사실상 크롤이 멈췄다.**
2. **표본의 모든 district 페이지가 "URL is unknown to Google"** 이다. `/gyeonggi/suwon`(P18-A 로 강화한 1순위 페이지), `/seoul/seocho`, `/busan/haeundae` 포함. sitemap 이 2026-08-24 에 오류 0 으로 다운로드됐는데도 **Google 이 이 URL 들을 큐에 넣지 않았다.**
3. 전 표본에서 `sitemap=None` — GSC 가 이 URL 들의 발견 경로를 sitemap 으로 귀속하지 않는다. 홈의 유일한 referring 은 `https://bag.fazr.co.kr/busan` 로 **내부 링크뿐이고, 외부 백링크가 하나도 관측되지 않는다.**

## 5-5. 형제 서브도메인 비교 — 도메인 전체 문제가 아니다

`sc-domain:fazr.co.kr` 90일 상위 행:

```
fuel.fazr.co.kr/chungnam-cheonan-premium-gasoline-price   clicks=6  impressions=34
sangsangpay.fazr.co.kr/                                    clicks=2  impressions=28
fazr.co.kr/ios-app-deals/google-docs-842842640/            clicks=1  impressions=14
headlines.fazr.co.kr/news/mexico-trump-assess-2            clicks=1  impressions=7
fazr.co.kr/                                                clicks=0  impressions=26
```

**형제 서브도메인들은 색인되어 트래픽을 받고 있다. `bag.fazr.co.kr` 만 0 이다.**

→ **도메인 단위 페널티나 DNS·호스팅 문제가 아니다.** 이 사이트 고유의 문제다.

---

# 6. 종합 판정

## 6-1. 확정된 것 (CONFIRMED)

1. **색인 0 은 사실이다.** 90일 노출 0, 클릭 0. `site:` 오독 아님.
2. **기술적 차단이 원인이 아니다.** robots 허용, noindex 없음, canonical 정상·충돌 0, pageFetch SUCCESSFUL, 소유권 확인됨, sitemap 오류 0.
3. **도메인 문제가 아니다.** 형제 서브도메인은 정상 색인·트래픽 수신 중.
4. **크롤은 됐고, 색인이 거부됐다.** 크롤된 5개 전부 `Crawled - currently not indexed`.
5. **district 229개는 크롤조차 되지 않았다.** 표본 전부 `unknown to Google`. sitemap 은 정상 다운로드됨.
6. **외부 백링크 0 관측.** 홈의 referring 이 내부 URL 하나뿐.

## 6-2. 가장 정합한 설명 (HYPOTHESIS — GPT 검증 요청 지점)

> Google 은 2026-04-26~30 에 홈·region·기사 소수를 크롤한 뒤 **초기 품질 평가에서 색인 가치 없음으로 판정**했고, 그 결과 sitemap 의 나머지 242 URL 에 크롤 예산을 배정하지 않았다. 4개월간 재크롤이 사실상 멈춘 것이 그 결과다.

이 가설이 §4 의 로컬 측정과 맞물리는 지점:

- Google 이 실제로 본 것은 **홈 + region + 기사**뿐이다. 이 중 region 페이지는 **매장 목록을 전혀 담지 않는다** — `StoreList` 컴포넌트는 `app/[region]/[district]/page.tsx` 에만 있고 `app/[region]/page.tsx` 에는 없다. 실측:

  | 페이지 | HTML 내 `roadAddress` 출현 | 가시 텍스트 |
  |---|---|---|
  | `/seoul` | **0** | 1,094자 |
  | `/gyeonggi` | **0** | 1,151자 |
  | `/seoul/gangnam` | 30 | 2,092자 |

  즉 **사이트의 유일한 차별화 자산(매장 69,292곳)이 Google 이 크롤한 페이지들에는 단 한 건도 들어 있지 않다.**
- district 페이지는 자산이 있지만 §4-3 대로 **초기 HTML 에 4.17% 만 렌더**되고, 애초에 크롤되지도 않았다.
- 즉 **Google 은 이 사이트에서 가치 있는 부분을 한 번도 본 적이 없다.**
- 신규 서브도메인 + 외부 링크 0 + 242 URL + 얇은 초기 표본 → 최소 크롤 예산 배정은 통상적 양상이다.

**반증 가능성:** §4 의 얇음·중복은 "저조한 색인"을 잘 설명하지만 "정확히 0"을 단독으로 설명하지는 못한다. 아래 §7-1 을 사람이 확인하기 전까지 이 가설은 확정이 아니다.

## 6-3. 게이트·데이터 파이프라인 판정

**P19 및 안전장치는 건전하다.** §2 의 실행 검증 결과 실질 MISMATCH 0건.
다만 §3 의 테스트 커버리지 구멍(A·C·E·F)과 마스킹된 테스트 2건은 **"현재 뚫린 구멍"이 아니라 "게이트가 망가져도 못 잡는 회귀 위험"** 이다. 이 구분을 흐리지 말 것.

---

# 7. 다음 행동 — 무엇을 하고 무엇을 하지 않는가

## 7-1. 사람이 GSC UI 에서 확인할 것 (API 로 불가)

Search Console API 는 아래를 노출하지 않는다. **코드를 고치기 전에 반드시 확인한다.**

1. **수동 조치(Manual Actions)** — `보안 및 수동 조치 > 수동 조치`. 여기에 항목이 있으면 §6-2 가설은 폐기되고 대응이 완전히 달라진다.
2. **보안 문제** — 같은 메뉴.
3. **페이지 색인 생성 리포트 전체 분포** — `색인 생성됨` 총계와 `색인이 생성되지 않음` 사유별 카운트. §5-4 는 13개 표본일 뿐이다.
4. **Vercel 도메인 설정** — apex/www, HTTP→HTTPS 리다이렉트. 저장소에 `vercel.json` 이 없어 전적으로 대시보드 설정이다.

## 7-2. 하지 않을 것 (영구 룰 준수)

- **유효성 검사 재실행 금지** / **대량 색인 요청 금지** — 이번 진단에서 0건 수행했고 계속 지킨다.
- **사이트 구조 흔들기 금지** / **모든 지역 일괄 수정 금지**
- **P19 SAFETY·VALUE 재판정 금지 / recollection 재실행 금지 / threshold 재논쟁 금지** (핸드오프 §12)

## 7-3. 원인 확정 전에는 코드를 고치지 않는다

§4-3(`INITIAL_COUNT = 15`)과 §4-6(`slice(0, 6)`)은 한 줄 수정처럼 보이지만, **§7-1 이 끝나기 전에 손대면 253페이지를 전부 흔들고 효과는 미지수다.** 특히 수동 조치가 걸려 있다면 어떤 콘텐츠 수정도 무의미하다.

## 7-4. GPT 판단을 요청하는 3가지

1. **§6-2 가설이 §5 데이터로 지지되는가.** 특히 "sitemap 정상 다운로드 + 오류 0 + 그러나 URL unknown" 조합을 크롤 예산 미배정 외에 달리 설명할 수 있는가.
2. **§7-1 확인 후 순서.** 수동 조치가 없다는 전제에서, `INITIAL_COUNT` 상향(H2)과 `adjacentDistricts` 정렬·확대(H5) 중 무엇을 먼저 해야 하는가. 둘 다 "일괄 수정 금지" 룰과 충돌 가능성이 있으므로 룰 해석도 함께 판단 요청.
3. **§3 의 테스트 구멍(A·C·E·F positive 0개, 마스킹 2건, 항진명제 1건)을 지금 닫을 것인가, 색인 문제 뒤로 미룰 것인가.** 현재 게이트는 §2 대로 작동하므로 긴급도는 낮다고 보나, 판단을 요청한다.

---

# 8. 재현 방법

```bash
# 핸드오프 정본 검증
git rev-parse HEAD origin/main
python3 scripts/test_collect.py ; echo $?          # PASS 226 / FAIL 0 / exit 0
find data -type f | sort | xargs shasum -a 256 | shasum -a 256 | cut -c1-16   # 59617a5e2965712e
npx tsc --noEmit ; npx next build                  # errors 0 / 253 routes
grep -o '<loc>' .next/server/app/sitemap.xml.body | wc -l                     # 241

# GSC 읽기 전용 진단 (scope: webmasters.readonly, 색인 요청 없음)
# [정정 2026-09-04] 아래 두 경로는 세션 스코프 스크래치패드라 새 세션에서 사라진다.
# +7일 관측용 READ-ONLY 재현 코드는 GPT-HANDOFF-20260903.md §13-4-1 코드블록이 정본이다.
python3 <scratchpad>/gsc_diag.py <service-account-key.json>
python3 <scratchpad>/gsc_deep.py <service-account-key.json>
```

키 파일은 저장소 밖에 두고 절대 커밋하지 않는다.

---

*이 문서는 `docs/gpt/GPT-HANDOFF-20260903.md` 를 대체하지 않는다. 정본은 여전히 그 문서이고, 이 문서는 §11 Deferred 의 "GSC indexing diagnosis" 항목에 대한 실측 보고와 세션 감사 결과다.*
