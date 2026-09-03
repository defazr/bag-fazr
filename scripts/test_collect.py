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


# ---------------------------------------------------------------- 결과
print("\n" + "=" * 60)
print(f"PASS {len(PASS)} / FAIL {len(FAIL)}")
if FAIL:
    for f in FAIL:
        print(f"  FAILED: {f}")
    sys.exit(1)
print("모든 안전장치 테스트 통과")
