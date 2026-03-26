import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumb from "@/components/seo/Breadcrumb";

export const metadata: Metadata = {
  title: "종량제 봉투 요즘 왜 없을까? 직접 확인해봤습니다 (2026)",
  description:
    "편의점마다 종량제 봉투가 없어서 직접 찾아봤습니다. 왜 이런 상황이 됐는지, 어디서 살 수 있는지 정리했습니다.",
  alternates: {
    canonical: "https://bag.fazr.co.kr/article/why-no-bags",
  },
};

export default function WhyNoBagsPage() {
  return (
    <>
      <Breadcrumb items={[{ label: "종량제 봉투 요즘 왜 없을까?" }]} />

      <article>
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white leading-tight">
            종량제 봉투 요즘 왜 없을까? 직접 확인해봤습니다
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-zinc-500">2026년 3월 기준</p>
        </header>

        <div className="space-y-5 text-[15px] text-gray-700 dark:text-zinc-400 leading-relaxed">
          <p>
            얼마 전 쓰레기를 버리려는데 종량제 봉투가 없었습니다. 집 앞
            편의점에 갔더니 &ldquo;품절&rdquo;이라고 하더군요. 그래서 옆
            편의점, 마트, 슈퍼까지 돌아봤는데 세 곳 다 없었습니다.
          </p>

          <p>
            주변에 물어보니 저만 그런 게 아니었습니다. 요즘 종량제 봉투
            구하기가 정말 어렵다는 이야기가 여기저기서 들립니다. 도대체 왜
            이런 상황이 된 걸까요?
          </p>

          <h2 className="text-lg font-bold text-gray-900 dark:text-white pt-2">
            원인은 나프타였습니다
          </h2>

          <p>
            종량제 봉투는 폴리에틸렌이라는 소재로 만드는데, 이 원료가
            나프타에서 나옵니다. 올해 초 중동 정세가 불안해지면서 나프타
            수입에 차질이 생겼고, 봉투 생산 자체가 줄어든 겁니다.
          </p>

          <p>
            거기에 &ldquo;봉투가 없다더라&rdquo;는 소문이 돌면서 사재기
            수요까지 겹쳤습니다. 일부 편의점에서는 1인당 2묶음까지만
            판매하고 있다고 합니다.
          </p>

          <h2 className="text-lg font-bold text-gray-900 dark:text-white pt-2">
            그래서 어디서 사야 하나?
          </h2>

          <p>
            한 곳에서 없다고 포기하지 마시고, 여러 곳을 확인해보세요. 의외로
            동네 슈퍼나 작은 마트에는 아직 재고가 남아있는 경우가 많습니다.
          </p>

          <p>
            저도 결국 찾았습니다. 집에서 좀 먼 슈퍼에 가니까 있더라고요.
            요즘은 미리 어디에 있는지 확인하고 가는 게 시간을 아끼는
            방법입니다.
          </p>

          {/* CTA */}
          <div className="rounded-lg border border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-900 p-5">
            <p className="font-bold text-gray-900 dark:text-white">
              종량제 봉투 판매처를 한눈에 찾을 수 있는 곳이 있습니다
            </p>
            <p className="mt-1 text-sm text-gray-600 dark:text-zinc-400">
              전국 69,000곳 이상의 판매처 정보를 지역별로 정리해둔
              사이트입니다. 가까운 곳부터 확인해보세요.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link
                href="/article/shortage-2026"
                className="rounded-md bg-gray-900 dark:bg-zinc-800 dark:border dark:border-zinc-700 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 dark:hover:bg-zinc-700"
              >
                종량제 봉투 대란 이유 보기 →
              </Link>
              <Link
                href="/"
                className="rounded-md border border-gray-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-4 py-2 text-sm font-medium text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-800"
              >
                전국 판매처 찾기 →
              </Link>
            </div>
          </div>

          <h2 className="text-lg font-bold text-gray-900 dark:text-white pt-2">
            앞으로는 어떻게 될까?
          </h2>

          <p>
            정부에서 대책을 마련 중이라고는 하지만, 당장 내일 해결될 문제는
            아닌 것 같습니다. 당분간은 봉투가 남아있을 때 1~2개 정도 여유분을
            사두는 게 현실적인 방법이 아닐까 싶습니다.
          </p>

          <p>
            혹시 종량제 봉투를 찾고 계신 분이 있다면, 아래 지역별 판매처
            정보를 활용해보세요.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Link
              href="/seoul/gangnam"
              className="rounded-lg border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:border-zinc-600"
            >
              강남구 판매처
            </Link>
            <Link
              href="/gyeonggi/suwon"
              className="rounded-lg border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:border-zinc-600"
            >
              수원시 판매처
            </Link>
            <Link
              href="/busan/haeundae"
              className="rounded-lg border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:border-zinc-600"
            >
              해운대구 판매처
            </Link>
          </div>
        </div>
      </article>

      {/* 신뢰 시그널 */}
      <div className="mt-10 rounded-lg bg-gray-50 dark:bg-zinc-900 px-4 py-3 text-xs text-gray-400 dark:text-zinc-500">
        <p>
          판매처 데이터 출처: 공공데이터포털 (행정안전부 자원환경
          쓰레기종량제봉투판매업)
        </p>
      </div>
    </>
  );
}
