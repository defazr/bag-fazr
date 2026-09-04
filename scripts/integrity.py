"""데이터 무결성 검증 (P3-13).

순수 검증 모듈이다. 파일을 쓰거나 지우지 않고, import 시 side effect가 없으며,
독립 실행 entrypoint도 아니다. 실제 promotion 허용 결정은 collect.py 내부의
단일 integrity gate만 담당한다. 이 모듈의 PASS 결과를 외부 상태처럼 신뢰하는
구조를 만들지 않기 위한 분리다.

두 용도를 지원한다.
  1. 현재 production data/ read-only 감사
  2. 재수집 candidate 검증 (promotion 전)

collect.py를 import하지 않는다. 주소 판정이 필요한 검사는 호출부가
derive 콜백을 넘긴다. 순환 의존을 만들지 않고, 검증 규칙과 분류 규칙이
같은 코드에서 나온다는 보장을 유지한다.
"""

import json
import os

# ─────────────────────────────────────────────────────────────────────────
# G. catastrophic-drop guard 임계값
#
# 전부 2026-09-04 SAFETY dry-run 2회 실측이 근거다 (raw 91,120 / final 69,292).
# 매직넘버를 함수 안에 흩뿌리지 않고 여기 모은다. 근거 없이 조정하지 않는다.
#
# 왜 전국 총계만으로는 안 되는가: 정상 전국 변동은 +0.04% 인데
# 서울(3,118건)이 통째로 사라져도 전국은 -4.37%, 제주 -90% 는 -1.03%,
# 세종 전멸은 -0.20% 에 불과하다. 시도·구군 층이 없으면 전부 통과한다.
# ─────────────────────────────────────────────────────────────────────────

# 전국. 비정상 축소의 최후 방어선. 정상 관측 +0.04% (2회).
# 실 규모(69,265)에서 25% 는 약 17,300건 소실이다.
#
# 절대량 하한을 두지 않는다. production 이 작다는 이유로 25%·50%·90% 축소를
# 허용할 이유가 없고, "작은 규모는 다른 계층이 본다"는 설명은 실제로 성립하지
# 않는다 - 3 -> 1 은 R1(>=30건)·D1(>=100건)·D2(>=20건)·AGG(>=20건) 어디에도
# 걸리지 않는다. bootstrap(production == 0)만 _loss() 에서 이미 제외된다.
NATIONAL_DROP_RATIO = 0.25

# 시도. 정상 최악은 서울 -2.05% / -64건 (2회 재현). 비율은 그 5배.
# 절대 조건은 세종(165건) 같은 소규모 시도의 1~2건 변동을 걸러낸다.
REGION_DROP_RATIO = 0.10
REGION_DROP_ABS = 30

# 구군. 두 조건의 교차로 정상 표본을 침범하지 않으면서 빈 구간을 메운다.
#   정상에서 절대 감소 >=100 인 사례의 최대 비율: 화성 -108 / -6.21%
#   정상에서 비율 >=10% 인 사례의 최대 절대량: -66 (마포 -10.96%, 부산중구 -18.54%)
# 따라서 (>=100건 AND >=10%) 는 오늘 정상 candidate 에서 발화 0 이면서
# 300 -> 160 (-140 / -46.7%) 같은 단일 구군 붕괴를 잡는다.
DISTRICT_DROP_ABS = 100
DISTRICT_DROP_RATIO = 0.10
# 비율이 낮아도 수백 건이 한 번에 사라지는 대형 구군용 fail-safe.
# 정상 최대 절대 감소 108건의 약 4.6배.
DISTRICT_DROP_ABS_HARD = 500

# 구군 전멸. 정상 전멸은 통영 prod=1 뿐이다(원인은 contradiction 격리).
# production 10건 미만 구군이 41개(합계 99건)라 한두 건 변동으로 쉽게 0이 된다.
DISTRICT_EXTINCT_MIN = 20

# 다중 급감. 개별로는 임계값 아래인데 여러 구군이 동시에 빠지는 사고용.
# 정상 material-drop 은 5개 / 합계 320건.
MASS_DROP_ABS = 20
MASS_DROP_RATIO = 0.05
MASS_DROP_COUNT = 15
MASS_DROP_TOTAL = 2000

# 실패 메시지에 싣는 상세 항목 상한 (report 폭주 방지).
MAX_OFFENDERS = 5


class IntegrityReport:
    """검증 결과. failures가 하나라도 있으면 promotion을 허용하지 않는다."""

    def __init__(self, subject: str):
        self.subject = subject
        self.failures: list[tuple[str, str]] = []
        self.notes: list[tuple[str, str]] = []

    def fail(self, code: str, message: str) -> None:
        self.failures.append((code, message))

    def note(self, code: str, message: str) -> None:
        """실패는 아니지만 기록해야 하는 사실 (accounted exclusion 등)."""
        self.notes.append((code, message))

    @property
    def ok(self) -> bool:
        return not self.failures

    def summary(self) -> str:
        lines = [f"[{self.subject}] failures={len(self.failures)} notes={len(self.notes)}"]
        for code, msg in self.failures:
            lines.append(f"  FAIL {code}: {msg}")
        for code, msg in self.notes:
            lines.append(f"  note {code}: {msg}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────
# 트리 읽기 (read-only)
# ─────────────────────────────────────────────────────────────────────────

def read_tree(root: str) -> dict:
    """data/ 또는 candidate 트리를 읽어 구조를 돌려준다. 쓰지 않는다.

    반환:
      {
        "root": str,
        "regions_json": dict | None,
        "regions": {region_slug: {"index": dict, "districts": {slug: dict}}},
        "unreadable": [경로],
        "files": {상대경로: 크기},
      }
    """
    out = {
        "root": root,
        "regions_json": None,
        "regions": {},
        "unreadable": [],
        "files": {},
    }
    if not os.path.isdir(root):
        return out

    def load(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            out["unreadable"].append(f"{os.path.relpath(path, root)}: {e}")
            return None

    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".json"):
                p = os.path.join(dirpath, fn)
                out["files"][os.path.relpath(p, root)] = os.path.getsize(p)

    rj = os.path.join(root, "regions.json")
    if os.path.exists(rj):
        out["regions_json"] = load(rj)

    for name in sorted(os.listdir(root)):
        rdir = os.path.join(root, name)
        if not os.path.isdir(rdir):
            continue
        ip = os.path.join(rdir, "index.json")
        if not os.path.exists(ip):
            continue
        index = load(ip)
        districts = {}
        for fn in sorted(os.listdir(rdir)):
            if fn == "index.json" or not fn.endswith(".json"):
                continue
            d = load(os.path.join(rdir, fn))
            if d is not None:
                districts[fn[:-5]] = d
        out["regions"][name] = {"index": index, "districts": districts}
    return out


# ─────────────────────────────────────────────────────────────────────────
# 개별 검사
# ─────────────────────────────────────────────────────────────────────────

def check_tree_counts(tree: dict, report: IntegrityReport) -> None:
    """F. 3계층 count 일치 — 실제 직렬화된 파일을 읽어 검증한다.

    district JSON의 stores 길이 / 각 district의 totalCount /
    region index.json의 count·totalCount / regions.json의 count·totalCount
    """
    if tree["unreadable"]:
        for u in tree["unreadable"]:
            report.fail("F.unreadable", u)

    grand_file = 0
    grand_index = 0
    region_counts = {}

    for rs, r in sorted(tree["regions"].items()):
        index = r["index"]
        if index is None:
            report.fail("F.index_missing", f"{rs}/index.json 읽기 실패")
            continue

        entries = {e["districtSlug"]: e for e in index.get("districts", [])}
        file_sum = 0
        for slug, d in sorted(r["districts"].items()):
            stores = d.get("stores")
            if not isinstance(stores, list):
                report.fail("F.schema", f"{rs}/{slug}.json 에 stores 배열이 없다")
                continue
            n = len(stores)
            if d.get("totalCount") != n:
                report.fail(
                    "F.file_selfcount",
                    f"{rs}/{slug}.json totalCount={d.get('totalCount')} != stores={n}",
                )
            e = entries.get(slug)
            if e is None:
                report.fail("F.orphan_file", f"{rs}/{slug}.json 이 index.json에 없다")
            elif e.get("count") != n:
                report.fail(
                    "F.index_vs_file",
                    f"{rs}/{slug} index count={e.get('count')} != 파일 stores={n}",
                )
            file_sum += n

        # index에 count>0인데 파일이 없는 경우
        for slug, e in sorted(entries.items()):
            if e.get("count", 0) > 0 and slug not in r["districts"]:
                report.fail(
                    "F.missing_file",
                    f"{rs}/{slug} index count={e['count']} 인데 파일이 없다",
                )

        index_sum = sum(e.get("count", 0) for e in index.get("districts", []))
        if index.get("totalCount") != index_sum:
            report.fail(
                "F.index_selfsum",
                f"{rs}/index.json totalCount={index.get('totalCount')} != 항목합 {index_sum}",
            )
        if index_sum != file_sum:
            report.fail(
                "F.index_vs_files",
                f"{rs} index 항목합 {index_sum} != 실제 파일 합 {file_sum}",
            )
        region_counts[rs] = file_sum
        grand_file += file_sum
        grand_index += index_sum

    rj = tree["regions_json"]
    if rj is None:
        report.fail("F.regions_json", "regions.json 이 없거나 읽을 수 없다")
    else:
        listed = {x["regionSlug"]: x.get("count", 0) for x in rj.get("regions", [])}
        for rs, cnt in sorted(region_counts.items()):
            if listed.get(rs) != cnt:
                report.fail(
                    "F.regions_vs_index",
                    f"regions.json {rs} count={listed.get(rs)} != 실제 {cnt}",
                )
        if rj.get("totalCount") != grand_file:
            report.fail(
                "F.regions_total",
                f"regions.json totalCount={rj.get('totalCount')} != 실제 파일 합 {grand_file}",
            )

    report.note("F.totals", f"파일 합계 {grand_file} / index 합계 {grand_index}")
    return grand_file


def check_store_locations(tree: dict, verify, report: IntegrityReport) -> None:
    """C. 최종 store 전체의 주소 유래 bucket == 저장 대상 bucket.

    verify(store, region_name, district_name) -> None | 사유
    """
    bad = 0
    samples = []
    for rs, r in sorted(tree["regions"].items()):
        index = r["index"] or {}
        region_name = index.get("region")
        entries = {e["districtSlug"]: e.get("district") for e in index.get("districts", [])}
        for slug, d in sorted(r["districts"].items()):
            district_name = d.get("district") or entries.get(slug)
            if not region_name or not district_name:
                report.fail("C.no_names", f"{rs}/{slug} 지역명을 알 수 없다")
                continue
            for s in d.get("stores", []):
                reason = verify(s, region_name, district_name)
                if reason:
                    bad += 1
                    if len(samples) < 10:
                        samples.append(f"{rs}/{slug} | {s.get('name', '?')} | {reason}")
    if bad:
        report.fail(
            "C.location_mismatch",
            f"최종 저장 대상과 주소 유래 지역이 다른 매장 {bad}건. 예: " + " ; ".join(samples),
        )
    else:
        report.note("C.location", "최종 store 전체 bucket 일치")


def check_reconciliation(stats: dict, report: IntegrityReport) -> None:
    """B. 단계별 산술 회계. 모든 active record의 행방이 설명돼야 한다."""
    active = stats["active"]
    unmatched = stats["unmatched_total"]
    dup = stats["duplicates_removed"]
    contra = stats["contradictions"]
    final = stats["final"]

    dedupe_input = active - unmatched
    if dedupe_input != stats["dedupe_input"]:
        report.fail(
            "B.stage1",
            f"active {active} - unmatched {unmatched} = {dedupe_input} != "
            f"실제 dedupe 입력 {stats['dedupe_input']}",
        )
    verified_input = stats["dedupe_input"] - dup
    if verified_input != stats["verified_input"]:
        report.fail(
            "B.stage2",
            f"dedupe 입력 {stats['dedupe_input']} - 중복 {dup} = {verified_input} != "
            f"실제 검증 입력 {stats['verified_input']}",
        )
    if stats["verified_input"] - contra != final:
        report.fail(
            "B.stage3",
            f"검증 입력 {stats['verified_input']} - contradiction {contra} = "
            f"{stats['verified_input'] - contra} != 최종 {final}",
        )
    if active != unmatched + dup + contra + final:
        report.fail(
            "B.closure",
            f"회계 불일치: active {active} != unmatched {unmatched} + 중복 {dup} "
            f"+ contradiction {contra} + 최종 {final} = {unmatched + dup + contra + final}",
        )

    by_reason = stats.get("unmatched_by_reason", {})
    if sum(by_reason.values()) != unmatched:
        report.fail(
            "B.unmatched_reasons",
            f"unmatched {unmatched} != reason별 합 {sum(by_reason.values())} ({by_reason})",
        )
    report.note(
        "B.chain",
        f"active {active} - unmatched {unmatched} - 중복 {dup} - contradiction {contra} = {final}",
    )
    report.note("B.unmatched_by_reason", str(by_reason))


def check_schema_drift(stats: dict, report: IntegrityReport) -> None:
    """D. 미등록 행정구역 0. historical exception은 unknown으로 세지 않고 따로 보존."""
    up = stats.get("unknown_provinces", {})
    ud = stats.get("unknown_districts", {})
    if up:
        report.fail("D.unknown_province", f"미등록 시도 {up}")
    if ud:
        report.fail("D.unknown_district", f"미등록 구군 {ud}")
    hist = stats.get("historical_exceptions", {})
    if hist:
        report.note("D.historical", f"과거 지명 잔존분 (자동 회수 안 함): {hist}")
    if not up and not ud:
        report.note("D.drift", "미등록 시도/구군 0")


def check_contradiction_accounting(stats: dict, tree: dict, report: IntegrityReport) -> None:
    """E. contradiction의 존재 자체가 아니라 행방이 완전히 설명되는지 본다.

    허용: quarantine되어 최종 dataset에서 제외되고 회계에 정확히 반영된 경우.
    실패: 최종에 들어갔거나, 집계에서 사라졌거나, 격리 목록과 수가 어긋난 경우.
    """
    declared = stats["contradictions"]
    listed = len(stats.get("contradiction_records", []))
    if declared != listed:
        report.fail(
            "E.count_vs_records",
            f"contradiction 집계 {declared} != 격리 기록 {listed}건",
        )
    # C 검사가 최종 트리에 contradiction이 남았는지 이미 본다. 여기서는 회계만.
    if declared:
        report.note(
            "E.accounted",
            f"contradiction {declared}건이 최종에서 제외되고 회계에 반영됨 (accounted exclusion)",
        )
    else:
        report.note("E.accounted", "contradiction 0")


def tree_store_total(tree: dict) -> int:
    """트리에 실제로 직렬화된 store 건수. 자기신고 totalCount가 아니라 실측."""
    total = 0
    for r in tree["regions"].values():
        for d in r["districts"].values():
            stores = d.get("stores")
            if isinstance(stores, list):
                total += len(stores)
    return total


def tree_level_counts(tree: dict) -> tuple[dict, dict]:
    """(시도별 합계, 구군별 합계). 구군 키는 "{region_slug}/{district_slug}"."""
    regions: dict[str, int] = {}
    districts: dict[str, int] = {}
    for rs, r in tree["regions"].items():
        n = 0
        for slug, d in r["districts"].items():
            stores = d.get("stores")
            c = len(stores) if isinstance(stores, list) else 0
            districts[f"{rs}/{slug}"] = c
            n += c
        regions[rs] = n
    return regions, districts


def _loss(prod: int, cand: int) -> tuple[int, float]:
    """(절대 손실, 손실 비율). 증가·production 0 은 손실 0 으로 취급한다.

    부호 실수를 막기 위해 항상 양수 loss 기준으로 계산한다.
    production == 0 은 비율 게이트 대상이 아니다(신규 데이터이지 drop 이 아니다).
    """
    loss = prod - cand
    if loss <= 0 or prod <= 0:
        return 0, 0.0
    return loss, loss / prod


def diff_trees(prod_root: str, cand_root: str) -> dict:
    """G. production 트리와 candidate 트리의 차이를 명시적으로 계산한다.

    stale 삭제는 즉시 mutation이 아니라 이 차이의 결과여야 한다.

    파일 목록뿐 아니라 양쪽 store 총계도 돌려준다. A~F는 전부 candidate 내부
    정합성만 보므로, candidate가 완벽하게 자기일관적인 '빈 트리'여도 통과한다.
    production과 비교하는 외부 기준점은 여기뿐이다.
    """
    prod_tree = read_tree(prod_root)
    cand_tree = read_tree(cand_root)
    prod = prod_tree["files"]
    cand = cand_tree["files"]
    created = sorted(set(cand) - set(prod))
    removed = sorted(set(prod) - set(cand))
    common = set(prod) & set(cand)
    modified = sorted(p for p in common if prod[p] != cand[p])
    kept = sorted(p for p in common if prod[p] == cand[p])
    prod_regions, prod_districts = tree_level_counts(prod_tree)
    cand_regions, cand_districts = tree_level_counts(cand_tree)
    return {
        "created": created,
        "removed": removed,
        "modified": modified,
        "kept": kept,
        "prod_files": len(prod),
        "cand_files": len(cand),
        "prod_stores": tree_store_total(prod_tree),
        "cand_stores": tree_store_total(cand_tree),
        # 전국 총계만 보면 지역 전멸을 놓친다. 세 레벨을 전부 싣는다.
        "prod_regions": prod_regions,
        "cand_regions": cand_regions,
        "prod_districts": prod_districts,
        "cand_districts": cand_districts,
    }


def _diag(key: str, prod: int, cand: int, loss: int, ratio: float, dstats: dict) -> str:
    """실패 메시지용 진단. 원인 분해를 '설명'에만 쓴다 - 면제 조건이 아니다."""
    base = f"{key} prod={prod} cand={cand} loss={loss} ({ratio * 100:.2f}%)"
    d = (dstats or {}).get(key)
    if d:
        base += (f" [classified={d.get('classified_before_dedupe')}"
                 f" dup={d.get('duplicates_removed')}"
                 f" after_dedupe={d.get('after_dedupe')}"
                 f" contra={d.get('contradictions_removed')}"
                 f" final={d.get('final')}]")
    return base


def check_drop_guard(plan: dict, stats: dict, report: IntegrityReport) -> None:
    """G. production 대비 candidate 급감 판정.

    A~F 는 전부 candidate 내부 정합성만 본다. 완벽하게 자기일관적인 '거의 빈'
    트리도 통과한다. production 과 비교하는 외부 기준점은 여기뿐이다.

    전부 report.fail 이다. note/warn 으로 두면 promotion 이 그대로 진행되므로
    안전장치가 아니다 (IntegrityReport.ok 는 failures 만 본다).

    원인 분해(district_stats)는 BLOCK 면제에 쓰지 않는다. dedupe 나
    verify_store_location 자체가 회귀한 사고를 놓치기 때문이다. 진단에만 쓴다.
    """
    dstats = (stats or {}).get("district_stats", {})
    P, C = plan["prod_stores"], plan["cand_stores"]

    # N1. 전면 삭제 (기존 G.total_wipe 유지)
    if P > 0 and C == 0:
        report.fail(
            "G.total_wipe",
            f"production {P}건 -> candidate 0건. 전면 삭제는 자동 promotion "
            f"대상이 아니다 (제거 예정 파일 {len(plan['removed'])}개).",
        )

    # N2. 전국 급감
    n_loss, n_ratio = _loss(P, C)
    if n_ratio >= NATIONAL_DROP_RATIO:
        report.fail(
            "G.national_drop",
            f"전국 prod={P} cand={C} loss={n_loss} ({n_ratio * 100:.2f}%) "
            f">= {NATIONAL_DROP_RATIO * 100:.0f}%",
        )

    # R1. 시도 급감 - production/candidate 키 합집합으로 순회한다.
    #     교집합만 보면 candidate 에서 통째로 사라진 시도를 놓친다.
    pr, cr = plan["prod_regions"], plan["cand_regions"]
    hits = []
    for rs in sorted(set(pr) | set(cr)):
        p, c = pr.get(rs, 0), cr.get(rs, 0)
        loss, ratio = _loss(p, c)
        if loss >= REGION_DROP_ABS and ratio >= REGION_DROP_RATIO:
            hits.append(_diag(rs, p, c, loss, ratio, None))
    if hits:
        report.fail(
            "G.region_drop",
            f"시도 급감 {len(hits)}건 (>={REGION_DROP_ABS}건 AND "
            f">={REGION_DROP_RATIO * 100:.0f}%): " + " / ".join(hits[:MAX_OFFENDERS])
            + (f" 외 {len(hits) - MAX_OFFENDERS}건" if len(hits) > MAX_OFFENDERS else ""),
        )

    pd, cd = plan["prod_districts"], plan["cand_districts"]
    keys = sorted(set(pd) | set(cd))

    # D1. 구군 대량 손실
    hits = []
    for k in keys:
        p, c = pd.get(k, 0), cd.get(k, 0)
        loss, ratio = _loss(p, c)
        if (loss >= DISTRICT_DROP_ABS and ratio >= DISTRICT_DROP_RATIO) or (
            loss >= DISTRICT_DROP_ABS_HARD
        ):
            hits.append(_diag(k, p, c, loss, ratio, dstats))
    if hits:
        report.fail(
            "G.district_drop",
            f"구군 대량 손실 {len(hits)}건 ((>={DISTRICT_DROP_ABS}건 AND "
            f">={DISTRICT_DROP_RATIO * 100:.0f}%) OR >={DISTRICT_DROP_ABS_HARD}건): "
            + " / ".join(hits[:MAX_OFFENDERS])
            + (f" 외 {len(hits) - MAX_OFFENDERS}건" if len(hits) > MAX_OFFENDERS else ""),
        )

    # D2. 구군 전멸. 원인이 contradiction 인지 여부는 면제 조건이 아니다.
    hits = []
    for k in keys:
        p, c = pd.get(k, 0), cd.get(k, 0)
        if p >= DISTRICT_EXTINCT_MIN and c == 0:
            hits.append(_diag(k, p, c, p, 1.0, dstats))
    if hits:
        report.fail(
            "G.district_extinction",
            f"구군 전멸 {len(hits)}건 (production >={DISTRICT_EXTINCT_MIN}건): "
            + " / ".join(hits[:MAX_OFFENDERS])
            + (f" 외 {len(hits) - MAX_OFFENDERS}건" if len(hits) > MAX_OFFENDERS else ""),
        )

    # AGG. 개별로는 임계값 아래인데 여러 구군이 동시에 빠지는 사고
    material = []
    for k in keys:
        p, c = pd.get(k, 0), cd.get(k, 0)
        loss, ratio = _loss(p, c)
        if loss >= MASS_DROP_ABS and ratio >= MASS_DROP_RATIO:
            material.append((k, p, c, loss, ratio))
    m_total = sum(x[3] for x in material)
    if len(material) >= MASS_DROP_COUNT or m_total >= MASS_DROP_TOTAL:
        top = sorted(material, key=lambda x: -x[3])[:MAX_OFFENDERS]
        report.fail(
            "G.mass_drop",
            f"다중 급감: material-drop 구군 {len(material)}개 / 합계 {m_total}건 "
            f"(기준 {MASS_DROP_COUNT}개 또는 {MASS_DROP_TOTAL}건). 상위: "
            + " / ".join(_diag(k, p, c, l, r, dstats) for k, p, c, l, r in top),
        )
    else:
        report.note(
            "G.mass_drop",
            f"material-drop 구군 {len(material)}개 / 합계 {m_total}건 (기준 미달)",
        )


# ─────────────────────────────────────────────────────────────────────────
# 조립
# ─────────────────────────────────────────────────────────────────────────

def audit_tree_structure(root: str, subject: str = "structure") -> IntegrityReport:
    """구조 무결성만 검증한다. 내용(주소-bucket 일치)은 보지 않는다.

    crash recovery 판정 전용이다. 중단된 promotion이 남기는 손상은 구조
    손상(파일 누락, count 불일치, 읽기 실패)이다. 반면 기존 production에는
    알려진 내용 이슈(위치 불일치 42건)가 있는데, 그것 때문에 복구가 막혀
    유일한 production을 못 되돌리는 상황을 만들면 안 된다.
    """
    report = IntegrityReport(subject)
    tree = read_tree(root)
    if not tree["regions"] and tree["regions_json"] is None:
        report.fail("S.empty", f"{root} 가 유효한 데이터 트리가 아니다")
        return report
    check_tree_counts(tree, report)
    return report


def audit_tree(root: str, verify, subject: str = "tree") -> IntegrityReport:
    """트리 하나에 대한 구조 무결성 감사 (read-only).

    production 현재 상태 감사에도, candidate 검증에도 같은 함수를 쓴다.
    """
    report = IntegrityReport(subject)
    tree = read_tree(root)
    check_tree_counts(tree, report)
    check_store_locations(tree, verify, report)
    return report


def validate_candidate(
    cand_root: str, prod_root: str, stats: dict, verify, subject: str = "candidate"
) -> tuple[IntegrityReport, dict]:
    """A~G 전체 검증. 반환: (report, plan).

    report.ok 가 False면 호출부는 promotion을 하지 않아야 한다.
    이 함수는 아무것도 쓰지 않는다.
    """
    report = IntegrityReport(subject)

    # A. API 완결성 (fetch_all이 이미 fail-closed로 막지만 게이트에서 재확인)
    if stats.get("raw") is not None and stats.get("expected_total") is not None:
        if stats["raw"] != stats["expected_total"]:
            report.fail(
                "A.api_completeness",
                f"raw {stats['raw']} != API totalCount {stats['expected_total']}",
            )
        else:
            report.note("A.api_completeness", f"raw == totalCount == {stats['raw']}")

    tree = read_tree(cand_root)
    check_reconciliation(stats, report)                  # B
    check_store_locations(tree, verify, report)           # C
    check_schema_drift(stats, report)                     # D
    check_contradiction_accounting(stats, tree, report)   # E
    cand_total = check_tree_counts(tree, report)          # F

    if cand_total is not None and cand_total != stats["final"]:
        report.fail(
            "F.tree_vs_stats",
            f"candidate 트리 실측 {cand_total} != 회계상 최종 {stats['final']}",
        )

    plan = diff_trees(prod_root, cand_root)               # G
    check_drop_guard(plan, stats, report)                 # G (catastrophic-drop)

    removed_stores = sum(
        plan["prod_districts"].get(f[:-5].replace(os.sep, "/"), 0)
        for f in plan["removed"]
        if f.endswith(".json") and "/" in f.replace(os.sep, "/")
    )
    report.note(
        "G.plan",
        f"생성 {len(plan['created'])} / 변경 {len(plan['modified'])} / "
        f"제거 {len(plan['removed'])} / 유지 {len(plan['kept'])} / "
        f"매장 {plan['prod_stores']} -> {plan['cand_stores']} / "
        f"제거 파일의 production 매장 합 {removed_stores}",
    )
    if plan["removed"]:
        report.note("G.removed_files", ", ".join(plan["removed"][:20]))
    return report, plan
