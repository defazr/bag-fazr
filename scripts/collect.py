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
import importlib.util
import json
import logging
import os
import shutil
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

# integrity.py는 순수 검증 모듈이다. collect.py가 어떤 방식으로 로드되든
# 같은 디렉터리의 파일을 그대로 읽어 쓴다. sys.path를 오염시키지 않는다.
_integrity_spec = importlib.util.spec_from_file_location(
    "bagfazr_integrity",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "integrity.py"),
)
integrity = importlib.util.module_from_spec(_integrity_spec)
_integrity_spec.loader.exec_module(integrity)

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


# 공공데이터포털이 정상 응답에 쓰는 성공 sentinel. 이 서비스의 실제 정상
# header는 아직 확보하지 못했다(저장소·로그·fixture 어디에도 header가 없다).
# 그래서 "00만 성공"으로 단정하지 않는다. 확실한 것만 실패로 본다:
#   - 게이트웨이 오류 봉투(OpenAPI_ServiceResponse / cmmMsgHeader)
#   - resultCode가 정수로 읽히고 0이 아닌 경우 (22=쿼터초과, 30=키오류 등)
# 정수로 읽히지 않는 미지의 코드는 판정하지 않고 경고만 남긴다. 근거 없이
# 조이면 이 API가 header를 안 보내거나 다른 형태로 보낼 때 수집이 100%
# 실패한다 - 드문 전멸 위험을 상시 수집 불능으로 바꾸는 셈이다.
# 실제 정상 header 확보 후 별도로 조인다(향후 dry-run 과제).
SUCCESS_RESULT_CODES = {"00", "0", "0000"}


def _clip(v, n: int = 120) -> str:
    """진단용 문자열. 응답 원문을 통째로 싣지 않는다(키·민감정보 유출 방지)."""
    t = str(v).replace("\n", " ").strip()
    return t[:n] + ("…" if len(t) > n else "")


def detect_api_error(data: dict) -> str | None:
    """응답이 '명백한 오류'면 사유 문자열, 아니면 None.

    body만 보면 오류 응답도 items=[] / totalCount=0 인 정상 완결처럼 보인다.
    실제로 쿼터 초과(resultCode 22) 응답이 그 형태로 온다. 그래서 body 파싱
    전에 봉투부터 판정한다. serviceKey는 어떤 경로로도 메시지에 넣지 않는다.
    """
    if not isinstance(data, dict):
        return f"응답이 dict가 아니다: {type(data).__name__}"

    # 게이트웨이 레벨 오류 봉투. 정상 응답에는 절대 나타나지 않는다.
    if "OpenAPI_ServiceResponse" in data:
        env = data.get("OpenAPI_ServiceResponse") or {}
        hdr = env.get("cmmMsgHeader", {}) if isinstance(env, dict) else {}
        return (
            "게이트웨이 오류 봉투(OpenAPI_ServiceResponse) "
            f"returnReasonCode={_clip(hdr.get('returnReasonCode'), 20)} "
            f"errMsg={_clip(hdr.get('errMsg'))}"
        )
    if "cmmMsgHeader" in data:
        hdr = data.get("cmmMsgHeader") or {}
        hdr = hdr if isinstance(hdr, dict) else {}
        return (
            "오류 봉투(cmmMsgHeader) "
            f"returnReasonCode={_clip(hdr.get('returnReasonCode'), 20)} "
            f"errMsg={_clip(hdr.get('errMsg'))}"
        )

    resp = data.get("response")
    if isinstance(resp, dict):
        if "cmmMsgHeader" in resp:
            hdr = resp.get("cmmMsgHeader") or {}
            hdr = hdr if isinstance(hdr, dict) else {}
            return (
                "오류 봉투(response.cmmMsgHeader) "
                f"returnReasonCode={_clip(hdr.get('returnReasonCode'), 20)} "
                f"errMsg={_clip(hdr.get('errMsg'))}"
            )
        header = resp.get("header")
        if isinstance(header, dict) and "resultCode" in header:
            code = header.get("resultCode")
            text = str(code).strip()
            if text in SUCCESS_RESULT_CODES:
                return None
            try:
                numeric = int(text)
            except (TypeError, ValueError):
                # 판정 불가. 여기서 막지 않는다(위 주석 참조).
                log.warning(
                    f"  판정할 수 없는 resultCode={_clip(code, 20)} "
                    f"resultMsg={_clip(header.get('resultMsg'))} - 계속 진행한다"
                )
                return None
            if numeric != 0:
                return (
                    f"resultCode={_clip(code, 20)} "
                    f"resultMsg={_clip(header.get('resultMsg'))}"
                )
    return None


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

        # body 파싱 전에 봉투부터 본다. 오류 응답도 items=[] / totalCount=0
        # 형태로 와서 body만 보면 '정상 완결'과 구분되지 않는다.
        api_error = detect_api_error(data)
        if api_error:
            raise CollectionError(
                f"page {page_no} API 오류 응답: {api_error}. "
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
            # totalCount=0 을 '정상 완결'로 인정하지 않는다.
            #
            # 형식상 정상인 빈 응답(점검·쿼터 초과·업스트림 장애)이 오면
            # 빈 candidate가 A~F 게이트를 전부 통과하고 production 전체가
            # 0건으로 교체된다(2026-09-04 실증). 정말 전국 판매처가 0이 되는
            # 상황은 자동 promotion 대상이 아니라 사람이 확인할 사건이다.
            if expected_total <= 0:
                raise CollectionError(
                    f"API totalCount={expected_total}. 빈 결과를 완결로 인정하지 "
                    "않는다 (점검·쿼터 초과·업스트림 장애와 구분할 수 없다). "
                    "기존 data/ 는 한 건도 변경·삭제되지 않는다."
                )
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


# ────────────────────────────────────────────────────────────────────────
# 인천 2026 행정구역 개편 (2026-07-01 시행) 대응.
#
# 2군 8구 -> 2군 9구. 중구 원도심 + 동구 -> 제물포구, 중구 영종·용유 -> 영종구,
# 서구 -> 서해구 + 검단구.
#
# 여기서 하는 일은 "현재 행정구역명을 옛 이름으로 바꾸는 것"이 아니다.
# 개편 전에 만들어진 저장 경로와 URL(/incheon/icjunggu 등)을 유지하기 위해
# 신규 구군명을 기존 route bucket으로 정규화할 뿐이다. 원본 주소 문자열은
# 그대로 보존한다. 표시 행정구역명 변경은 별도 콘텐츠 결정이다.
# ────────────────────────────────────────────────────────────────────────

# 신규 구군 -> 기존 route bucket 구군명. 단일 대응이 가능한 것만 둔다.
# 서해구·검단구는 현재 API에 0건이지만 선제 등록한다. API가 나중에 반영해도
# silent unmatched가 발생하지 않아야 한다.
LEGACY_ROUTE_DISTRICT_MAP = {
    ("인천광역시", "영종구"): "중구",
    ("인천광역시", "서해구"): "서구",
    ("인천광역시", "검단구"): "서구",
}

# 두 개 이상의 옛 구가 합쳐진 구는 단일 대응이 불가능하다. 법정동 토큰을
# 완전 일치로 대조해 갈라야 한다. 순서대로 검사하며, 어느 집합에도 없으면
# 저장 전에 중단한다.
LEGACY_ROUTE_SPLIT_DISTRICTS = {
    ("인천광역시", "제물포구"): (
        ("old_donggu", "동구"),
        ("old_junggu", "중구"),
    ),
}

# 과거 행정구역명이 남은 오래된 주소. 신규 개편과 구분하기 위한 예외 목록이다.
# 이름만으로 허용하면 다른 시도의 동명이나 미래 오류까지 가려지므로
# 반드시 (시도, 구군) 쌍으로 관리한다.
# 이 예외는 drift 오탐 방지 용도일 뿐이며, 여기 있는 건을 새 지역으로
# 자동 회수하지 않는다. (연기군 -> 세종, 군위군 -> 대구는 별도 작업)
HISTORICAL_DISTRICT_EXCEPTIONS = {
    ("충청남도", "연기군"),
    ("경상북도", "군위군"),
}

# legacy_districts.json에서 로드한 법정동 집합
LEGACY_DISTRICT_SETS: dict[str, set[str]] = {}


def load_legacy_districts():
    """제물포구 분리에 쓰는 법정동 집합을 로드한다.

    매장 표본에서 추출하지 않는다. 표본은 옛 동구가 1종뿐이라
    규칙을 만들 수 없다. 정본 파일을 그대로 쓴다.
    """
    path = os.path.join(os.path.dirname(__file__), "legacy_districts.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    for key, value in raw.items():
        if key.startswith("_"):
            continue
        LEGACY_DISTRICT_SETS[key] = set(value)
    log.info(
        "Loaded legacy districts: "
        + ", ".join(f"{k} {len(v)}종" for k, v in LEGACY_DISTRICT_SETS.items())
    )


def resolve_legacy_district(
    region_name: str, district_name: str, parts: list[str]
) -> tuple[str | None, str | None]:
    """신규 구군명을 기존 route bucket 구군명으로 정규화한다.

    반환: (구군명, None) 정상 / (None, 사유) 미해결
    개편과 무관한 이름은 그대로 돌려준다.
    """
    key = (region_name, district_name)

    mapped = LEGACY_ROUTE_DISTRICT_MAP.get(key)
    if mapped:
        return mapped, None

    split = LEGACY_ROUTE_SPLIT_DISTRICTS.get(key)
    if split:
        if not LEGACY_DISTRICT_SETS:
            raise CollectionError(
                "load_legacy_districts() 미실행 - 통합된 구를 분리할 수 없다."
            )
        # 주소의 세 번째 토큰이 법정동이다. 완전 일치만 인정한다.
        dong = parts[2] if len(parts) > 2 else None
        if not dong:
            return None, f"'{district_name}' 주소에 법정동 토큰이 없다"
        for set_name, legacy_name in split:
            if dong in LEGACY_DISTRICT_SETS.get(set_name, ()):
                return legacy_name, None
        return None, f"'{district_name}'의 법정동 '{dong}'을 옛 구로 분리할 수 없다"

    return district_name, None


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
        region_name, district_name = resolve_merged_sido(parts)
    else:
        region_name = normalize_region(addr)
        if not region_name:
            return None, None
        district_name = extract_district(addr, region_name)
    if region_name and district_name:
        # 신·구 행정구역명 차이는 허용하되 실제 귀속 차이는 허용하지 않는다.
        # 정규화 실패 시에는 원본 이름을 그대로 둬서 비교에서 드러나게 한다.
        resolved, _ = resolve_legacy_district(region_name, district_name, parts)
        if resolved:
            district_name = resolved
    return region_name, district_name


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


def build_candidate(
    items: list[dict],
    updated_at: str,
    workspace: str,
) -> dict:
    """분류 결과를 workspace(candidate 트리)에만 기록하고 회계 통계를 돌려준다.

    production data/ 는 한 바이트도 건드리지 않는다. _unmatched.json도
    candidate의 일부다. contradiction 검증도 여기서 전량 끝낸다.
    stale 삭제는 이 단계에 없다 - candidate 트리에 그 파일이 없는 것이
    곧 삭제 계획이며, 실제 반영은 promote_candidate()의 트리 교체로만 일어난다.
    """
    # 1. Filter active only
    active = [i for i in items if str(i.get("SALS_STTS_CD", "")) == "01"]
    log.info(f"Active (영업/정상): {len(active)}/{len(items)}")

    # 2. Transform + classify
    # region_slug -> district_slug -> [stores]
    classified: dict[str, dict[str, list[dict]]] = {}
    unmatched: list[dict] = []
    # "regionSlug/구군명" -> 건수. 정확 매칭 실패 집계용 (매핑 테이블 보강 근거)
    unmatched_districts: dict[tuple[str, str], int] = {}
    # 개편된 구를 legacy bucket으로 분리하지 못한 사유
    drift_reasons: dict[tuple[str, str], str] = {}
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
        # 매칭 실패는 집계만 하고, 저장 전 preflight에서 판정한다.
        if district_name:
            resolved, reason = resolve_legacy_district(region_name, district_name, parts)
            if resolved is None:
                # 개편된 구인데 legacy bucket으로 분리하지 못했다.
                key = (region_name, district_name)
                unmatched_districts[key] = unmatched_districts.get(key, 0) + 1
                drift_reasons.setdefault(key, reason)
            else:
                district_slug = name_to_slug.get(resolved)
                if not district_slug:
                    key = (region_name, resolved)
                    unmatched_districts[key] = unmatched_districts.get(key, 0) + 1

        if not district_slug:
            unmatched.append(store)
            continue

        if region_slug not in classified:
            classified[region_slug] = {}
        if district_slug not in classified[region_slug]:
            classified[region_slug][district_slug] = []
        classified[region_slug][district_slug].append(store)

    # ── preflight: 구군 schema drift 게이트 ────────────────────────────
    # 반드시 모든 active 레코드 분류가 끝난 뒤, 어떤 JSON write/delete/index
    # write/_unmatched write 보다도 먼저 수행한다. 한 건씩 처리하다가 중간에
    # 새 구군을 만나면 이미 앞부분 파일을 써버리므로 fail closed가 아니다.
    #
    # 불변조건: unknown administrative district > 0
    #   -> CollectionError -> district JSON 0 / stale delete 0
    #      / region index 0 / _unmatched.json 0
    drift = {
        key: cnt
        for key, cnt in unmatched_districts.items()
        if key not in HISTORICAL_DISTRICT_EXCEPTIONS
    }
    if drift:
        lines = []
        for (region_name_d, district_name_d), cnt in sorted(
            drift.items(), key=lambda x: -x[1]
        ):
            why = drift_reasons.get((region_name_d, district_name_d), "매핑에 없는 구군")
            lines.append(f"{region_name_d} {district_name_d}: {cnt}건 ({why})")
        raise CollectionError(
            "미등록 구군 발견 (행정구역 개편 가능성). 매핑을 갱신하기 전에는 "
            "저장·삭제를 진행하지 않는다: " + " / ".join(lines)
        )

    known_historical = {
        key: cnt
        for key, cnt in unmatched_districts.items()
        if key in HISTORICAL_DISTRICT_EXCEPTIONS
    }
    if known_historical:
        log.warning(
            "과거 행정구역명 잔존분 (drift 아님, 자동 회수하지 않음): "
            + ", ".join(f"{r} {d}: {c}건" for (r, d), c in known_historical.items())
        )

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

    # 4. candidate 에 unmatched 기록
    data_dir = workspace
    os.makedirs(workspace, exist_ok=True)
    if unmatched:
        unmatched_path = os.path.join(workspace, "_unmatched.json")
        with open(unmatched_path, "w", encoding="utf-8") as f:
            json.dump(unmatched, f, ensure_ascii=False, indent=2)
        log.info(f"Unmatched: {len(unmatched)} → _unmatched.json (candidate)")

    # 5. candidate 에 region/district 기록
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
            # count가 0인 구군은 candidate 트리에 파일을 만들지 않는다.
            # 그 부재가 곧 삭제 계획이며, promote_candidate()의 트리 교체로만
            # 실제 반영된다. 여기서 production 파일을 직접 지우지 않는다.

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

    return {
        "raw": len(items),
        "active": len(active),
        "unmatched_total": len(unmatched),
        "unmatched_by_reason": {
            "no_region_or_malformed": len(malformed_addresses),
            "district_unresolved": len(unmatched)
            - len(malformed_addresses)
            - sum(known_historical.values()),
            "historical": sum(known_historical.values()),
        },
        "dedupe_input": total_before_dedupe,
        "duplicates_removed": total_before_dedupe - total_after_dedupe,
        "verified_input": total_after_dedupe,
        "contradictions": len(rejected_stores),
        "contradiction_records": rejected_stores,
        "final": total_all,
        # 정상 경로에서는 항상 비어 있다. 미등록 시도는 위에서 즉시
        # CollectionError를, 미등록 구군은 drift preflight가 workspace write
        # 이전에 CollectionError를 던지기 때문이다. 즉 게이트 D는 그 preflight의
        # 이중 안전망이며, 여기 도달했다는 것 자체가 unknown 0을 뜻한다.
        # preflight를 게이트 뒤로 옮기지 않는다 - 지금이 더 강한 불변조건이다.
        # (D의 판정 로직 자체는 test_collect.py에서 직접 주입해 검증한다.)
        "unknown_provinces": {},
        "unknown_districts": {},
        "historical_exceptions": {f"{r} {d}": c for (r, d), c in known_historical.items()},
        "workspace": workspace,
    }


def promotion_paths(data_dir: str) -> tuple[str, str]:
    """(candidate, backup) 경로. data_dir의 형제 디렉터리여야 rename이 된다."""
    parent = os.path.dirname(os.path.abspath(data_dir))
    return (
        os.path.join(parent, ".data-candidate"),
        os.path.join(parent, ".data-backup"),
    )


def recover_promotion_state(data_dir: str) -> str:
    """프로그램 시작 시 중단된 promotion 상태를 판정하고 복구한다.

    .data-backup 은 잔여물이 아니다. promotion이 첫 rename 직후 죽으면
    그것이 유일하게 남은 production이다. SIGKILL·전원 차단·OS 크래시는
    Python 예외가 아니므로 promote_candidate의 rollback이 실행되지 않는다.
    따라서 다음 실행 시작 시 디스크 상태로 판정해야 한다.

    애매한 조합은 추측해서 정리하지 않고 fail closed 한다.

      data  backup  candidate  판정
      ────  ──────  ─────────  ─────────────────────────────────────────
       O      X         X      A) 정상
       O      X         O      E) production 확인 후 candidate 정리
       X      O        any     B) backup -> data 복구, 실행 중단
       O      O        any     C) data 구조 감사 PASS면 backup 제거,
                                  FAIL이면 backup 보존 + fail closed
       X      X        any     D) production 상실. HARD FAIL

    반환: 상태 코드. fail closed가 필요하면 CollectionError를 던진다.
    """
    candidate, backup = promotion_paths(data_dir)
    has_data = os.path.isdir(data_dir)
    has_backup = os.path.isdir(backup)
    has_cand = os.path.isdir(candidate)

    # D) production 상실 - 수집으로 새로 만들어 덮지 않는다
    if not has_data and not has_backup:
        raise CollectionError(
            f"production {data_dir} 와 {backup} 이 모두 없다. "
            "수집으로 새 데이터를 만들어 덮어서 해결하지 않는다. "
            "사람이 복구해야 한다. (recovery state D)"
        )

    # B) 첫 rename 직후 중단 - backup이 유일한 production
    if not has_data and has_backup:
        log.error("=" * 50)
        log.error(
            "이전 promotion이 첫 rename 직후 중단된 상태다. "
            f"{backup} 이 유일한 production이다."
        )
        os.rename(backup, data_dir)  # 대상 없음 -> 성공
        report = integrity.audit_tree_structure(data_dir, "recovered")
        log.error(f"복구 완료. 구조 감사: {report.summary()}")
        log.error("=" * 50)
        raise CollectionError(
            "중단된 promotion을 복구했다 (backup -> data). 같은 실행에서 "
            "수집·promotion을 이어가지 않는다. 상태를 확인한 뒤 다시 실행할 것. "
            f"(recovery state B, 구조 failures={len(report.failures)})"
        )

    # C) data와 backup이 동시에 존재 - 두 번째 crash window
    if has_data and has_backup:
        report = integrity.audit_tree_structure(data_dir, "post-crash data")
        if report.ok:
            log.warning(
                "이전 promotion이 backup 정리 전에 중단됐다. 현재 data/ 구조 감사가 "
                "통과했으므로 backup을 제거한다. (recovery state C)"
            )
            shutil.rmtree(backup)
        else:
            raise CollectionError(
                f"{data_dir} 와 {backup} 이 함께 존재하고 현재 data/ 구조 감사가 "
                "실패했다. backup을 보존한다 (자동 삭제·덮어쓰기 금지). "
                f"(recovery state C-fail) failures={len(report.failures)}: "
                + " / ".join(f"{c}: {m}" for c, m in report.failures[:3])
            )
    elif has_cand:
        # E) candidate 잔여물 - production이 정상 존재할 때만 정리
        log.warning(f"이전 실행의 candidate 잔여물을 제거한다: {candidate}")
        shutil.rmtree(candidate)
        return "E.candidate_cleaned"

    if has_cand and os.path.isdir(candidate):
        shutil.rmtree(candidate)

    return "C.backup_cleaned" if has_backup else "A.normal"


def promote_candidate(workspace: str, data_dir: str) -> None:
    """ROLLBACK-SAFE PROMOTION.

    엄밀한 의미의 원자적 swap이 아니다. 디렉터리 rename 두 번이 필요하고
    그 사이에 실패 구간이 있다. 따라서 실패 시 기존 production이 자동
    복구되는 것으로 보장 수준을 정의한다.

    최종 상태는 반드시 둘 중 하나다.
      A. 기존 production 완전 유지
      B. candidate 전체 반영
    old/new 혼합 상태는 만들지 않는다.

    실측(macOS/APFS, 2026-09-03): os.rename과 os.replace 모두 비어 있지 않은
    대상 디렉터리를 덮어쓰지 못하고 ENOTEMPTY(66)로 실패한다. 파일과 동작이
    다르다. 그래서 "대상이 없는 상태"를 먼저 만들고 rename한다.
    """
    _, backup = promotion_paths(data_dir)

    # backup이 남아 있으면 이전 promotion이 중단된 상태다. 여기서 지우면
    # 유일하게 남은 production을 삭제할 수 있다. recover_promotion_state()가
    # 시작 시 판정했어야 하므로, 여기 도달했다는 것 자체가 이상 상태다.
    if os.path.exists(backup):
        raise CollectionError(
            f"{backup} 이 이미 존재한다. 이전 promotion이 중단된 상태일 수 있어 "
            "덮어쓰거나 삭제하지 않는다. recover_promotion_state()를 먼저 실행할 것."
        )

    had_production = os.path.isdir(data_dir)
    if had_production:
        os.rename(data_dir, backup)  # 대상 없음 -> 성공

    try:
        os.rename(workspace, data_dir)  # 대상 없음 -> 성공
    except BaseException:
        # candidate 반영 실패. 기존 production을 되돌린다.
        if had_production and not os.path.isdir(data_dir):
            os.rename(backup, data_dir)
            log.error("promotion 실패 - 기존 production data 복구 완료 (rollback)")
        raise

    if had_production:
        shutil.rmtree(backup)


def classify_and_save(
    items: list[dict],
    updated_at: str,
    complete: bool = False,
    data_dir: str | None = None,
    expected_total: int | None = None,
):
    """candidate 생성 -> 단일 integrity gate -> promotion.

    이 함수가 production data/ 를 바꾸는 유일한 경로다. 게이트가 실패하면
    promote_candidate()를 호출하지 않으므로 production은 그대로 남는다.

    complete=False면 candidate 검증까지만 하고 promotion을 생략한다
    (dry-run). 수집이 완결됐음을 증명한 실행만 True로 호출한다.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    workspace, _ = promotion_paths(data_dir)
    # 시작 시 recovery가 이미 판정했어야 한다. 여기서 candidate가 남아 있다면
    # 같은 실행 안의 잔여물이므로 정리한다. backup은 절대 건드리지 않는다.
    if os.path.exists(workspace):
        shutil.rmtree(workspace)

    try:
        stats = build_candidate(items, updated_at, workspace)
        stats["expected_total"] = expected_total

        # ── SINGLE INTEGRITY GATE ─────────────────────────────────────
        report, plan = integrity.validate_candidate(
            workspace, data_dir, stats, verify_store_location
        )
        log.info(report.summary())
        if not report.ok:
            raise CollectionError(
                f"무결성 게이트 실패 {len(report.failures)}건 - promotion 하지 않는다: "
                + " / ".join(f"{c}: {m}" for c, m in report.failures[:5])
            )
        log.info(
            f"promotion 계획: 생성 {len(plan['created'])} / 변경 {len(plan['modified'])} "
            f"/ 제거 {len(plan['removed'])} / 유지 {len(plan['kept'])}"
        )

        if not complete:
            log.warning(
                "complete=False - candidate 검증만 수행하고 promotion을 생략한다. "
                "production 무변경."
            )
            return stats["final"]

        promote_candidate(workspace, data_dir)
        log.info(f"promotion 완료: {stats['final']}곳")
        return stats["final"]
    finally:
        if os.path.exists(workspace):
            shutil.rmtree(workspace, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    args = parser.parse_args()

    load_district_slugs()
    load_legacy_districts()
    today = time.strftime("%Y-%m-%d")

    # production 상태가 애매한데 API fetch부터 시작하지 않는다.
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    try:
        state = recover_promotion_state(data_dir)
        log.info(f"promotion recovery state: {state}")
    except CollectionError as e:
        log.error("=" * 50)
        log.error(f"시작 전 production 상태 이상: {e}")
        log.error("=" * 50)
        sys.exit(1)

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
        total = classify_and_save(
            items, today, complete=True, expected_total=expected_total
        )
    except CollectionError as e:
        log.error("=" * 50)
        log.error(f"분류 중단 - 저장·삭제를 진행하지 않는다: {e}")
        log.error("기존 data/ 파일은 한 건도 변경·삭제되지 않았다.")
        log.error("=" * 50)
        sys.exit(1)

    log.info(f"\nDone! Total: {total}곳, API calls: {calls}")


if __name__ == "__main__":
    main()
