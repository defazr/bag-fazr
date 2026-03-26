import type { Store } from "@/lib/types";

export default function StoreCard({ store }: { store: Store }) {
  const displayAddress = store.roadAddress || store.address;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium text-gray-900">{store.name}</h3>
        <span className="shrink-0 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
          {store.status}
        </span>
      </div>
      <p className="mt-1 text-sm text-gray-600">{displayAddress}</p>
    </div>
  );
}
