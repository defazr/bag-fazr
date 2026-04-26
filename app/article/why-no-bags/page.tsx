import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumb from "@/components/seo/Breadcrumb";
import FaqSection from "@/components/seo/FaqSection";
import RegionLinks from "@/components/article/RegionLinks";

export const metadata: Metadata = {
  title: "종량제 봉투 요즘 왜 없을까? 직접 확인해봤습니다 (2026)",
  description:
    "편의점마다 종량제 봉투가 없어서 직접 찾아봤습니다. 왜 이런 상황이 됐는지, 어디서 살 수 있는지 정리했습니다.",
  alternates: {
    canonical: "https://bag.fazr.co.kr/article/why-no-bags",
  },
  openGraph: {
    title: "종량제 봉투 요즘 왜 없을까?",
    description: "직접 돌아다녀보고 정리한 종량제 봉투 구매 가이드",
  },
};

export default function WhyNoBagsPage() {
  const faqs = [
    {
      question: "종량제 봉투 품절이 언제까지 이어지나요?",
      answer:
        "원자재 수급과 중동 정세에 따라 달라지지만, 업계에서는 2026년 하반기 이후 점진적 안정화를 기대하고 있습니다.",
    },
    {
      question: "동네 슈퍼에서도 종량제 봉투를 살 수 있나요?",
      answer:
        "네, 동네 슈퍼마켓은 편의점보다 수요가 적어서 재고가 남아있는 경우가 많습니다. 가까운 슈퍼를 먼저 확인해보세요.",
    },
    {
      question: "종량제 봉투를 온라인으로 살 수 있나요?",
      answer:
        "종량제 봉투는 지자체에서 지정한 오프라인 판매처에서만 정식 판매됩니다. 중고 거래 플랫폼의 웃돈 거래는 권장하지 않습니다.",
    },
    {
      question: "우리 동네 판매처는 어디서 확인할 수 있나요?",
      answer:
        "전국 69,000곳 이상의 종량제 봉투 판매처를 지역별로 정리해두었습니다. 홈페이지에서 지역을 선택하면 바로 확인할 수 있습니다.",
    },
  ];

  return (
    <>
      <Breadcrumb items={[{ label: "종량제 봉투 요즘 왜 없을까?" }]} />

      <article>
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white leading-tight">
            종량제 봉투 요즘 왜 없을까? 직접 확인해봤습니다
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-zinc-500">
            2026년 3월 기준
          </p>
        </header>

        <div className="space-y-6 text-[15px] text-gray-700 dark:text-zinc-300 leading-relaxed">
          {/* 1. 공감 도입 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              쓰레기 버리는 날인데 봉투가 없습니다
            </h2>
            <p>
              얼마 전 쓰레기를 버리려는데 종량제 봉투가 딱 떨어졌습니다. 별생각 없이
              집 앞 편의점에 갔더니 &ldquo;품절&rdquo;이라는 안내문만 붙어있더군요.
              옆 편의점도 마찬가지, 마트까지 걸어갔는데 거기도 없었습니다.
            </p>
            <p className="mt-3">
              결국 봉투 하나 사려고 동네를 30분 넘게 돌아다녔습니다. 예전에는 아무
              편의점에서나 1분이면 살 수 있었던 건데, 대체 무슨 일이 생긴 걸까요?
            </p>
          </section>

          {/* 2. 문제 확대 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              물어보니 다들 같은 상황이었습니다
            </h2>
            <p>
              처음에는 우리 동네만 그런 줄 알았습니다. 그런데 주변 사람들한테 물어보니
              다들 비슷한 경험을 하고 있었습니다. &ldquo;나도 3일째 찾고 있어&rdquo;,
              &ldquo;마트에서도 없다더라&rdquo;라는 이야기가 계속 나왔습니다.
            </p>
            <p className="mt-3">
              동네 카페에도 &ldquo;종량제 봉투 어디서 사요?&rdquo;라는 글이 매일
              올라옵니다. 서울뿐만 아니라 경기, 부산, 대구 어디나 마찬가지라고 합니다.
              이건 단순히 재고가 부족한 수준이 아니라, 전국적인 현상인 겁니다.
            </p>
          </section>

          {/* 3. 원인 설명 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              알고 보니 원인이 여러 가지였습니다
            </h2>
            <p>
              &ldquo;왜 갑자기?&rdquo;라는 궁금증에 찾아봤는데, 원인이 한 가지가
              아니었습니다.
            </p>
            <p className="mt-3">
              가장 큰 원인은 <strong className="text-gray-900 dark:text-white">나프타 수급 문제</strong>였습니다.
              종량제 봉투는 폴리에틸렌이라는 플라스틱으로 만드는데, 이 원료가 나프타에서
              나옵니다. 올해 초 중동 정세가 불안해지면서 나프타 수입에 차질이 생겼고,
              봉투 생산 자체가 줄어든 겁니다.
            </p>
            <p className="mt-3">
              여기에 <strong className="text-gray-900 dark:text-white">사재기</strong>가
              겹쳤습니다. &ldquo;봉투가 없다더라&rdquo;는 소문이 돌면서 한 번에
              5~10묶음씩 사가는 사람들이 생겼고, 그러면 그다음 사람은 못 사는 악순환이
              반복됩니다. 거기에 물류 비용까지 올라서, 만들어진 봉투가 판매처에 도착하는
              시간도 길어졌습니다.
            </p>
            <p className="mt-3">
              정리하면 — 생산은 줄었는데, 수요는 늘었고, 배송은 느려진 겁니다. 삼중으로
              겹치니 이렇게 된 거죠.
            </p>
          </section>

          {/* 4. 해결 방향 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              무작정 찾아다니면 시간만 낭비됩니다
            </h2>
            <p>
              제가 30분 동안 돌아다닌 것처럼, 그냥 아무 데나 가보는 건 비효율적입니다.
              없는 곳은 가봤자 없습니다. 중요한 건 &ldquo;어디에 아직 재고가 있을 수
              있는지&rdquo;를 먼저 파악하는 겁니다.
            </p>
            <p className="mt-3">
              저도 나중에야 알았는데, 전국 판매처를 지역별로 정리해둔 데이터가
              있었습니다.{" "}
              <Link href="/seoul" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">서울</Link>,{" "}
              <Link href="/gyeonggi" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">경기</Link>,{" "}
              <Link href="/busan" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">부산</Link>{" "}
              등 주요 지역은 바로 확인 가능합니다. 미리 확인했으면 헛걸음 안 했을 텐데 하는 생각이 들더라고요.
            </p>
            <p className="mt-3">
              전국 판매처를 한눈에 확인하려면{" "}
              <Link href="/article/where-to-buy" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">쓰레기봉투 파는곳 총정리</Link>
              를 함께 보시면 도움이 됩니다.
            </p>
          </section>

          {/* 5. CTA 중간 */}
          <div className="rounded-xl border border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 p-6 text-center shadow-sm">
            <p className="font-bold text-gray-900 dark:text-white">
              종량제 봉투 판매처, 미리 확인하세요
            </p>
            <p className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
              내 주변 판매처를 미리 확인하고 가면 시간을 아낄 수 있습니다
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
              직접 돌아다녀보고 느낀 것들
            </h2>
            <p>
              여러 곳을 다녀보면서 느낀 건, 같은 동네라도 판매처마다 상황이 완전히
              다르다는 점이었습니다.
            </p>
            <ul className="mt-3 space-y-3">
              <li>
                <strong className="text-gray-900 dark:text-white">편의점</strong>
                <span className="ml-1">
                  — 가장 접근성이 좋지만, 그만큼 가장 먼저 품절됩니다. 입고일 아침에
                  가면 있을 수 있는데, 그 타이밍을 알기가 어렵습니다.
                </span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">대형마트</strong>
                <span className="ml-1">
                  — 한꺼번에 많이 들어오기 때문에 편의점보다는 오래 갑니다. 거리가
                  있어도 한 번에 사올 수 있으니 가성비는 나쁘지 않습니다.
                </span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">동네 슈퍼</strong>
                <span className="ml-1">
                  — 제가 결국 봉투를 산 곳입니다. 사람들이 잘 안 가는 작은 슈퍼에는
                  의외로 재고가 남아있었습니다. 히든 스팟이라고 할 수 있습니다.
                </span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">주민센터</strong>
                <span className="ml-1">
                  — 판매하는 곳이 있고 안 하는 곳이 있습니다. 전화 한 통 해보면 확인
                  가능합니다.
                </span>
              </li>
            </ul>
            <p className="mt-3">
              결론적으로, 편의점만 고집하지 말고 동네 슈퍼나 마트를 같이 봐야 합니다.
              그리고 가기 전에 판매처 위치를 미리 파악해두는 게 진짜 시간을 아끼는
              방법입니다.
            </p>
          </section>

          {/* 전망 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              앞으로는 나아질까?
            </h2>
            <p>
              정부에서 대책을 마련 중이라고는 하지만, 솔직히 당장 내일 해결될
              분위기는 아닙니다. 하반기쯤 되면 좀 나아질 거라는 전망이 있지만,
              그때까지는 &ldquo;미리 확인하고 사는 습관&rdquo;을 들이는 게 가장
              현실적입니다.
            </p>
            <p className="mt-3">
              봉투 하나 때문에 스트레스받는 게 말이 안 되는 것 같지만, 현실이 그렇습니다.
              그나마 다행인 건, 판매처 정보를 미리 알 수 있는 방법이 있다는 겁니다.
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
              <li>→ 나프타 공급 불안 + 사재기 + 물류 지연이 겹쳐서 전국적 품귀 발생</li>
              <li>→ 편의점보다 동네 슈퍼·마트에 재고가 남아있을 확률이 높음</li>
              <li>→ 무작정 찾아다니지 말고, 판매처를 미리 확인하고 가는 게 정답</li>
              <li>→ 하반기 이후 점진적 안정화 기대, 그 전까지는 미리 확인 후 구매</li>
            </ul>
          </section>
        </div>
      </article>

      <FaqSection faqs={faqs} />

      {/* 신뢰 시그널 */}
      <div className="mt-10 rounded-xl bg-gray-50 dark:bg-zinc-900 px-5 py-3 text-xs text-gray-400 dark:text-zinc-500">
        <p>
          판매처 데이터 출처: 공공데이터포털 (행정안전부 자원환경
          쓰레기종량제봉투판매업)
        </p>
      </div>
    </>
  );
}
