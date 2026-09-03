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
import sys
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


class CollectionError(RuntimeError):
    """수집이 완결됐음을 증명하지 못한 상태.

    이 예외가 발생하면 저장 단계에 절대 진입하지 않는다. 기존 data/ 파일은
    한 건도 쓰이거나 삭제되지 않는다. (fail closed)
    """


def fetch_all(service_key: str) -> tuple[list[dict], int, int]:
    """전국 데이터 1회 수집.

    반환: (items, api_calls, expected_total)

    부분 수집을 정상 반환하지 않는다. 네트워크/파싱 실패와 "데이터가 정상적으로
    끝남"을 같은 값으로 표현하지 않는다 - 전자는 CollectionError로 중단시킨다.
    수집 건수가 API totalCount와 일치할 때만 정상 반환한다.
    """
    all_items = []
    page_no = 1
    calls = 0
    expected_total: int | None = None
    pages_needed: int | None = None

    while True:
        if page_no % 50 == 1:
            log.info(f"  page {page_no}...")
        data = fetch_page(service_key, page_no)
        calls += 1

        if not data:
            # 재시도 소진. 정상 종료가 아니다.
            raise CollectionError(
                f"page {page_no} 응답 실패 (재시도 {MAX_RETRIES}회 소진). "
                f"{len(all_items)}건 수집 후 중단."
            )

        try:
            body = data["response"]["body"]
            items = body.get("items", [])
            if isinstance(items, dict):
                items = items.get("item", [])
            if isinstance(items, dict):
                items = [items]
            total_count = int(body.get("totalCount", 0))
        except (KeyError, TypeError, ValueError) as e:
            raise CollectionError(
                f"page {page_no} 응답 파싱 실패: {e}. {len(all_items)}건 수집 후 중단."
            ) from e

        if expected_total is None:
            expected_total = total_count
            # 페이지 크기는 요청값(NUM_OF_ROWS)이 아니라 첫 응답의 실제 반환 개수로
            # 계산한다. 이 API는 numOfRows=1000을 요청해도 100건만 돌려준다(실측).
            # 요청값을 믿으면 필요한 페이지 수를 10분의 1로 잘못 계산해 수집이
            # 조기 종료된다.
            page_size = len(items) if items else NUM_OF_ROWS
            pages_needed = (expected_total + page_size - 1) // page_size
            log.info(
                f"  totalCount={expected_total}, page_size={page_size}(실측), "
                f"pages={pages_needed}"
            )

        if not items:
            # 아직 받을 페이지가 남아 있는데 빈 응답이면 정상 종료로 취급하지 않는다.
            if page_no <= pages_needed:
                raise CollectionError(
                    f"page {page_no}/{pages_needed} 빈 응답. "
                    f"예상 {expected_total}건 중 {len(all_items)}건만 수집."
                )
            break

        all_items.extend(items)

        # 종료 판정은 수집 건수 기준이다. 페이지 수는 안전 상한으로만 쓴다.
        if len(all_items) >= expected_total:
            break

        page_no += 1
        if page_no > pages_needed:
            raise CollectionError(
                f"예상 페이지 {pages_needed}를 넘겼는데 "
                f"{len(all_items)}/{expected_total}건. 페이지 크기 가정이 틀렸다."
            )
        time.sleep(0.2)

    if expected_total is None:
        raise CollectionError("API totalCount를 한 번도 확보하지 못했다.")

    if len(all_items) != expected_total:
        raise CollectionError(
            f"수집 건수 불일치: API totalCount={expected_total}, "
            f"실제 수집={len(all_items)}"
        )

    log.info(f"  완결성 검증 통과: {len(all_items)} == totalCount {expected_total}")
    return all_items, calls, expected_total


# ────────────────────────────────────────────────────────────────────────
# 통합 시도 대응 (2026-07-01 전남광주통합특별시 출범).
#
# 종전 전라남도 + 광주광역시가 하나의 시도로 통합되어 API 주소가
# "전남광주통합특별시 남구 …" 형태로 온다. 시도 이름 앞부분으로 판정하면
# "전남"으로 시작한다는 이유만으로 전라남도에 흡수되고, 광주 5개 구는
# 매칭에 실패해 통째로 폐기된다.
#
# 하위 행정구역 이름을 완전 일치로 대조해 논리적으로 다시 분리한다.
# 부분 문자열 판정은 쓰지 않는다 - 광양시(전남)나 경기도 광주시가
# 오분류된다. 광주 5구와 전남 22시군은 이름이 겹치지 않는다(검증됨).
# ────────────────────────────────────────────────────────────────────────
MERGED_SIDO_TOKENS = {"전남광주통합특별시", "전남광주"}

# 미등록 시도 토큰 판별용. 한국의 시/도는 전부 이 접미사로 끝난다.
# "안양시"처럼 평범한 '시'는 시도 단위에 존재하지 않으므로 깨진 주소로 본다.
SIDO_SUFFIXES = ("특별시", "광역시", "특별자치시", "특별자치도")


def classify_unknown_sido(token: str) -> str:
    """미등록 시도 토큰을 분류한다.

    new_region_token  - 행정구역 개편으로 보이는 새 시도명. 저장을 중단해야 한다.
    malformed_address - 시도가 빠졌거나 깨진 주소. 집계 후 넘어간다.
    """
    if not token or any(ch.isdigit() for ch in token):
        return "malformed_address"
    if token.endswith(SIDO_SUFFIXES):
        return "new_region_token"
    if token.endswith("도") and len(token) >= 3:
        return "new_region_token"
    return "malformed_address"


def resolve_merged_sido(parts: list[str]) -> tuple[str | None, str | None]:
    """통합 시도 주소를 하위 행정구역 완전 일치로 논리 분리한다.

    반환: (시도명, 구군명). 어느 집합에도 없으면 (None, None).
    집합은 lib/regions.ts에서 로드한 DISTRICT_SLUG_MAP을 그대로 쓴다(SSOT 단일화).
    """
    gwangju = DISTRICT_SLUG_MAP.get("gwangju", {})
    jeonnam = DISTRICT_SLUG_MAP.get("jeonnam", {})
    if not gwangju or not jeonnam:
        raise CollectionError(
            "load_district_slugs() 미실행 - 통합 시도를 분리할 수 없다."
        )
    # 앞 3개 토큰만 본다. 통합 표기 변형이 있어도 구군 토큰이 이 안에 든다.
    for token in parts[1:4]:
        if token in gwangju:
            return "광주광역시", token
        if token in jeonnam:
            return "전라남도", token
    return None, None


def normalize_region(addr: str) -> str | None:
    """주소에서 시/도명 추출 + 정규화.

    부분 매칭(startswith) fallback은 제거했다. 실측 결과 이 경로가 처리하던
    유일한 케이스가 "전남광주통합특별시" -> "전라남도" 오분류였고, 나머지
    22개 시도 토큰은 전부 정확 매칭이나 정규화표를 탄다. 모르는 지명을
    조용히 기존 지역으로 흡수하는 것보다 미매칭으로 드러나는 편이 안전하다.
    통합 시도는 resolve_merged_sido()가 따로 처리한다.
    """
    if not addr:
        return None
    parts = addr.strip().split()
    if not parts:
        return None
    region_part = parts[0]
    # 정확 매칭
    if region_part in REGION_NAME_TO_SLUG:
        return region_part
    # 정규화 (구 명칭 포함, 완전 일치만)
    return REGION_NORMALIZE.get(region_part)


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


def derive_location(addr: str) -> tuple[str | None, str | None]:
    """주소 문자열 하나에서 (시/도명, 구·군명)을 독립적으로 추출한다.

    저장 직전 검증 전용. 분류 결과를 참조하지 않고 주소만 보고 판정한다.
    통합 시도는 분류부와 같은 규칙으로 논리 분리한다.
    """
    if not addr:
        return None, None
    parts = addr.strip().split()
    if not parts:
        return None, None
    if parts[0] in MERGED_SIDO_TOKENS:
        return resolve_merged_sido(parts)
    region_name = normalize_region(addr)
    if not region_name:
        return None, None
    return region_name, extract_district(addr, region_name)


def verify_store_location(
    store: dict, expected_region: str, expected_district: str
) -> str | None:
    """매장이 기대한 지역/구군에 속하는지 독립 검증. 정상이면 None, 아니면 사유 문자열.

    roadAddress와 address를 둘 다 본다. 한쪽만 믿고 통과시키면
    지번은 전남 광양, 도로명은 서울 노원인 레코드가 서울 페이지에 실린다.
    """
    candidates = []
    for field in ("roadAddress", "address"):
        raw = (store.get(field) or "").strip()
        if not raw:
            continue
        region, district = derive_location(raw)
        if region:
            candidates.append((field, region, district))

    if not candidates:
        return "주소에서 시/도를 추출하지 못함"

    regions = {c[1] for c in candidates}
    if len(regions) > 1:
        return f"도로명/지번 시도 불일치: {sorted(regions)}"

    districts = {c[2] for c in candidates if c[2]}
    if len(districts) > 1:
        return f"도로명/지번 구군 불일치: {sorted(districts)}"

    derived_region = regions.pop()
    if derived_region != expected_region:
        return f"시/도 불일치: 기대={expected_region} 주소={derived_region}"

    if not districts:
        return "주소에서 구/군을 추출하지 못함"

    derived_district = districts.pop()
    if derived_district != expected_district:
        return f"구/군 불일치: 기대={expected_district} 주소={derived_district}"

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


def classify_and_save(
    items: list[dict],
    updated_at: str,
    complete: bool = False,
    data_dir: str | None = None,
):
    """전국 데이터를 주소 기반으로 분류 + 저장.

    complete=False면 stale 파일 삭제를 수행하지 않는다. 수집이 완결됐다는
    사실을 증명한 실행에서만 True로 호출할 것. data_dir은 테스트용 주입점이다.
    """
    # 1. Filter active only
    active = [i for i in items if str(i.get("SALS_STTS_CD", "")) == "01"]
    log.info(f"Active (영업/정상): {len(active)}/{len(items)}")

    # 2. Transform + classify
    # region_slug -> district_slug -> [stores]
    classified: dict[str, dict[str, list[dict]]] = {}
    unmatched: list[dict] = []
    # "regionSlug/구군명" -> 건수. 정확 매칭 실패 집계용 (매핑 테이블 보강 근거)
    unmatched_districts: dict[str, int] = {}
    # 저장 직전 지역 검증에서 격리된 매장 (사유 포함)
    rejected_stores: list[str] = []
    # 시도가 빠졌거나 깨진 주소. 행정구역 개편과 성격이 달라 별도 집계한다.
    malformed_addresses: list[str] = []

    for item in active:
        store = transform_item(item)
        addr = store["roadAddress"] or store["address"]
        parts = addr.strip().split() if addr else []
        sido_token = parts[0] if parts else ""

        # Region 매칭
        forced_district = None
        if sido_token in MERGED_SIDO_TOKENS:
            # 통합 시도 - 하위 행정구역 완전 일치로 논리 분리
            region_name, forced_district = resolve_merged_sido(parts)
            if region_name is None:
                # 통합 시도인데 어느 집합에도 없다. 조용히 버리면 해당 구군이
                # count=0이 되어 stale 삭제로 파일까지 사라진다. 저장 전에 멈춘다.
                raise CollectionError(
                    f"통합 시도 '{sido_token}' 주소를 광주 5구/전남 22시군 어느 쪽으로도 "
                    f"분리하지 못했다: {' '.join(parts[:3])} "
                    f"(하위 행정구역 집합 갱신이 필요하다)"
                )
        else:
            region_name = normalize_region(addr)
            if not region_name:
                kind = classify_unknown_sido(sido_token)
                if kind == "new_region_token":
                    # 새 행정구역으로 보인다. 1건이라도 나오면 저장을 중단한다.
                    raise CollectionError(
                        f"미등록 시도 토큰 '{sido_token}' 발견 (행정구역 개편 가능성). "
                        f"매핑을 갱신하기 전에는 저장·삭제를 진행하지 않는다: "
                        f"{' '.join(parts[:3])}"
                    )
                malformed_addresses.append(
                    f"{store.get('name', '?')} | {' '.join(parts[:3])}"
                )
                unmatched.append(store)
                continue

        region_slug = REGION_NAME_TO_SLUG.get(region_name)
        if not region_slug:
            unmatched.append(store)
            continue

        # District 매칭
        district_name = forced_district or extract_district(addr, region_name)
        name_to_slug = DISTRICT_SLUG_MAP.get(region_slug, {})
        district_slug = None

        # 정확 매칭만 허용한다.
        # 부분 매칭 fallback은 "북구" → "강북구"처럼 다른 구로 조용히 오배치되어
        # 2026-03 seoul/gangbuk 오염(타 지역 1,779곳)을 만든 원인이므로 사용하지 않는다.
        # 매칭 실패는 _unmatched.json으로 보내고 로그로 드러낸다.
        if district_name:
            district_slug = name_to_slug.get(district_name)
            if not district_slug:
                key = f"{region_slug}/{district_name}"
                unmatched_districts[key] = unmatched_districts.get(key, 0) + 1

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
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    if unmatched:
        unmatched_path = os.path.join(data_dir, "_unmatched.json")
        with open(unmatched_path, "w", encoding="utf-8") as f:
            json.dump(unmatched, f, ensure_ascii=False, indent=2)
        log.info(f"Unmatched: {len(unmatched)} → _unmatched.json")

    if unmatched_districts:
        log.warning(
            f"정확 매칭 실패 구군 {len(unmatched_districts)}종 "
            f"(부분 매칭으로 때우지 말고 lib/regions.ts에 명시적으로 추가할 것)"
        )
        for key, cnt in sorted(unmatched_districts.items(), key=lambda x: -x[1]):
            log.warning(f"  {key}: {cnt}건")

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

            # 저장 직전 지역 일치 검증 (2026-03 seoul/gangbuk 오염 재발 방지).
            #
            # 분류에 쓴 값을 다시 비교하면 항등식이라 절대 발화하지 않는다.
            # verify_store_location()은 분류 결과를 참조하지 않고 주소만 보고
            # 시/도와 구/군을 독립 판정하며, roadAddress와 address를 둘 다 본다.
            verified = []
            for s in stores:
                reason = verify_store_location(s, region_name, district_name)
                if reason is None:
                    verified.append(s)
                else:
                    rejected_stores.append(
                        f"{region_slug}/{district_slug} | {s.get('name', '?')} | {reason}"
                    )
            if len(verified) != len(stores):
                log.error(
                    f"  지역 검증 실패로 제외: {region_name} {district_name} "
                    f"{len(stores) - len(verified)}건 (저장하지 않음)"
                )
                stores = verified

            count = len(stores)
            districts_meta.append({
                "district": district_name,
                "districtSlug": district_slug,
                "count": count,
            })
            region_total += count

            filepath = os.path.join(region_dir, f"{district_slug}.json")
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
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(district_data, f, ensure_ascii=False, indent=2)
            elif os.path.exists(filepath):
                # count가 0이 된 구군의 이전 회차 파일을 남기지 않는다.
                # index.json만 갱신되고 고아 파일이 살아남아 잘못된 페이지를
                # 서비스한 사례(seoul/gangbuk)가 있어 명시적으로 삭제한다.
                #
                # 단, 수집이 완결됐다고 증명된 실행에서만 지운다. 부분 수집에서
                # 삭제하면 네트워크 한 번 끊긴 것이 전국 데이터 소실이 된다.
                if complete:
                    os.remove(filepath)
                    log.warning(
                        f"  stale 파일 삭제: {region_slug}/{district_slug}.json (count=0)"
                    )
                else:
                    log.warning(
                        f"  stale 파일 보존(수집 미완결): {region_slug}/{district_slug}.json"
                    )

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

    if malformed_addresses:
        log.warning(f"시도 토큰이 깨진 주소 {len(malformed_addresses)}건 (개편 아님, 미매칭 처리):")
        for m in malformed_addresses[:20]:
            log.warning(f"  {m}")
        if len(malformed_addresses) > 20:
            log.warning(f"  ... 외 {len(malformed_addresses) - 20}건")

    if rejected_stores:
        log.error(f"지역 검증에서 격리된 매장 {len(rejected_stores)}건:")
        for r in rejected_stores[:50]:
            log.error(f"  {r}")
        if len(rejected_stores) > 50:
            log.error(f"  ... 외 {len(rejected_stores) - 50}건")

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
    try:
        items, calls, expected_total = fetch_all(args.key)
    except CollectionError as e:
        log.error("=" * 50)
        log.error(f"수집 미완결 — 저장 단계에 진입하지 않는다: {e}")
        log.error("기존 data/ 파일은 한 건도 변경·삭제되지 않았다.")
        log.error("=" * 50)
        # cron이 성공으로 오인하지 않도록 non-zero exit.
        sys.exit(1)

    log.info(f"수집 완료: {len(items)}건 (totalCount {expected_total}), {calls} API calls")

    # 분류 + 저장. 여기까지 왔다는 것은 수집이 완결됐다는 뜻이므로
    # stale 파일 삭제를 허용한다.
    log.info("=" * 50)
    log.info("주소 기반 분류 시작")
    log.info("=" * 50)
    try:
        total = classify_and_save(items, today, complete=True)
    except CollectionError as e:
        log.error("=" * 50)
        log.error(f"분류 중단 - 저장·삭제를 진행하지 않는다: {e}")
        log.error("기존 data/ 파일은 한 건도 변경·삭제되지 않았다.")
        log.error("=" * 50)
        sys.exit(1)

    log.info(f"\nDone! Total: {total}곳, API calls: {calls}")


if __name__ == "__main__":
    main()
