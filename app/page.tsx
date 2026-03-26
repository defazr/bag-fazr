import type { Metadata } from "next";
import Link from "next/link";
import { getRegionsData } from "@/lib/data";
import RegionGrid from "@/components/region/RegionGrid";
import FaqSection from "@/components/seo/FaqSection";
import AdSlot from "@/components/ads/AdSlot";

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
      <section className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900">
          종량제 봉투 판매처 찾기
        </h1>
        <p className="mt-2 text-gray-600">
          전국 {data.totalCount.toLocaleString()}곳의 판매처 정보를 제공합니다
        </p>
        <p className="mt-1 text-sm text-gray-400">
          데이터 갱신일: {data.updatedAt}
        </p>
      </section>

      {/* 광고: 상단 */}
      <AdSlot slotId="8836749083" className="mb-6" />

      <section>
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          지역별 판매처
        </h2>
        <RegionGrid regions={data.regions} />
      </section>

      {/* 최근 이슈 */}
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900">
          최근 종량제 봉투 이슈
        </h2>
        <Link
          href="/article/shortage-2026"
          className="block rounded-lg border border-gray-200 bg-white p-4 hover:border-blue-300 hover:shadow-sm"
        >
          <p className="font-semibold text-gray-900">
            종량제 봉투 대란 이유 총정리 (2026 최신)
          </p>
          <p className="mt-1 text-sm text-gray-500">
            나프타 수급 불안, 수요 급증, 물류 지연까지. 왜 종량제 봉투를 못
            구하는지 원인과 대처법을 정리했습니다.
          </p>
        </Link>
      </section>

      <FaqSection faqs={faqs} />

      {/* 광고: 하단 */}
      <AdSlot slotId="6518541657" className="mt-8" />
    </>
  );
}
