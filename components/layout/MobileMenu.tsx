"use client";

import { useState } from "react";
import Link from "next/link";

export default function MobileMenu() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="sm:hidden rounded-lg p-2 text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
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
            onClick={() => setOpen(false)}
          />
          <div className="fixed top-0 right-0 z-50 h-full w-64 bg-white dark:bg-gray-900 shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 px-4 py-4">
              <span className="font-bold text-gray-900 dark:text-white">
                메뉴
              </span>
              <button
                onClick={() => setOpen(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                aria-label="메뉴 닫기"
              >
                ✕
              </button>
            </div>
            <nav className="px-4 py-4 space-y-1">
              <Link
                href="/"
                onClick={() => setOpen(false)}
                className="block rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                홈
              </Link>
              <Link
                href="/"
                onClick={() => setOpen(false)}
                className="block rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                지역 전체 보기
              </Link>
              <Link
                href="/article/shortage-2026"
                onClick={() => setOpen(false)}
                className="block rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                종량제 봉투 대란 이유
              </Link>
              <Link
                href="/article/why-no-bags"
                onClick={() => setOpen(false)}
                className="block rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                봉투 구하기 어려운 이유
              </Link>
            </nav>
          </div>
        </>
      )}
    </>
  );
}
