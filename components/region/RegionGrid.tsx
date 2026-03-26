import Link from "next/link";
import type { RegionMeta } from "@/lib/types";

export default function RegionGrid({ regions }: { regions: RegionMeta[] }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
      {regions.map((r) => (
        <Link
          key={r.regionSlug}
          href={`/${r.regionSlug}`}
          className="flex flex-col items-center rounded-lg border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 p-4 text-center transition hover:border-blue-300 hover:shadow-md duration-200"
        >
          <span className="font-medium text-gray-900 dark:text-gray-100">{r.region}</span>
          <span className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {r.count > 0 ? `${r.count}곳` : "준비중"}
          </span>
        </Link>
      ))}
    </div>
  );
}
