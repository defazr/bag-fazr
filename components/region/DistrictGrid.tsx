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
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
      {districts.map((d) => (
        <Link
          key={d.districtSlug}
          href={`/${regionSlug}/${d.districtSlug}`}
          className="flex flex-col items-center rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 text-center transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
        >
          <span className="font-medium text-gray-900 dark:text-white">{d.district}</span>
          <span className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
            {d.count > 0 ? `${d.count}곳` : "판매처 정보 없음"}
          </span>
        </Link>
      ))}
    </div>
  );
}
