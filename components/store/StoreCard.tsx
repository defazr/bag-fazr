import type { Store } from "@/lib/types";

export default function StoreCard({ store }: { store: Store }) {
  const displayAddress = store.roadAddress || store.address;

  return (
    <div className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200">
      <h3 className="font-semibold text-gray-900 dark:text-white text-[15px]">
        {store.name}
      </h3>
      <p className="mt-1.5 text-sm text-gray-500 dark:text-zinc-400 leading-snug">
        {displayAddress}
      </p>
    </div>
  );
}
