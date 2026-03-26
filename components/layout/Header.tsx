import Link from "next/link";
import ThemeToggle from "./ThemeToggle";
import MobileMenu from "./MobileMenu";

export default function Header() {
  return (
    <header className="border-b border-gray-200 bg-white dark:border-zinc-800 dark:bg-zinc-950 h-14 flex items-center">
      <div className="mx-auto max-w-4xl w-full px-5 flex items-center justify-between">
        <Link
          href="/"
          className="text-base font-bold text-gray-900 dark:text-white"
        >
          홈
        </Link>
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <MobileMenu />
        </div>
      </div>
    </header>
  );
}
