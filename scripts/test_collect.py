"""collect.py 안전장치 회귀 테스트 (P17.7).

목적: "수집이 완결됐다는 사실을 증명하지 못하면 기존 데이터에 쓰기·삭제를
한 건도 하지 않는다"는 불변식을 고정한다.

실행:
  python3 scripts/test_collect.py

네트워크를 쓰지 않는다. fetch_page를 가짜 응답으로 대체하고, 파일 조작은
임시 디렉터리에서만 수행한다. data/ 를 건드리는 테스트는 실행 전후
체크섬을 비교해 무변경을 증명한다.
"""

import hashlib
import importlib.util
import json
import os
import re
import atexit
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

spec = importlib.util.spec_from_file_location(
    "collect", os.path.join(ROOT, "scripts", "collect.py")
)
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)
collect.load_district_slugs()
collect.load_legacy_districts()

PASS, FAIL = [], []

# ── 요약/exit 게이트 무력화 방지 (런타임 계측)
#
# 파일 하단의 리터럴 "check(" 스캔만으로는 부족하다. 실측으로 확인된 우회 3형태
#   chk = check ; chk(...)      /  check (...)      /  globals()["check"](...)
# 는 전부 통과하고, 요약 블록 '앞'에 sys.exit(0) 이 들어가면 요약도 스캔도 아예
# 실행되지 않아 exit 0 으로 끝난다.
#
# 실행된 check() 횟수를 요약 시점과 프로세스 종료 시점에 비교하면 호출 형태와
# 무관하게 잡힌다. 문자열이 아니라 실제 실행을 세기 때문이다.
_gate = {"summary_count": None}


def _gate_verdict(executed, summary_count):
    """None 이면 정상. 문자열이면 게이트 무력화 사유."""
    if summary_count is None:
        return f"요약 블록이 실행되지 않았다 (검사 {executed}건이 exit 판정에 미반영)"
    if executed != summary_count:
        return f"요약 이후에 검사 {executed - summary_count}건이 실행됐다"
    return None


def _final_gate():
    verdict = _gate_verdict(len(PASS) + len(FAIL), _gate["summary_count"])
    if verdict:
        sys.stdout.write("\n" + "=" * 60 + f"\nGATE FAIL: {verdict}.\n"
                         "        새 검사는 요약 블록 '앞'에 넣어라.\n")
        sys.stdout.flush()
        os._exit(1)


atexit.register(_final_gate)

if os.environ.get("TEST_COLLECT_SELFTEST") == "early_exit":
    # 게이트 자체의 종단 검증용. 요약 블록 앞에서 성공 코드로 빠져나가는 상황을
    # 실제로 재현한다. atexit 게이트가 이것을 exit 1 로 뒤집어야 한다.
    sys.exit(0)


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"\n        {detail}" if detail else ""))


def data_fingerprint(root):
    """data/ 전체의 (경로, 크기, 내용해시) 지문."""
    h = hashlib.sha256()
    files = []
    for dirpath, _, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not fn.endswith(".json"):
                continue
            p = os.path.join(dirpath, fn)
            files.append(os.path.relpath(p, root))
            with open(p, "rb") as f:
                h.update(os.path.relpath(p, root).encode())
                h.update(f.read())
    return len(files), h.hexdigest()


def make_page(items, total_count):
    return {"response": {"body": {"items": items, "totalCount": total_count}}}


def item(name, road, lot=""):
    return {
        "BPLC_NM": name,
        "ROAD_NM_ADDR": road,
        "LOTNO_ADDR": lot,
        "SALS_STTS_CD": "01",
        "SALS_STTS_NM": "영업/정상",
        "APLY_YMD": "2020-01-01",
    }


SEOUL_GANGNAM = item("테스트마트", "서울특별시 강남구 테헤란로 1")


# ---------------------------------------------------------------- 1
print("\n[1] 정상 전체 응답 → 기존과 동일하게 완결 처리")
pages = {1: make_page([SEOUL_GANGNAM] * 1000, 1500), 2: make_page([SEOUL_GANGNAM] * 500, 1500)}
collect.fetch_page = lambda k, n: pages.get(n)
try:
    items, calls, total = collect.fetch_all("KEY")
    check("정상 응답 완결 반환", len(items) == 1500 and total == 1500, f"items={len(items)} total={total}")
except Exception as e:
    check("정상 응답 완결 반환", False, f"예외 발생: {e}")


# --------------------------------------------------------------- 1b
print("\n[1b] API가 numOfRows를 무시하고 100건씩만 반환 → 전량 수집해야 함")
# 실측: 이 API는 numOfRows=1000을 요청해도 100건만 반환한다.
# 요청값으로 페이지 수를 계산하면 10분의 1에서 조기 종료된다.
TOTAL, SIZE = 2350, 100
collect.fetch_page = lambda k, n: make_page(
    [SEOUL_GANGNAM] * min(SIZE, max(0, TOTAL - (n - 1) * SIZE)), TOTAL
)
try:
    items, calls, total = collect.fetch_all("KEY")
    check(
        "요청값이 아닌 실제 페이지 크기로 전량 수집",
        len(items) == TOTAL and calls == 24,
        f"items={len(items)} (기대 {TOTAL}), calls={calls} (기대 24)",
    )
except Exception as e:
    check("요청값이 아닌 실제 페이지 크기로 전량 수집", False, f"예외 발생: {e}")


# ---------------------------------------------------------------- 2
print("\n[2] 91페이지 중 5페이지에서 3회 실패 → 프로세스 실패 + data/ 무변경")
before = data_fingerprint(os.path.join(ROOT, "data"))
collect.fetch_page = lambda k, n: make_page([SEOUL_GANGNAM] * 1000, 91000) if n < 5 else None
raised = None
try:
    collect.fetch_all("KEY")
except collect.CollectionError as e:
    raised = str(e)
after = data_fingerprint(os.path.join(ROOT, "data"))
check("재시도 소진 시 CollectionError", raised is not None, raised or "예외가 발생하지 않음")
check("data/ 파일 수 무변경", before[0] == after[0], f"{before[0]} -> {after[0]}")
check("data/ 내용 무변경", before[1] == after[1])


# ---------------------------------------------------------------- 3
print("\n[3] 중간 페이지 빈 응답 → 실패 + 기존 데이터 보존")
before = data_fingerprint(os.path.join(ROOT, "data"))
collect.fetch_page = lambda k, n: (
    make_page([SEOUL_GANGNAM] * 1000, 91000) if n < 5 else make_page([], 91000)
)
raised = None
try:
    collect.fetch_all("KEY")
except collect.CollectionError as e:
    raised = str(e)
after = data_fingerprint(os.path.join(ROOT, "data"))
check("빈 응답을 정상 종료로 취급하지 않음", raised is not None, raised or "예외가 발생하지 않음")
check("data/ 무변경", before == after)


# ---------------------------------------------------------------- 4
print("\n[4] API totalCount=0 → 완결로 인정하지 않는다 (fail closed)")
# 2026-09-04 실증: 형식상 정상인 빈 응답이 오면 빈 candidate가 A~F를 전부
# 통과하고 production 전체가 0건으로 교체됐다. 이 블록은 원래 그 동작을
# "정상"으로 단언하고 있었다. 테스트가 파괴적 동작을 보증하고 있었던 셈이다.
before = data_fingerprint(os.path.join(ROOT, "data"))
collect.fetch_page = lambda k, n: make_page([], 0)
raised = None
try:
    collect.fetch_all("KEY")
except collect.CollectionError as e:
    raised = str(e)
check("totalCount=0은 완결로 인정하지 않음", raised is not None, raised or "예외 없음")
check("data/ 무변경", before == data_fingerprint(os.path.join(ROOT, "data")))

# stale 삭제 자체는 계속 동작해야 한다. 단 '빈 candidate'가 아니라
# 매장이 있는 정상 candidate 기준으로 증명한다.
tmp = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(tmp, "busan"))
    stale = os.path.join(tmp, "busan", "bsjunggu.json")
    with open(stale, "w", encoding="utf-8") as f:
        json.dump({"totalCount": 1, "stores": []}, f)
    collect.classify_and_save([SEOUL_GANGNAM], "2026-09-03", complete=True, data_dir=tmp)
    check("complete=True면 stale 파일 삭제", not os.path.exists(stale))

    os.makedirs(os.path.join(tmp, "busan"), exist_ok=True)
    with open(stale, "w", encoding="utf-8") as f:
        json.dump({"totalCount": 1, "stores": []}, f)
    collect.classify_and_save([SEOUL_GANGNAM], "2026-09-03", complete=False, data_dir=tmp)
    check("complete=False면 stale 파일 보존", os.path.exists(stale))
finally:
    shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- 5
print("\n[5] totalCount와 raw 수집 건수 불일치 → 저장/삭제 0")
before = data_fingerprint(os.path.join(ROOT, "data"))
collect.fetch_page = lambda k, n: make_page([SEOUL_GANGNAM] * 10, 5000) if n == 1 else make_page([], 5000)
raised = None
try:
    collect.fetch_all("KEY")
except collect.CollectionError as e:
    raised = str(e)
after = data_fingerprint(os.path.join(ROOT, "data"))
check("건수 불일치 시 CollectionError", raised is not None, raised or "예외가 발생하지 않음")
check("data/ 무변경", before == after)


# ---------------------------------------------------------------- 6~8
print("\n[6~8] 저장 직전 지역 검증")
check(
    "6) 다른 시도 주소 주입 → 거부",
    collect.verify_store_location(
        {"roadAddress": "대구광역시 북구 경진로1길 10", "address": ""}, "서울특별시", "강북구"
    )
    is not None,
)
check(
    "7) 같은 시도 다른 구군 주소 주입 → 거부",
    collect.verify_store_location(
        {"roadAddress": "부산광역시 북구 만덕대로 1", "address": ""}, "부산광역시", "강서구"
    )
    is not None,
)
r8 = collect.verify_store_location(
    {
        "roadAddress": "서울특별시 노원구 섬밭로 52",
        "address": "전라남도 광양시 광양읍 인동리 385-2",
    },
    "서울특별시",
    "노원구",
)
check("8) roadAddress/address가 다른 지역 → 격리", r8 is not None, f"사유: {r8}")
check(
    "정상 레코드는 통과",
    collect.verify_store_location(
        {"roadAddress": "서울특별시 강남구 테헤란로 1", "address": "서울특별시 강남구 역삼동 1"},
        "서울특별시",
        "강남구",
    )
    is None,
)


# -------------------------------------------------------------- 10~16
print("\n[10~16] 통합 시도(전남광주통합특별시) 논리 분리")

gj = set(collect.DISTRICT_SLUG_MAP["gwangju"])
jn = set(collect.DISTRICT_SLUG_MAP["jeonnam"])
check("10) 광주 5구 집합", gj == {"동구", "서구", "남구", "북구", "광산구"}, f"{sorted(gj)}")
check("10) 전남 22시군 집합", len(jn) == 22, f"{len(jn)}개")
check("10) 두 집합 서로소 (드리프트 가드)", not (gj & jn), f"교집합 {sorted(gj & jn)}")

for token in ("전남광주통합특별시", "전남광주"):
    r = collect.resolve_merged_sido([token, "남구", "봉선로"])
    check(f"11) '{token} 남구' → 광주광역시/남구", r == ("광주광역시", "남구"), f"{r}")
    r = collect.resolve_merged_sido([token, "나주시", "그린로"])
    check(f"12) '{token} 나주시' → 전라남도/나주시", r == ("전라남도", "나주시"), f"{r}")

check(
    "13) 통합 표기 + 미지 토큰 → (None, None)",
    collect.resolve_merged_sido(["전남광주통합특별시", "없는구", "어딘가"]) == (None, None),
)
check(
    "14) 광양시(전남) → 전라남도 (광주 오분류 방지)",
    collect.resolve_merged_sido(["전남광주통합특별시", "광양시", "중동"]) == ("전라남도", "광양시"),
)
check(
    "14) 경기도 광주시는 통합 resolver 미진입 → 경기도",
    collect.derive_location("경기도 광주시 경안로 1") == ("경기도", "광주시"),
)
check(
    "15) 구 명칭 잔존분 정상 처리 (전라남도/광주광역시)",
    collect.derive_location("전라남도 나주시 그린로 1") == ("전라남도", "나주시")
    and collect.derive_location("광주광역시 남구 봉선로 1") == ("광주광역시", "남구"),
)
check(
    "16) startswith fallback 제거 — '전남광주통합특별시'가 전라남도로 흡수되지 않음",
    collect.normalize_region("전남광주통합특별시 남구 봉선로 1") is None,
)
check(
    "16) 정규화표 완전일치는 유지 ('강원도' → 강원특별자치도)",
    collect.normalize_region("강원도 춘천시 1") == "강원특별자치도",
)

print("\n[17] 미등록 시도 토큰 분류 — new_region_token vs malformed_address")
for tok, want in [
    ("전남광주통합특별시", "new_region_token"),
    ("가상특별자치도", "new_region_token"),
    ("안양시", "malformed_address"),
    ("385-2", "malformed_address"),
    ("220", "malformed_address"),
    ("", "malformed_address"),
]:
    got = collect.classify_unknown_sido(tok)
    check(f"17) {tok or '(빈값)':16s} → {want}", got == want, f"실제 {got}")
check(
    "17) 기존 17개 시도명은 전부 시도로 인식",
    all(collect.classify_unknown_sido(r) == "new_region_token" for r in collect.REGION_NAME_TO_SLUG),
)

print("\n[19] end-to-end — 정상 merged 주소가 classify_and_save() 전 경로를 통과")
# 단위 테스트(resolve_merged_sido)만으로는 분기 순서 버그를 잡을 수 없다.
# 실제 저장 함수를 통과시켜 최종 파일까지 확인한다. data/는 건드리지 않는다.
before = data_fingerprint(os.path.join(ROOT, "data"))
tmp = tempfile.mkdtemp()
try:
    e2e_items = [
        item("광주남구마트", "전남광주통합특별시 남구 봉선로 1"),
        item("광산구마트", "전남광주통합특별시 광산구 상무대로 1"),
        item("나주마트", "전남광주통합특별시 나주시 그린로 1"),
        item("여수마트", "전남광주 여수시 좌수영로 1"),
        item("서울마트", "서울특별시 강남구 테헤란로 1"),
    ]
    total = collect.classify_and_save(e2e_items, "2026-09-03", complete=True, data_dir=tmp)

    def loaded(region, slug):
        p = os.path.join(tmp, region, slug + ".json")
        if not os.path.exists(p):
            return None
        return json.load(open(p, encoding="utf-8"))

    gn = loaded("gwangju", "gjnamgu")
    gs = loaded("gwangju", "gwangsan")
    nj = loaded("jeonnam", "naju")
    ys = loaded("jeonnam", "yeosu")
    check("19) '전남광주통합특별시 남구' → gwangju/gjnamgu 저장", gn is not None and gn["totalCount"] == 1,
          f"{gn['totalCount'] if gn else '파일 없음'}")
    check("19) '전남광주통합특별시 광산구' → gwangju/gwangsan 저장", gs is not None and gs["totalCount"] == 1,
          f"{gs['totalCount'] if gs else '파일 없음'}")
    check("19) '전남광주통합특별시 나주시' → jeonnam/naju 저장", nj is not None and nj["totalCount"] == 1,
          f"{nj['totalCount'] if nj else '파일 없음'}")
    check("19) 축약 변형 '전남광주 여수시' → jeonnam/yeosu 저장", ys is not None and ys["totalCount"] == 1,
          f"{ys['totalCount'] if ys else '파일 없음'}")
    check("19) 5건 전부 분류 성공 (총계)", total == 5, f"total={total}")

    unm = os.path.join(tmp, "_unmatched.json")
    if os.path.exists(unm):
        rows = json.load(open(unm, encoding="utf-8"))
    else:
        rows = []
    check("19) valid merged 주소가 _unmatched에 들어가지 않음", len(rows) == 0,
          f"_unmatched {len(rows)}건: {[r.get('name') for r in rows]}")

    gidx = json.load(open(os.path.join(tmp, "gwangju", "index.json"), encoding="utf-8"))
    jidx = json.load(open(os.path.join(tmp, "jeonnam", "index.json"), encoding="utf-8"))
    check("19) gwangju index totalCount=2", gidx["totalCount"] == 2, f"{gidx['totalCount']}")
    check("19) jeonnam index totalCount=2", jidx["totalCount"] == 2, f"{jidx['totalCount']}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
check("19) 실제 data/ 무변경", before == data_fingerprint(os.path.join(ROOT, "data")))


print("\n[18] 새 시도 토큰 1건이라도 나오면 저장·삭제 0")
before = data_fingerprint(os.path.join(ROOT, "data"))
raised = None
try:
    collect.classify_and_save(
        [item("가짜마트", "가상특별자치도 어딘가 1")], "2026-09-03", complete=True
    )
except collect.CollectionError as e:
    raised = str(e)
after = data_fingerprint(os.path.join(ROOT, "data"))
check("18) 새 시도 토큰 → CollectionError", raised is not None, raised or "예외 없음")
check("18) data/ 무변경", before == after)

before = data_fingerprint(os.path.join(ROOT, "data"))
raised = None
try:
    collect.classify_and_save(
        [item("가짜마트", "전남광주통합특별시 없는구 1")], "2026-09-03", complete=True
    )
except collect.CollectionError as e:
    raised = str(e)
after = data_fingerprint(os.path.join(ROOT, "data"))
check("18) 통합 시도 분리 실패 → CollectionError", raised is not None, raised or "예외 없음")
check("18) data/ 무변경", before == after)


# ---------------------------------------------------------------- 9
print("\n[9] 현행 69,265건에 새 검증 적용 — 예상치 못한 대량 탈락 여부")
rejected = {}
total_checked = 0
data_root = os.path.join(ROOT, "data")
for region_slug in sorted(os.listdir(data_root)):
    rdir = os.path.join(data_root, region_slug)
    if not os.path.isdir(rdir):
        continue
    idx_path = os.path.join(rdir, "index.json")
    if not os.path.exists(idx_path):
        continue
    with open(idx_path, encoding="utf-8") as f:
        idx = json.load(f)
    region_name = idx["region"]
    for entry in idx["districts"]:
        fp = os.path.join(rdir, entry["districtSlug"] + ".json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            d = json.load(f)
        for s in d["stores"]:
            total_checked += 1
            reason = collect.verify_store_location(s, region_name, entry["district"])
            if reason:
                key = reason.split(":")[0]
                rejected.setdefault(key, []).append(
                    f"{region_slug}/{entry['districtSlug']} | {s.get('name', '?')} | {reason}"
                )

n_rejected = sum(len(v) for v in rejected.values())
print(f"        검사 {total_checked:,}건 / 탈락 {n_rejected}건 ({n_rejected / total_checked * 100:.3f}%)")
for key, rows in sorted(rejected.items(), key=lambda x: -len(x[1])):
    print(f"        · {key}: {len(rows)}건")
    for r in rows[:3]:
        print(f"            {r}")
check("9) 탈락률 1% 미만 (대량 탈락 아님)", n_rejected / total_checked < 0.01,
      f"{n_rejected}/{total_checked}")
print("        ※ 9번은 자동 수정하지 않는다. 위 목록은 보고용이다.")




# ============================================================ P17.8
# 인천 2026 행정구역 개편 — legacy route bucket 정규화
# ============================================================
print("\n[P17.8-A~G] 인천 신규 구군 → legacy route bucket")

OJ = collect.LEGACY_DISTRICT_SETS["old_junggu"]
OY = collect.LEGACY_DISTRICT_SETS["old_junggu_yeongjong"]
OD = collect.LEGACY_DISTRICT_SETS["old_donggu"]

check("집합 교집합 0 (중구 원도심 ∩ 동구)", not (OJ & OD), f"{sorted(OJ & OD)}")
check("집합 교집합 0 (영종 ∩ 동구)", not (OY & OD), f"{sorted(OY & OD)}")
check("공식 동구 7개 법정동 전부 포함",
      OD == {"만석동", "화수동", "화평동", "송현동", "송림동", "금곡동", "창영동"}, f"{sorted(OD)}")


def loc(addr):
    return collect.derive_location(addr)


check("A) 제물포구 + 옛 중구 법정동 → 중구",
      loc("인천광역시 제물포구 항동7가 1") == ("인천광역시", "중구"), f"{loc('인천광역시 제물포구 항동7가 1')}")
check("B) 제물포구 + 옛 동구 법정동 → 동구",
      loc("인천광역시 제물포구 송림동 1") == ("인천광역시", "동구"), f"{loc('인천광역시 제물포구 송림동 1')}")
r, why = collect.resolve_legacy_district("인천광역시", "제물포구", ["인천광역시", "제물포구", "없는동", "1"])
check("C) 제물포구 + 미등록 법정동 → 미해결", r is None, f"{r} / {why}")
check("D) 영종구 → 중구 bucket",
      loc("인천광역시 영종구 중산동 1") == ("인천광역시", "중구"), f"{loc('인천광역시 영종구 중산동 1')}")
check("E) 서해구 → 서구 bucket",
      loc("인천광역시 서해구 검암로 1") == ("인천광역시", "서구"), f"{loc('인천광역시 서해구 검암로 1')}")
check("F) 검단구 → 서구 bucket",
      loc("인천광역시 검단구 원당대로 1") == ("인천광역시", "서구"),
      f"{loc('인천광역시 검단구 원당대로 1')}")

print("  G) 유사명 완전일치 — 부분문자열로 섞이지 않는가")
for dong, want in [("송림동", "동구"), ("송현동", "동구"),
                   ("송월동1가", "중구"), ("송학동3가", "중구")]:
    got = loc(f"인천광역시 제물포구 {dong} 1")
    check(f"G) 제물포구 {dong} → {want}", got == ("인천광역시", want), f"{got}")

print("\n[P17.8-H~J] road/lot 신구 표기 혼재 — legacy bucket 비교")
check("H) road=중구 / lot=제물포구 옛 중구 → 정상",
      collect.verify_store_location(
          {"roadAddress": "인천광역시 중구 서해대로 1",
           "address": "인천광역시 제물포구 항동7가 76-2"}, "인천광역시", "중구") is None)
check("I) road=동구 / lot=제물포구 옛 동구 → 정상",
      collect.verify_store_location(
          {"roadAddress": "인천광역시 동구 봉수대로 82",
           "address": "인천광역시 제물포구 송림동 296-2"}, "인천광역시", "동구") is None)
j = collect.verify_store_location(
    {"roadAddress": "인천광역시 중구 서해대로 1",
     "address": "인천광역시 제물포구 송림동 296-2"}, "인천광역시", "중구")
check("J) road=중구 / lot=제물포구 옛 동구 → contradiction 격리", j is not None, f"사유: {j}")

print("\n[P17.8-K~L] 구군 drift preflight — write 전 fail closed")
before = data_fingerprint(os.path.join(ROOT, "data"))
tmp = tempfile.mkdtemp()
raised = None
try:
    collect.classify_and_save(
        [item("가짜", "인천광역시 제물포구 없는동 1")], "2026-09-03", complete=True, data_dir=tmp)
except collect.CollectionError as e:
    raised = str(e)
wrote = sum(len(f) for _, _, f in os.walk(tmp))
shutil.rmtree(tmp, ignore_errors=True)
check("K) 미등록 구군 1건 → CollectionError", raised is not None, raised or "예외 없음")
check("K) 임시 디렉터리에 파일 write 0 (index/_unmatched 포함)", wrote == 0, f"{wrote}개 생성됨")
check("K) 실제 data/ 무변경", before == data_fingerprint(os.path.join(ROOT, "data")))

tmp = tempfile.mkdtemp()
raised = None
try:
    collect.classify_and_save(
        [item("연기군매장", "충청남도 연기군 조치원읍 1"),
         item("군위매장", "경상북도 군위군 군위읍 1"),
         item("정상매장", "서울특별시 강남구 테헤란로 1")],
        "2026-09-03", complete=True, data_dir=tmp)
except collect.CollectionError as e:
    raised = str(e)
unm = os.path.join(tmp, "_unmatched.json")
n_unm = len(json.load(open(unm, encoding="utf-8"))) if os.path.exists(unm) else 0
gn = os.path.exists(os.path.join(tmp, "sejong", "sejongsi.json"))
gd = os.path.exists(os.path.join(tmp, "daegu", "gunwi.json"))
shutil.rmtree(tmp, ignore_errors=True)
check("L) historical exception은 CollectionError를 유발하지 않음", raised is None, raised or "")
check("L) 자동 재귀속하지 않음 (세종/대구로 옮기지 않음)", not gn and not gd)
check("L) historical 2건은 _unmatched에 남음", n_unm == 2, f"{n_unm}건")


# ============================================================ P17.9
# legacy destructive collector 재등장 방지 가드
#
# 2026-09-03에 classify_all.py / reclassify.py / reclassify_all.py를 삭제했다.
# 셋 다 호출처가 0인데 인자 없이 실행 가능했고, data/*.json을 통째로 지운 뒤
# 강북구 오염을 만든 부분 매칭 fallback으로 재분류했다.
#
# 목적은 "오늘 치운 위험이 조용히 다시 생기지 못하게" 하는 것이다.
# Python 보안 분석기를 만드는 것이 아니다.
# ============================================================
print("\n[P17.9] legacy destructive entrypoint 재등장 방지")

SCRIPTS_DIR = os.path.join(ROOT, "scripts")

# 감사를 마친 Python entrypoint. 새 도구 추가 자체를 금지하지 않는다.
# 다만 destructive path(data/ write·delete) 감사 없이 조용히 늘어나지는 못한다.
#
# integrity.py 추가 근거 (2026-09-03 P3-13 감사):
#   write/delete/rename 계열 호출 0건, open() 1곳 전부 읽기 모드,
#   모듈 레벨 실행문 없음(import 안전), __main__/argparse/sys.argv 0건,
#   import 전후 data/ 체크섬 동일. 순수 검증 모듈이며 독립 entrypoint 아님.
ALLOWED_SCRIPTS = {"collect.py", "test_collect.py", "integrity.py"}

# 삭제된 legacy. 복원하지 않는다. 필요한 기능은 현재 collect.py의
# exact-match / fail-closed 원칙 위에서 새로 구현한다.
RETIRED_SCRIPTS = {"classify_all.py", "reclassify.py", "reclassify_all.py"}

present = {f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".py")}

unexpected = sorted(present - ALLOWED_SCRIPTS)
check(
    "A) scripts/ Python entrypoint가 감사된 목록뿐",
    not unexpected,
    "새 Python entrypoint: " + ", ".join(unexpected) + "\n"
    "        의도된 추가라면 data/ write·delete 경로를 감사한 뒤\n"
    "        ALLOWED_SCRIPTS에 추가하라. 추가 자체가 금지는 아니다."
    if unexpected else "",
)

revived = sorted(present & RETIRED_SCRIPTS)
check(
    "B) 삭제된 legacy collector가 복원되지 않음",
    not revived,
    "복원됨: " + ", ".join(revived) + "\n"
    "        이 파일들은 data/*.json을 통째로 지우고 부분 매칭으로 재분류한다.\n"
    "        복원하지 말고 collect.py 기반으로 새로 구현하라."
    if revived else "",
)

# 강북구 오염을 만든 "양방향 부분 포함" 검사를 잡는다.
# 두 변수를 서로의 부분 문자열로 두 번 비교하는 형태로, 변수명이
# 달라져도 걸리도록 코드 모양으로 매칭한다. 주석과 문자열은 제외한다.
BIDIR_SUBSTRING = re.compile(r"(\w+)\s+in\s+(\w+)\s+or\s+\2\s+in\s+\1")

offenders = []
for fn in sorted(present):
    path = os.path.join(SCRIPTS_DIR, fn)
    for i, raw_line in enumerate(open(path, encoding="utf-8"), 1):
        line = raw_line.split("#", 1)[0]  # 주석 제외, 실제 코드만 본다
        if BIDIR_SUBSTRING.search(line):
            offenders.append(f"{fn}:{i}  {line.strip()[:70]}")

check(
    "C) 양방향 부분 포함 매칭이 재등장하지 않음",
    not offenders,
    "\n        ".join(offenders) + "\n"
    "        양방향 부분 포함 검사는 \"북구\"를 \"강북구\"로 흡수시킨다.\n"
    "        구군 판정은 토큰 완전 일치만 쓴다."
    if offenders else "",
)





# ============================================================ P3-13
# Single Integrity Gate + Rollback-safe Promotion
#
# 핵심 불변조건:
#   integrity failure > 0  ->  promotion 0  ->  exit non-zero
#                          ->  기존 production 보존
# validator가 실행됐다는 것만으로는 부족하다. FAIL이 반드시 promotion
# 차단으로 이어져야 한다.
# ============================================================
print("\n[P3-13] 단일 무결성 게이트 + rollback-safe promotion")


def make_prod(root, region="seoul", slug="gangnam", district="강남구",
              region_name="서울특별시", n=1):
    """production 트리 흉내. 검증 대상이 아니라 '보존되는지' 확인용."""
    os.makedirs(os.path.join(root, region), exist_ok=True)
    stores = [{"name": f"기존{i}", "address": f"{region_name} {district} 역삼동 {i}",
               "roadAddress": f"{region_name} {district} 테헤란로 {i}",
               "status": "영업/정상", "licenseDate": "2020-01-01"} for i in range(n)]
    json.dump({"region": region_name, "regionSlug": region, "district": district,
               "districtSlug": slug, "updatedAt": "2026-03-27",
               "totalCount": n, "stores": stores},
              open(os.path.join(root, region, f"{slug}.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    json.dump({"region": region_name, "regionSlug": region, "updatedAt": "2026-03-27",
               "totalCount": n,
               "districts": [{"district": district, "districtSlug": slug, "count": n}]},
              open(os.path.join(root, region, "index.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    json.dump({"updatedAt": "2026-03-27", "totalCount": n,
               "regions": [{"region": region_name, "regionSlug": region, "count": n}]},
              open(os.path.join(root, "regions.json"), "w", encoding="utf-8"),
              ensure_ascii=False)


def tree_sig(root):
    h = hashlib.sha256()
    for dp, _, fns in sorted(os.walk(root)):
        for fn in sorted(fns):
            p = os.path.join(dp, fn)
            h.update(os.path.relpath(p, root).encode())
            h.update(open(p, "rb").read())
    return h.hexdigest()


GOOD = [item("정상마트", "서울특별시 강남구 테헤란로 9", "서울특별시 강남구 역삼동 9")]

# rollback/promotion mechanics fixture; not intended to exercise catastrophic-drop guard.
# make_prod(n=3) 과 짝을 이뤄 production 3건 -> candidate 3건(감소 0%)이 되게 한다.
# GOOD(1건)을 쓰면 3 -> 1 = -66.7% 라 G.national_drop 이 정당하게 발화해서
# rename 주입 지점까지 도달하지 못한다. 안전 규칙을 약화하는 대신 fixture 를 맞춘다.
GOOD3 = [
    item("정상마트", "서울특별시 강남구 테헤란로 9", "서울특별시 강남구 역삼동 9"),
    item("정상마트2", "서울특별시 강남구 테헤란로 10", "서울특별시 강남구 역삼동 10"),
    item("정상마트3", "서울특별시 강남구 테헤란로 11", "서울특별시 강남구 역삼동 11"),
]


def make_prod_multi(root, counts, region="seoul", region_name="서울특별시"):
    """다중 district production 트리. counts = {slug: (district명, n)}.

    단일 district fixture 로는 "candidate 파일 하나 누락" 을 시험할 수 없다.
    유일한 파일을 지우면 candidate 가 0건이 되어 G.total_wipe 가 대신 막아버리고,
    F.missing_file 탐지가 통째로 죽어도 테스트가 통과한다. 큰 district 하나와
    아주 작은 district 하나를 두면, 작은 쪽을 지워도 전국·시도·구군 게이트가
    전부 임계값 미달이라 F 계열만 발화한다.
    """
    os.makedirs(os.path.join(root, region), exist_ok=True)
    entries = []
    total = 0
    for slug, (district, n) in counts.items():
        stores = [{"name": f"기존{slug}{i}",
                   "address": f"{region_name} {district} 역삼동 {i}",
                   "roadAddress": f"{region_name} {district} 테헤란로 {i}",
                   "status": "영업/정상", "licenseDate": "2020-01-01"} for i in range(n)]
        json.dump({"region": region_name, "regionSlug": region, "district": district,
                   "districtSlug": slug, "updatedAt": "2026-03-27",
                   "totalCount": n, "stores": stores},
                  open(os.path.join(root, region, f"{slug}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False)
        entries.append({"district": district, "districtSlug": slug, "count": n})
        total += n
    json.dump({"region": region_name, "regionSlug": region, "updatedAt": "2026-03-27",
               "totalCount": total, "districts": entries},
              open(os.path.join(root, region, "index.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    json.dump({"updatedAt": "2026-03-27", "totalCount": total,
               "regions": [{"region": region_name, "regionSlug": region, "count": total}]},
              open(os.path.join(root, "regions.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    return total


# 강남 199 + 서초 1 = 200. 서초 파일 하나를 지우면 candidate 199 (-0.5%) 라
# 전국(>=25%)·시도(>=30건)·구군(>=100건 / 전멸은 prod>=20) 어디에도 걸리지 않는다.
BIG200 = (
    [item(f"강남마트{i}", f"서울특별시 강남구 테헤란로 {i}",
          f"서울특별시 강남구 역삼동 {i}") for i in range(199)]
    + [item("서초마트", "서울특별시 서초구 서초대로 1", "서울특별시 서초구 서초동 1")]
)

# ── 1. integrity failure 1건 → promotion 0, production 보존, exit 1 경로
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3)
    sig0 = tree_sig(tmp)
    orig = collect.integrity.validate_candidate

    def failing(cand, prod, stats, verify, subject="candidate"):
        rep, plan = orig(cand, prod, stats, verify, subject)
        rep.fail("TEST.injected", "주입된 무결성 실패")
        return rep, plan

    collect.integrity.validate_candidate = failing
    promoted = {"called": False}
    orig_promote = collect.promote_candidate
    collect.promote_candidate = lambda *a, **k: promoted.__setitem__("called", True)
    raised = None
    try:
        # GOOD3(3건). GOOD(1건)을 쓰면 prod 3 -> cand 1 = -66.7% 라 G.national_drop 이
        # 대신 막아버려서, 주입한 TEST.injected 가 없어도 이 테스트가 통과한다.
        # 그러면 "임의의 미지 실패 코드가 promotion 을 차단한다"는 것을 증명하지 못한다.
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    collect.integrity.validate_candidate = orig
    collect.promote_candidate = orig_promote
    check("1) integrity failure → CollectionError", raised is not None, raised or "예외 없음")
    # 주입한 코드가 실제 차단 사유여야 한다. 다른 게이트가 대신 막은 것이면 무의미하다.
    check("1) 차단 사유가 주입한 TEST.injected", "TEST.injected" in (raised or ""), raised or "예외 없음")
    check("1) 다른 게이트가 대신 막지 않았다 (G 미발화)", "G." not in (raised or ""), raised or "")
    check("1) promote_candidate 호출 0", not promoted["called"])
    check("1) production 트리 보존", tree_sig(tmp) == sig0)

    # mutation 검증: 주입을 제거하면 같은 fixture 가 promotion 까지 간다.
    # 이것이 성립해야 위 3개 단언이 "주입 때문에" 막혔음을 증명한다.
    promoted2 = {"called": False}
    collect.promote_candidate = lambda *a, **k: promoted2.__setitem__("called", True)
    raised2 = None
    try:
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised2 = str(e)
    collect.promote_candidate = orig_promote
    check("1-mut) 주입 제거 시 게이트 통과 (masking 아님 증명)",
          raised2 is None and promoted2["called"], raised2 or "promote 미호출")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── 2. candidate index mismatch → promotion 0
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)
    orig_build = collect.build_candidate

    def corrupt_index(items, updated_at, workspace):
        st = orig_build(items, updated_at, workspace)
        ip = os.path.join(workspace, "seoul", "index.json")
        d = json.load(open(ip, encoding="utf-8"))
        d["totalCount"] = d["totalCount"] + 7
        json.dump(d, open(ip, "w", encoding="utf-8"), ensure_ascii=False)
        return st

    collect.build_candidate = corrupt_index
    raised = None
    try:
        collect.classify_and_save(GOOD, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    collect.build_candidate = orig_build
    check("2) candidate index mismatch → FAIL", raised is not None and "F." in (raised or ""), raised or "예외 없음")
    check("2) production 보존", tree_sig(tmp) == sig0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── 3. candidate district 파일 누락 → promotion 0
#
# fixture 설계 근거: 단일 district(강남 3건) + GOOD 로 하면 파일을 지운 candidate 가
# 0건이 되어 G.total_wipe 가 발화한다. 그러면 F.missing_file 계열 탐지가 통째로
# 죽어도 이 테스트는 PASS 한다. 200건 중 1건짜리 구군만 지우면 급감 가드가 전부
# 임계값 미달이라 F 계열만 남는다. 게이트를 약화하지 않고 fixture 를 맞춘 것이다.
tmp = tempfile.mkdtemp()
try:
    make_prod_multi(tmp, {"gangnam": ("강남구", 199), "seocho": ("서초구", 1)})
    sig0 = tree_sig(tmp)

    def drop_file(items, updated_at, workspace):
        st = orig_build(items, updated_at, workspace)
        os.remove(os.path.join(workspace, "seoul", "seocho.json"))
        return st

    collect.build_candidate = drop_file
    raised = None
    try:
        collect.classify_and_save(BIG200, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    collect.build_candidate = orig_build
    check("3) candidate 파일 누락 → FAIL", raised is not None, raised or "예외 없음")
    check("3) 차단 사유가 F.missing_file", "F.missing_file" in (raised or ""), raised or "")
    check("3) 급감 가드가 대신 막지 않았다 (G 미발화)", "G." not in (raised or ""), raised or "")
    check("3) production 보존", tree_sig(tmp) == sig0)

    # mutation 검증: 파일을 지우지 않으면 같은 fixture 가 promotion 까지 간다.
    promoted3 = {"called": False}
    orig_promote3 = collect.promote_candidate
    collect.promote_candidate = lambda *a, **k: promoted3.__setitem__("called", True)
    raised3 = None
    try:
        collect.classify_and_save(BIG200, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised3 = str(e)
    collect.promote_candidate = orig_promote3
    check("3-mut) 변이 제거 시 게이트 통과 (masking 아님 증명)",
          raised3 is None and promoted3["called"], raised3 or "promote 미호출")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── 4. unknown district 1건 → promotion 0 (기존 preflight 재확인)
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)
    raised = None
    try:
        collect.classify_and_save(
            [item("가짜", "인천광역시 제물포구 없는동 1")], "2026-09-03",
            complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    check("4) unknown district → CollectionError", raised is not None, raised or "예외 없음")
    check("4) production 보존", tree_sig(tmp) == sig0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── 5. accounted contradiction → 정상 quarantine + reconciliation PASS
tmp = tempfile.mkdtemp()
try:
    mixed = GOOD + [item("모순마트", "서울특별시 강남구 테헤란로 1",
                         "전라남도 광양시 광양읍 1")]
    total = collect.classify_and_save(mixed, "2026-09-03", complete=True, data_dir=tmp)
    gn = json.load(open(os.path.join(tmp, "seoul", "gangnam.json"), encoding="utf-8"))
    check("5) contradiction 격리 후 promotion 성공", total == 1 and gn["totalCount"] == 1,
          f"total={total} file={gn['totalCount']}")
    check("5) contradiction이 최종 store에 없음",
          all("광양" not in (s.get("address") or "") for s in gn["stores"]))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── 6. unaccounted contradiction → FAIL
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)

    def lose_accounting(items, updated_at, workspace):
        st = orig_build(items, updated_at, workspace)
        st["contradictions"] = 0          # 집계에서 사라뜨림
        st["contradiction_records"] = []
        return st

    collect.build_candidate = lose_accounting
    raised = None
    try:
        collect.classify_and_save(
            GOOD + [item("모순", "서울특별시 강남구 테헤란로 1", "전라남도 광양시 광양읍 1")],
            "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    collect.build_candidate = orig_build
    check("6) 회계에서 사라진 contradiction → FAIL", raised is not None and "B." in (raised or ""),
          raised or "예외 없음")
    check("6) production 보존", tree_sig(tmp) == sig0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── 7. 첫 rename 전 실패 → production unchanged
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)
    real_rename = os.rename

    def fail_first(src, dst):
        if os.path.abspath(src) == os.path.abspath(tmp):
            raise OSError("주입: data/ -> backup rename 실패")
        return real_rename(src, dst)

    collect.os.rename = fail_first
    raised = None
    try:
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True, data_dir=tmp)
    except OSError as e:
        raised = str(e)
    collect.os.rename = real_rename
    check("7) 첫 rename 실패 → 예외 전파", raised is not None, raised or "예외 없음")
    check("7) production 완전 유지", tree_sig(tmp) == sig0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── 8. backup 성공 후 candidate->data 실패 → rollback
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)
    real_rename = os.rename
    state = {"step": 0}

    def fail_second(src, dst):
        # data/ -> backup 은 통과, candidate -> data/ 에서 실패
        if os.path.abspath(dst) == os.path.abspath(tmp) and ".data-candidate" in src:
            raise OSError("주입: candidate -> data rename 실패")
        return real_rename(src, dst)

    collect.os.rename = fail_second
    raised = None
    try:
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True, data_dir=tmp)
    except OSError as e:
        raised = str(e)
    collect.os.rename = real_rename
    check("8) 두 번째 rename 실패 → 예외 전파", raised is not None, raised or "예외 없음")
    check("8) rollback으로 production 원상복구", os.path.isdir(tmp) and tree_sig(tmp) == sig0,
          f"존재={os.path.isdir(tmp)}")
    check("8) backup 잔여물 없음",
          not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(tmp)), ".data-backup")))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── 10. 성공 promotion → candidate 전체 반영 + 3계층 일치
tmp = tempfile.mkdtemp()
try:
    # rollback/promotion mechanics fixture; not intended to exercise
    # catastrophic-drop guard. production 3건(busan) -> candidate 3건(seoul)
    # 이라 전국 감소 0%. GOOD(1건)이면 3 -> 1 = -66.7% 로 정당하게 막힌다.
    #
    # 시도·구군 층이 조용한 이유도 함께 적는다. 이 fixture 는 busan 시도와
    # bsjunggu 구군이 통째로 사라지지만, 손실 3건은 R1(시도 >=30건)·
    # D1(구군 >=100건)·D2(구군 전멸은 production >=20건)·AGG(material 은
    # >=20건) 어디에도 미달이라 정상적으로 미발화한다. 즉 이 침묵은 게이트
    # 결함이 아니라 임계값 설계의 결과다. 임계값 경계 자체는 S1~S24 가 본다.
    make_prod(tmp, region="busan", slug="bsjunggu", district="중구",
              region_name="부산광역시", n=3)
    stale = os.path.join(tmp, "busan", "bsjunggu.json")
    check("10) 사전조건: stale 파일 존재", os.path.exists(stale))
    total = collect.classify_and_save(GOOD3, "2026-09-09", complete=True, data_dir=tmp)
    check("10) promotion 성공", total == 3, f"total={total}")
    check("10) candidate에 없던 stale 파일이 사라짐", not os.path.exists(stale))
    check("10) 새 파일 반영", os.path.exists(os.path.join(tmp, "seoul", "gangnam.json")))
    rep = collect.integrity.audit_tree(tmp, collect.verify_store_location, "promoted")
    check("10) 반영된 트리 3계층 일치", rep.ok, rep.summary())
    check("10) candidate workspace 잔여물 없음",
          not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(tmp)), ".data-candidate")))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── 9. validator FAIL인데 exit 0이 되지 않음 (회귀 방지)
#
# 여기 있던 `issubclass(collect.CollectionError, Exception)` 단언을 제거했다.
# CollectionError 는 `class CollectionError(RuntimeError)` 이므로 그 조건은 클래스
# 정의만으로 항상 참이었다. 모든 게이트가 조용히 통과하도록 바뀌어도 PASS 였다.
#
# 이 항목이 보증하려던 것(게이트 실패가 silent success 가 되지 않고 process exit
# non-zero 로 전파된다)은 아래 [P3-13 exit] 섹션의 자식 프로세스 테스트가 실제
# 행위로 단언한다: totalCount=0 / API 오류 봉투 / G.total_wipe 3시나리오에서
# returncode != 0 과 production 무변경을 확인한다. 중복 단언을 억지로 만들지 않는다.

# ============================================================ F 개별 코드
# F.* 는 12개 실패 코드를 갖는데, 감사 시점에 이름이 고정된 것은 0개였다.
# 유일한 F 계열 단언이 접두사 검사(`"F." in raised`) 하나뿐이어서, 예컨대
# F.missing_file 탐지가 죽고 F.index_selfsum 만 살아 있어도 통과했다.
#
# 여기서는 합성 트리를 check_tree_counts 에 직접 넣어 **정확한 코드 집합**을
# 단언한다. read_tree 가 돌려주는 구조를 그대로 만들므로 report.fail 배선을
# 실제로 통과한다. validate_candidate → check_tree_counts 배선은 [P3-13] 2·3 이
# e2e 로 이미 덮는다.
#
# 코드 선정: production 에서 실제로 발생 가능한 경로와 root cause 가 서로 다른
# 것만 개별 고정한다. F.index_vs_files / F.regions_vs_index 는 다른 변이에서
# 파생적으로 함께 발화하므로 exact-set 단언이 자동으로 덮는다.
# ============================================================
print("\n[F] 개별 failure code 고정")


def ftree(districts, index_entries=None, index_total=None,
          regions_total=None, regions_count=None, regions_json="ok",
          index="ok", unreadable=()):
    """read_tree 반환 구조를 합성한다. districts = {slug: district json dict}.

    regions.json 은 기본값으로 **실제 파일 합** 을 쓴다. 따라서 index 가 파일과
    어긋나는 케이스에서 regions.json 은 파일과 일치하고 F.regions_vs_index 는
    발화하지 않는다. 최상위 집계 불일치는 regions_count / regions_total 인자로
    따로 주입해 독립적으로 시험한다.
    """
    if index_entries is None:
        index_entries = [{"district": f"{k}구", "districtSlug": k,
                          "count": len(v.get("stores") or [])}
                         for k, v in districts.items()]
    if index_total is None:
        index_total = sum(e.get("count", 0) for e in index_entries)
    file_sum = sum(len(v.get("stores") or []) for v in districts.values()
                   if isinstance(v.get("stores"), list))
    idx = None if index is None else {
        "region": "서울특별시", "regionSlug": "seoul",
        "totalCount": index_total, "districts": index_entries,
    }
    rj = None if regions_json is None else {
        "updatedAt": "2026-09-04",
        "totalCount": file_sum if regions_total is None else regions_total,
        "regions": [{"region": "서울특별시", "regionSlug": "seoul",
                     "count": file_sum if regions_count is None else regions_count}],
    }
    return {"root": "<synthetic>", "regions_json": rj,
            "regions": {"seoul": {"index": idx, "districts": districts}},
            "unreadable": list(unreadable), "files": {}}


def dfile(n, total=None, stores="list"):
    st = [{"name": f"s{i}"} for i in range(n)]
    if stores != "list":
        st = stores
    return {"region": "서울특별시", "regionSlug": "seoul", "district": "강남구",
            "districtSlug": "gangnam", "updatedAt": "2026-09-04",
            "totalCount": n if total is None else total, "stores": st}


def fcodes(tree):
    rep = collect.integrity.IntegrityReport("f-test")
    collect.integrity.check_tree_counts(tree, rep)
    return {c for c, _ in rep.failures}


def fcase(label, tree, expected):
    got = fcodes(tree)
    check(f"F-code) {label}", got == set(expected), f"기대={sorted(expected)} 실제={sorted(got)}")


# negative 대조군 — 정합한 트리는 F 실패 0
fcase("정합 트리는 실패 0 (negative 대조군)", ftree({"gangnam": dfile(5)}), [])

# 자기정합
fcase("파일 totalCount != stores 길이 → F.file_selfcount",
      ftree({"gangnam": dfile(5, total=7)}), ["F.file_selfcount"])
fcase("index totalCount != 항목합 → F.index_selfsum",
      ftree({"gangnam": dfile(5)}, index_total=9), ["F.index_selfsum"])

# 교차정합
fcase("index count != 파일 stores → F.index_vs_file",
      ftree({"gangnam": dfile(5)},
            index_entries=[{"district": "강남구", "districtSlug": "gangnam", "count": 8}]),
      ["F.index_vs_file", "F.index_vs_files"])
fcase("index 에 없는 파일 → F.orphan_file",
      ftree({"gangnam": dfile(5)}, index_entries=[]),
      ["F.orphan_file", "F.index_vs_files"])
fcase("index count>0 인데 파일 없음 → F.missing_file",
      ftree({}, index_entries=[{"district": "서초구", "districtSlug": "seocho", "count": 3}]),
      ["F.missing_file", "F.index_vs_files"])

# 스키마 / 읽기
fcase("stores 가 배열이 아님 → F.schema",
      ftree({"gangnam": dfile(0, total=0, stores={"not": "a list"})},
            index_entries=[{"district": "강남구", "districtSlug": "gangnam", "count": 0}]),
      ["F.schema"])
fcase("index.json 읽기 실패 → F.index_missing",
      ftree({"gangnam": dfile(5)}, index=None),
      ["F.index_missing", "F.regions_total"])
fcase("regions.json 없음 → F.regions_json",
      ftree({"gangnam": dfile(5)}, regions_json=None), ["F.regions_json"])
fcase("JSON 파손 → F.unreadable",
      ftree({"gangnam": dfile(5)}, unreadable=["seoul/x.json: bad json"]),
      ["F.unreadable"])

# 최상위 집계
fcase("regions.json count != 실제 → F.regions_vs_index",
      ftree({"gangnam": dfile(5)}, regions_count=99),
      ["F.regions_vs_index"])
fcase("regions.json totalCount != 파일 합 → F.regions_total",
      ftree({"gangnam": dfile(5)}, regions_total=99), ["F.regions_total"])

# F.tree_vs_stats 는 check_tree_counts 가 아니라 validate_candidate 가 낸다.
# 트리 실측과 회계상 최종을 어긋나게 해서 직접 발화시킨다.
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)

    def inflate_final(items, updated_at, workspace):
        st = orig_build(items, updated_at, workspace)
        # 회계만 부풀린다. B 는 stage3/closure 가 함께 깨지므로 그것도 함께 나온다.
        st["final"] = st["final"] + 1
        return st

    collect.build_candidate = inflate_final
    raised = None
    try:
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    collect.build_candidate = orig_build
    check("F-code) 트리 실측 != 회계 최종 → F.tree_vs_stats",
          "F.tree_vs_stats" in (raised or ""), raised or "예외 없음")
    check("F-code) production 보존", tree_sig(tmp) == sig0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)


# ============================================================ A/C/E positive
# 게이트 A · C · E 의 "발화 배선" 직접 검증
#
# 감사에서 확인된 구멍: A.api_completeness / C.no_names / C.location_mismatch /
# E.count_vs_records 는 테스트 파일 전체에서 코드명 출현이 0회였다. 함수 단위
# 테스트(verify_store_location)는 있었으나, 그 결과가 report.fail 로 실려
# promotion 을 막는 배선은 어떤 테스트도 통과시키지 않았다. 즉 이 게이트들이
# 통째로 죽어도 스위트는 초록색이었다.
#
# D 게이트는 같은 상황(정상 경로에서 항상 empty)인데도 직접 주입 positive 2개 +
# negative 1개를 갖고 있다. 여기서는 그 방식을 A·C·E 에 동일하게 적용한다.
#
# 각 fixture 는 대상 코드만 발화하고 다른 게이트가 대신 막지 않음을 함께 단언한다.
# ============================================================
print("\n[A/C/E] 게이트 발화 배선 직접 검증")


def _codes(raised):
    """CollectionError 메시지에서 실패 코드 접두 집합을 뽑는다."""
    return set(re.findall(r"\b([A-Z]+\.[a-z_]+)", raised or ""))


# ── A. api_completeness — classify_and_save 의 expected_total 인자로 직접 주입
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)
    raised = None
    try:
        # GOOD3 는 raw 3건. expected_total 을 4로 주면 raw != totalCount.
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True,
                                  data_dir=tmp, expected_total=4)
    except collect.CollectionError as e:
        raised = str(e)
    check("A+) raw != expected_total → A.api_completeness 발화",
          "A.api_completeness" in (raised or ""), raised or "예외 없음")
    check("A+) 다른 게이트가 대신 막지 않았다", _codes(raised) == {"A.api_completeness"},
          f"발화 코드={sorted(_codes(raised))}")
    check("A+) production 보존", tree_sig(tmp) == sig0)

    # negative: raw == expected_total 이면 통과해야 한다 (게이트가 항상 발화하는 게 아님)
    promoted = {"called": False}
    orig_promote = collect.promote_candidate
    collect.promote_candidate = lambda *a, **k: promoted.__setitem__("called", True)
    raised_n = None
    try:
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True,
                                  data_dir=tmp, expected_total=3)
    except collect.CollectionError as e:
        raised_n = str(e)
    collect.promote_candidate = orig_promote
    check("A-) raw == expected_total 이면 통과", raised_n is None and promoted["called"],
          raised_n or "promote 미호출")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── C.location_mismatch — candidate 트리의 store 주소만 바꾼다 (건수 불변 → F/G 무발화)
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)

    def move_store_out_of_bucket(items, updated_at, workspace):
        st = orig_build(items, updated_at, workspace)
        fp = os.path.join(workspace, "seoul", "gangnam.json")
        d = json.load(open(fp, encoding="utf-8"))
        # 강남구 파일에 저장돼 있는데 주소는 부산. 건수는 그대로라 F·G 는 조용하다.
        d["stores"][0]["address"] = "부산광역시 중구 남포동 1"
        d["stores"][0]["roadAddress"] = "부산광역시 중구 구덕로 1"
        json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
        return st

    collect.build_candidate = move_store_out_of_bucket
    raised = None
    try:
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    collect.build_candidate = orig_build
    check("C+) 저장 bucket != 주소 유래 지역 → C.location_mismatch 발화",
          "C.location_mismatch" in (raised or ""), raised or "예외 없음")
    check("C+) 다른 게이트가 대신 막지 않았다", _codes(raised) == {"C.location_mismatch"},
          f"발화 코드={sorted(_codes(raised))}")
    check("C+) production 보존", tree_sig(tmp) == sig0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── C.no_names — 지역명을 알 수 없는 트리
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)

    def strip_names(items, updated_at, workspace):
        st = orig_build(items, updated_at, workspace)
        ip = os.path.join(workspace, "seoul", "index.json")
        d = json.load(open(ip, encoding="utf-8"))
        d.pop("region", None)                       # region_name 소실
        for e in d["districts"]:
            e.pop("district", None)                 # entries fallback 도 소실
        json.dump(d, open(ip, "w", encoding="utf-8"), ensure_ascii=False)
        fp = os.path.join(workspace, "seoul", "gangnam.json")
        f = json.load(open(fp, encoding="utf-8"))
        f.pop("district", None)                     # district_name 소실
        json.dump(f, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
        return st

    collect.build_candidate = strip_names
    raised = None
    try:
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    collect.build_candidate = orig_build
    check("C+) 지역명 소실 → C.no_names 발화", "C.no_names" in (raised or ""),
          raised or "예외 없음")
    check("C+) no_names 는 급감 가드와 무관하게 발화", "G." not in (raised or ""), raised or "")
    check("C+) production 보존", tree_sig(tmp) == sig0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── E.count_vs_records — 집계와 격리 기록 수를 어긋나게 한다
#    contradictions(선언값)를 바꾸면 B.stage3·B.closure 가 함께 터져 E 를 가린다.
#    반대로 contradiction_records(목록)만 늘리면 B 는 선언값만 보므로 조용하고,
#    E 만 발화한다. 이것이 E 를 고립시키는 유일한 방향이다.
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)

    def phantom_record(items, updated_at, workspace):
        st = orig_build(items, updated_at, workspace)
        st["contradiction_records"] = list(st["contradiction_records"]) + [
            {"name": "유령기록", "reason": "테스트 주입"}
        ]
        return st

    collect.build_candidate = phantom_record
    raised = None
    try:
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    collect.build_candidate = orig_build
    check("E+) 집계 != 격리 기록 수 → E.count_vs_records 발화",
          "E.count_vs_records" in (raised or ""), raised or "예외 없음")
    check("E+) 다른 게이트가 대신 막지 않았다", _codes(raised) == {"E.count_vs_records"},
          f"발화 코드={sorted(_codes(raised))}")
    check("E+) production 보존", tree_sig(tmp) == sig0)

    # negative: 집계와 기록이 일치하면 통과
    promoted = {"called": False}
    orig_promote = collect.promote_candidate
    collect.promote_candidate = lambda *a, **k: promoted.__setitem__("called", True)
    raised_n = None
    try:
        collect.classify_and_save(GOOD3, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised_n = str(e)
    collect.promote_candidate = orig_promote
    check("E-) 집계 == 기록 수 이면 통과", raised_n is None and promoted["called"],
          raised_n or "promote 미호출")
finally:
    shutil.rmtree(tmp, ignore_errors=True)


# ============================================================ P3-13 recovery
# startup recovery state machine — 실제 프로세스 사망 후 복구
#
# SIGKILL·전원 차단·OS 크래시는 Python 예외가 아니다. promote_candidate의
# rollback except가 실행되지 않으므로, 다음 실행 시작 시 디스크 상태로
# 판정해야 한다. .data-backup 은 잔여물이 아니라 유일한 production일 수 있다.
# ============================================================
print("\n[P3-13 recovery] 프로세스 강제 종료 후 startup 복구")

_CRASH_CHILD = r'''
import importlib.util, os, sys
ROOT = sys.argv[3]
spec = importlib.util.spec_from_file_location("collect", os.path.join(ROOT, "scripts", "collect.py"))
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
c.load_district_slugs(); c.load_legacy_districts()
data_dir, window = sys.argv[1], sys.argv[2]
candidate, backup = c.promotion_paths(data_dir)
items = [{"BPLC_NM": "새마트", "ROAD_NM_ADDR": "서울특별시 강남구 테헤란로 9",
          "LOTNO_ADDR": "서울특별시 강남구 역삼동 9", "SALS_STTS_CD": "01",
          "SALS_STTS_NM": "영업/정상", "APLY_YMD": "2026-01-01"}]
c.build_candidate(items, "2026-09-09", candidate)
os.rename(data_dir, backup)
if window == "after_first":
    os._exit(9)
os.rename(candidate, data_dir)
if window == "after_second":
    os._exit(9)
os._exit(0)
'''


def run_crash(data_dir, window):
    """자식 프로세스에서 crash window를 실제로 재현한다 (os._exit)."""
    child = os.path.join(tempfile.mkdtemp(), "crash_child.py")
    open(child, "w", encoding="utf-8").write(_CRASH_CHILD)
    r = subprocess.run([sys.executable, child, data_dir, window, ROOT], capture_output=True)
    shutil.rmtree(os.path.dirname(child), ignore_errors=True)
    return r.returncode


def cleanup_promo(data_dir):
    for p in collect.promotion_paths(data_dir):
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=True)


# ── window 1: 첫 rename 직후 강제 종료
base = tempfile.mkdtemp()
try:
    data = os.path.join(base, "data")
    make_prod(data, n=3)
    orig = tree_sig(data)
    cand, backup = collect.promotion_paths(data)
    rc = run_crash(data, "after_first")
    check("R1) 자식이 강제 종료됨 (Python 예외 아님)", rc != 0, f"returncode={rc}")
    check("R1) crash window 재현: data 없음 + backup 있음",
          not os.path.isdir(data) and os.path.isdir(backup),
          f"data={os.path.isdir(data)} backup={os.path.isdir(backup)}")
    raised = None
    try:
        collect.recover_promotion_state(data)
    except collect.CollectionError as e:
        raised = str(e)
    check("R1) recovery가 fail closed (같은 실행에서 수집 안 이어감)", raised is not None,
          raised or "예외 없음")
    check("R1) data 자동 복구", os.path.isdir(data))
    check("R1) production checksum 원상복구", tree_sig(data) == orig)
    check("R1) backup을 잘못 삭제하지 않음 (복구로 소비)", not os.path.isdir(backup))
    gn = json.load(open(os.path.join(data, "seoul", "gangnam.json"), encoding="utf-8"))
    check("R1) candidate가 production으로 승격되지 않음", gn["totalCount"] == 3,
          f"totalCount={gn['totalCount']} (구 production 3이어야 함)")
    cleanup_promo(data)
finally:
    shutil.rmtree(base, ignore_errors=True)

# ── window 2: 두 번째 rename 성공 후 backup 정리 전 강제 종료
base = tempfile.mkdtemp()
try:
    data = os.path.join(base, "data")
    make_prod(data, n=3)
    old = tree_sig(data)
    cand, backup = collect.promotion_paths(data)
    rc = run_crash(data, "after_second")
    check("R2) crash window 재현: data 있음 + backup 있음",
          os.path.isdir(data) and os.path.isdir(backup),
          f"data={os.path.isdir(data)} backup={os.path.isdir(backup)}")
    new_sig = tree_sig(data)
    check("R2) data가 candidate로 교체된 상태", new_sig != old)
    state = collect.recover_promotion_state(data)
    check("R2) recovery 상태 C (backup 정리)", state == "C.backup_cleaned", state)
    check("R2) backup 제거됨", not os.path.isdir(backup))
    check("R2) 새 data 유지 (되돌리지 않음)", tree_sig(data) == new_sig)
    rep = collect.integrity.audit_tree_structure(data, "after-recovery")
    check("R2) 복구 후 구조 감사 PASS", rep.ok, rep.summary())
    cleanup_promo(data)
finally:
    shutil.rmtree(base, ignore_errors=True)

# ── state C-fail: data 구조가 깨졌으면 backup 보존
base = tempfile.mkdtemp()
try:
    data = os.path.join(base, "data")
    make_prod(data, n=3)
    cand, backup = collect.promotion_paths(data)
    os.makedirs(backup, exist_ok=True)
    make_prod(backup, n=3)
    ip = os.path.join(data, "seoul", "index.json")
    j = json.load(open(ip, encoding="utf-8"))
    j["totalCount"] = 999
    json.dump(j, open(ip, "w", encoding="utf-8"), ensure_ascii=False)
    raised = None
    try:
        collect.recover_promotion_state(data)
    except collect.CollectionError as e:
        raised = str(e)
    check("R3) data 구조 손상 + backup 존재 → fail closed", raised is not None,
          raised or "예외 없음")
    check("R3) backup 보존 (자동 삭제·덮어쓰기 금지)", os.path.isdir(backup))
    cleanup_promo(data)
finally:
    shutil.rmtree(base, ignore_errors=True)

# ── state D: data·backup 모두 없음 → HARD FAIL
base = tempfile.mkdtemp()
try:
    data = os.path.join(base, "data")
    raised = None
    try:
        collect.recover_promotion_state(data)
    except collect.CollectionError as e:
        raised = str(e)
    check("R4) data·backup 모두 없음 → HARD FAIL", raised is not None and "state D" in (raised or ""),
          raised or "예외 없음")
finally:
    shutil.rmtree(base, ignore_errors=True)

# ── promote_candidate는 backup이 남아 있으면 스스로 거부한다
base = tempfile.mkdtemp()
try:
    data = os.path.join(base, "data")
    make_prod(data, n=3)
    sig0 = tree_sig(data)
    cand, backup = collect.promotion_paths(data)
    os.makedirs(backup, exist_ok=True)
    make_prod(backup, n=1)
    os.makedirs(cand, exist_ok=True)
    make_prod(cand, n=2)
    raised = None
    try:
        collect.promote_candidate(cand, data)
    except collect.CollectionError as e:
        raised = str(e)
    check("R5) backup 잔존 시 promote_candidate 자체가 거부", raised is not None,
          raised or "예외 없음")
    check("R5) production 보존", tree_sig(data) == sig0)
    check("R5) backup 삭제되지 않음", os.path.isdir(backup))
    cleanup_promo(data)
finally:
    shutil.rmtree(base, ignore_errors=True)


# ---------------------------------------------------------------- P19 SAFETY
print("\n[P19-SAFETY] 빈 응답/오류 봉투 → promotion 0, 전면 삭제 차단")

# ── A. totalCount=0 → CollectionError → promotion 0
#    (fetch_all 차단은 [4]에서 확인. 여기서는 promotion 경로가 뚫리지 않는지 본다.)
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=10)
    sig0 = tree_sig(tmp)
    collect.fetch_page = lambda k, n: make_page([], 0)
    raised = None
    try:
        collect.fetch_all("KEY")
    except collect.CollectionError as e:
        raised = str(e)
    check("A) totalCount=0 → CollectionError", raised is not None, raised or "예외 없음")
    check("A) 그 결과로 promotion 시도 자체가 없음 → production 10건 유지",
          tree_sig(tmp) == sig0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── B. 게이트웨이 오류 봉투 3형태 → CollectionError
ERR_ENVELOPES = [
    ("OpenAPI_ServiceResponse",
     {"OpenAPI_ServiceResponse": {"cmmMsgHeader": {
         "returnReasonCode": "30", "errMsg": "SERVICE ERROR"}}}),
    ("top-level cmmMsgHeader",
     {"cmmMsgHeader": {"returnReasonCode": "30", "errMsg": "SERVICE ERROR"}}),
    ("response.header resultCode=22",
     {"response": {"header": {"resultCode": "22",
                              "resultMsg": "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR"},
                   "body": {"items": [], "totalCount": 0}}}),
]
before = data_fingerprint(os.path.join(ROOT, "data"))
for label, envelope in ERR_ENVELOPES:
    collect.fetch_page = lambda k, n, _e=envelope: _e
    raised = None
    try:
        collect.fetch_all("KEY")
    except collect.CollectionError as e:
        raised = str(e)
    check(f"B) 오류 봉투({label}) → CollectionError", raised is not None,
          raised or "예외 없음")
check("B) 오류 봉투 처리 중 data/ 무변경",
      before == data_fingerprint(os.path.join(ROOT, "data")))

# 오류 메시지에 serviceKey가 절대 들어가지 않는다
collect.fetch_page = lambda k, n: {"response": {"header": {
    "resultCode": "22", "resultMsg": "QUOTA"}, "body": {"items": [], "totalCount": 0}}}
msg = ""
try:
    collect.fetch_all("SUPER-SECRET-KEY-abc123")
except collect.CollectionError as e:
    msg = str(e)
check("B) 오류 메시지에 serviceKey 미포함", "SUPER-SECRET-KEY" not in msg, msg[:120])

# ── C. header 없는 기존 정상 fixture + 양수 totalCount → 정상 경로 유지
#    실제 정상 header를 아직 모르므로, header 부재를 실패로 보면 수집이
#    100% 실패한다. 그 회귀를 여기서 고정한다.
collect.fetch_page = lambda k, n: make_page([SEOUL_GANGNAM] * 100, 100) if n == 1 else make_page([], 100)
raised = None
try:
    items, calls, total = collect.fetch_all("KEY")
except Exception as e:
    raised = f"{type(e).__name__}: {e}"
check("C) header 없는 정상 응답 + 양수 totalCount → 통과", raised is None, raised or "")
check("C) 전량 수집", raised is None and len(items) == 100 and total == 100)

# 성공 sentinel이 명시된 header도 통과
collect.fetch_page = lambda k, n: (
    {"response": {"header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
                  "body": {"items": [SEOUL_GANGNAM], "totalCount": 1}}}
    if n == 1 else make_page([], 1))
raised = None
try:
    collect.fetch_all("KEY")
except Exception as e:
    raised = f"{type(e).__name__}: {e}"
check("C) resultCode=00 정상 header → 통과", raised is None, raised or "")

# 판정 불가한 미지의 코드는 막지 않는다 (근거 없는 hardcode 금지 원칙)
collect.fetch_page = lambda k, n: (
    {"response": {"header": {"resultCode": "NORMAL_SERVICE", "resultMsg": "OK"},
                  "body": {"items": [SEOUL_GANGNAM], "totalCount": 1}}}
    if n == 1 else make_page([], 1))
raised = None
try:
    collect.fetch_all("KEY")
except Exception as e:
    raised = f"{type(e).__name__}: {e}"
check("C) 판정 불가 resultCode는 차단하지 않음 (경고만)", raised is None, raised or "")

# ── D. production > 0 / candidate == 0 → G.total_wipe → promotion 0
#    2026-09-04에 실증한 전멸 시나리오와 동일한 fixture다.
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=10)
    sig0 = tree_sig(tmp)
    raised = None
    try:
        collect.classify_and_save([], "2026-09-04", complete=True, data_dir=tmp,
                                  expected_total=0)
    except collect.CollectionError as e:
        raised = str(e)
    check("D) production 10건 + candidate 0건 → CollectionError", raised is not None,
          raised or "예외 없음")
    check("D) 실패 사유가 G.total_wipe", "G.total_wipe" in (raised or ""), raised or "")
    check("D) promotion 0 — production 원본 그대로", tree_sig(tmp) == sig0)
    gn = json.load(open(os.path.join(tmp, "seoul", "gangnam.json"), encoding="utf-8"))
    check("D) production 매장 10건 유지", gn["totalCount"] == 10 and len(gn["stores"]) == 10,
          f"totalCount={gn['totalCount']} stores={len(gn['stores'])}")
    check("D) backup/candidate 잔여물 없음",
          not any(os.path.exists(p) for p in collect.promotion_paths(tmp)))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# diff_trees가 store 총계를 실제로 돌려주는지 (G 판정의 입력)
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=7)
    plan = collect.integrity.diff_trees(tmp, tmp)
    check("D) diff_trees가 prod_stores/cand_stores 반환",
          plan.get("prod_stores") == 7 and plan.get("cand_stores") == 7,
          f"prod={plan.get('prod_stores')} cand={plan.get('cand_stores')}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── F. bootstrap: production 부재/0건 → total-wipe guard 오발화 0
tmp = tempfile.mkdtemp()
try:
    empty = os.path.join(tmp, "data")   # 아직 존재하지 않는 production
    total = collect.classify_and_save(GOOD, "2026-09-04", complete=True,
                                      data_dir=empty, expected_total=1)
    check("F) production 부재 bootstrap → promotion 성공", total == 1, f"total={total}")
    check("F) 최초 트리 생성됨",
          os.path.exists(os.path.join(empty, "seoul", "gangnam.json")))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
    for p in collect.promotion_paths(os.path.join(tmp, "data")):
        shutil.rmtree(p, ignore_errors=True)

tmp = tempfile.mkdtemp()
try:
    data = os.path.join(tmp, "data")
    os.makedirs(data)
    total = collect.classify_and_save(GOOD, "2026-09-04", complete=True,
                                      data_dir=data, expected_total=1)
    check("F) 빈 production(0건) bootstrap → promotion 성공", total == 1, f"total={total}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
    for p in collect.promotion_paths(os.path.join(tmp, "data")):
        shutil.rmtree(p, ignore_errors=True)

# ── G. D 게이트 직접 주입 — 정상 경로에서 안 쓰인다고 죽은 게 아님을 증명
_rep = collect.integrity.IntegrityReport("D-direct")
collect.integrity.check_schema_drift(
    {"unknown_provinces": {"화성특별시": 3}, "unknown_districts": {}}, _rep)
check("G) D.unknown_province 직접 주입 시 실제 fail",
      not _rep.ok and any(c == "D.unknown_province" for c, _ in _rep.failures),
      _rep.summary())
_rep = collect.integrity.IntegrityReport("D-direct")
collect.integrity.check_schema_drift(
    {"unknown_provinces": {}, "unknown_districts": {("서울특별시", "없는구"): 1}}, _rep)
check("G) D.unknown_district 직접 주입 시 실제 fail",
      not _rep.ok and any(c == "D.unknown_district" for c, _ in _rep.failures),
      _rep.summary())
_rep = collect.integrity.IntegrityReport("D-direct")
collect.integrity.check_schema_drift({"unknown_provinces": {}, "unknown_districts": {}}, _rep)
check("G) unknown 0이면 D 통과", _rep.ok, _rep.summary())


# ── E. 게이트 실패가 실제 process exit non-zero 로 전파되는가
#    main()의 except CollectionError -> sys.exit(1) 경로를 자식에서 실행한다.
#    main()은 data_dir을 하드코딩하므로 classify_and_save를 임시 디렉터리로
#    감싸 실제 저장소 data/ 를 절대 건드리지 않게 한다.
_EXIT_CHILD = r"""
import importlib.util, os, sys
ROOT, scenario, data_dir = sys.argv[1], sys.argv[2], sys.argv[3]
spec = importlib.util.spec_from_file_location("collect", os.path.join(ROOT, "scripts", "collect.py"))
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

item = {"BPLC_NM": "정상마트", "ROAD_NM_ADDR": "서울특별시 강남구 테헤란로 9",
        "LOTNO_ADDR": "서울특별시 강남구 역삼동 9", "SALS_STTS_CD": "01",
        "SALS_STTS_NM": "영업/정상", "APLY_YMD": "2026-01-01"}

c.recover_promotion_state = lambda d: "A.normal"
_real = c.classify_and_save
c.classify_and_save = (lambda items, updated_at, **kw:
                       _real(items, updated_at, complete=kw.get("complete", False),
                             data_dir=data_dir, expected_total=kw.get("expected_total")))

if scenario == "empty_total":
    c.fetch_page = lambda k, n: {"response": {"body": {"items": [], "totalCount": 0}}}
elif scenario == "error_envelope":
    c.fetch_page = lambda k, n: {"OpenAPI_ServiceResponse": {"cmmMsgHeader": {
        "returnReasonCode": "30", "errMsg": "SERVICE KEY IS NOT REGISTERED ERROR"}}}
elif scenario == "gate_wipe":
    # fetch는 통과시키고 게이트에서 막히게 한다: candidate 0건 vs production >0
    c.fetch_page = lambda k, n: {"response": {"body": {"items": [item], "totalCount": 1}}}
    c.build_candidate = (lambda items, updated_at, workspace, _b=c.build_candidate:
                         _b([], updated_at, workspace))
sys.argv = ["collect.py", "--key", "TEST"]
c.main()
"""


def run_main(scenario, data_dir):
    child = os.path.join(tempfile.mkdtemp(), "exit_child.py")
    open(child, "w", encoding="utf-8").write(_EXIT_CHILD)
    r = subprocess.run([sys.executable, child, ROOT, scenario, data_dir],
                       capture_output=True)
    shutil.rmtree(os.path.dirname(child), ignore_errors=True)
    return r.returncode


for _scenario, _label in [("empty_total", "totalCount=0"),
                          ("error_envelope", "오류 봉투"),
                          ("gate_wipe", "G.total_wipe")]:
    tmp = tempfile.mkdtemp()
    try:
        data = os.path.join(tmp, "data")
        make_prod(data, n=10)
        sig0 = tree_sig(data)
        rc = run_main(_scenario, data)
        check(f"E) {_label} → process exit non-zero", rc != 0, f"returncode={rc}")
        check(f"E) {_label} → production 10건 유지", tree_sig(data) == sig0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        for p in collect.promotion_paths(os.path.join(tmp, "data")):
            shutil.rmtree(p, ignore_errors=True)


# ── H. state E: build_candidate 진행 중 hard exit → candidate 고아만 남음
_BUILD_CRASH_CHILD = r"""
import importlib.util, os, sys
ROOT, data_dir = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("collect", os.path.join(ROOT, "scripts", "collect.py"))
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
c.load_district_slugs(); c.load_legacy_districts()
candidate, backup = c.promotion_paths(data_dir)
item = {"BPLC_NM": "새마트", "ROAD_NM_ADDR": "서울특별시 강남구 테헤란로 9",
        "LOTNO_ADDR": "서울특별시 강남구 역삼동 9", "SALS_STTS_CD": "01",
        "SALS_STTS_NM": "영업/정상", "APLY_YMD": "2026-01-01"}
# workspace에 파일이 만들어지기 시작한 뒤 강제 종료한다 (Python 예외 아님).
_real_verify = c.verify_store_location
def boom(*a, **k):
    os._exit(9)
c.verify_store_location = boom
c.build_candidate([item], "2026-09-09", candidate)
os._exit(0)
"""


def run_build_crash(data_dir):
    child = os.path.join(tempfile.mkdtemp(), "build_crash_child.py")
    open(child, "w", encoding="utf-8").write(_BUILD_CRASH_CHILD)
    r = subprocess.run([sys.executable, child, ROOT, data_dir], capture_output=True)
    shutil.rmtree(os.path.dirname(child), ignore_errors=True)
    return r.returncode


base = tempfile.mkdtemp()
try:
    data = os.path.join(base, "data")
    make_prod(data, n=3)
    orig = tree_sig(data)
    cand, backup = collect.promotion_paths(data)
    rc = run_build_crash(data)
    check("H) build_candidate 중 강제 종료됨 (Python 예외 아님)", rc != 0, f"returncode={rc}")
    check("H) production 무접촉", os.path.isdir(data) and tree_sig(data) == orig)
    check("H) candidate 고아가 남음", os.path.isdir(cand))
    check("H) backup은 생기지 않음", not os.path.isdir(backup))
    state = collect.recover_promotion_state(data)
    check("H) 다음 startup이 state E로 정리", state == "E.candidate_cleaned", state)
    check("H) candidate 제거됨", not os.path.isdir(cand))
    check("H) production 여전히 원본", tree_sig(data) == orig)
    cleanup_promo(data)
finally:
    shutil.rmtree(base, ignore_errors=True)


# ------------------------------------------------------- P19 계측 (구군별 분해)
print("\n[P19-INSTR] district_stats — 구군별 손실 원인 분해")

def _it(name, road, lot):
    return {"BPLC_NM": name, "ROAD_NM_ADDR": road, "LOTNO_ADDR": lot,
            "SALS_STTS_CD": "01", "SALS_STTS_NM": "영업/정상", "APLY_YMD": "2026-01-01"}

# 강남: 정상 3 + duplicate 2 + contradiction 1  → 6 / 2 / 4 / 1 / 3
GN_A = _it("정상A", "서울특별시 강남구 테헤란로 1", "서울특별시 강남구 역삼동 1")
FIX_GANGNAM = [
    GN_A, GN_A, GN_A,                                                    # dedupe 2건 제거
    _it("정상B", "서울특별시 강남구 테헤란로 2", "서울특별시 강남구 역삼동 2"),
    _it("정상C", "서울특별시 강남구 테헤란로 3", "서울특별시 강남구 역삼동 3"),
    # road 는 강남 → 강남으로 분류되지만 lot 이 전남이라 저장 직전 격리된다
    _it("모순", "서울특별시 강남구 테헤란로 9", "전라남도 강진군 강진읍 1"),
]
# 해운대: 정상 2 + duplicate 1 + contradiction 0  → 3 / 1 / 2 / 0 / 2
HD_A = _it("해운대A", "부산광역시 해운대구 해운대로 1", "부산광역시 해운대구 우동 1")
FIX_HAEUNDAE = [
    HD_A, HD_A,
    _it("해운대B", "부산광역시 해운대구 해운대로 2", "부산광역시 해운대구 우동 2"),
]

before_repo = data_fingerprint(os.path.join(ROOT, "data"))
tmp = tempfile.mkdtemp()
try:
    ws = os.path.join(tmp, "cand")
    stats = collect.build_candidate(FIX_GANGNAM + FIX_HAEUNDAE, "2026-09-04", ws)
    ds = stats["district_stats"]

    # ── 핵심 fixture: 6 / 2 / 4 / 1 / 3
    gn = ds.get("seoul/gangnam")
    check("INSTR) 강남 district_stats 존재", gn is not None, str(sorted(ds)[:5]))
    check("INSTR) 강남 classified_before_dedupe = 6",
          gn and gn["classified_before_dedupe"] == 6, str(gn))
    check("INSTR) 강남 duplicates_removed = 2", gn and gn["duplicates_removed"] == 2, str(gn))
    check("INSTR) 강남 after_dedupe = 4", gn and gn["after_dedupe"] == 4, str(gn))
    check("INSTR) 강남 contradictions_removed = 1 (재할당 전 계측)",
          gn and gn["contradictions_removed"] == 1, str(gn))
    check("INSTR) 강남 final = 3", gn and gn["final"] == 3, str(gn))

    # ── B) 여러 구군이 서로 오염되지 않음
    hd = ds.get("busan/haeundae")
    check("INSTR-B) 해운대 3 / 1 / 2 / 0 / 2",
          hd == {"classified_before_dedupe": 3, "duplicates_removed": 1, "after_dedupe": 2,
                 "contradictions_removed": 0, "final": 2}, str(hd))
    others = {k: v for k, v in ds.items()
              if k not in ("seoul/gangnam", "busan/haeundae") and any(v.values())}
    check("INSTR-B) 나머지 구군은 전부 0 (오염 없음)", not others, str(list(others)[:5]))

    # ── A) 0건 구군도 5개 값 전부 0으로 존재
    total_districts = sum(len(v) for v in collect.DISTRICT_SLUG_MAP.values())
    check("INSTR-A) 전체 구군이 district_stats 에 존재",
          len(ds) == total_districts, f"{len(ds)} != {total_districts}")
    zeros = ds.get("jeju/jejusi")
    check("INSTR-A) 0건 구군도 5개 값 0으로 존재",
          zeros == {"classified_before_dedupe": 0, "duplicates_removed": 0, "after_dedupe": 0,
                    "contradictions_removed": 0, "final": 0}, str(zeros))
    check("INSTR-A) 모든 항목이 5개 키를 갖춤",
          all(set(v) == {"classified_before_dedupe", "duplicates_removed", "after_dedupe",
                         "contradictions_removed", "final"} for v in ds.values()))

    # ── 구군 단위 reconciliation 두 등식
    bad = [k for k, v in ds.items()
           if v["classified_before_dedupe"] != v["duplicates_removed"] + v["after_dedupe"]]
    check("INSTR) 구군: classified = duplicates + after_dedupe", not bad, str(bad[:5]))
    bad = [k for k, v in ds.items()
           if v["after_dedupe"] != v["contradictions_removed"] + v["final"]]
    check("INSTR) 구군: after_dedupe = contradictions + final", not bad, str(bad[:5]))

    # ── 전국 합계가 기존 stats 와 일치 (unmatched 는 귀속하지 않는다)
    S = lambda f: sum(v[f] for v in ds.values())
    check("INSTR) Σ classified_before_dedupe == stats.dedupe_input",
          S("classified_before_dedupe") == stats["dedupe_input"],
          f"{S('classified_before_dedupe')} != {stats['dedupe_input']}")
    check("INSTR) Σ duplicates_removed == stats.duplicates_removed",
          S("duplicates_removed") == stats["duplicates_removed"],
          f"{S('duplicates_removed')} != {stats['duplicates_removed']}")
    check("INSTR) Σ after_dedupe == stats.verified_input",
          S("after_dedupe") == stats["verified_input"],
          f"{S('after_dedupe')} != {stats['verified_input']}")
    check("INSTR) Σ contradictions_removed == stats.contradictions",
          S("contradictions_removed") == stats["contradictions"],
          f"{S('contradictions_removed')} != {stats['contradictions']}")
    check("INSTR) Σ final == stats.final",
          S("final") == stats["final"], f"{S('final')} != {stats['final']}")
    check("INSTR) unmatched 는 구군에 귀속되지 않음 (전국 회계에만)",
          stats["active"] - stats["unmatched_total"] == S("classified_before_dedupe"),
          f"active {stats['active']} - unmatched {stats['unmatched_total']} "
          f"!= Σ {S('classified_before_dedupe')}")

    # ── C) 계측값이 candidate 트리로 새어 나가지 않음
    leaked = []
    for dp, _, fns in os.walk(ws):
        for fn in fns:
            if not fn.endswith(".json"):
                continue
            raw = open(os.path.join(dp, fn), encoding="utf-8").read()
            for k in ("district_stats", "classified_before_dedupe", "duplicates_removed",
                      "after_dedupe", "contradictions_removed"):
                if k in raw:
                    leaked.append(f"{fn}:{k}")
    check("INSTR-C) 계측 키가 candidate 파일에 기록되지 않음", not leaked, str(leaked[:5]))

    # ── D) 게이트 A–G 가 계측 전과 동일하게 동작
    rep, plan = collect.integrity.validate_candidate(
        ws, os.path.join(tmp, "no-such-prod"), stats, collect.verify_store_location)
    check("INSTR-D) A–G 통과 (계측이 게이트 판정에 영향 없음)", rep.ok, rep.summary())
    check("INSTR-D) bootstrap 이므로 G.total_wipe 미발화",
          not any(c == "G.total_wipe" for c, _ in rep.failures))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

check("INSTR-F) production data checksum 무변경",
      before_repo == data_fingerprint(os.path.join(ROOT, "data")))


# ------------------------------------------------- P19 catastrophic-drop guard
print("\n[P19-GUARD] G 급감 가드 — S1~S24 시나리오 매트릭스")

# 2026-09-04 SAFETY dry-run 의 실제 (district, production, candidate) 229개.
# 이 fixture 가 새 게이트를 하나도 발화시키지 않아야 한다 — 우리가 가진
# 유일한 정상 표본이므로, 여기서 발화하면 정상 수집이 매번 막힌다.
REAL_20260904 = [
    ("busan/bsbukgu",1,1), ("busan/bsdonggu",597,596), ("busan/bsgangseo",138,138),
    ("busan/bsjunggu",356,290), ("busan/bsnamgu",503,503), ("busan/bsseogu",2,4),
    ("busan/busanjin",321,321), ("busan/dongnae",239,239), ("busan/geumjeong",17,17),
    ("busan/gijang",87,86), ("busan/haeundae",331,329), ("busan/saha",155,155),
    ("busan/sasang",462,462), ("busan/suyeong",489,489), ("busan/yeongdo",465,465),
    ("busan/yeonje",1,1), ("chungbuk/boeun",167,167), ("chungbuk/cheongju",973,973),
    ("chungbuk/chungju",3,3), ("chungbuk/danyang",119,120), ("chungbuk/eumseong",1,1),
    ("chungbuk/goesan",101,103), ("chungbuk/jecheon",591,591), ("chungbuk/jeungpyeong",168,168),
    ("chungbuk/jincheon",116,116), ("chungbuk/okcheon",121,124), ("chungbuk/yeongdong",12,12),
    ("chungnam/asan",1160,1171), ("chungnam/boryeong",582,582), ("chungnam/buyeo",0,0),
    ("chungnam/cheonan",1152,1151), ("chungnam/cheongyang",0,0), ("chungnam/dangjin",0,0),
    ("chungnam/geumsan",515,517), ("chungnam/gongju",22,22), ("chungnam/gyeryong",86,94),
    ("chungnam/hongseong",208,205), ("chungnam/nonsan",497,497), ("chungnam/seocheon",121,122),
    ("chungnam/seosan",4,4), ("chungnam/taean",199,199), ("chungnam/yesan",254,264),
    ("daegu/dalseo",1296,1296), ("daegu/dalseong",230,230), ("daegu/dgbukgu",931,934),
    ("daegu/dgdonggu",832,831), ("daegu/dgjunggu",482,482), ("daegu/dgnamgu",10,10),
    ("daegu/dgseogu",448,448), ("daegu/gunwi",44,44), ("daegu/suseong",471,470),
    ("daejeon/daedeok",607,607), ("daejeon/djdonggu",4,4), ("daejeon/djjunggu",1310,1310),
    ("daejeon/djseogu",11,11), ("daejeon/yuseong",284,284), ("gangwon/cheorwon",149,149),
    ("gangwon/chuncheon",125,124), ("gangwon/donghae",133,142), ("gangwon/gangneung",507,519),
    ("gangwon/gwgoseong",0,0), ("gangwon/hoengseong",129,129), ("gangwon/hongcheon",259,259),
    ("gangwon/hwacheon",36,37), ("gangwon/inje",43,47), ("gangwon/jeongseon",13,13),
    ("gangwon/pyeongchang",170,170), ("gangwon/samcheok",81,81), ("gangwon/sokcho",22,22),
    ("gangwon/taebaek",52,54), ("gangwon/wonju",1531,1556), ("gangwon/yanggu",205,205),
    ("gangwon/yangyang",12,12), ("gangwon/yeongwol",343,346), ("gwangju/gjbukgu",665,666),
    ("gwangju/gjdonggu",567,566), ("gwangju/gjnamgu",527,479), ("gwangju/gjseogu",754,754),
    ("gwangju/gwangsan",11,13), ("gyeongbuk/andong",111,111), ("gyeongbuk/bonghwa",127,127),
    ("gyeongbuk/cheongdo",242,246), ("gyeongbuk/cheongsong",112,112),
    ("gyeongbuk/chilgok",210,210), ("gyeongbuk/gimcheon",324,324),
    ("gyeongbuk/goryeong",230,230), ("gyeongbuk/gumi",1063,1063),
    ("gyeongbuk/gyeongju",1078,1081), ("gyeongbuk/gyeongsan",56,56),
    ("gyeongbuk/mungyeong",409,409), ("gyeongbuk/pohang",511,511), ("gyeongbuk/sangju",102,102),
    ("gyeongbuk/seongju",28,29), ("gyeongbuk/uiseong",201,203), ("gyeongbuk/uljin",139,138),
    ("gyeongbuk/ulleung",47,47), ("gyeongbuk/yecheon",132,133),
    ("gyeongbuk/yeongcheon",488,488), ("gyeongbuk/yeongdeok",206,206),
    ("gyeongbuk/yeongju",298,305), ("gyeongbuk/yeongyang",89,89), ("gyeonggi/ansan",992,992),
    ("gyeonggi/anseong",411,411), ("gyeonggi/anyang",25,26), ("gyeonggi/bucheon",2,2),
    ("gyeonggi/dongducheon",352,352), ("gyeonggi/gapyeong",304,308), ("gyeonggi/ggwangju",4,4),
    ("gyeonggi/gimpo",1227,1233), ("gyeonggi/goyang",1793,1806), ("gyeonggi/gunpo",433,432),
    ("gyeonggi/guri",247,247), ("gyeonggi/gwacheon",166,166), ("gyeonggi/gwangmyeong",303,323),
    ("gyeonggi/hanam",23,22), ("gyeonggi/hwaseong",1738,1630), ("gyeonggi/icheon",2,1),
    ("gyeonggi/namyangju",907,1002), ("gyeonggi/osan",421,422), ("gyeonggi/paju",901,901),
    ("gyeonggi/pocheon",4,4), ("gyeonggi/pyeongtaek",1141,1141), ("gyeonggi/seongnam",11,11),
    ("gyeonggi/siheung",1,1), ("gyeonggi/suwon",41,39), ("gyeonggi/uijeongbu",935,949),
    ("gyeonggi/uiwang",184,192), ("gyeonggi/yangju",4,4), ("gyeonggi/yangpyeong",227,227),
    ("gyeonggi/yeoju",585,585), ("gyeonggi/yeoncheon",108,108), ("gyeonggi/yongin",1682,1680),
    ("gyeongnam/changnyeong",113,113), ("gyeongnam/changwon",430,429),
    ("gyeongnam/geochang",187,187), ("gyeongnam/geoje",540,550), ("gyeongnam/gimhae",1397,1397),
    ("gyeongnam/gsngoseong",7,7), ("gyeongnam/hadong",6,6), ("gyeongnam/haman",133,133),
    ("gyeongnam/hamyang",5,5), ("gyeongnam/hapcheon",1,1), ("gyeongnam/jinju",563,562),
    ("gyeongnam/miryang",1,1), ("gyeongnam/namhae",256,256), ("gyeongnam/sacheon",99,99),
    ("gyeongnam/sancheong",36,34), ("gyeongnam/tongyeong",1,0), ("gyeongnam/uiryeong",194,193),
    ("gyeongnam/yangsan",786,786), ("incheon/bupyeong",369,368), ("incheon/ganghwa",193,193),
    ("incheon/gyeyang",10,10), ("incheon/icdonggu",1,1), ("incheon/icjunggu",82,82),
    ("incheon/icseogu",3,3), ("incheon/michuhol",84,84), ("incheon/namdong",2,1),
    ("incheon/ongjin",76,76), ("incheon/yeonsu",325,325), ("jeju/jejusi",201,201),
    ("jeju/seogwipo",614,618), ("jeonbuk/buan",270,279), ("jeonbuk/gimje",79,80),
    ("jeonbuk/gochang",223,238), ("jeonbuk/gunsan",662,662), ("jeonbuk/iksan",318,318),
    ("jeonbuk/imsil",215,218), ("jeonbuk/jangsu",45,47), ("jeonbuk/jeongeup",478,483),
    ("jeonbuk/jeonju",1880,1916), ("jeonbuk/jinan",127,128), ("jeonbuk/muju",175,176),
    ("jeonbuk/namwon",340,339), ("jeonbuk/sunchang",12,15), ("jeonbuk/wanju",315,318),
    ("jeonnam/boseong",357,357), ("jeonnam/damyang",296,296), ("jeonnam/gangjin",117,85),
    ("jeonnam/goheung",353,356), ("jeonnam/gokseong",273,273), ("jeonnam/gurye",152,153),
    ("jeonnam/gwangyang",293,292), ("jeonnam/haenam",282,281), ("jeonnam/hampyeong",175,175),
    ("jeonnam/hwasun",438,437), ("jeonnam/jangheung",237,237), ("jeonnam/jangseong",218,218),
    ("jeonnam/jindo",384,384), ("jeonnam/mokpo",22,21), ("jeonnam/muan",104,104),
    ("jeonnam/naju",462,468), ("jeonnam/sinan",56,56), ("jeonnam/suncheon",455,448),
    ("jeonnam/wando",364,364), ("jeonnam/yeongam",277,277), ("jeonnam/yeonggwang",331,331),
    ("jeonnam/yeosu",1090,1090), ("sejong/sejongsi",165,165), ("seoul/dobong",4,4),
    ("seoul/dongdaemun",813,812), ("seoul/dongjak",1,1), ("seoul/eunpyeong",70,70),
    ("seoul/gangbuk",0,0), ("seoul/gangdong",3,3), ("seoul/gangnam",31,30),
    ("seoul/gangseo",3,2), ("seoul/geumcheon",47,47), ("seoul/guro",4,4), ("seoul/gwanak",6,6),
    ("seoul/gwangjin",86,86), ("seoul/jongno",632,639), ("seoul/junggu",24,24),
    ("seoul/jungnang",0,0), ("seoul/mapo",602,536), ("seoul/nowon",89,87),
    ("seoul/seocho",291,291), ("seoul/seodaemun",4,4), ("seoul/seongbuk",394,394),
    ("seoul/seongdong",5,6), ("seoul/songpa",0,0), ("seoul/yangcheon",2,2),
    ("seoul/yeongdeungpo",5,5), ("seoul/yongsan",2,1), ("ulsan/ulju",0,0),
    ("ulsan/usbukgu",104,104), ("ulsan/usdonggu",154,154), ("ulsan/usjunggu",270,270),
    ("ulsan/usnamgu",857,857)
]


def mkplan(pairs, removed=None):
    """[(key, prod, cand)] → check_drop_guard 가 받는 plan 형태."""
    pd = {k: p for k, p, _ in pairs}
    cd = {k: c for k, _, c in pairs}
    pr, cr = {}, {}
    for k, p, c in pairs:
        rs = k.split("/")[0]
        pr[rs] = pr.get(rs, 0) + p
        cr[rs] = cr.get(rs, 0) + c
    return {"created": [], "removed": removed or [], "modified": [], "kept": [],
            "prod_files": len(pd), "cand_files": sum(1 for _, _, c in pairs if c > 0),
            "prod_stores": sum(pd.values()), "cand_stores": sum(cd.values()),
            "prod_regions": pr, "cand_regions": cr,
            "prod_districts": pd, "cand_districts": cd}


def guard(pairs, stats=None, removed=None):
    """발화한 실패 코드 집합을 돌려준다."""
    rep = collect.integrity.IntegrityReport("scenario")
    collect.integrity.check_drop_guard(mkplan(pairs, removed), stats or {}, rep)
    return sorted(c for c, _ in rep.failures)


def scen(name, pairs, expect, stats=None):
    got = guard(pairs, stats)
    if expect == "PASS":
        check(f"{name} → PASS", got == [], f"발화: {got}")
    else:
        ok = bool(got) and all(e in got for e in expect)
        check(f"{name} → BLOCK {expect}", ok, f"발화: {got}")
    return got


REAL = [(d, p, c) for d, p, c in REAL_20260904]
by = {d: (p, c) for d, p, c in REAL}

# ── S1 현재 정상 candidate → 발화 0
got = scen("S1 정상(오늘 실측 229개)", REAL, "PASS")
check("S1) prod 69,265 / cand 69,292 확인",
      sum(p for _, p, _ in REAL) == 69265 and sum(c for _, _, c in REAL) == 69292)

# ── S7~S10, S13: 정상 표본 안의 개별 사례가 S1 PASS 에 포함됨
for nm, key, ep, ec in [("S7/S13 통영 1→0(contradiction)", "gyeongnam/tongyeong", 1, 0),
                        ("S8 강진 117→85", "jeonnam/gangjin", 117, 85),
                        ("S9 마포 602→536", "seoul/mapo", 602, 536),
                        ("S10 화성 1738→1630", "gyeonggi/hwaseong", 1738, 1630)]:
    check(f"{nm} fixture 확인", by[key] == (ep, ec), str(by.get(key)))
check("S7~S10) 위 사례가 포함된 S1 이 PASS (오탐 0)", got == [], str(got))

# ── S2 전체 0
scen("S2 전체 0", [(d, p, 0) for d, p, _ in REAL],
     ["G.total_wipe", "G.national_drop", "G.region_drop", "G.district_drop",
      "G.district_extinction", "G.mass_drop"])

# ── S3 전체 1
s3 = [(d, p, 1 if d == "seoul/gangnam" else 0) for d, p, _ in REAL]
got3 = scen("S3 전체 1", s3, ["G.national_drop", "G.region_drop", "G.district_drop"])
check("S3) candidate 1건이라 G.total_wipe 는 발화 안 함", "G.total_wipe" not in got3, str(got3))

# ── S4 서울 전체 소실
scen("S4 서울 전체 소실", [(d, p, 0 if d.startswith("seoul/") else c) for d, p, c in REAL],
     ["G.region_drop"])
check("S4) 전국 감소율은 -4.4% 수준이라 전국 게이트만으로는 못 잡음",
      (sum(c for d, _, c in REAL if not d.startswith("seoul/")) - 69265) / 69265 > -0.25)

# ── S5 경기 -30%
scen("S5 경기 -30%", [(d, p, int(p * 0.7) if d.startswith("gyeonggi/") else c) for d, p, c in REAL],
     ["G.region_drop"])

# ── S6 최대 district 전체 소실
big = max(REAL, key=lambda x: x[1])[0]
scen(f"S6 최대 district({big}) 소실",
     [(d, p, 0 if d == big else c) for d, p, c in REAL],
     ["G.district_drop", "G.district_extinction"])

# ── S11 상위 50개 district 각 -8%
top50 = {d for d, _, _ in sorted(REAL, key=lambda x: -x[1])[:50]}
got11 = scen("S11 상위 50개 각 -8%", [(d, p, int(p * 0.92) if d in top50 else c) for d, p, c in REAL],
             ["G.mass_drop"])
check("S11) 개별 district 규칙만으로는 못 잡음 (mass_drop 이 유일)",
      got11 == ["G.mass_drop"], str(got11))

# ── S12 dedupe 대량 회귀: 원인 분해로 면제되지 않아야 한다
fake_ds = {d: {"classified_before_dedupe": p, "duplicates_removed": p - p // 10,
               "after_dedupe": p // 10, "contradictions_removed": 0, "final": p // 10}
           for d, p, _ in REAL}
got12 = scen("S12 dedupe 회귀로 90% 소실 (raw 정상)",
             [(d, p, p // 10) for d, p, _ in REAL],
             ["G.national_drop", "G.region_drop", "G.district_drop"],
             stats={"district_stats": fake_ds})
check("S12) 원인이 100% dedupe 여도 면제되지 않음", "G.national_drop" in got12, str(got12))

# ── S14 한 시도 거의 전멸 (제주 -90%), 전국 영향은 작음
scen("S14 제주 -90%", [(d, p, int(p * 0.1) if d.startswith("jeju/") else c) for d, p, c in REAL],
     ["G.region_drop"])

# ── S15 D1 수정의 이유: 300 → 160
scen("S15 단일 구군 300→160 (-140/-46.7%)",
     [("x/a", 300, 160), ("x/b", 5000, 5000)], ["G.district_drop"])

# ── S16 비율 <10% 인데 절대 500건
scen("S16 대형 구군 -500건 / 비율 <10%",
     [("x/a", 6000, 5500), ("x/b", 60000, 60000)], ["G.district_drop"])

# ── S17~S19 D1 경계
scen("S17 99건 감소 + 20%", [("x/a", 495, 396), ("x/b", 50000, 50000)], "PASS")
scen("S18 100건 감소 + 9.99%", [("x/a", 1001, 901), ("x/b", 50000, 50000)], "PASS")
scen("S19 100건 감소 + 10.00%", [("x/a", 1000, 900), ("x/b", 50000, 50000)],
     ["G.district_drop"])

# ── S20~S21 R1 경계
scen("S20 시도 29건 감소 + 50%", [("x/a", 58, 29), ("y/b", 50000, 50000)], "PASS")
scen("S21 시도 30건 감소 + 10.00%", [("x/a", 300, 270), ("y/b", 50000, 50000)],
     ["G.region_drop"])

# ── S22~S24 AGG 경계
def mass(n, loss, prod):
    """n 개 district 를 각각 prod→prod-loss 로. 비율 <10% 라 D1 은 발화하지 않는다."""
    out = [(f"m{i}/d", prod, prod - loss) for i in range(n)]
    out.append(("pad/d", 400000, 400000))       # 전국·시도 게이트 회피용 패딩
    return out
# mass() 가 이미 pad 를 붙인다. 예전에는 여기서 한 번 더 append 해서 같은 키가
# 두 번 들어갔고, dict comprehension 인 prod_districts 는 400,000 으로 합쳐지는데
# 루프 누적인 prod_regions 는 800,000 이 되어 정합하지 않은 트리를 나타냈다.
# 판정에는 영향이 없었지만(prod·cand 가 같이 두 배라 감소 0) fixture 를 고친다.
# AGG 임계값 자체는 건드리지 않는다.
s22 = mass(13, 143, 1589) + [("m13/d", 1556, 1416)]
scen("S22 material 14개 / 합계 1999", s22, "PASS")
scen("S23 material 15개 / 합계 1950", mass(15, 130, 1445), ["G.mass_drop"])
s24 = mass(13, 143, 1589) + [("m13/d", 1567, 1426)]
scen("S24 material 14개 / 합계 2000", s24, ["G.mass_drop"])

# ── 전국 게이트 경계
# 전국 게이트 경계는 코드 단위로 본다. 이만한 손실이면 구군 게이트도 함께
# 발화하는 게 정상이므로(층이 겹치는 설계), 여기서는 G.national_drop 만 본다.
def scen_code(name, pairs, code, present):
    got = guard(pairs)
    check(f"{name} → {code} {'발화' if present else '미발화'}",
          (code in got) == present, f"발화: {got}")

# N2 에는 절대량 하한을 두지 않는다. production 이 작다는 이유로 25%·50%·90%
# 축소를 허용할 이유가 없고, 그 구간을 다른 계층이 본다는 설명은 성립하지 않는다
# (3 -> 1 은 R1 >=30건 / D1 >=100건 / D2 >=20건 / AGG >=20건 어디에도 안 걸린다).
scen_code("N2-A production 3 → candidate 1 (-66.67%)", [("x/a", 3, 1)],
          "G.national_drop", True)
got_a = guard([("x/a", 3, 1)])
check("N2-A) 다른 계층은 이 규모를 잡지 못함 (N2 가 유일)",
      got_a == ["G.national_drop"], f"발화: {got_a}")
scen_code("N2-B production 4 → candidate 3 (정확히 -25%)", [("x/a", 4, 3)],
          "G.national_drop", True)
scen_code("N2-C production 10000 → 7501 (-24.99%)", [("x/a", 10000, 7501)],
          "G.national_drop", False)
scen_code("N2-D production 10000 → 7500 (-25.00%)", [("x/a", 10000, 7500)],
          "G.national_drop", True)
scen("N2-E bootstrap production 0 → candidate 500", [("x/a", 0, 500)], "PASS")
# ── AGG material 판정 경계 (4.99% vs 5.00%)
scen("AGG 경계 4.99% (material 아님)",
     [(f"m{i}/d", 401, 381) for i in range(20)] + [("pad/d", 400000, 400000)], "PASS")
scen("AGG 경계 5.00% (material)",
     [(f"m{i}/d", 400, 380) for i in range(20)] + [("pad/d", 400000, 400000)],
     ["G.mass_drop"])

# ── D2 전멸 경계
scen("D2 경계 prod=19 전멸", [("x/a", 19, 0), ("x/b", 50000, 50000)], "PASS")
scen("D2 경계 prod=20 전멸", [("x/a", 20, 0), ("x/b", 50000, 50000)],
     ["G.district_extinction"])

# ── production=0 / 증가는 drop 대상 아님
scen("신규 district (prod=0)", [("x/a", 0, 500), ("x/b", 50000, 50000)], "PASS")
scen("전체 증가", [(d, p, p + 5) for d, p, _ in REAL], "PASS")

# ── bootstrap: production 자체가 없음
scen("bootstrap (production 0건)", [("x/a", 0, 100)], "PASS")

# ── 실제 트리로 plan 레벨 집계가 생성되는지 (end-to-end)
tmp = tempfile.mkdtemp()
try:
    ws = os.path.join(tmp, "cand")
    prod = os.path.join(tmp, "prod")
    # rollback/promotion mechanics fixture; not intended to exercise
    # catastrophic-drop guard. production 3건 -> candidate 3건(감소 0%).
    make_prod(prod, n=3)
    stats = collect.build_candidate(GOOD3, "2026-09-04", ws)
    rep, plan = collect.integrity.validate_candidate(ws, prod, stats,
                                                    collect.verify_store_location)
    check("GUARD-E2E) plan 에 시도/구군 레벨 집계 포함",
          all(k in plan for k in ("prod_regions", "cand_regions",
                                  "prod_districts", "cand_districts")), str(sorted(plan)))
    check("GUARD-E2E) prod_districts 가 실제 production 을 읽음",
          plan["prod_districts"].get("seoul/gangnam") == 3,
          str(plan["prod_districts"]))
    check("GUARD-E2E) prod 3건 → cand 3건 (감소 0%) 은 게이트 통과", rep.ok, rep.summary())
finally:
    shutil.rmtree(tmp, ignore_errors=True)

check("GUARD) 기존 G.total_wipe 코드명 유지",
      "G.total_wipe" in guard([("x/a", 10, 0), ("x/b", 10, 0)]))


# ---------------------------------------------------------------- 자기 검사
# 요약 블록은 반드시 파일의 마지막이어야 한다. 뒤에 check()가 붙으면
# 그 검사는 집계·exit code에 반영되지 않는다. 2026-09-03에 이 실수를
# 두 번 했다(P17.8 추가 시, P3-13 추가 시). 그래서 구조로 막는다.
_self_src = open(os.path.abspath(__file__), encoding="utf-8").read()
# 기준 문자열을 조립한다. 리터럴로 쓰면 이 가드 자신이 오탐된다.
_summary_marker = 'print(f"PASS {len(' + 'PASS)} / FAIL'
_after_summary = _self_src.split(_summary_marker, 1)[-1]
_summary_tail_ok = "check(" not in _after_summary
check(
    "요약 블록 이후에 검사가 없음 (게이트 무력화 방지)",
    _summary_tail_ok,
    ""
    if _summary_tail_ok
    else "요약 블록 뒤에 check() 호출이 있다. 그 검사는 exit code에 반영되지 않는다.\n"
    "        새 검사는 요약 블록 '앞'에 넣어라.",
)

# 위 리터럴 스캔은 1차 방어일 뿐이다. 실제 방어는 런타임 계측(_final_gate)이며,
# 아래에서 판정 로직과 종단 배선을 각각 검증한다.
check("SELF) 요약 미실행을 게이트가 잡는다", _gate_verdict(10, None) is not None)
check("SELF) 요약 이후 추가 검사를 게이트가 잡는다", _gate_verdict(11, 10) is not None)
check("SELF) 정상 종료는 게이트를 통과한다", _gate_verdict(10, 10) is None)

# 종단 검증: 실제 자식 프로세스에서 요약 앞 sys.exit(0) 을 재현하고, atexit 게이트가
# exit code 를 1 로 뒤집는지 본다. 리터럴 스캔이 절대 잡지 못하는 경로다.
_self_child = subprocess.run(
    [sys.executable, os.path.abspath(__file__)],
    env={**os.environ, "TEST_COLLECT_SELFTEST": "early_exit"},
    capture_output=True, text=True,
)
_self_ok = _self_child.returncode != 0
_self_msg = "GATE FAIL" in _self_child.stdout
check("SELF) 요약 전 sys.exit(0) 이 exit 1 로 뒤집힌다",
      _self_ok, "" if _self_ok else f"returncode={_self_child.returncode}")
# detail 은 실패할 때만 넘긴다. check() 는 PASS 에서도 detail 을 출력하므로
# 자식 stdout 을 그대로 주면 자식의 GATE FAIL 메시지가 부모 출력에 섞여
# 이후 진단을 오독하게 만든다.
check("SELF) 그 때 GATE FAIL 사유가 출력된다",
      _self_msg, "" if _self_msg else _self_child.stdout[-200:])


# ---------------------------------------------------------------- 결과
# 이 블록은 반드시 파일 맨 끝에 있어야 한다. 중간에 있으면 뒤쪽 검사가
# 실패해도 exit code가 0이 되어 커밋 게이트가 무력해진다.
print("\n" + "=" * 60)
# 이 시점의 검사 수를 기록한다. 프로세스 종료 시 _final_gate 가 실제 실행된
# 검사 수와 비교해, 요약 이후에 실행된 검사가 있으면 exit 1 로 뒤집는다.
_gate["summary_count"] = len(PASS) + len(FAIL)
print(f"PASS {len(PASS)} / FAIL {len(FAIL)}")
if FAIL:
    for f in FAIL:
        print(f"  FAILED: {f}")
    sys.exit(1)
print("모든 안전장치 테스트 통과")
