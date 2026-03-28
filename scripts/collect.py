"""
종량제 봉투 판매처 데이터 수집 스크립트 (v2)

변경: 1회 수집 → 주소 기반 전체 분류 (localCode 반복 호출 제거)
분류: 주소 파싱 기반 (시/도 → 구/군/시)
중복: name + address 기준 dedupe
미매칭: _unmatched.json에 저장 (데이터 손실 없음)

사용법:
  python3 scripts/collect.py --key YOUR_KEY
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

# 시/도 정규화 매핑
REGION_NORMALIZE = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
    # 이전 명칭
    "강원도": "강원특별자치도",
    "전라북도": "전북특별자치도",
}

REGION_NAME_TO_SLUG = {
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


def fetch_page(service_key: str, page_no: int) -> dict | None:
    params = urllib.parse.urlencode({
        "serviceKey": service_key,
        "pageNo": page_no,
        "numOfRows": NUM_OF_ROWS,
        "type": "json",
        "localCode": "6110000_ALL",
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


def fetch_all(service_key: str) -> tuple[list[dict], int]:
    """전국 데이터 1회 수집"""
    all_items = []
    page_no = 1
    calls = 0

    while True:
        if page_no % 50 == 1:
            log.info(f"  page {page_no}...")
        data = fetch_page(service_key, page_no)
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


def normalize_region(addr: str) -> str | None:
    """주소에서 시/도명 추출 + 정규화"""
    if not addr:
        return None
    parts = addr.strip().split()
    if not parts:
        return None
    region_part = parts[0]
    # 정확 매칭
    if region_part in REGION_NAME_TO_SLUG:
        return region_part
    # 정규화
    normalized = REGION_NORMALIZE.get(region_part)
    if normalized:
        return normalized
    # 부분 매칭 (예: "충청남" → "충청남도")
    for short, full in REGION_NORMALIZE.items():
        if region_part.startswith(short):
            return full
    return None


def extract_district(addr: str, region_name: str | None = None) -> str | None:
    """주소에서 구/군/시명 추출. 세종은 구 없이 읍/면 단위 → '세종시'로 매핑"""
    if not addr:
        return None
    if region_name == "세종특별자치시":
        return "세종시"
    parts = addr.strip().split()
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


def dedupe_stores(stores: list[dict]) -> list[dict]:
    """name + address 기준 중복 제거"""
    seen = set()
    result = []
    for s in stores:
        key = (s["name"], s["address"])
        if key not in seen:
            seen.add(key)
            result.append(s)
    return result


def classify_and_save(items: list[dict], updated_at: str):
    """전국 데이터를 주소 기반으로 분류 + 저장"""
    # 1. Filter active only
    active = [i for i in items if str(i.get("SALS_STTS_CD", "")) == "01"]
    log.info(f"Active (영업/정상): {len(active)}/{len(items)}")

    # 2. Transform + classify
    # region_slug -> district_slug -> [stores]
    classified: dict[str, dict[str, list[dict]]] = {}
    unmatched: list[dict] = []

    for item in active:
        store = transform_item(item)
        addr = store["roadAddress"] or store["address"]

        # Region 매칭
        region_name = normalize_region(addr)
        if not region_name:
            unmatched.append(store)
            continue

        region_slug = REGION_NAME_TO_SLUG.get(region_name)
        if not region_slug:
            unmatched.append(store)
            continue

        # District 매칭
        district_name = extract_district(addr, region_name)
        name_to_slug = DISTRICT_SLUG_MAP.get(region_slug, {})
        district_slug = None

        if district_name:
            district_slug = name_to_slug.get(district_name)
            if not district_slug:
                for name, s in name_to_slug.items():
                    if district_name in name or name in district_name:
                        district_slug = s
                        break

        if not district_slug:
            unmatched.append(store)
            continue

        if region_slug not in classified:
            classified[region_slug] = {}
        if district_slug not in classified[region_slug]:
            classified[region_slug][district_slug] = []
        classified[region_slug][district_slug].append(store)

    # 3. Dedupe per district
    total_before_dedupe = sum(
        sum(len(stores) for stores in districts.values())
        for districts in classified.values()
    )
    for region_slug in classified:
        for district_slug in classified[region_slug]:
            classified[region_slug][district_slug] = dedupe_stores(
                classified[region_slug][district_slug]
            )
    total_after_dedupe = sum(
        sum(len(stores) for stores in districts.values())
        for districts in classified.values()
    )
    log.info(f"Dedupe: {total_before_dedupe} → {total_after_dedupe} ({total_before_dedupe - total_after_dedupe} removed)")

    # 4. Save unmatched
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    if unmatched:
        unmatched_path = os.path.join(data_dir, "_unmatched.json")
        with open(unmatched_path, "w", encoding="utf-8") as f:
            json.dump(unmatched, f, ensure_ascii=False, indent=2)
        log.info(f"Unmatched: {len(unmatched)} → _unmatched.json")

    # 5. Save per region/district
    total_all = 0
    regions_list = []

    for region_slug, name_to_slug in sorted(DISTRICT_SLUG_MAP.items()):
        region_name = None
        for rn, rs in REGION_NAME_TO_SLUG.items():
            if rs == region_slug:
                region_name = rn
                break

        region_dir = os.path.join(data_dir, region_slug)
        os.makedirs(region_dir, exist_ok=True)

        districts_meta = []
        region_total = 0

        for district_name, district_slug in sorted(name_to_slug.items(), key=lambda x: x[1]):
            stores = classified.get(region_slug, {}).get(district_slug, [])
            count = len(stores)
            districts_meta.append({
                "district": district_name,
                "districtSlug": district_slug,
                "count": count,
            })
            region_total += count

            if stores:
                district_data = {
                    "region": region_name,
                    "regionSlug": region_slug,
                    "district": district_name,
                    "districtSlug": district_slug,
                    "updatedAt": updated_at,
                    "totalCount": count,
                    "stores": stores,
                }
                filepath = os.path.join(region_dir, f"{district_slug}.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(district_data, f, ensure_ascii=False, indent=2)

            if count > 0:
                log.info(f"  {region_name} {district_name}: {count}곳")

        # index.json
        index = {
            "region": region_name,
            "regionSlug": region_slug,
            "updatedAt": updated_at,
            "totalCount": region_total,
            "districts": districts_meta,
        }
        with open(os.path.join(region_dir, "index.json"), "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        regions_list.append({"region": region_name, "regionSlug": region_slug, "count": region_total})
        total_all += region_total
        log.info(f"  === {region_name} 완료: {region_total}곳 ===")

    # 6. regions.json
    with open(os.path.join(data_dir, "regions.json"), "w", encoding="utf-8") as f:
        json.dump({"updatedAt": updated_at, "totalCount": total_all, "regions": regions_list},
                  f, ensure_ascii=False, indent=2)
    log.info(f"\nregions.json updated: total {total_all}")

    return total_all


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    args = parser.parse_args()

    load_district_slugs()
    today = time.strftime("%Y-%m-%d")

    # 1회 수집
    log.info("=" * 50)
    log.info("전국 데이터 1회 수집 시작")
    log.info("=" * 50)
    items, calls = fetch_all(args.key)
    log.info(f"수집 완료: {len(items)}건, {calls} API calls")

    # 분류 + 저장
    log.info("=" * 50)
    log.info("주소 기반 분류 시작")
    log.info("=" * 50)
    total = classify_and_save(items, today)

    log.info(f"\nDone! Total: {total}곳, API calls: {calls}")


if __name__ == "__main__":
    main()
