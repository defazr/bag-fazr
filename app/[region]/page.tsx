import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getRegionIndex } from "@/lib/data";
import { getRegionBySlug, REGIONS } from "@/lib/regions";
import { getRegionFaqs } from "@/lib/seo";
import DistrictGrid from "@/components/region/DistrictGrid";
import Breadcrumb from "@/components/seo/Breadcrumb";
import FaqSection from "@/components/seo/FaqSection";

export const revalidate = 86400;

interface PageProps {
  params: Promise<{ region: string }>;
}

export async function generateStaticParams() {
  return REGIONS.map((r) => ({ region: r.slug }));
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { region } = await params;
  const regionInfo = getRegionBySlug(region);
  if (!regionInfo) return {};

  const data = getRegionIndex(region);
  const districtCount = data?.districts.length ?? 0;

  return {
    title: `${regionInfo.name} 종량제 봉투 파는곳 | 구별 판매처 총정리`,
    description: `${regionInfo.name} ${districtCount}개 지역의 종량제 봉투 판매처를 확인하세요.`,
    alternates: {
      canonical: `https://bag.fazr.co.kr/${region}`,
    },
  };
}

export default async function RegionPage({ params }: PageProps) {
  const { region } = await params;
  const regionInfo = getRegionBySlug(region);
  if (!regionInfo) notFound();

  const data = getRegionIndex(region);
  if (!data) notFound();

  const faqs = getRegionFaqs(regionInfo.name, data.districts.length);

  // 인접 시/도 링크 (현재 region 제외)
  const adjacentRegions = REGIONS.filter((r) => r.slug !== region).slice(0, 4);

  return (
    <>
      <Breadcrumb items={[{ label: regionInfo.name }]} />

      <section className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          {regionInfo.name} 종량제 봉투 판매처
        </h1>
        <p className="mt-1 text-gray-600">
          총 {data.totalCount.toLocaleString()}곳 · 데이터 갱신일:{" "}
          {data.updatedAt}
        </p>
      </section>

      {/* 광고 슬롯 */}
      <div className="mb-6 min-h-[90px] rounded-lg border border-dashed border-gray-300 bg-gray-50 flex items-center justify-center text-sm text-gray-400">
        광고 영역
      </div>

      <section>
        <h2 className="mb-4 text-lg font-bold text-gray-900">
          {regionInfo.name} 지역별 판매처
        </h2>
        <DistrictGrid regionSlug={region} districts={data.districts} />
      </section>

      <FaqSection faqs={faqs} />

      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900">
          다른 지역 판매처
        </h2>
        <div className="flex flex-wrap gap-2">
          {adjacentRegions.map((r) => (
            <a
              key={r.slug}
              href={`/${r.slug}`}
              className="rounded-full border border-gray-200 px-3 py-1 text-sm text-gray-600 hover:border-blue-300 hover:text-blue-600"
            >
              {r.name}
            </a>
          ))}
        </div>
      </section>
    </>
  );
}
