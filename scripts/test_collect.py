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
import shutil
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
print("\n[4] API totalCount=0 정상 응답 → 완결로 인정, stale 삭제 허용")
collect.fetch_page = lambda k, n: make_page([], 0)
try:
    items, calls, total = collect.fetch_all("KEY")
    check("totalCount=0은 완결로 인정", items == [] and total == 0)
except Exception as e:
    check("totalCount=0은 완결로 인정", False, f"예외 발생: {e}")

tmp = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(tmp, "seoul"))
    stale = os.path.join(tmp, "seoul", "gangnam.json")
    with open(stale, "w", encoding="utf-8") as f:
        json.dump({"totalCount": 1, "stores": []}, f)
    collect.classify_and_save([], "2026-09-03", complete=True, data_dir=tmp)
    check("complete=True면 stale 파일 삭제", not os.path.exists(stale))

    with open(stale, "w", encoding="utf-8") as f:
        json.dump({"totalCount": 1, "stores": []}, f)
    collect.classify_and_save([], "2026-09-03", complete=False, data_dir=tmp)
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
ALLOWED_SCRIPTS = {"collect.py", "test_collect.py"}

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


# ---------------------------------------------------------------- 결과
# 이 블록은 반드시 파일 맨 끝에 있어야 한다. 중간에 있으면 뒤쪽 검사가
# 실패해도 exit code가 0이 되어 커밋 게이트가 무력해진다.
print("\n" + "=" * 60)
print(f"PASS {len(PASS)} / FAIL {len(FAIL)}")
if FAIL:
    for f in FAIL:
        print(f"  FAILED: {f}")
    sys.exit(1)
print("모든 안전장치 테스트 통과")
