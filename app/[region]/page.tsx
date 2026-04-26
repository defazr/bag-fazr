import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { getRegionIndex } from "@/lib/data";
import { getRegionBySlug, REGIONS } from "@/lib/regions";
import { getRegionFaqs } from "@/lib/seo";
import DistrictGrid from "@/components/region/DistrictGrid";
import Breadcrumb from "@/components/seo/Breadcrumb";
import FaqSection from "@/components/seo/FaqSection";
import AdSlot from "@/components/ads/AdSlot";

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

  const totalCount = data?.totalCount ?? 0;
  return {
    title: `${regionInfo.name} 종량제 봉투 파는곳 총정리 | 가격 | 크기 (2026)`,
    description: `${regionInfo.name} ${districtCount}개 지역 종량제 봉투 판매처 ${totalCount.toLocaleString()}곳. 가격, 크기, 편의점 구매 정보까지 한눈에.`,
    alternates: {
      canonical: `https://bag.fazr.co.kr/${region}`,
    },
    openGraph: {
      title: `${regionInfo.name} 종량제 봉투 판매처 찾기`,
      description: `${regionInfo.name} ${districtCount}개 지역 판매처 ${totalCount.toLocaleString()}곳`,
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {regionInfo.name} 종량제 봉투 판매처
        </h1>
        <p className="mt-1 text-gray-600 dark:text-zinc-400">
          총 {data.totalCount.toLocaleString()}곳 · 데이터 갱신일:{" "}
          {data.updatedAt}
        </p>
        <p className="mt-2 text-xs text-gray-400 dark:text-zinc-500">
          지역별 판매처 수는 공공데이터 기준이며, 일부 지역은 실제와 차이가 있을 수 있습니다.
        </p>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-bold text-gray-900 dark:text-white">
          {regionInfo.name} 지역별 판매처
        </h2>
        <DistrictGrid regionSlug={region} districts={data.districts} />
      </section>

      {/* 광고: 리스트 아래 */}
      <AdSlot slotId="8836749083" className="my-6" />

      <div className="mt-6 mb-6">
        <p className="text-sm text-gray-600 dark:text-zinc-400">
          종량제봉투 어디서 사는지 한눈에 보려면{" "}
          <Link
            href="/article/where-to-buy"
            className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition"
          >
            전국 판매처 총정리
          </Link>
          를 확인하세요.
        </p>
        <p className="mt-1 text-xs text-gray-500 dark:text-zinc-500">
          지역별 판매처 기준과 구매 방법을 정리한 페이지입니다.
        </p>
      </div>

      <FaqSection faqs={faqs} />

      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900 dark:text-white">
          다른 지역 판매처
        </h2>
        <div className="flex flex-wrap gap-2">
          {adjacentRegions.map((r) => (
            <Link
              key={r.slug}
              href={`/${r.slug}`}
              className="rounded-full border border-gray-200 dark:border-zinc-800 px-3 py-1 text-sm text-gray-600 dark:text-zinc-400 hover:bg-gray-50 dark:hover:bg-zinc-800 transition duration-200"
            >
              {r.name}
            </Link>
          ))}
        </div>
      </section>

      {/* 광고: 하단 */}
      <AdSlot slotId="6518541657" className="mt-8" />
    </>
  );
}
