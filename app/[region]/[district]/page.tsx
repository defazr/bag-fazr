import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { getDistrictData, getRegionIndex } from "@/lib/data";
import {
  getRegionBySlug,
  getDistrictBySlug,
  getDistrictsByRegion,
  REGIONS,
} from "@/lib/regions";
import { getDistrictFaqs } from "@/lib/seo";
import StoreList from "@/components/store/StoreList";
import Breadcrumb from "@/components/seo/Breadcrumb";
import FaqSection from "@/components/seo/FaqSection";

export const revalidate = 86400;

interface PageProps {
  params: Promise<{ region: string; district: string }>;
}

export async function generateStaticParams() {
  const params: { region: string; district: string }[] = [];
  for (const r of REGIONS) {
    const districts = getDistrictsByRegion(r.slug);
    for (const d of districts) {
      params.push({ region: r.slug, district: d.slug });
    }
  }
  return params;
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { region, district } = await params;
  const regionInfo = getRegionBySlug(region);
  const districtInfo = getDistrictBySlug(region, district);
  if (!regionInfo || !districtInfo) return {};

  const data = getDistrictData(region, district);
  const count = data?.totalCount ?? 0;

  return {
    title:
      count > 0
        ? `${districtInfo.name} 종량제 봉투 파는곳 ${count}곳 (2026 최신)`
        : `${districtInfo.name} 종량제 봉투 판매처 | 데이터 준비중`,
    description:
      count > 0
        ? `${districtInfo.name}에서 종량제 봉투를 구매할 수 있는 판매처 ${count}곳을 확인하세요. 영업 중인 곳만 제공합니다.`
        : `${districtInfo.name} 종량제 봉투 판매처 정보를 준비하고 있습니다. ${regionInfo.name}의 다른 지역 판매처를 먼저 확인해보세요.`,
    alternates: {
      canonical: `https://bag.fazr.co.kr/${region}/${district}`,
    },
  };
}

export default async function DistrictPage({ params }: PageProps) {
  const { region, district } = await params;
  const regionInfo = getRegionBySlug(region);
  const districtInfo = getDistrictBySlug(region, district);
  if (!regionInfo || !districtInfo) notFound();

  const data = getDistrictData(region, district);

  // 인접 지역: 같은 region의 다른 district (데이터 있는 곳)
  const regionIndex = getRegionIndex(region);
  const adjacentDistricts = (regionIndex?.districts ?? [])
    .filter((d) => d.districtSlug !== district && d.count > 0)
    .slice(0, 6);

  // 판매처 0개 → 안내 페이지 (soft 404 방지: 콘텐츠 + 링크 + FAQ 포함)
  if (!data || data.totalCount === 0) {
    const emptyFaqs = [
      {
        question: `${districtInfo.name} 종량제 봉투 어디서 사나요?`,
        answer: `${districtInfo.name}의 종량제 봉투 판매처 데이터를 현재 수집 중입니다. 일반적으로 편의점(GS25, CU, 세븐일레븐), 대형마트, 동네 슈퍼마켓에서 구매할 수 있습니다.`,
      },
      {
        question: `종량제 봉투가 품귀인 이유는?`,
        answer: `2026년 3월 기준 중동 정세 불안으로 나프타 수급에 차질이 생기면서 종량제 봉투 원료 공급이 불안정해졌습니다.`,
      },
    ];

    return (
      <>
        <Breadcrumb
          items={[
            { label: regionInfo.name, href: `/${region}` },
            { label: districtInfo.name },
          ]}
        />

        <section className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">
            {districtInfo.name} 종량제 봉투 판매처
          </h1>
          <p className="mt-1 text-gray-600">
            {regionInfo.name} {districtInfo.name} 종량제 봉투 판매처 정보
          </p>
        </section>

        <div className="rounded-lg border border-blue-200 bg-blue-50 p-6">
          <p className="text-lg font-medium text-blue-800">
            {districtInfo.name} 판매처 데이터를 준비하고 있습니다
          </p>
          <p className="mt-2 text-sm text-blue-600">
            공공데이터포털에서 {districtInfo.name} 지역의 종량제 봉투 판매처
            정보를 수집 중입니다. 곧 업데이트될 예정이며, 아래 인근 지역
            판매처를 먼저 확인해보세요.
          </p>
          <p className="mt-3 text-sm text-blue-600">
            종량제 봉투는 보통 편의점, 마트, 슈퍼마켓에서 구매할 수 있습니다.
            가까운 편의점을 방문해보시기 바랍니다.
          </p>
        </div>

        {adjacentDistricts.length > 0 && (
          <section className="mt-8">
            <h2 className="mb-3 text-lg font-bold text-gray-900">
              {regionInfo.name} 인근 지역 판매처
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {adjacentDistricts.map((d) => (
                <Link
                  key={d.districtSlug}
                  href={`/${region}/${d.districtSlug}`}
                  className="flex flex-col items-center rounded-lg border border-gray-200 bg-white p-4 text-center transition hover:border-blue-300 hover:shadow-sm"
                >
                  <span className="font-medium text-gray-900">
                    {d.district}
                  </span>
                  <span className="mt-1 text-sm text-gray-500">
                    {d.count}곳
                  </span>
                </Link>
              ))}
            </div>
          </section>
        )}

        <FaqSection faqs={emptyFaqs} />

        <div className="mt-6 text-center">
          <Link
            href={`/${region}`}
            className="inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            {regionInfo.name} 전체 보기
          </Link>
        </div>
      </>
    );
  }

  const faqs = getDistrictFaqs(
    regionInfo.name,
    districtInfo.name,
    data.totalCount
  );

  return (
    <>
      <Breadcrumb
        items={[
          { label: regionInfo.name, href: `/${region}` },
          { label: districtInfo.name },
        ]}
      />

      <section className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {districtInfo.name} 종량제 봉투 판매처
        </h1>
        <p className="mt-1 text-gray-600">
          총 {data.totalCount}곳 · 데이터 갱신일: {data.updatedAt}
        </p>
      </section>

      <StoreList stores={data.stores} />

      {data.totalCount < 3 && adjacentDistricts.length > 0 && (
        <section className="mt-6 rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <p className="font-medium text-yellow-800">
            인근 지역 판매처도 확인해보세요
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {adjacentDistricts.map((d) => (
              <a
                key={d.districtSlug}
                href={`/${region}/${d.districtSlug}`}
                className="rounded-full border border-yellow-300 px-3 py-1 text-sm text-yellow-700 hover:bg-yellow-100"
              >
                {d.district} ({d.count}곳)
              </a>
            ))}
          </div>
        </section>
      )}

      <FaqSection faqs={faqs} />

      {adjacentDistricts.length > 0 && (
        <section className="mt-10">
          <h2 className="mb-3 text-lg font-bold text-gray-900">
            {regionInfo.name} 다른 지역 판매처
          </h2>
          <div className="flex flex-wrap gap-2">
            {adjacentDistricts.map((d) => (
              <a
                key={d.districtSlug}
                href={`/${region}/${d.districtSlug}`}
                className="rounded-full border border-gray-200 px-3 py-1 text-sm text-gray-600 hover:border-blue-300 hover:text-blue-600"
              >
                {d.district} ({d.count}곳)
              </a>
            ))}
          </div>
        </section>
      )}
    </>
  );
}
