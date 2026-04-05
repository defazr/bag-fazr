import Link from "next/link";

export default function RegionLinks() {
  const regions = [
    { name: "서울", href: "/seoul" },
    { name: "경기", href: "/gyeonggi" },
    { name: "부산", href: "/busan" },
    { name: "인천", href: "/incheon" },
    { name: "대구", href: "/daegu" },
    { name: "광주", href: "/gwangju" },
  ];

  return (
    <section className="mt-8">
      <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-white">
        지역별 종량제 봉투 판매처 바로가기
      </h3>

      <div className="flex flex-wrap gap-2">
        {regions.map((r) => (
          <Link
            key={r.href}
            href={r.href}
            className="inline-block px-3 py-1.5 text-xs rounded-full border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-800 transition"
          >
            {r.name}
          </Link>
        ))}
      </div>
    </section>
  );
}
