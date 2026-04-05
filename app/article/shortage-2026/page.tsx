import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumb from "@/components/seo/Breadcrumb";
import FaqSection from "@/components/seo/FaqSection";
import RegionLinks from "@/components/article/RegionLinks";

export const metadata: Metadata = {
  title: "종량제 봉투 대란 이유 총정리 (2026 최신)",
  description:
    "2026년 종량제 봉투 품귀 현상의 원인과 대처 방법을 정리했습니다. 나프타 수급 불안, 가격 인상, 구매처 안내까지.",
  alternates: {
    canonical: "https://bag.fazr.co.kr/article/shortage-2026",
  },
  openGraph: {
    title: "종량제 봉투 대란 이유 총정리 (2026)",
    description: "왜 봉투를 못 구하는지, 어디서 사야 하는지 정리했습니다",
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
    {
      question: "우리 동네 판매처는 어디서 확인할 수 있나요?",
      answer:
        "전국 69,000곳 이상의 종량제 봉투 판매처를 지역별로 정리해두었습니다. 홈페이지에서 지역을 선택하면 바로 확인할 수 있습니다.",
    },
  ];

  return (
    <>
      <Breadcrumb items={[{ label: "종량제 봉투 대란 이유 총정리" }]} />

      <article>
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white leading-tight">
            종량제 봉투 대란 이유 총정리 (2026 최신)
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-zinc-500">
            2026년 3월 기준
          </p>
        </header>

        <div className="space-y-6 text-[15px] text-gray-700 dark:text-zinc-300 leading-relaxed">
          {/* 1. 공감 도입 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              편의점 3곳을 돌았는데 봉투가 없습니다
            </h2>
            <p>
              쓰레기 버리는 날인데 종량제 봉투가 없습니다. 집 앞 CU에 갔더니
              &ldquo;입고 미정&rdquo;이라는 안내문만 붙어있고, GS25도 마찬가지.
              마트까지 가봤지만 &ldquo;어제 다 나갔어요&rdquo;라는 말만 들었습니다.
            </p>
            <p className="mt-3">
              이게 하루 이틀이 아닙니다. 2026년 들어서 전국적으로 종량제 봉투를 구하기
              어렵다는 이야기가 끊이지 않고 있습니다. 분명 예전에는 아무 편의점에서나
              살 수 있었는데, 요즘은 재고가 있는 곳을 찾는 것 자체가 일이 됐습니다.
            </p>
          </section>

          {/* 2. 문제 확대 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              나만 겪는 문제가 아닙니다
            </h2>
            <p>
              지역 커뮤니티에 &ldquo;종량제 봉투 어디서 사요?&rdquo;라는 글이 하루에
              수십 개씩 올라옵니다. 댓글마다 &ldquo;저도 못 구했어요&rdquo;,
              &ldquo;3일째 찾고 있어요&rdquo;라는 반응이 이어집니다. 일부 지역에서는
              1인당 2묶음까지만 판매하는 곳도 생겼고, 중고 거래 플랫폼에서 봉투가
              웃돈에 거래되는 상황까지 벌어지고 있습니다.
            </p>
            <p className="mt-3">
              서울만의 문제가 아닙니다. 경기, 부산, 대구, 광주 할 것 없이 전국적으로
              같은 현상이 일어나고 있습니다. 분명 어딘가에는 재고가 있을 텐데, 문제는
              &ldquo;어디에&rdquo; 있는지 모른다는 겁니다.
            </p>
          </section>

          {/* 3. 원인 설명 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              원인은 하나가 아닙니다
            </h2>
            <p>
              종량제 봉투 품귀의 원인은 여러 가지가 복합적으로 작용하고 있습니다.
              하나만 해결된다고 바로 나아지기 어려운 구조입니다.
            </p>
            <ul className="mt-3 space-y-3">
              <li>
                <strong className="text-gray-900 dark:text-white">나프타 수급 불안</strong>
                <span className="ml-1">
                  — 종량제 봉투 원료인 폴리에틸렌(PE)은 나프타에서 만들어집니다. 2026년
                  초 중동 정세 불안으로 원유 및 나프타 공급에 차질이 생기면서 봉투 생산
                  원가가 크게 올랐습니다.
                </span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">사재기 수요</strong>
                <span className="ml-1">
                  — &ldquo;봉투가 없다&rdquo;는 소문이 돌면서 평소보다 많이 사두려는
                  수요가 생겼습니다. 한 사람이 5~10묶음씩 사가면 다음 사람은 못 사는
                  구조입니다.
                </span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">물류 지연</strong>
                <span className="ml-1">
                  — 생산량이 줄어든 상태에서 물류 비용까지 올라, 봉투가 만들어져도
                  판매처까지 도달하는 시간이 평소보다 길어지고 있습니다.
                </span>
              </li>
            </ul>
          </section>

          {/* 4. 해결 방향 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              그냥 찾아다니지 마세요. 확인하고 가세요.
            </h2>
            <p>
              솔직히 말해서, 발품 팔아봤자 없는 곳은 없습니다. 편의점 5곳을 돌아도
              결과는 같을 수 있습니다. 중요한 건 &ldquo;아직 재고가 있는 곳&rdquo;을
              먼저 파악하는 겁니다.
            </p>
            <p className="mt-3">
              지금 전국 69,000곳 이상의 종량제 봉투 판매처 정보를 지역별로 정리해둔
              데이터가 있습니다. 내 주변에 어디서 살 수 있는지 먼저 확인한 다음에
              움직이는 게 시간도 아끼고 헛걸음도 줄이는 방법입니다.
            </p>
          </section>

          {/* 5. CTA 중간 */}
          <div className="rounded-xl border border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 p-6 text-center shadow-sm">
            <p className="font-bold text-gray-900 dark:text-white">
              종량제 봉투 판매처, 미리 확인하세요
            </p>
            <p className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
              전국 69,000곳 이상의 판매처를 지역별로 검색할 수 있습니다
            </p>
            <Link
              href="/"
              className="mt-4 inline-block rounded-xl bg-gray-900 dark:bg-zinc-700 px-6 py-2.5 text-sm font-medium text-white hover:bg-gray-800 dark:hover:bg-zinc-600 transition"
            >
              종량제 봉투 판매처 확인하기 →
            </Link>
          </div>

          {/* 6. 현실 팁 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              어디서 사는 게 가장 현실적인가?
            </h2>
            <p>
              같은 동네라도 판매처마다 재고 상황이 다릅니다. 직접 경험을 바탕으로
              정리하면 이렇습니다.
            </p>
            <ul className="mt-3 space-y-3">
              <li>
                <strong className="text-gray-900 dark:text-white">편의점 (CU, GS25, 세븐일레븐)</strong>
                <span className="ml-1">
                  — 접근성은 가장 좋지만, 요즘은 가장 먼저 품절됩니다. 입고 주기가
                  짧아서 아침 일찍 가면 있을 확률이 높습니다.
                </span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">대형마트 (이마트, 홈플러스, 롯데마트)</strong>
                <span className="ml-1">
                  — 한 번에 많은 양이 입고되기 때문에 편의점보다 재고가 오래 유지됩니다.
                  다만 거리가 있을 수 있으니 미리 확인하고 가는 게 좋습니다.
                </span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">동네 슈퍼마켓</strong>
                <span className="ml-1">
                  — 의외의 히든 스팟입니다. 대형 체인점보다 수요가 적어서 재고가 남아있는
                  경우가 많습니다. 집 주변 작은 슈퍼를 먼저 확인해보세요.
                </span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">주민센터</strong>
                <span className="ml-1">
                  — 판매하는 곳도 있고 안 하는 곳도 있습니다. 전화로 미리 확인하면
                  확실합니다.
                </span>
              </li>
            </ul>
          </section>

          {/* 전망 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              언제쯤 나아질까?
            </h2>
            <p>
              정부에서 비축유 방출과 대체 원료 도입을 검토하고 있고, 업계에서는
              하반기 이후 점진적 안정화를 기대하고 있습니다. 하지만 솔직히 당장
              내일 해결될 문제는 아닙니다.
            </p>
            <p className="mt-3">
              그래서 지금 시점에서 가장 현실적인 방법은, 발품을 팔기 전에 판매처
              정보를 먼저 확인하는 겁니다. 어디에 재고가 있을 수 있는지 알고 가는
              것만으로도 상황이 많이 달라집니다.
            </p>
          </section>

          {/* 7. CTA 하단 */}
          <div className="rounded-xl border border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 p-6 text-center shadow-sm">
            <p className="font-bold text-gray-900 dark:text-white">
              종량제 봉투 판매처, 지금 바로 확인하세요
            </p>
            <p className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
              지역을 선택하면 가까운 판매처 목록을 바로 볼 수 있습니다
            </p>
            <Link
              href="/"
              className="mt-4 inline-block rounded-xl bg-gray-900 dark:bg-zinc-700 px-6 py-2.5 text-sm font-medium text-white hover:bg-gray-800 dark:hover:bg-zinc-600 transition"
            >
              종량제 봉투 판매처 확인하기 →
            </Link>
          </div>

          <RegionLinks />

          {/* 8. 정리 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              정리
            </h2>
            <ul className="space-y-1">
              <li>→ 나프타 수급 불안 + 사재기 + 물류 지연이 겹쳐 전국적 품귀 발생</li>
              <li>→ 편의점보다 동네 슈퍼·대형마트에 재고가 남아있을 확률이 높음</li>
              <li>→ 돌아다니기 전에 판매처를 먼저 확인하는 게 가장 현실적인 방법</li>
              <li>→ 하반기 이후 점진적 안정화 예상, 그 전까지는 미리 확인 후 구매 권장</li>
            </ul>
          </section>
        </div>
      </article>

      <FaqSection faqs={faqs} />

      {/* 신뢰 시그널 */}
      <div className="mt-10 rounded-xl bg-gray-50 dark:bg-zinc-900 px-5 py-3 text-xs text-gray-400 dark:text-zinc-500">
        <p>
          본 콘텐츠는 공개된 뉴스 및 공공데이터를 바탕으로 작성되었습니다.
          판매처 데이터 출처: 공공데이터포털 (행정안전부)
        </p>
      </div>
    </>
  );
}
