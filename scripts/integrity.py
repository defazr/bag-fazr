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


def diff_trees(prod_root: str, cand_root: str) -> dict:
    """G. production 트리와 candidate 트리의 차이를 명시적으로 계산한다.

    stale 삭제는 즉시 mutation이 아니라 이 차이의 결과여야 한다.
    """
    prod = read_tree(prod_root)["files"]
    cand = read_tree(cand_root)["files"]
    created = sorted(set(cand) - set(prod))
    removed = sorted(set(prod) - set(cand))
    common = set(prod) & set(cand)
    modified = sorted(p for p in common if prod[p] != cand[p])
    kept = sorted(p for p in common if prod[p] == cand[p])
    return {
        "created": created,
        "removed": removed,
        "modified": modified,
        "kept": kept,
        "prod_files": len(prod),
        "cand_files": len(cand),
    }


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
    report.note(
        "G.plan",
        f"생성 {len(plan['created'])} / 변경 {len(plan['modified'])} / "
        f"제거 {len(plan['removed'])} / 유지 {len(plan['kept'])}",
    )
    return report, plan
