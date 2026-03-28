"use client";

import { useState, useEffect, useRef } from "react";
import type { Store } from "@/lib/types";
import StoreCard from "./StoreCard";

const INITIAL_COUNT = 15;

const SEARCH_ALIAS: Record<string, string[]> = {
  cu: ["씨유", "CU"],
  gs: ["GS25", "지에스", "gs25"],
  gs25: ["GS25", "지에스"],
  세븐: ["세븐일레븐", "7-Eleven"],
  이마트: ["이마트", "EMART", "E-MART"],
  홈플러스: ["홈플러스", "HOMEPLUS"],
  롯데마트: ["롯데마트", "LOTTE"],
  미니스톱: ["미니스톱", "MINISTOP"],
};

interface StoreListProps {
  stores: Store[];
}

export default function StoreList({ stores }: StoreListProps) {
  const [query, setQuery] = useState("");
  const [visibleCount, setVisibleCount] = useState(INITIAL_COUNT);
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setDebouncedQuery(query);
      setVisibleCount(INITIAL_COUNT);
    }, 200);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [query]);

  const filtered = debouncedQuery
    ? stores.filter((s) => {
        const q = debouncedQuery.toLowerCase();
        const aliases = SEARCH_ALIAS[q] ?? [];
        const keywords = [debouncedQuery, ...aliases];
        const haystack = `${s.name} ${s.address ?? ""} ${s.roadAddress ?? ""}`;
        return keywords.some((kw) => haystack.toLowerCase().includes(kw.toLowerCase()));
      })
    : stores;

  const visible = filtered.slice(0, visibleCount);
  const hasMore = visibleCount < filtered.length;

  return (
    <div className="space-y-3">
      {/* 검색 */}
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="편의점·마트 이름으로 검색 (예: CU, GS25, 이마트)"
        className="w-full rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 py-2.5 text-sm text-gray-900 dark:text-zinc-100 placeholder-gray-400 dark:placeholder-zinc-500 outline-none focus:border-zinc-500 dark:focus:border-zinc-600"
      />

      {/* 결과 수 */}
      {debouncedQuery && (
        <p className="text-xs text-gray-500 dark:text-zinc-500">
          검색 결과: {filtered.length}곳
        </p>
      )}

      {/* 리스트 */}
      {visible.length === 0 ? (
        <div className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 py-8 text-center text-sm text-gray-500 dark:text-zinc-500">
          검색 결과 없음
        </div>
      ) : (
        visible.map((store, i) => (
          <StoreCard key={i} store={store} />
        ))
      )}

      {/* 더보기 */}
      {hasMore && (
        <button
          onClick={() => setVisibleCount((prev) => prev + 15)}
          className="w-full rounded-xl bg-gray-100 dark:bg-zinc-800 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-zinc-300 hover:bg-gray-200 dark:hover:bg-zinc-700 transition duration-200"
        >
          판매처 더 보기 ({filtered.length - visibleCount}곳 남음)
        </button>
      )}
    </div>
  );
}
