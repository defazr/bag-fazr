import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { getRegionIndex } from "@/lib/data";
import { getRegionBySlug, getRegionDisplay, REGIONS } from "@/lib/regions";
import { buildOpenGraph, getRegionFaqs } from "@/lib/seo";
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

  // 2026 통합으로 폐지된 시도명을 쓰는 region은 법정 약칭 + 옛 이름 병기.
  const rd = getRegionDisplay(region);
  const displayName = rd ? rd.longLabel : regionInfo.name;

  const totalCount = data?.totalCount ?? 0;
  return {
    title: rd
      // 병기 label이 길어서 공통 suffix(가격·크기·2026)를 뺀다.
      // 정확한 행정명 전달이 title 패턴 통일보다 우선이다.
      ? `${displayName} 종량제 봉투 파는곳 총정리`
      : `${displayName} 종량제 봉투 파는곳 총정리 | 가격 | 크기 (2026)`,
    description: `${displayName} ${districtCount}개 지역 종량제 봉투 판매처 ${totalCount.toLocaleString()}곳. 가격, 크기, 편의점 구매 정보까지 한눈에.`,
    alternates: {
      canonical: `https://bag.fazr.co.kr/${region}`,
    },
    openGraph: buildOpenGraph(
      `${displayName} 종량제 봉투 판매처 찾기`,
      `${displayName} ${districtCount}개 지역 판매처 ${totalCount.toLocaleString()}곳`,
      `/${region}`
    ),
  };
}

export default async function RegionPage({ params }: PageProps) {
  const { region } = await params;
  const regionInfo = getRegionBySlug(region);
  if (!regionInfo) notFound();

  const data = getRegionIndex(region);
  if (!data) notFound();

  const rd = getRegionDisplay(region);
  // title/H1/meta/FAQ가 같은 표시명을 쓰도록 한 곳에서 만든다.
  const displayName = rd ? rd.longLabel : regionInfo.name;
  // 링크 anchor·섹션 제목처럼 짧아야 하는 곳은 현재 행정명만 쓴다.
  const currentLabel = rd ? rd.currentLabel : regionInfo.name;

  // FAQ 답변이 "N개 시/군/구"로 개수를 말하므로 범위를 한정하는 병기형을 쓴다.
  // currentLabel만 쓰면 "광주특별시에는 5개 시/군/구"가 되어 사실과 다르다
  // (통합특별시 전체는 27개, 이 페이지는 옛 광주광역시 영역 5개).
  const faqs = getRegionFaqs(displayName, data.districts.length);

  // 인접 시/도 링크 (현재 region 제외)
  const adjacentRegions = REGIONS.filter((r) => r.slug !== region).slice(0, 4);

  return (
    <>
      <Breadcrumb items={[{ label: rd ? rd.shortLabel : regionInfo.name }]} />

      <section className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {displayName} 종량제 봉투 판매처
        </h1>
        <p className="mt-1 text-gray-600 dark:text-zinc-400">
          총 {data.totalCount.toLocaleString()}곳 · 데이터 수집일:{" "}
          {data.updatedAt}
        </p>
        <p className="mt-2 text-xs text-gray-400 dark:text-zinc-500">
          지역별 판매처 수는 공공데이터 기준이며, 일부 지역은 실제와 차이가 있을 수 있습니다.
        </p>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-bold text-gray-900 dark:text-white">
          {currentLabel} 지역별 판매처
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
              {getRegionDisplay(r.slug)?.currentLabel ?? r.name}
            </Link>
          ))}
        </div>
      </section>

      {/* 광고: 하단 */}
      <AdSlot slotId="6518541657" className="mt-8" />
    </>
  );
}
