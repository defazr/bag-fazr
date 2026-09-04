import Link from "next/link";
import { getLegacyDisplay } from "@/lib/regions";
import type { RegionIndexEntry, Store } from "@/lib/types";

interface DistrictGridProps {
  regionSlug: string;
  districts: RegionIndexEntry[];
  // P20 Phase 1 pilot. 넘기지 않으면 기존 렌더와 완전히 동일하다.
  samples?: Record<string, Store>;
}

export default function DistrictGrid({
  regionSlug,
  districts,
  samples,
}: DistrictGridProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
      {districts.map((d) => {
        // 2026 행정구역 개편으로 이름이 달라진 legacy bucket은 현재 행정구역명을
        // 주 label로, 옛 이름을 보조 문구로 2단 표시한다. 괄호 병기 한 줄로 넣으면
        // 좁은 카드에서 줄바꿈이 지저분해진다.
        const legacy = getLegacyDisplay(regionSlug, d.districtSlug);
        // 판매처가 없는 구군은 대표 매장을 출력하지 않는다. 다른 구군 매장으로
        // 대체하거나 placeholder를 만들지 않는다.
        const sample = samples?.[d.districtSlug];
        const sampleAddress = sample
          ? sample.roadAddress || sample.address
          : "";
        return (
        <Link
          key={d.districtSlug}
          href={`/${regionSlug}/${d.districtSlug}`}
          className="group flex items-center justify-between rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 cursor-pointer transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
        >
          <div className="min-w-0">
            <span className="font-medium text-gray-900 dark:text-white">
              {legacy ? legacy.selectorMain : d.district}
            </span>
            {legacy && (
              <span className="block text-xs text-gray-400 dark:text-zinc-500">
                {legacy.selectorLegacy}
              </span>
            )}
            <span className="block text-sm text-gray-500 dark:text-zinc-400">
              {d.count > 0 ? `${d.count}곳` : "판매처 정보 없음"}
            </span>
            {sample && (
              <span className="mt-2 block text-xs text-gray-500 dark:text-zinc-400 leading-snug">
                판매처 예시: {sample.name}
                {sampleAddress && ` · ${sampleAddress}`}
              </span>
            )}
          </div>
          <span className="shrink-0 text-gray-400 dark:text-zinc-500 group-hover:text-gray-700 dark:group-hover:text-zinc-300 transition duration-200">→</span>
        </Link>
        );
      })}
    </div>
  );
}
