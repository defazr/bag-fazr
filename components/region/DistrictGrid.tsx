import Link from "next/link";
import type { RegionIndexEntry } from "@/lib/types";

interface DistrictGridProps {
  regionSlug: string;
  districts: RegionIndexEntry[];
}

export default function DistrictGrid({
  regionSlug,
  districts,
}: DistrictGridProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
      {districts.map((d) => (
        <Link
          key={d.districtSlug}
          href={`/${regionSlug}/${d.districtSlug}`}
          className="flex flex-col items-center rounded-lg border border-gray-200 bg-white p-4 text-center transition hover:border-blue-300 hover:shadow-sm"
        >
          <span className="font-medium text-gray-900">{d.district}</span>
          <span className="mt-1 text-sm text-gray-500">
            {d.count > 0 ? `${d.count}곳` : "준비중"}
          </span>
        </Link>
      ))}
    </div>
  );
}
