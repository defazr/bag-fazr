import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { getDistrictData, getRegionIndex } from "@/lib/data";
import {
  getRegionBySlug,
  getDistrictBySlug,
  getDistrictsByRegion,
  getDistrictDisplayName,
  getLegacyDisplay,
  getRegionDisplay,
  REGIONS,
} from "@/lib/regions";
import { buildOpenGraph, getDistrictFaqs } from "@/lib/seo";
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

  // 2026 통합으로 폐지된 시도명 대신 현재 행정명을 쓴다. 구·군 이름 자체는
  // 그대로 유효하므로 district의 title/H1은 손대지 않는다.
  const regionLabel = getRegionDisplay(region)?.currentLabel ?? regionInfo.name;

  // 이름이 겹치는 구군(중구/동구/서구/남구/북구/강서구/고성군)만 시/도 축약명을 붙인다.
  // 2026 행정구역 개편으로 표시명이 달라진 legacy bucket은 그 값을 우선한다.
  const legacy = getLegacyDisplay(region, district);
  const displayName = legacy
    ? legacy.longLabel
    : getDistrictDisplayName(region, districtInfo.name);

  return {
    title:
      // 개편 페이지는 label 자체가 길어서 공통 suffix(가격·크기·2026)를 뺀다.
      // 정확한 행정명 전달이 title 패턴 통일보다 우선이다.
      legacy
        ? count > 0
          ? `${displayName} 종량제 봉투 파는곳 총정리`
          : `${displayName} 종량제 봉투 판매처 안내`
        : count > 0
        ? `${displayName} 종량제 봉투 파는곳 총정리 | 가격 | 크기 (2026)`
        : `${displayName} 종량제 봉투 판매처 안내`,
    description:
      count > 0
        ? `${displayName} 종량제 봉투 판매처 ${count}곳. 가격, 크기, 편의점 구매 가능 여부까지. 공공데이터를 바탕으로 정리했습니다.`
        : `${displayName} 종량제 봉투 판매처 정보가 없습니다. ${regionLabel}의 다른 지역 판매처를 확인해보세요.`,
    alternates: {
      canonical: `https://bag.fazr.co.kr/${region}/${district}`,
    },
    openGraph: buildOpenGraph(
      `${displayName} 종량제 봉투 판매처 찾기`,
      count > 0
        ? `${displayName} 종량제 봉투 판매처 ${count}곳 목록`
        : `${displayName} 종량제 봉투 판매처 정보 없음`,
      `/${region}/${district}`
    ),
  };
}

export default async function DistrictPage({ params }: PageProps) {
  const { region, district } = await params;
  const regionInfo = getRegionBySlug(region);
  const districtInfo = getDistrictBySlug(region, district);
  if (!regionInfo || !districtInfo) notFound();

  // title/H1/FAQ가 같은 표시명을 쓰도록 한 곳에서 만든다.
  const legacy = getLegacyDisplay(region, district);
  const displayName = legacy
    ? legacy.longLabel
    : getDistrictDisplayName(region, districtInfo.name);
  // breadcrumb 상위 노드·내부링크 anchor·섹션 제목·FAQ 답변에 쓰는 시도명.
  // 폐지된 시도명(광주광역시/전라남도)을 현재형으로 쓰지 않기 위한 것이고,
  // 여기서 옛 이름까지 병기하면 한 페이지에서 같은 설명이 여러 번 반복된다.
  const regionLabel = getRegionDisplay(region)?.currentLabel ?? regionInfo.name;
  // breadcrumb은 시도가 앞에 오므로 축약형을 쓴다.
  const crumbLabel = legacy ? legacy.shortLabel : districtInfo.name;
  // FAQ 답변·본문에서 "이 페이지가 다루는 범위"를 가리킬 때 쓴다.
  // longLabel을 답변에 넣으면 제물포구 전체 + 영종구 전체의 합으로 읽힌다.
  const scopeName = legacy ? legacy.scopeLabel : districtInfo.name;
  // 인접 지역 링크 chip: 개편된 구는 현재 행정구역명으로 보여준다.
  // chip은 좁아서 옛 이름 병기는 넣지 않는다. 목적지 페이지가 설명한다.
  const chipLabel = (slug: string, fallback: string) =>
    getLegacyDisplay(region, slug)?.selectorMain ?? fallback;

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
        question: `${displayName} 종량제 봉투 어디서 사나요?`,
        answer: `${scopeName}의 종량제 봉투 판매처 데이터를 현재 수집 중입니다. 일반적으로 편의점(GS25, CU, 세븐일레븐), 대형마트, 동네 슈퍼마켓에서 구매할 수 있습니다.`,
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
            { label: regionLabel, href: `/${region}` },
            { label: crumbLabel },
          ]}
        />

        <section className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {displayName} 종량제 봉투 판매처
          </h1>
          <p className="mt-1 text-gray-600 dark:text-zinc-400">
            {legacy ? scopeName : `${regionLabel} ${scopeName}`} 종량제 봉투 판매처 정보
          </p>
        </section>

        {/* 데이터 없음 안내 + 구매 가능 장소 (통합) */}
        <div className="rounded-xl border border-yellow-200 dark:border-yellow-500/30 bg-yellow-50 dark:bg-yellow-500/10 p-5">
          <p className="text-lg font-semibold text-yellow-800 dark:text-yellow-200">
            {scopeName}에 등록된 판매처가 없습니다
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
              {regionLabel} 인근 지역 판매처
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {adjacentDistricts.map((d) => (
                <Link
                  key={d.districtSlug}
                  href={`/${region}/${d.districtSlug}`}
                  className="flex flex-col items-center rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 text-center transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
                >
                  <span className="font-medium text-gray-900 dark:text-white">
                    {chipLabel(d.districtSlug, d.district)}
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
              인근 {chipLabel(adjacentDistricts[0].districtSlug, adjacentDistricts[0].district)} 판매처 보기
            </Link>
          )}
          <Link
            href={`/${region}`}
            className="inline-block rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-white hover:bg-gray-50 dark:hover:bg-zinc-700"
          >
            {regionLabel} 전체 보기
          </Link>
        </div>
      </>
    );
  }

  const baseFaqs = getDistrictFaqs(
    legacy ? "" : regionLabel,
    scopeName,
    data.totalCount,
    displayName
  );

  const suwonExtraFaqs =
    region === "gyeonggi" && district === "suwon"
      ? [
          {
            question:
              "수원에서 종량제 봉투를 가장 쉽게 살 수 있는 곳은 어디인가요?",
            answer:
              "거주하시는 구의 편의점(CU, GS25, 세븐일레븐, 이마트24)이 접근성이 가장 좋습니다. 편의점에서 품절일 경우 동네 슈퍼나 마트를 확인해보시는 것이 좋습니다.",
          },
          {
            question:
              "수원시 4개 구 중 어느 구의 봉투를 사용해야 하나요?",
            answer:
              "수원시는 4개 구가 같은 시 안에 있으므로 일반적으로 수원시 종량제 봉투를 사용합니다. 다만 봉투 종류와 사용 가능 여부는 품목이나 배출 방식에 따라 달라질 수 있어, 정확한 내용은 수원시청 또는 판매처 안내를 확인하는 것이 좋습니다.",
          },
          {
            question:
              "수원에서 50L, 100L 같은 대용량 봉투는 어디서 살 수 있나요?",
            answer:
              "대용량 봉투는 편의점보다 대형마트(이마트, 홈플러스, 롯데마트)나 동네 마트에서 확인하시는 것이 좋습니다. 사이즈별 재고는 매장마다 다를 수 있으니 방문 전 확인을 권장합니다.",
          },
        ]
      : [];

  const faqs = [...baseFaqs, ...suwonExtraFaqs];

  return (
    <>
      <Breadcrumb
        items={[
          { label: regionLabel, href: `/${region}` },
          { label: crumbLabel },
        ]}
      />

      <section className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {displayName} 종량제 봉투 파는곳
        </h1>
        <p className="mt-1 text-gray-600 dark:text-zinc-400">
          총 {data.totalCount}곳 · 데이터 수집일: {data.updatedAt}
        </p>
        <p className="mt-2 text-xs text-gray-400 dark:text-zinc-500">
          지역별 판매처 수는 공공데이터 기준이며, 일부 지역은 실제와 차이가 있을 수 있습니다.
        </p>
        {legacy && (
          <p className="mt-2 text-xs text-gray-500 dark:text-zinc-400 leading-relaxed">
            {legacy.notice}
          </p>
        )}
        <p className="mt-3 text-sm text-gray-500 dark:text-zinc-400 leading-relaxed">
          종량제 봉투는 지역별 가격과 크기가 다르며, 편의점과 마트에서도 구매할
          수 있습니다. 아래에서 {scopeName} 종량제 봉투 판매처를
          확인하세요.
        </p>
      </section>

      {region === "gyeonggi" && district === "suwon" && (
        <div className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 mb-6">
          <p className="text-sm text-gray-600 dark:text-zinc-400 leading-relaxed">
            <strong className="text-gray-900 dark:text-white">수원시 종량제 봉투 판매처 안내</strong>
          </p>
          <p className="mt-2 text-sm text-gray-600 dark:text-zinc-400 leading-relaxed">
            수원시는 장안구, 권선구, 영통구, 팔달구로 나뉘어 있습니다. 아래 매장
            목록에서 거주 지역과 가까운 판매처를 확인하시고, 매장에 직접 문의 후
            방문하시는 것을 권장합니다.
          </p>
          <p className="mt-2 text-sm text-gray-600 dark:text-zinc-400 leading-relaxed">
            편의점(CU, GS25, 세븐일레븐, 이마트24)은 가까운 곳에서 빠르게
            구매하기 좋고, 마트(이마트, 홈플러스, 롯데마트)는 다양한 사이즈를 한
            번에 확인할 수 있습니다.
          </p>
        </div>
      )}

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
                {chipLabel(d.districtSlug, d.district)} ({d.count}곳)
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

      {region === "gyeonggi" && district === "suwon" && (
        <section className="mt-10">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            수원시 구별로 찾는 법
          </h2>
          <div className="mt-3 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
            <ul className="space-y-2.5 text-sm text-gray-600 dark:text-zinc-400 leading-relaxed">
              <li>
                <strong className="text-gray-900 dark:text-white">장안구</strong>
                <span className="ml-1">— 율전동, 정자동, 영화동 일대. 거주 지역 가까운 편의점과 동네 슈퍼를 먼저 확인해보시는 것이 좋습니다.</span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">권선구</strong>
                <span className="ml-1">— 권선동, 세류동, 호매실동 일대. 마트와 동네 슈퍼를 함께 확인해보는 것을 권장합니다.</span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">영통구</strong>
                <span className="ml-1">— 영통동, 매탄동, 망포동 일대. 대형마트 접근성이 좋은 편입니다.</span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">팔달구</strong>
                <span className="ml-1">— 우만동, 인계동, 화서동 일대. 구도심으로 동네 슈퍼와 편의점이 함께 분포되어 있습니다.</span>
              </li>
            </ul>
          </div>

          <h2 className="mt-8 text-lg font-bold text-gray-900 dark:text-white">
            매장 유형별 구매 팁
          </h2>
          <div className="mt-3 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
            <ul className="space-y-2.5 text-sm text-gray-600 dark:text-zinc-400 leading-relaxed">
              <li>
                <strong className="text-gray-900 dark:text-white">편의점 (CU, GS25, 세븐일레븐, 이마트24)</strong>
                <span className="ml-1">— 24시간 운영으로 접근성이 가장 좋습니다. 다만 인기 사이즈는 빠르게 소진될 수 있어 미리 확인 후 방문하는 것이 좋습니다.</span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">대형마트 (이마트, 홈플러스, 롯데마트)</strong>
                <span className="ml-1">— 다양한 사이즈를 한 번에 확인할 수 있습니다. 영통구와 권선구 일대에서는 대형마트와 마트를 함께 확인해보는 것이 좋습니다.</span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">동네 슈퍼/마트</strong>
                <span className="ml-1">— 편의점보다 재고가 오래 유지되는 경우가 많습니다. 편의점에서 품절일 때 가장 확실한 대안입니다.</span>
              </li>
            </ul>
          </div>
        </section>
      )}

      {/* 종량제 봉투 안내 콘텐츠 블록 */}
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900 dark:text-white">
          {scopeName} 종량제 봉투 안내
        </h2>
        <div className="space-y-3 text-sm text-gray-600 dark:text-zinc-400 leading-relaxed">
          <p>
            종량제 봉투 가격은 지자체마다 다르게 책정됩니다.{" "}
            {scopeName} 기준 일반 가정용 20L 봉투는 약 500~1,000원
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
            href={
              region === "gyeonggi" && district === "suwon"
                ? "/article/where-to-buy"
                : `/${region}`
            }
            className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 text-sm text-gray-700 dark:text-zinc-300 transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
          >
            {region === "gyeonggi" && district === "suwon"
              ? "쓰레기봉투 파는곳 총정리 →"
              : `${regionLabel} 종량제 봉투 가격 안내 →`}
          </Link>
          <Link
            href={`/${region}`}
            className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 text-sm text-gray-700 dark:text-zinc-300 transition hover:bg-gray-50 dark:hover:bg-zinc-800 duration-200"
          >
            {regionLabel} 종량제 봉투 크기별 판매처 →
          </Link>
        </div>
      </section>

      {/* 인접 지역 */}
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold text-gray-900 dark:text-white">
          {regionLabel} 다른 지역 판매처
        </h2>
        {adjacentDistricts.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {adjacentDistricts.map((d) => (
              <Link
                key={d.districtSlug}
                href={`/${region}/${d.districtSlug}`}
                className="rounded-full border border-gray-200 dark:border-zinc-800 px-3 py-1 text-sm text-gray-600 dark:text-zinc-400 hover:bg-gray-50 dark:hover:bg-zinc-800 transition duration-200"
              >
                {chipLabel(d.districtSlug, d.district)} ({d.count}곳)
              </Link>
            ))}
          </div>
        )}
        <div className="mt-4">
          <Link
            href={`/${region}`}
            className="inline-block text-sm text-gray-600 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white transition"
          >
            {regionLabel} 전체 판매처 보기 →
          </Link>
        </div>
      </section>

      {/* 신뢰 시그널 */}
      <div className="mt-10 mb-20 sm:mb-0 rounded-xl bg-gray-50 dark:bg-zinc-900 px-5 py-3 text-xs text-gray-400 dark:text-zinc-500">
        <p>
          데이터 출처: 공공데이터포털 (행정안전부 자원환경
          쓰레기종량제봉투판매업) · 데이터 수집일: {data.updatedAt} ·
          공공데이터 기준 판매처 정보
        </p>
      </div>

      {/* 광고: 하단 */}
      <AdSlot slotId="6518541657" className="mt-8" />
    </>
  );
}
