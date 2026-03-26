"use client";

import AdSlot from "./AdSlot";

export default function StickyBottomAd() {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 sm:hidden">
      <AdSlot slotId="3611374960" format="auto" className="min-h-[50px]" />
    </div>
  );
}
