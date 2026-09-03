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
        collect.classify_and_save(GOOD, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    collect.integrity.validate_candidate = orig
    collect.promote_candidate = orig_promote
    check("1) integrity failure → CollectionError", raised is not None, raised or "예외 없음")
    check("1) promote_candidate 호출 0", not promoted["called"])
    check("1) production 트리 보존", tree_sig(tmp) == sig0)
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
tmp = tempfile.mkdtemp()
try:
    make_prod(tmp, n=3); sig0 = tree_sig(tmp)

    def drop_file(items, updated_at, workspace):
        st = orig_build(items, updated_at, workspace)
        os.remove(os.path.join(workspace, "seoul", "gangnam.json"))
        return st

    collect.build_candidate = drop_file
    raised = None
    try:
        collect.classify_and_save(GOOD, "2026-09-03", complete=True, data_dir=tmp)
    except collect.CollectionError as e:
        raised = str(e)
    collect.build_candidate = orig_build
    check("3) candidate 파일 누락 → FAIL", raised is not None, raised or "예외 없음")
    check("3) production 보존", tree_sig(tmp) == sig0)
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
        collect.classify_and_save(GOOD, "2026-09-03", complete=True, data_dir=tmp)
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
        collect.classify_and_save(GOOD, "2026-09-03", complete=True, data_dir=tmp)
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
    make_prod(tmp, region="busan", slug="bsjunggu", district="중구",
              region_name="부산광역시", n=5)
    stale = os.path.join(tmp, "busan", "bsjunggu.json")
    check("10) 사전조건: stale 파일 존재", os.path.exists(stale))
    total = collect.classify_and_save(GOOD, "2026-09-09", complete=True, data_dir=tmp)
    check("10) promotion 성공", total == 1, f"total={total}")
    check("10) candidate에 없던 stale 파일이 사라짐", not os.path.exists(stale))
    check("10) 새 파일 반영", os.path.exists(os.path.join(tmp, "seoul", "gangnam.json")))
    rep = collect.integrity.audit_tree(tmp, collect.verify_store_location, "promoted")
    check("10) 반영된 트리 3계층 일치", rep.ok, rep.summary())
    check("10) candidate workspace 잔여물 없음",
          not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(tmp)), ".data-candidate")))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ── 9. validator FAIL인데 exit 0이 되지 않음 (회귀 방지)
check("9) 게이트 실패는 CollectionError로만 표현된다 (silent pass 없음)",
      issubclass(collect.CollectionError, Exception))

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
