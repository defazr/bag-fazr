import Link from "next/link";

export default function NotFound() {
  return (
    <div className="py-20 text-center">
      <h1 className="text-4xl font-bold text-gray-900 dark:text-white">404</h1>
      <p className="mt-2 text-gray-600 dark:text-zinc-400">페이지를 찾을 수 없습니다.</p>
      <Link
        href="/"
        className="mt-4 inline-block rounded-lg bg-blue-600 dark:bg-zinc-800 dark:border dark:border-zinc-700 px-4 py-2 text-sm text-white hover:bg-blue-700 dark:hover:bg-zinc-700"
      >
        메인으로 돌아가기
      </Link>
    </div>
  );
}
