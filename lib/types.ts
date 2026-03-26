export interface Store {
  name: string;
  address: string;
  roadAddress: string;
  status: string;
  licenseDate: string;
}

export interface DistrictData {
  region: string;
  regionSlug: string;
  district: string;
  districtSlug: string;
  updatedAt: string;
  totalCount: number;
  stores: Store[];
}

export interface RegionIndexEntry {
  district: string;
  districtSlug: string;
  count: number;
}

export interface RegionIndex {
  region: string;
  regionSlug: string;
  updatedAt: string;
  totalCount: number;
  districts: RegionIndexEntry[];
}

export interface RegionMeta {
  region: string;
  regionSlug: string;
  count: number;
}

export interface RegionsJson {
  updatedAt: string;
  totalCount: number;
  regions: RegionMeta[];
}

export interface DistrictMapping {
  name: string;
  slug: string;
  regionSlug: string;
  apiCode: string;
}

export interface RegionMapping {
  name: string;
  slug: string;
  apiCode: string;
}
