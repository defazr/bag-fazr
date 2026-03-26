import Link from "next/link";

export default function NotFound() {
  return (
    <div className="py-20 text-center">
      <h1 className="text-4xl font-bold text-gray-900 dark:text-white">404</h1>
      <p className="mt-2 text-gray-600 dark:text-zinc-400">페이지를 찾을 수 없습니다.</p>
      <Link
        href="/"
        className="mt-4 inline-block rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-white hover:bg-gray-50 dark:hover:bg-zinc-700"
      >
        메인으로 돌아가기
      </Link>
    </div>
  );
}
