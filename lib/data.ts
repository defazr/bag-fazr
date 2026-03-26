import fs from "fs";
import path from "path";
import type { RegionsJson, RegionIndex, DistrictData } from "./types";

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
