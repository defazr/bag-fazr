import type { Store } from "@/lib/types";

export default function StoreCard({ store }: { store: Store }) {
  const displayAddress = store.roadAddress || store.address;

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900 text-[15px]">
          {store.name}
        </h3>
        <span className="shrink-0 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
          영업중
        </span>
      </div>
      <p className="mt-1.5 text-sm text-gray-500 leading-snug">
        {displayAddress}
      </p>
    </div>
  );
}
