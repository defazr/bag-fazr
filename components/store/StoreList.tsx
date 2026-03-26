import type { Store } from "@/lib/types";
import StoreCard from "./StoreCard";

interface StoreListProps {
  stores: Store[];
}

export default function StoreList({ stores }: StoreListProps) {
  return (
    <div className="space-y-3">
      {/* 광고 슬롯: 상단 */}
      <div className="min-h-[90px] rounded-lg border border-dashed border-gray-300 dark:border-zinc-600 bg-gray-50 dark:bg-zinc-800 flex items-center justify-center text-sm text-gray-400 dark:text-gray-500">
        광고 영역
      </div>

      {stores.map((store, i) => (
        <div key={i}>
          <StoreCard store={store} />
          {/* 광고 슬롯: 5개마다 */}
          {(i + 1) % 5 === 0 && i < stores.length - 1 && (
            <div className="mt-3 min-h-[90px] rounded-lg border border-dashed border-gray-300 dark:border-zinc-600 bg-gray-50 dark:bg-zinc-800 flex items-center justify-center text-sm text-gray-400 dark:text-gray-500">
              광고 영역
            </div>
          )}
        </div>
      ))}

      {/* 광고 슬롯: 하단 */}
      <div className="min-h-[90px] rounded-lg border border-dashed border-gray-300 dark:border-zinc-600 bg-gray-50 dark:bg-zinc-800 flex items-center justify-center text-sm text-gray-400 dark:text-gray-500">
        광고 영역
      </div>
    </div>
  );
}
