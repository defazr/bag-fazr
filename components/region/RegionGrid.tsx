import Link from "next/link";
import { getRegionDisplay } from "@/lib/regions";
import type { RegionMeta } from "@/lib/types";

export default function RegionGrid({ regions }: { regions: RegionMeta[] }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
      {regions.map((r) => {
        // 2026 통합으로 시도명이 바뀐 region은 카드에 옛 이름을 한 줄 덧붙인다.
        // /gwangju와 /jeonnam은 주 label이 둘 다 "광주특별시"라서
        // 이 보조 문구가 없으면 카드만 보고 구분할 수 없다.
        const rd = getRegionDisplay(r.regionSlug);
        return (
        <Link
          key={r.regionSlug}
          href={`/${r.regionSlug}`}
          className="flex flex-col items-center rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 text-center transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
        >
          <span className="font-medium text-gray-900 dark:text-white">
            {rd ? rd.currentLabel : r.region}
          </span>
          {rd && (
            <span className="mt-0.5 text-xs text-gray-500 dark:text-zinc-400">
              {rd.legacyLabel}
            </span>
          )}
          <span className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
            {r.count > 0 ? `${r.count}곳` : "준비중"}
          </span>
        </Link>
        );
      })}
    </div>
  );
}
