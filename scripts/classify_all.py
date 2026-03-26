"""
_unmatched.json의 전국 데이터를 시/도별로 분류
API 호출 없이 기존 데이터만으로 전국 완성
"""

import json
import os
import re

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
REGIONS_TS = os.path.join(os.path.dirname(__file__), "..", "lib", "regions.ts")

REGION_NAMES = {
    "서울특별시": "seoul", "부산광역시": "busan", "대구광역시": "daegu",
    "인천광역시": "incheon", "광주광역시": "gwangju", "대전광역시": "daejeon",
    "울산광역시": "ulsan", "세종특별자치시": "sejong", "경기도": "gyeonggi",
    "강원특별자치도": "gangwon", "충청북도": "chungbuk", "충청남도": "chungnam",
    "전북특별자치도": "jeonbuk", "전라남도": "jeonnam", "경상북도": "gyeongbuk",
    "경상남도": "gyeongnam", "제주특별자치도": "jeju",
    # 구 명칭 호환
    "강원도": "gangwon", "전라북도": "jeonbuk",
}

SLUG_TO_NAME = {v: k for k, v in REGION_NAMES.items() if "_" not in k and "도" not in k or k in [
    "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시",
    "대전광역시", "울산광역시", "세종특별자치시", "경기도", "강원특별자치도",
    "충청북도", "충청남도", "전북특별자치도", "전라남도", "경상북도", "경상남도", "제주특별자치도",
]}


def load_district_map():
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


def extract_parts(address):
    if not address:
        return None, None
    parts = address.strip().split()
    if len(parts) < 2:
        return parts[0] if parts else None, None
    return parts[0], parts[1]


def main():
    district_map = load_district_map()

    # _unmatched.json 로드
    unmatched_path = os.path.join(BASE_DIR, "_unmatched.json")
    with open(unmatched_path, "r", encoding="utf-8") as f:
        unmatched = json.load(f)
    print(f"Loaded {len(unmatched)} unmatched stores")

    # 시/도별 → 구별 분류
    # region_slug -> district_slug -> [stores]
    classified = {}
    still_unmatched = []

    for store in unmatched:
        addr = store.get("roadAddress") or store.get("address", "")
        sido, district = extract_parts(addr)

        region_slug = REGION_NAMES.get(sido) if sido else None
        if not region_slug:
            still_unmatched.append(store)
            continue

        name_to_slug = district_map.get(region_slug, {})
        slug = None

        if district and district.endswith(("구", "군", "시")):
            slug = name_to_slug.get(district)
            if not slug:
                for name, s in name_to_slug.items():
                    if district in name or name in district:
                        slug = s
                        break

        if not slug:
            still_unmatched.append(store)
            continue

        if region_slug not in classified:
            classified[region_slug] = {}
        if slug not in classified[region_slug]:
            classified[region_slug][slug] = []
        classified[region_slug][slug].append(store)

    # 결과 저장
    today = "2026-03-26"
    total_all = 0

    for region_slug, districts in sorted(classified.items()):
        region_name = SLUG_TO_NAME.get(region_slug, region_slug)
        name_to_slug = district_map.get(region_slug, {})
        slug_to_name = {v: k for k, v in name_to_slug.items()}

        data_dir = os.path.join(BASE_DIR, region_slug)
        os.makedirs(data_dir, exist_ok=True)

        # 기존 데이터 병합
        existing_districts = {}
        for fname in os.listdir(data_dir):
            if fname == "index.json" or not fname.endswith(".json"):
                continue
            fpath = os.path.join(data_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                d = json.load(f)
            dslug = fname.replace(".json", "")
            existing_districts[dslug] = d.get("stores", [])

        # 새 데이터 병합
        for dslug, stores in districts.items():
            if dslug in existing_districts:
                existing_districts[dslug].extend(stores)
            else:
                existing_districts[dslug] = stores

        # 저장
        districts_meta = []
        region_total = 0

        for name, slug in sorted(name_to_slug.items(), key=lambda x: x[1]):
            stores = existing_districts.get(slug, [])
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

        print(f"  {region_name}: {region_total}곳")
        total_all += region_total

    # 서울은 이미 있으니 합산
    seoul_index = os.path.join(BASE_DIR, "seoul", "index.json")
    with open(seoul_index) as f:
        seoul_total = json.load(f).get("totalCount", 0)
    total_all += seoul_total

    # regions.json 갱신
    region_order = [
        "seoul", "busan", "daegu", "incheon", "gwangju", "daejeon", "ulsan",
        "sejong", "gyeonggi", "gangwon", "chungbuk", "chungnam", "jeonbuk",
        "jeonnam", "gyeongbuk", "gyeongnam", "jeju",
    ]
    regions_list = []
    grand_total = 0
    for slug in region_order:
        idx_path = os.path.join(BASE_DIR, slug, "index.json")
        count = 0
        rname = slug
        if os.path.exists(idx_path):
            with open(idx_path) as f:
                idx = json.load(f)
                count = idx.get("totalCount", 0)
                rname = idx.get("region", slug)
        regions_list.append({"region": rname, "regionSlug": slug, "count": count})
        grand_total += count

    with open(os.path.join(BASE_DIR, "regions.json"), "w", encoding="utf-8") as f:
        json.dump({"updatedAt": today, "totalCount": grand_total, "regions": regions_list},
                  f, ensure_ascii=False, indent=2)

    # 남은 unmatched 저장
    with open(unmatched_path, "w", encoding="utf-8") as f:
        json.dump(still_unmatched, f, ensure_ascii=False, indent=2)

    print(f"\n전국 총: {grand_total}곳")
    print(f"남은 미매칭: {len(still_unmatched)}건")
    print("Done!")


if __name__ == "__main__":
    main()
