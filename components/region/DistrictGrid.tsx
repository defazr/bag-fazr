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
          className="group flex items-center justify-between rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 cursor-pointer transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
        >
          <div>
            <span className="font-medium text-gray-900 dark:text-white">{d.district}</span>
            <span className="block text-sm text-gray-500 dark:text-zinc-400">
              {d.count > 0 ? `${d.count}곳` : "판매처 정보 없음"}
            </span>
          </div>
          <span className="text-gray-400 dark:text-zinc-500 group-hover:text-gray-700 dark:group-hover:text-zinc-300 transition duration-200">→</span>
        </Link>
      ))}
    </div>
  );
}
