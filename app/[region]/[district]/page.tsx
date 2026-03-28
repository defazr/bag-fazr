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
import AdSlot from "@/components/ads/AdSlot";

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
        ? `${districtInfo.name} 종량제 봉투 파는곳 총정리 | 가격 | 크기 (2026)`
        : `${districtInfo.name} 종량제 봉투 판매처 안내`,
    description:
      count > 0
        ? `${districtInfo.name} 종량제 봉투 판매처 ${count}곳. 가격, 크기, 편의점 구매 가능 여부까지. 영업 중인 곳만 제공합니다.`
        : `${districtInfo.name} 종량제 봉투 판매처 정보가 없습니다. ${regionInfo.name}의 다른 지역 판매처를 확인해보세요.`,
    alternates: {
      canonical: `https://bag.fazr.co.kr/${region}/${district}`,
    },
    openGraph: {
      title: `${districtInfo.name} 종량제 봉투 판매처 찾기`,
      description:
        count > 0
          ? `${districtInfo.name} 종량제 봉투 판매처 ${count}곳 목록`
          : `${districtInfo.name} 종량제 봉투 판매처 정보 없음`,
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {districtInfo.name} 종량제 봉투 판매처
          </h1>
          <p className="mt-1 text-gray-600 dark:text-zinc-400">
            {regionInfo.name} {districtInfo.name} 종량제 봉투 판매처 정보
          </p>
        </section>

        {/* 데이터 없음 안내 + 구매 가능 장소 (통합) */}
        <div className="rounded-xl border border-yellow-200 dark:border-yellow-500/30 bg-yellow-50 dark:bg-yellow-500/10 p-5">
          <p className="text-lg font-semibold text-yellow-800 dark:text-yellow-200">
            {districtInfo.name}에 등록된 판매처가 없습니다
          </p>
          <p className="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
            공공데이터 기준이며, 실제로는 아래 장소에서 구매 가능합니다.
          </p>
          <ul className="mt-3 space-y-2 text-sm text-yellow-700 dark:text-yellow-300">
            <li className="flex items-center gap-2"><span className="text-green-500">✔</span>편의점 (CU, GS25, 세븐일레븐)</li>
            <li className="flex items-center gap-2"><span className="text-green-500">✔</span>대형마트 (이마트, 홈플러스, 롯데마트)</li>
            <li className="flex items-center gap-2"><span className="text-green-500">✔</span>동네 슈퍼마켓</li>
            <li className="flex items-center gap-2"><span className="text-green-500">✔</span>주민센터</li>
          </ul>
          <p className="mt-3 text-xs text-yellow-600 dark:text-yellow-400">
            품절 시 여러 곳을 확인해보시기 바랍니다.
          </p>
        </div>

        {adjacentDistricts.length > 0 && (
          <section className="mt-10">
            <h2 className="mb-3 text-lg font-bold text-gray-900 dark:text-white">
              {regionInfo.name} 인근 지역 판매처
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {adjacentDistricts.map((d) => (
                <Link
                  key={d.districtSlug}
                  href={`/${region}/${d.districtSlug}`}
                  className="flex flex-col items-center rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 text-center transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
                >
                  <span className="font-medium text-gray-900 dark:text-white">
                    {d.district}
                  </span>
                  <span className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
                    {d.count}곳
                  </span>
                </Link>
              ))}
            </div>
          </section>
        )}

        <FaqSection faqs={emptyFaqs} />

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          {adjacentDistricts.length > 0 && (
            <Link
              href={`/${region}/${adjacentDistricts[0].districtSlug}`}
              className="inline-block rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-white hover:bg-gray-50 dark:hover:bg-zinc-700"
            >
              인근 {adjacentDistricts[0].district} 판매처 보기
            </Link>
          )}
          <Link
            href={`/${region}`}
            className="inline-block rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-white hover:bg-gray-50 dark:hover:bg-zinc-700"
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {districtInfo.name} 종량제 봉투 파는곳
        </h1>
        <p className="mt-1 text-gray-600 dark:text-zinc-400">
          총 {data.totalCount}곳 · 데이터 갱신일: {data.updatedAt}
        </p>
        <p className="mt-2 text-xs text-gray-400 dark:text-zinc-500">
          지역별 판매처 수는 공공데이터 기준이며, 일부 지역은 실제와 차이가 있을 수 있습니다.
        </p>
        <p className="mt-3 text-sm text-gray-500 dark:text-zinc-400 leading-relaxed">
          종량제 봉투는 지역별 가격과 크기가 다르며, 편의점과 마트에서도 구매할
          수 있습니다. 아래에서 {districtInfo.name} 종량제 봉투 판매처를
          확인하세요.
        </p>
      </section>

      {/* 데이터 안내 (통합) */}
      <div className="rounded-xl border border-yellow-200 dark:border-yellow-500/30 bg-yellow-50 dark:bg-yellow-500/10 p-5 mb-6">
        <div className="flex items-start gap-2">
          <span className="text-yellow-600 dark:text-yellow-400 text-lg">⚠️</span>
          <div className="text-sm text-yellow-800 dark:text-yellow-200">
            <p className="font-semibold mb-1">
              공공데이터 기준이며 일부 정보가 제한될 수 있습니다
            </p>
            <p>
              편의점(CU, GS25, 세븐일레븐), 대형마트, 주민센터에서도 구매 가능합니다.
              품절 시 여러 곳을 확인해보세요.
            </p>
          </div>
        </div>
      </div>

      <StoreList stores={data.stores} />

      {/* 광고: 리스트 아래 */}
      <AdSlot slotId="7831623329" className="mt-6" />

      {data.totalCount < 3 && adjacentDistricts.length > 0 && (
        <section className="mt-10 rounded-xl border border-yellow-200 dark:border-yellow-500/30 bg-yellow-50 dark:bg-yellow-500/10 p-5">
          <p className="font-medium text-yellow-800 dark:text-yellow-200">
            인근 지역 판매처도 확인해보세요
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {adjacentDistricts.map((d) => (
              <Link
                key={d.districtSlug}
                href={`/${region}/${d.districtSlug}`}
                className="rounded-full border border-yellow-300 dark:border-yellow-700 px-3 py-1 text-sm text-yellow-700 dark:text-yellow-300 hover:bg-yellow-100 dark:hover:bg-yellow-900/30"
              >
                {d.district} ({d.count}곳)
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* 다른 지역 보기 버튼 */}
      {adjacentDistricts.length > 0 && (
        <div className="mt-8 text-center">
          <Link
            href={`/${region}`}
            className="inline-block rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-white hover:bg-gray-50 dark:hover:bg-zinc-700"
          >
            가까운 다른 지역 판매처 보기
          </Link>
        </div>
      )}

      {/* 종량제 봉투 안내 콘텐츠 블록 */}
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900 dark:text-white">
          {districtInfo.name} 종량제 봉투 안내
        </h2>
        <div className="space-y-3 text-sm text-gray-600 dark:text-zinc-400 leading-relaxed">
          <p>
            종량제 봉투 가격은 지자체마다 다르게 책정됩니다.{" "}
            {districtInfo.name} 기준 일반 가정용 20L 봉투는 약 500~1,000원
            수준이며, 음식물 쓰레기용은 별도 가격이 적용됩니다.
          </p>
          <p>
            봉투 크기는 5L, 10L, 20L, 50L, 100L 등이 있으며, 1~2인 가구는
            10~20L, 3인 이상 가구는 20~50L을 주로 사용합니다.
          </p>
          <p>
            GS25, CU, 세븐일레븐 등 편의점에서도 종량제 봉투를 구매할 수
            있습니다. 다만 2026년 나프타 수급 불안으로 일부 매장에서는 재고가
            부족할 수 있으니, 여러 곳을 확인해보시기 바랍니다.
          </p>
        </div>
      </section>

      <FaqSection faqs={faqs} />

      {/* 함께 많이 찾는 정보 */}
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900 dark:text-white">
          함께 많이 찾는 정보
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link
            href={`/${region}`}
            className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 text-sm text-gray-700 dark:text-zinc-300 transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
          >
            {regionInfo.name} 종량제 봉투 가격 안내 →
          </Link>
          <Link
            href={`/${region}`}
            className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 text-sm text-gray-700 dark:text-zinc-300 transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
          >
            {regionInfo.name} 종량제 봉투 크기별 판매처 →
          </Link>
        </div>
      </section>

      {/* 인접 지역 */}
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900 dark:text-white">
          {regionInfo.name} 다른 지역 판매처
        </h2>
        {adjacentDistricts.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {adjacentDistricts.map((d) => (
              <Link
                key={d.districtSlug}
                href={`/${region}/${d.districtSlug}`}
                className="rounded-full border border-gray-200 dark:border-zinc-800 px-3 py-1 text-sm text-gray-600 dark:text-zinc-400 hover:bg-gray-50 dark:hover:bg-zinc-800 transition duration-200"
              >
                {d.district} ({d.count}곳)
              </Link>
            ))}
          </div>
        )}
        <div className="mt-4">
          <Link
            href={`/${region}`}
            className="inline-block text-sm text-gray-600 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white transition"
          >
            {regionInfo.name} 전체 판매처 보기 →
          </Link>
        </div>
      </section>

      {/* 신뢰 시그널 */}
      <div className="mt-10 mb-20 sm:mb-0 rounded-xl bg-gray-50 dark:bg-zinc-900 px-5 py-3 text-xs text-gray-400 dark:text-zinc-500">
        <p>
          데이터 출처: 공공데이터포털 (행정안전부 자원환경
          쓰레기종량제봉투판매업) · 갱신일: {data.updatedAt} · 영업 중인
          판매처만 제공
        </p>
      </div>

      {/* 광고: 하단 */}
      <AdSlot slotId="6518541657" className="mt-8" />
    </>
  );
}
