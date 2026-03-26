import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto max-w-4xl px-4 py-4">
        <Link href="/" className="text-xl font-bold text-gray-900">
          🗑️ 종량제 봉투 판매처 찾기
        </Link>
      </div>
    </header>
  );
}
