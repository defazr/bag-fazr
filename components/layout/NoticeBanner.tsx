"use client";

import { useState } from "react";

export default function NoticeBanner() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="sticky top-0 z-50 bg-amber-500 text-white text-sm">
      <div className="mx-auto max-w-4xl px-4 py-2 flex items-center justify-between">
        <p>
          ⚠️ 현재 일부 지역은 종량제 봉투 품절이 발생하고 있습니다. 데이터가
          제한될 수 있습니다.
        </p>
        <button
          onClick={() => setDismissed(true)}
          className="ml-4 shrink-0 text-white/80 hover:text-white text-lg leading-none"
          aria-label="공지 닫기"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
