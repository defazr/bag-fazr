import type { Store } from "@/lib/types";

export default function StoreCard({ store }: { store: Store }) {
  const displayAddress = store.roadAddress || store.address;

  return (
    <div className="rounded-lg border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 py-3 shadow-sm transition hover:shadow-md duration-200">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-[15px]">
          {store.name}
        </h3>
        <span className="shrink-0 rounded-full bg-green-100 dark:bg-green-900/30 px-2 py-0.5 text-xs font-medium text-green-700 dark:text-green-400">
          영업중
        </span>
      </div>
      <p className="mt-1.5 text-sm text-gray-500 dark:text-gray-400 leading-snug">
        {displayAddress}
      </p>
    </div>
  );
}
