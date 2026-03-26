import type { Metadata } from "next";
import Link from "next/link";
import { getRegionsData } from "@/lib/data";
import RegionGrid from "@/components/region/RegionGrid";
import FaqSection from "@/components/seo/FaqSection";
// import AdSlot from "@/components/ads/AdSlot";

export const revalidate = 86400;

export const metadata: Metadata = {
  title: "종량제 봉투 파는곳 | 전국 판매처 찾기 (2026 최신)",
  description:
    "전국 종량제 봉투 판매처를 지역별로 빠르게 찾아보세요. 영업 중인 판매점만 제공합니다.",
  alternates: {
    canonical: "https://bag.fazr.co.kr",
  },
};

export default function HomePage() {
  const data = getRegionsData();

  const faqs = [
    {
      question: "종량제 봉투는 어디서 사나요?",
      answer:
        "종량제 봉투는 편의점, 마트, 슈퍼마켓 등에서 구매할 수 있습니다. 이 사이트에서 지역별 판매처를 확인하세요.",
    },
    {
      question: "종량제 봉투가 품귀인 이유는?",
      answer:
        "2026년 3월 기준 중동 정세 불안으로 나프타 수급에 차질이 생기면서 종량제 봉투 원료 공급이 불안정해졌습니다.",
    },
    {
      question: "종량제 봉투 가격은 전국 동일한가요?",
      answer:
        "아닙니다. 종량제 봉투 가격은 지자체마다 다르게 책정됩니다. 정확한 가격은 해당 지역 판매처에 문의하세요.",
    },
  ];

  return (
    <>
      <section className="mt-10 mb-2 text-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          종량제 봉투 판매처 찾기
        </h1>
        <p className="mt-2 text-gray-600 dark:text-zinc-400 text-sm">
          전국 {data.totalCount.toLocaleString()}곳의 판매처 정보를 제공합니다
        </p>
        <p className="mt-1 text-sm text-gray-400 dark:text-zinc-500">
          데이터 갱신일: {data.updatedAt}
        </p>
      </section>

      {/* 자주 찾는 지역 */}
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900 dark:text-white">
          자주 찾는 지역
        </h2>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {[
            { name: "강남구", href: "/seoul/gangnam" },
            { name: "송파구", href: "/seoul/songpa" },
            { name: "서초구", href: "/seoul/seocho" },
            { name: "수원시", href: "/gyeonggi/suwon" },
            { name: "성남시", href: "/gyeonggi/seongnam" },
            { name: "해운대구", href: "/busan/haeundae" },
          ].map((d) => (
            <Link
              key={d.href}
              href={d.href}
              className="whitespace-nowrap rounded-full border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 py-1.5 text-sm text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-800 transition duration-200"
            >
              {d.name}
            </Link>
          ))}
        </div>
      </section>

      {/* 광고: 상단
      <AdSlot slotId="8836749083" className="my-10" /> */}

      <section id="regions" className="mt-10">
        <h2 className="mb-4 text-lg font-bold text-gray-900 dark:text-white">
          지역별 판매처
        </h2>
        <RegionGrid regions={data.regions} />
      </section>

      {/* 종량제 봉투 이슈 */}
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900 dark:text-white">
          종량제 봉투, 요즘 왜 이런가요?
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link
            href="/article/shortage-2026"
            className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 hover:bg-gray-50 dark:hover:bg-zinc-800 transition duration-200"
          >
            <p className="font-semibold text-gray-900 dark:text-white">
              종량제 봉투 대란 이유 총정리
            </p>
            <p className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
              나프타 수급 불안, 사재기, 물류 지연까지. 원인과 대처법을 정리했습니다.
            </p>
          </Link>
          <Link
            href="/article/why-no-bags"
            className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 hover:bg-gray-50 dark:hover:bg-zinc-800 transition duration-200"
          >
            <p className="font-semibold text-gray-900 dark:text-white">
              종량제 봉투 왜 없을까? 직접 확인해봤습니다
            </p>
            <p className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
              편의점 3곳을 돌아도 없어서 직접 찾아본 후기와 구매 팁을 정리했습니다.
            </p>
          </Link>
        </div>
      </section>

      {/* 종량제 봉투 가격 */}
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900 dark:text-white">
          종량제 봉투 가격
        </h2>
        <div className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
          <div className="flex gap-6">
            <div>
              <span className="text-sm text-gray-500 dark:text-zinc-500">10L</span>
              <p className="text-lg font-bold text-gray-900 dark:text-white">250원</p>
            </div>
            <div>
              <span className="text-sm text-gray-500 dark:text-zinc-500">20L</span>
              <p className="text-lg font-bold text-gray-900 dark:text-white">490원</p>
            </div>
            <div>
              <span className="text-sm text-gray-500 dark:text-zinc-500">50L</span>
              <p className="text-lg font-bold text-gray-900 dark:text-white">1,250원</p>
            </div>
          </div>
          <p className="mt-3 text-xs text-gray-400 dark:text-zinc-500">
            ※ 가격은 지역에 따라 다를 수 있습니다
          </p>
          <a
            href="#regions"
            className="mt-3 inline-block rounded-xl border border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 px-4 py-2 text-sm font-medium text-gray-700 dark:text-white hover:bg-gray-100 dark:hover:bg-zinc-700 transition"
          >
            지역별 가격 확인하기 →
          </a>
        </div>
      </section>

      <FaqSection faqs={faqs} />

      {/* 광고: 하단
      <AdSlot slotId="6518541657" className="my-10" /> */}
    </>
  );
}
