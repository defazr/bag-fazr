"""
이미 수집된 데이터를 주소 기반으로 재분류
API 재호출 없이 _unmatched.json + 기존 district JSON을 합쳐서 주소로 분류
"""

import json
import os
import re

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
REGIONS_TS = os.path.join(os.path.dirname(__file__), "..", "lib", "regions.ts")


def load_district_map() -> dict[str, dict[str, str]]:
    """regions.ts에서 regionSlug -> {district_name: slug} 매핑 로드"""
    with open(REGIONS_TS, "r", encoding="utf-8") as f:
        content = f.read()

    region_map: dict[str, dict[str, str]] = {}
    pattern = r'\{\s*name:\s*"([^"]+)",\s*slug:\s*"([^"]+)",\s*regionSlug:\s*"([^"]+)"'
    for match in re.finditer(pattern, content):
        name, slug, region_slug = match.groups()
        if region_slug not in region_map:
            region_map[region_slug] = {}
        region_map[region_slug][name] = slug

    return region_map


def load_region_names() -> dict[str, str]:
    """regions.ts에서 slug -> 한글명"""
    with open(REGIONS_TS, "r", encoding="utf-8") as f:
        content = f.read()
    names = {}
    pattern = r'\{\s*name:\s*"([^"]+)",\s*slug:\s*"([^"]+)",\s*apiCode:\s*"[^"]*_ALL"'
    for match in re.finditer(pattern, content):
        name, slug = match.groups()
        names[slug] = name
    return names


def extract_district(address: str) -> str | None:
    """주소에서 시/군/구명 추출"""
    if not address:
        return None
    parts = address.strip().split()
    if len(parts) < 2:
        return None
    candidate = parts[1]
    if candidate.endswith(("구", "군", "시")):
        return candidate
    return None


def extract_region(address: str) -> str | None:
    """주소에서 시/도명 추출"""
    if not address:
        return None
    parts = address.strip().split()
    return parts[0] if parts else None


def reclassify_region(region_slug: str, district_map: dict[str, str], region_name: str):
    """한 시/도의 모든 store를 주소 기반으로 재분류"""
    region_dir = os.path.join(BASE_DIR, region_slug)
    if not os.path.exists(region_dir):
        print(f"  SKIP: {region_dir} not found")
        return 0, 0

    # 1. 기존 모든 district JSON에서 store 수집
    all_stores = []
    for fname in os.listdir(region_dir):
        if fname == "index.json":
            continue
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(region_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        stores = data.get("stores", [])
        all_stores.extend(stores)

    # 2. _unmatched.json에서 이 region에 해당하는 것 추가
    unmatched_path = os.path.join(BASE_DIR, "_unmatched.json")
    remaining_unmatched = []
    if os.path.exists(unmatched_path):
        with open(unmatched_path, "r", encoding="utf-8") as f:
            unmatched = json.load(f)
        for store in unmatched:
            addr = store.get("roadAddress") or store.get("address", "")
            region_in_addr = extract_region(addr)
            if region_in_addr and region_in_addr == region_name:
                all_stores.append(store)
            else:
                remaining_unmatched.append(store)
        # unmatched 업데이트
        with open(unmatched_path, "w", encoding="utf-8") as f:
            json.dump(remaining_unmatched, f, ensure_ascii=False, indent=2)

    print(f"  Total stores to classify: {len(all_stores)}")

    # 3. 주소 기반 분류
    # name -> slug 매핑
    name_to_slug = district_map
    # slug -> name 역매핑
    slug_to_name = {v: k for k, v in name_to_slug.items()}

    grouped: dict[str, list[dict]] = {}
    unmatched_count = 0

    for store in all_stores:
        addr = store.get("roadAddress") or store.get("address", "")
        district_name = extract_district(addr)

        slug = None
        if district_name:
            slug = name_to_slug.get(district_name)
            # 부분 매칭
            if not slug:
                for name, s in name_to_slug.items():
                    if district_name in name or name in district_name:
                        slug = s
                        break

        if slug:
            if slug not in grouped:
                grouped[slug] = []
            grouped[slug].append(store)
        else:
            unmatched_count += 1

    # 4. 기존 district JSON 삭제 (index.json 제외)
    for fname in os.listdir(region_dir):
        if fname == "index.json":
            continue
        if fname.endswith(".json"):
            os.remove(os.path.join(region_dir, fname))

    # 5. 새 district JSON 저장
    today = "2026-03-26"
    districts_meta = []
    total = 0

    # 모든 district에 대해 (0건 포함)
    for name, slug in sorted(name_to_slug.items(), key=lambda x: x[1]):
        stores = grouped.get(slug, [])
        districts_meta.append({
            "district": name,
            "districtSlug": slug,
            "count": len(stores),
        })
        total += len(stores)

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
            filepath = os.path.join(region_dir, f"{slug}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(district_data, f, ensure_ascii=False, indent=2)
            print(f"    {name}: {len(stores)}곳")

    # 6. index.json 갱신
    index = {
        "region": region_name,
        "regionSlug": region_slug,
        "updatedAt": today,
        "totalCount": total,
        "districts": districts_meta,
    }
    with open(os.path.join(region_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"  → {region_name}: {total}곳 매칭, {unmatched_count}건 미매칭")
    return total, unmatched_count


def update_regions_json():
    """regions.json 갱신"""
    region_names = load_region_names()
    region_order = [
        "seoul", "busan", "daegu", "incheon", "gwangju", "daejeon", "ulsan",
        "sejong", "gyeonggi", "gangwon", "chungbuk", "chungnam", "jeonbuk",
        "jeonnam", "gyeongbuk", "gyeongnam", "jeju",
    ]
    total_all = 0
    regions_list = []
    for slug in region_order:
        name = region_names.get(slug, slug)
        index_path = os.path.join(BASE_DIR, slug, "index.json")
        count = 0
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                count = json.load(f).get("totalCount", 0)
        regions_list.append({"region": name, "regionSlug": slug, "count": count})
        total_all += count

    with open(os.path.join(BASE_DIR, "regions.json"), "w", encoding="utf-8") as f:
        json.dump({"updatedAt": "2026-03-26", "totalCount": total_all, "regions": regions_list},
                  f, ensure_ascii=False, indent=2)
    print(f"\nregions.json: total {total_all}")


def main():
    district_map = load_district_map()
    region_names = load_region_names()

    # 서울만 재분류 (현재 데이터 있는 곳)
    for region_slug in ["seoul"]:
        name = region_names.get(region_slug, region_slug)
        dm = district_map.get(region_slug, {})
        print(f"\n{'='*50}")
        print(f"Reclassifying {name} ({region_slug})")
        print(f"  Known districts: {len(dm)}")
        print(f"{'='*50}")
        reclassify_region(region_slug, dm, name)

    update_regions_json()
    print("\nDone!")


if __name__ == "__main__":
    main()
