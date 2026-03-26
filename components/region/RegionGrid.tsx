import Link from "next/link";
import type { RegionMeta } from "@/lib/types";

export default function RegionGrid({ regions }: { regions: RegionMeta[] }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
      {regions.map((r) => (
        <Link
          key={r.regionSlug}
          href={`/${r.regionSlug}`}
          className="flex flex-col items-center rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 text-center transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
        >
          <span className="font-medium text-gray-900 dark:text-white">{r.region}</span>
          <span className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
            {r.count > 0 ? `${r.count}곳` : "준비중"}
          </span>
        </Link>
      ))}
    </div>
  );
}
