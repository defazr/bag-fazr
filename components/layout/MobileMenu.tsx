"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

export default function MobileMenu() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open]);

  const close = () => setOpen(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="sm:hidden rounded-lg p-2 text-gray-600 hover:bg-gray-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
        aria-label="메뉴 열기"
      >
        <svg
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-50 bg-black/40"
            onClick={close}
          />
          <div className="fixed top-0 right-0 z-50 h-full w-64 bg-white dark:bg-zinc-950 shadow-xl animate-slide-in overflow-y-auto">
            {/* 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-200 dark:border-zinc-800 px-4 py-4">
              <span className="font-bold text-gray-900 dark:text-white">
                메뉴
              </span>
              <button
                onClick={close}
                className="text-gray-500 hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200"
                aria-label="메뉴 닫기"
              >
                ✕
              </button>
            </div>

            {/* ① CTA */}
            <div className="px-4 pt-4 pb-2">
              <Link
                href="/"
                onClick={close}
                className="block rounded-xl bg-gray-900 dark:bg-zinc-800 px-4 py-3.5 text-center text-sm font-medium text-white hover:bg-gray-800 dark:hover:bg-zinc-700 transition duration-200"
              >
                종량제 봉투 판매처 확인하기 →
              </Link>
            </div>

            {/* ② 빠른 이동 */}
            <div className="px-4 pt-4">
              <p className="px-3 pb-2 text-xs font-medium text-gray-400 dark:text-zinc-500">
                빠른 이동
              </p>
              <nav className="space-y-1">
                <Link
                  href="/seoul"
                  onClick={close}
                  className="block rounded-xl px-3 py-2.5 text-sm text-gray-700 hover:bg-gray-100 dark:text-zinc-300 dark:hover:bg-zinc-800 transition duration-200"
                >
                  서울
                </Link>
                <Link
                  href="/gyeonggi"
                  onClick={close}
                  className="block rounded-xl px-3 py-2.5 text-sm text-gray-700 hover:bg-gray-100 dark:text-zinc-300 dark:hover:bg-zinc-800 transition duration-200"
                >
                  경기
                </Link>
                <Link
                  href="/busan"
                  onClick={close}
                  className="block rounded-xl px-3 py-2.5 text-sm text-gray-700 hover:bg-gray-100 dark:text-zinc-300 dark:hover:bg-zinc-800 transition duration-200"
                >
                  부산
                </Link>
                <Link
                  href="/incheon"
                  onClick={close}
                  className="block rounded-xl px-3 py-2.5 text-sm text-gray-700 hover:bg-gray-100 dark:text-zinc-300 dark:hover:bg-zinc-800 transition duration-200"
                >
                  인천
                </Link>
              </nav>
            </div>

            {/* ③ 정보 */}
            <div className="px-4 pt-4">
              <p className="px-3 pb-2 text-xs font-medium text-gray-400 dark:text-zinc-500">
                정보
              </p>
              <nav className="space-y-1">
                <Link
                  href="/article/why-no-bags"
                  onClick={close}
                  className="block rounded-xl px-3 py-2.5 text-sm text-gray-700 hover:bg-gray-100 dark:text-zinc-300 dark:hover:bg-zinc-800 transition duration-200"
                >
                  왜 종량제 봉투가 없을까?
                </Link>
                <Link
                  href="/article/shortage-2026"
                  onClick={close}
                  className="block rounded-xl px-3 py-2.5 text-sm text-gray-700 hover:bg-gray-100 dark:text-zinc-300 dark:hover:bg-zinc-800 transition duration-200"
                >
                  종량제 봉투 대란 이유
                </Link>
              </nav>
            </div>
          </div>
        </>
      )}
    </>
  );
}
