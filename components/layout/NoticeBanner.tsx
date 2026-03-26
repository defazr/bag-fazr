"use client";

import { useState, useEffect } from "react";

export default function NoticeBanner() {
  const [dismissed, setDismissed] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("notice-dismissed");
    if (stored !== "true") {
      setDismissed(false);
    }
  }, []);

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem("notice-dismissed", "true");
  };

  if (dismissed) return null;

  return (
    <div className="sticky top-0 z-50 h-8 bg-orange-100 dark:bg-orange-900/30 border-b border-orange-200 dark:border-orange-800/30 overflow-hidden flex items-center">
      <div className="flex-1 overflow-hidden relative group">
        <p className="text-orange-800 dark:text-orange-300 text-xs whitespace-nowrap animate-ticker group-hover:[animation-play-state:paused]">
          현재 일부 지역은 종량제 봉투 품절이 발생하고 있습니다. 방문 전 재고
          확인을 권장드립니다.
        </p>
      </div>
      <button
        onClick={handleDismiss}
        className="shrink-0 px-2 text-orange-600 dark:text-orange-400 hover:text-orange-800 dark:hover:text-orange-200 text-xs leading-none"
        aria-label="공지 닫기"
      >
        ✕
      </button>
    </div>
  );
}
