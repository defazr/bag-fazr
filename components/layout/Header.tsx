import Link from "next/link";
import ThemeToggle from "./ThemeToggle";
import MobileMenu from "./MobileMenu";

export default function Header() {
  return (
    <header className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
      <div className="mx-auto max-w-4xl px-4 py-4 flex items-center justify-between">
        <Link
          href="/"
          className="text-xl font-bold text-gray-900 dark:text-white"
        >
          🗑️ 종량제 봉투 판매처 찾기
        </Link>
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <MobileMenu />
        </div>
      </div>
    </header>
  );
}
