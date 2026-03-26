"use client";

import { useEffect, useRef, useState } from "react";

interface AdSlotProps {
  slotId: string;
  format?: "auto" | "fluid" | "rectangle";
  className?: string;
}

declare global {
  interface Window {
    adsbygoogle: unknown[];
  }
}

export default function AdSlot({
  slotId,
  format = "auto",
  className = "",
}: AdSlotProps) {
  const adRef = useRef<HTMLModElement>(null);
  const pushed = useRef(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (!adRef.current) return;
    if (pushed.current) return;

    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
      pushed.current = true;
    } catch (e) {
      // AdSense not loaded yet
    }
  }, [mounted]);

  if (!mounted) return null;

  return (
    <div className={`ad-container overflow-hidden ${className}`}>
      <ins
        key={slotId}
        ref={adRef}
        className="adsbygoogle"
        style={{ display: "block" }}
        data-ad-client="ca-pub-7976139023602789"
        data-ad-slot={slotId}
        data-ad-format={format}
        data-full-width-responsive="true"
      />
    </div>
  );
}
