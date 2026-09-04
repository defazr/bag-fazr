import fs from "fs";
import path from "path";
import type { RegionsJson, RegionIndex, DistrictData, Store } from "./types";

const DATA_DIR = path.join(process.cwd(), "data");

export function getRegionsData(): RegionsJson {
  const filePath = path.join(DATA_DIR, "regions.json");
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as RegionsJson;
}

export function getRegionIndex(regionSlug: string): RegionIndex | null {
  const filePath = path.join(DATA_DIR, regionSlug, "index.json");
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as RegionIndex;
}

export function getDistrictData(
  regionSlug: string,
  districtSlug: string
): DistrictData | null {
  const filePath = path.join(DATA_DIR, regionSlug, `${districtSlug}.json`);
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as DistrictData;
}

// P20 Phase 1: region 페이지에 노출할 district 대표 판매처 1곳을 고른다.
//
// 표시 가능한 기존 필드만으로 완전 결정적 순서를 만든다. name 하나만으로 정렬하면
// 동일 상호명이 있을 때 수집 순서(API 응답 순서)가 tie-breaker로 다시 새어 들어와,
// 재수집마다 대표 매장이 바뀌어 pilot 측정이 오염된다.
//
// localeCompare는 쓰지 않는다. ICU 로케일 데이터에 의존해 Node 버전·플랫폼마다
// 결과가 달라질 수 있어 빌드 재현성을 보장하지 못한다. 코드포인트 비교는 결정적이다.
const SAMPLE_SORT_KEYS: (keyof Store)[] = [
  "name",
  "roadAddress",
  "address",
  "licenseDate",
  "status",
];

export function getDistrictSampleStore(
  regionSlug: string,
  districtSlug: string
): Store | null {
  const data = getDistrictData(regionSlug, districtSlug);
  if (!data || data.stores.length === 0) return null;

  // 원본 배열을 in-place sort 하지 않는다.
  const sorted = [...data.stores].sort((a, b) => {
    for (const key of SAMPLE_SORT_KEYS) {
      const av = a[key] ?? "";
      const bv = b[key] ?? "";
      if (av !== bv) return av < bv ? -1 : 1;
    }
    return 0;
  });
  return sorted[0];
}
