"""
종량제 봉투 판매처 데이터 수집 스크립트

분류: 주소 파싱 기반 (OPN_ATMY_GRP_CD 사용하지 않음)
미매칭: _unmatched.json에 무조건 저장 (데이터 손실 없음)

사용법:
  python3 scripts/collect.py --key YOUR_KEY --region seoul
  python3 scripts/collect.py --key YOUR_KEY  # 전체
"""

import argparse
import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scripts/collect.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

BASE_URL = "https://apis.data.go.kr/1741000/pay_as_you_throw_bag_retailers/info"
NUM_OF_ROWS = 1000
MAX_RETRIES = 3
RETRY_DELAY = 5
DAILY_LIMIT = 10000

REGIONS = {
    "seoul": ("서울특별시", "6110000_ALL"),
    "busan": ("부산광역시", "6260000_ALL"),
    "daegu": ("대구광역시", "6270000_ALL"),
    "incheon": ("인천광역시", "6280000_ALL"),
    "gwangju": ("광주광역시", "6290000_ALL"),
    "daejeon": ("대전광역시", "6300000_ALL"),
    "ulsan": ("울산광역시", "6310000_ALL"),
    "sejong": ("세종특별자치시", "5690000_ALL"),
    "gyeonggi": ("경기도", "6410000_ALL"),
    "gangwon": ("강원특별자치도", "6530000_ALL"),
    "chungbuk": ("충청북도", "6430000_ALL"),
    "chungnam": ("충청남도", "6440000_ALL"),
    "jeonbuk": ("전북특별자치도", "6540000_ALL"),
    "jeonnam": ("전라남도", "6460000_ALL"),
    "gyeongbuk": ("경상북도", "6470000_ALL"),
    "gyeongnam": ("경상남도", "6480000_ALL"),
    "jeju": ("제주특별자치도", "6500000_ALL"),
}

# regionSlug -> {district_name: slug}
DISTRICT_SLUG_MAP: dict[str, dict[str, str]] = {}


def load_district_slugs():
    """lib/regions.ts에서 district slug 매핑 로드"""
    regions_ts = os.path.join(os.path.dirname(__file__), "..", "lib", "regions.ts")
    with open(regions_ts, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r'\{\s*name:\s*"([^"]+)",\s*slug:\s*"([^"]+)",\s*regionSlug:\s*"([^"]+)"'
    for match in re.finditer(pattern, content):
        name, slug, region_slug = match.groups()
        if region_slug not in DISTRICT_SLUG_MAP:
            DISTRICT_SLUG_MAP[region_slug] = {}
        DISTRICT_SLUG_MAP[region_slug][name] = slug

    log.info(f"Loaded district slugs: {sum(len(v) for v in DISTRICT_SLUG_MAP.values())} districts in {len(DISTRICT_SLUG_MAP)} regions")


def fetch_page(service_key: str, local_code: str, page_no: int) -> dict | None:
    params = urllib.parse.urlencode({
        "serviceKey": service_key,
        "pageNo": page_no,
        "numOfRows": NUM_OF_ROWS,
        "type": "json",
        "localCode": local_code,
    })
    url = f"{BASE_URL}?{params}"

    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            log.warning(f"  Retry {attempt + 1}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    return None


def fetch_all_pages(service_key: str, local_code: str) -> tuple[list[dict], int]:
    all_items = []
    page_no = 1
    calls = 0

    while True:
        if page_no % 50 == 1:
            log.info(f"  page {page_no}...")
        data = fetch_page(service_key, local_code, page_no)
        calls += 1

        if not data:
            break

        try:
            body = data["response"]["body"]
            items = body.get("items", [])
            if isinstance(items, dict):
                items = items.get("item", [])
            if isinstance(items, dict):
                items = [items]
            total_count = int(body.get("totalCount", 0))
        except (KeyError, TypeError, ValueError) as e:
            log.error(f"Parse error: {e}")
            break

        if not items:
            break

        all_items.extend(items)

        if page_no == 1:
            pages_needed = (total_count + NUM_OF_ROWS - 1) // NUM_OF_ROWS
            log.info(f"  totalCount={total_count}, pages={pages_needed}")

        if len(all_items) >= total_count:
            break

        page_no += 1
        time.sleep(0.2)

    return all_items, calls


def extract_district(address: str) -> str | None:
    """주소에서 구/군/시명 추출: '서울특별시 강남구 ...' → '강남구'"""
    if not address:
        return None
    parts = address.strip().split()
    if len(parts) < 2:
        return None
    candidate = parts[1]
    if candidate.endswith(("구", "군", "시")):
        return candidate
    return None


def transform_item(item: dict) -> dict:
    """API 응답 → store 스키마"""
    return {
        "name": item.get("BPLC_NM", "이름 없음"),
        "address": item.get("LOTNO_ADDR", "") or item.get("LCTN", ""),
        "roadAddress": item.get("ROAD_NM_ADDR", ""),
        "status": item.get("SALS_STTS_NM", "영업/정상"),
        "licenseDate": item.get("APLY_YMD", ""),
    }


def save_unmatched(stores: list[dict]):
    """_unmatched.json에 append (기존 데이터 보존)"""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "_unmatched.json")
    existing = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    existing.extend(stores)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    log.info(f"  Saved {len(stores)} unmatched → _unmatched.json (total: {len(existing)})")


def process_region(service_key: str, region_slug: str, updated_at: str) -> int:
    """한 시/도 수집 + 주소 기반 분류 + 저장"""
    region_name, api_code = REGIONS[region_slug]
    name_to_slug = DISTRICT_SLUG_MAP.get(region_slug, {})
    slug_to_name = {v: k for k, v in name_to_slug.items()}

    # 1. Fetch
    log.info(f"Fetching {region_name} ({api_code})...")
    items, calls = fetch_all_pages(service_key, api_code)
    log.info(f"Fetched: {len(items)} items, {calls} API calls")

    # 2. Filter active
    active = [i for i in items if str(i.get("SALS_STTS_CD", "")) == "01"]
    log.info(f"Active (영업/정상): {len(active)}/{len(items)}")

    # 3. Transform + classify by ADDRESS
    grouped: dict[str, list[dict]] = {}  # slug -> stores
    unmatched: list[dict] = []

    for item in active:
        store = transform_item(item)
        addr = store["roadAddress"] or store["address"]
        district_name = extract_district(addr)

        slug = None
        if district_name:
            # 정확 매칭
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
            unmatched.append(store)

    matched_count = sum(len(v) for v in grouped.values())
    log.info(f"Matched: {matched_count}")
    log.info(f"Unmatched: {len(unmatched)}")

    # 4. Save unmatched (데이터 손실 방지)
    if unmatched:
        save_unmatched(unmatched)

    # 5. Save district JSONs
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", region_slug)
    os.makedirs(data_dir, exist_ok=True)

    districts_meta = []
    total_stores = 0

    for name, slug in sorted(name_to_slug.items(), key=lambda x: x[1]):
        stores = grouped.get(slug, [])
        districts_meta.append({
            "district": name,
            "districtSlug": slug,
            "count": len(stores),
        })
        total_stores += len(stores)

        if stores:
            district_data = {
                "region": region_name,
                "regionSlug": region_slug,
                "district": name,
                "districtSlug": slug,
                "updatedAt": updated_at,
                "totalCount": len(stores),
                "stores": stores,
            }
            filepath = os.path.join(data_dir, f"{slug}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(district_data, f, ensure_ascii=False, indent=2)
            log.info(f"    {name}: {len(stores)}곳")

    # 6. index.json
    index = {
        "region": region_name,
        "regionSlug": region_slug,
        "updatedAt": updated_at,
        "totalCount": total_stores,
        "districts": districts_meta,
    }
    with open(os.path.join(data_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    log.info(f"  === {region_name} 완료: {total_stores}곳 저장 ===")
    return calls


def update_regions_json(updated_at: str):
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    total_all = 0
    regions_list = []
    for slug in REGIONS:
        name = REGIONS[slug][0]
        index_path = os.path.join(data_dir, slug, "index.json")
        count = 0
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                count = json.load(f).get("totalCount", 0)
        regions_list.append({"region": name, "regionSlug": slug, "count": count})
        total_all += count

    with open(os.path.join(data_dir, "regions.json"), "w", encoding="utf-8") as f:
        json.dump({"updatedAt": updated_at, "totalCount": total_all, "regions": regions_list},
                  f, ensure_ascii=False, indent=2)
    log.info(f"regions.json updated: total {total_all}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--region", help="시/도 slug")
    args = parser.parse_args()

    load_district_slugs()
    today = time.strftime("%Y-%m-%d")
    total_calls = 0

    targets = [args.region] if args.region else list(REGIONS.keys())

    for slug in targets:
        if slug not in REGIONS:
            log.error(f"Unknown: {slug}")
            continue

        log.info(f"\n{'='*50}")
        log.info(f"{REGIONS[slug][0]} ({slug})")
        log.info(f"{'='*50}")

        calls = process_region(args.key, slug, today)
        total_calls += calls

        log.info(f"Total API calls so far: {total_calls}/{DAILY_LIMIT}")
        if total_calls > DAILY_LIMIT - 100:
            log.warning(f"Approaching limit! Stopping.")
            break

        time.sleep(1)

    update_regions_json(today)
    log.info(f"\nDone! Total API calls: {total_calls}")


if __name__ == "__main__":
    main()
