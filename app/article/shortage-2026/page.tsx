import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumb from "@/components/seo/Breadcrumb";
import FaqSection from "@/components/seo/FaqSection";

export const metadata: Metadata = {
  title: "종량제 봉투 대란 이유 총정리 (2026 최신)",
  description:
    "2026년 종량제 봉투 품귀 현상의 원인과 대처 방법을 정리했습니다. 나프타 수급 불안, 가격 인상, 구매처 안내까지.",
  alternates: {
    canonical: "https://bag.fazr.co.kr/article/shortage-2026",
  },
};

export default function ShortageArticlePage() {
  const faqs = [
    {
      question: "종량제 봉투 대란은 언제까지 계속되나요?",
      answer:
        "중동 정세와 나프타 수급 상황에 따라 달라질 수 있습니다. 전문가들은 2026년 하반기 이후 안정화를 예상하고 있지만, 정확한 시점은 미정입니다.",
    },
    {
      question: "종량제 봉투를 미리 사두면 되나요?",
      answer:
        "대량 구매는 오히려 품귀를 심화시킬 수 있습니다. 필요한 만큼만 구매하시고, 여러 판매처를 확인해보시기 바랍니다.",
    },
    {
      question: "종량제 봉투 가격이 오르나요?",
      answer:
        "원자재 가격 상승으로 일부 지자체에서 가격 인상을 검토 중입니다. 현재까지 대부분 지역은 기존 가격을 유지하고 있습니다.",
    },
  ];

  return (
    <>
      <Breadcrumb items={[{ label: "종량제 봉투 대란 이유 총정리" }]} />

      <article>
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 leading-tight">
            종량제 봉투 대란 이유 총정리 (2026 최신)
          </h1>
          <p className="mt-2 text-sm text-gray-500">2026년 3월 기준</p>
        </header>

        <div className="space-y-6 text-[15px] text-gray-700 leading-relaxed">
          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">
              왜 종량제 봉투를 못 구하나요?
            </h2>
            <p>
              2026년 들어 전국적으로 종량제 봉투 품귀 현상이 발생하고 있습니다.
              편의점과 마트에서 봉투를 찾기 어렵다는 민원이 급증하면서, 많은
              사람들이 가까운 판매처를 찾고 있습니다.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">
              원인 1: 나프타 수급 불안
            </h2>
            <p>
              종량제 봉투의 원료인 폴리에틸렌(PE)은 나프타에서 만들어집니다.
              2026년 초 중동 정세 불안으로 원유 및 나프타 공급에 차질이 생기면서
              봉투 생산 원가가 크게 상승했습니다. 국내 석유화학 업체들의
              생산량이 줄어들면서 봉투 공급이 수요를 따라가지 못하고 있습니다.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">
              원인 2: 수요 급증
            </h2>
            <p>
              품귀 소식이 전해지면서 사재기 수요까지 겹쳐 상황이 악화되고
              있습니다. 일부 지역에서는 1인당 구매 수량을 제한하는 곳도
              나타나고 있으며, 온라인 중고 거래 플랫폼에서 웃돈을 붙여
              거래되는 사례도 보고되고 있습니다.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">
              원인 3: 물류 지연
            </h2>
            <p>
              원자재 수급 불안에 더해 물류 비용 상승과 배송 지연이 겹치면서,
              생산된 봉투가 판매처까지 도달하는 데 평소보다 시간이 오래
              걸리고 있습니다.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">
              지금 종량제 봉투를 사려면?
            </h2>
            <p>
              가까운 편의점, 마트, 슈퍼마켓에서 구매할 수 있습니다. 한 곳에서
              품절이라면 여러 판매처를 확인해보세요. 아래 링크에서 지역별
              판매처를 바로 찾을 수 있습니다.
            </p>

            <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Link
                href="/seoul/gangnam"
                className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-center text-sm font-medium text-blue-700 hover:bg-blue-100"
              >
                강남구 판매처 찾기
              </Link>
              <Link
                href="/gyeonggi/suwon"
                className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-center text-sm font-medium text-blue-700 hover:bg-blue-100"
              >
                수원시 판매처 찾기
              </Link>
              <Link
                href="/busan/haeundae"
                className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-center text-sm font-medium text-blue-700 hover:bg-blue-100"
              >
                해운대구 판매처 찾기
              </Link>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">
              앞으로 전망은?
            </h2>
            <p>
              정부는 종량제 봉투 원료 확보를 위해 비축유 방출과 대체 원료 도입을
              검토하고 있습니다. 업계에서는 하반기 이후 점진적 안정화를 예상하고
              있지만, 당분간은 재고 확인 후 구매하시는 것을 권장합니다.
            </p>
          </section>
        </div>

        {/* 전국 판매처 찾기 CTA */}
        <div className="mt-10 rounded-lg border border-blue-200 bg-blue-50 p-6 text-center">
          <p className="font-bold text-gray-900">
            가까운 종량제 봉투 판매처를 찾고 계신가요?
          </p>
          <p className="mt-1 text-sm text-gray-600">
            전국 69,000곳 이상의 판매처 정보를 제공합니다
          </p>
          <Link
            href="/"
            className="mt-4 inline-block rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            전국 판매처 찾기 →
          </Link>
        </div>
      </article>

      <FaqSection faqs={faqs} />

      {/* 신뢰 시그널 */}
      <div className="mt-10 rounded-lg bg-gray-50 px-4 py-3 text-xs text-gray-400">
        <p>
          본 콘텐츠는 공개된 뉴스 및 공공데이터를 바탕으로 작성되었습니다.
          판매처 데이터 출처: 공공데이터포털 (행정안전부)
        </p>
      </div>
    </>
  );
}
