"""
전체 데이터 재분류 (API 호출 없음)

1. 모든 district JSON + _unmatched.json에서 store 전부 수거
2. 주소 normalize
3. 시/도 먼저 확정 → 그 안에서 구/군/시 매칭
4. 전체 JSON 재생성
"""

import json
import os
import re

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
REGIONS_TS = os.path.join(os.path.dirname(__file__), "..", "lib", "regions.ts")

# ── 시/도 매핑 (정식 + 축약 + 구명칭) ──
REGION_NAMES = {
    "서울특별시": "seoul",
    "부산광역시": "busan",
    "대구광역시": "daegu",
    "인천광역시": "incheon",
    "광주광역시": "gwangju",
    "대전광역시": "daejeon",
    "울산광역시": "ulsan",
    "세종특별자치시": "sejong",
    "경기도": "gyeonggi",
    "강원특별자치도": "gangwon",
    "충청북도": "chungbuk",
    "충청남도": "chungnam",
    "전북특별자치도": "jeonbuk",
    "전라남도": "jeonnam",
    "경상북도": "gyeongbuk",
    "경상남도": "gyeongnam",
    "제주특별자치도": "jeju",
    # 구 명칭
    "강원도": "gangwon",
    "전라북도": "jeonbuk",
}

SLUG_TO_REGION_NAME = {
    "seoul": "서울특별시", "busan": "부산광역시", "daegu": "대구광역시",
    "incheon": "인천광역시", "gwangju": "광주광역시", "daejeon": "대전광역시",
    "ulsan": "울산광역시", "sejong": "세종특별자치시", "gyeonggi": "경기도",
    "gangwon": "강원특별자치도", "chungbuk": "충청북도", "chungnam": "충청남도",
    "jeonbuk": "전북특별자치도", "jeonnam": "전라남도", "gyeongbuk": "경상북도",
    "gyeongnam": "경상남도", "jeju": "제주특별자치도",
}

# ── 주소 normalize 규칙 ──
NORMALIZE_RULES = [
    ("서울 ", "서울특별시 "),
    ("부산 ", "부산광역시 "),
    ("대구 ", "대구광역시 "),
    ("인천 ", "인천광역시 "),
    ("광주 ", "광주광역시 "),
    ("대전 ", "대전광역시 "),
    ("울산 ", "울산광역시 "),
    ("세종 ", "세종특별자치시 "),
    # "~시" 축약
    ("서울시 ", "서울특별시 "),
    ("부산시 ", "부산광역시 "),
    ("대구시 ", "대구광역시 "),
    ("인천시 ", "인천광역시 "),
    ("광주시 ", "광주광역시 "),
    ("대전시 ", "대전광역시 "),
    ("울산시 ", "울산광역시 "),
    ("세종시 ", "세종특별자치시 "),
    # 옛 지명
    ("충청남도 연기군 ", "세종특별자치시 "),
]


def normalize_address(addr: str) -> str:
    if not addr:
        return addr
    for old, new in NORMALIZE_RULES:
        if addr.startswith(old):
            addr = new + addr[len(old):]
            break
    return addr


def load_district_map() -> dict[str, dict[str, str]]:
    """regions.ts에서 regionSlug -> {district_name: slug} 로드"""
    with open(REGIONS_TS, "r", encoding="utf-8") as f:
        content = f.read()
    district_map = {}
    pattern = r'\{\s*name:\s*"([^"]+)",\s*slug:\s*"([^"]+)",\s*regionSlug:\s*"([^"]+)"'
    for match in re.finditer(pattern, content):
        name, slug, region_slug = match.groups()
        if region_slug not in district_map:
            district_map[region_slug] = {}
        district_map[region_slug][name] = slug
    return district_map


def collect_all_stores() -> list[dict]:
    """모든 district JSON + _unmatched.json에서 store 전부 수거"""
    all_stores = []
    seen = set()  # 중복 방지 (name + address)

    def add_store(store):
        key = (store.get("name", ""), store.get("address", ""), store.get("roadAddress", ""))
        if key not in seen:
            seen.add(key)
            all_stores.append(store)

    # district JSON files
    for region_dir in sorted(os.listdir(BASE_DIR)):
        region_path = os.path.join(BASE_DIR, region_dir)
        if not os.path.isdir(region_path) or region_dir.startswith("_"):
            continue
        for fname in os.listdir(region_path):
            if fname == "index.json" or not fname.endswith(".json"):
                continue
            fpath = os.path.join(region_path, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for store in data.get("stores", []):
                add_store(store)

    # _unmatched.json
    um_path = os.path.join(BASE_DIR, "_unmatched.json")
    if os.path.exists(um_path):
        with open(um_path, "r", encoding="utf-8") as f:
            for store in json.load(f):
                add_store(store)

    return all_stores


def classify_store(store, district_map):
    """
    STRICT ORDER:
    1. normalize address
    2. extract REGION
    3. extract DISTRICT inside that region
    """
    addr = store.get("roadAddress") or store.get("address", "")
    addr = normalize_address(addr)

    if not addr:
        return None, None

    parts = addr.strip().split()
    if not parts:
        return None, None

    # STEP 1: region 확정
    sido = parts[0]
    region_slug = REGION_NAMES.get(sido)
    if not region_slug:
        return None, None

    # STEP 2: 세종 특수 처리 (구 없음 → 전부 sejongsi)
    if region_slug == "sejong":
        return region_slug, "sejongsi"

    # STEP 3: district 추출 (region 안에서만)
    if len(parts) < 2:
        return None, None

    candidate = parts[1]
    name_to_slug = district_map.get(region_slug, {})

    if candidate.endswith(("구", "군", "시")):
        # 정확 매칭
        slug = name_to_slug.get(candidate)
        if slug:
            return region_slug, slug

        # 부분 매칭 (region 안에서만!)
        for name, s in name_to_slug.items():
            if candidate in name or name in candidate:
                return region_slug, s

    return None, None


def main():
    district_map = load_district_map()

    # 1. 전체 store 수거
    print("Collecting all stores...")
    all_stores = collect_all_stores()
    print(f"  Total unique stores: {len(all_stores)}")

    # 2. 재분류
    # region_slug -> district_slug -> [stores]
    classified = {}
    unmatched = []

    for store in all_stores:
        region_slug, district_slug = classify_store(store, district_map)
        if region_slug and district_slug:
            classified.setdefault(region_slug, {}).setdefault(district_slug, []).append(store)
        else:
            unmatched.append(store)

    matched_count = sum(
        sum(len(stores) for stores in districts.values())
        for districts in classified.values()
    )
    print(f"  Matched: {matched_count}")
    print(f"  Unmatched: {len(unmatched)}")

    # 3. JSON 재생성
    today = "2026-03-26"
    region_order = [
        "seoul", "busan", "daegu", "incheon", "gwangju", "daejeon", "ulsan",
        "sejong", "gyeonggi", "gangwon", "chungbuk", "chungnam", "jeonbuk",
        "jeonnam", "gyeongbuk", "gyeongnam", "jeju",
    ]

    grand_total = 0
    regions_list = []

    for region_slug in region_order:
        region_name = SLUG_TO_REGION_NAME[region_slug]
        name_to_slug = district_map.get(region_slug, {})
        region_districts = classified.get(region_slug, {})

        data_dir = os.path.join(BASE_DIR, region_slug)
        os.makedirs(data_dir, exist_ok=True)

        # 기존 district JSON 삭제 (깨끗하게 재생성)
        for fname in os.listdir(data_dir):
            if fname.endswith(".json"):
                os.remove(os.path.join(data_dir, fname))

        districts_meta = []
        region_total = 0

        for name, slug in sorted(name_to_slug.items(), key=lambda x: x[1]):
            stores = region_districts.get(slug, [])
            districts_meta.append({
                "district": name,
                "districtSlug": slug,
                "count": len(stores),
            })
            region_total += len(stores)

            if stores:
                district_data = {
                    "region": region_name,
                    "regionSlug": region_slug,
                    "district": name,
                    "districtSlug": slug,
                    "updatedAt": today,
                    "totalCount": len(stores),
                    "stores": stores,
                }
                filepath = os.path.join(data_dir, f"{slug}.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(district_data, f, ensure_ascii=False, indent=2)

        # index.json
        index = {
            "region": region_name,
            "regionSlug": region_slug,
            "updatedAt": today,
            "totalCount": region_total,
            "districts": districts_meta,
        }
        with open(os.path.join(data_dir, "index.json"), "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        regions_list.append({
            "region": region_name,
            "regionSlug": region_slug,
            "count": region_total,
        })
        grand_total += region_total

        # 0건 구 표시
        zero_districts = [d["district"] for d in districts_meta if d["count"] == 0]
        zero_str = f"  (0건: {', '.join(zero_districts)})" if zero_districts else ""
        print(f"  {region_name}: {region_total:>6d}곳{zero_str}")

    # regions.json
    with open(os.path.join(BASE_DIR, "regions.json"), "w", encoding="utf-8") as f:
        json.dump({"updatedAt": today, "totalCount": grand_total, "regions": regions_list},
                  f, ensure_ascii=False, indent=2)

    # _unmatched.json
    um_path = os.path.join(BASE_DIR, "_unmatched.json")
    with open(um_path, "w", encoding="utf-8") as f:
        json.dump(unmatched, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"전국 총: {grand_total}곳")
    print(f"미매칭: {len(unmatched)}건")
    print(f"매칭률: {matched_count / (matched_count + len(unmatched)) * 100:.2f}%")

    # 미매칭 샘플
    if unmatched:
        print(f"\n미매칭 샘플 (최대 10건):")
        for s in unmatched[:10]:
            addr = s.get("roadAddress") or s.get("address", "")
            print(f"  {s.get('name', '?')}: {addr[:60]}")

    print("\nDone!")


if __name__ == "__main__":
    main()
